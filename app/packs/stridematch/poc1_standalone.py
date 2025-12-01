#!/usr/bin/env python3
"""
POC 1 - StrideMatch Gait Analysis Standalone Script

This standalone script analyzes running gait from a video file using MediaPipe Pose.
It extracts biomechanical angles, classifies gait type, and measures performance.

Usage:
    python poc1_standalone.py <video_file> [--output annotated_video.mp4] [--mode detailed]

Example:
    python poc1_standalone.py test_running.mp4 --output results.mp4 --mode detailed
"""

import sys
import argparse
from pathlib import Path
import cv2
import numpy as np
from typing import List, Optional
import time

# Add current directory to path for imports
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Import ML modules (handle both relative and absolute imports)
try:
    from ml.pose_estimator import MediaPipePoseEstimator, create_pose_estimator
    from ml.angle_calculator import calculate_biomechanical_angles, aggregate_angles, angles_to_dict
    from ml.gait_classifier import GaitType
    from ml.gait_state_machine import GaitCycleStateMachine, GaitPhase
    from ml.landmark_filter import AdaptiveLandmarkSmoother
except ImportError:
    # Try absolute import from app.packs.stridematch
    from app.packs.stridematch.ml.pose_estimator import MediaPipePoseEstimator, create_pose_estimator
    from app.packs.stridematch.ml.angle_calculator import calculate_biomechanical_angles, aggregate_angles, angles_to_dict
    from app.packs.stridematch.ml.gait_classifier import GaitType
    from app.packs.stridematch.ml.gait_state_machine import GaitCycleStateMachine, GaitPhase
    from app.packs.stridematch.ml.landmark_filter import AdaptiveLandmarkSmoother


class GaitAnalysisResults:
    """Container for analysis results."""

    def __init__(self):
        self.gait_type: Optional[GaitType] = None
        self.confidence: float = 0.0
        self.avg_angles: dict = {}
        self.avg_latency_ms: float = 0.0
        self.frame_count: int = 0
        self.frames_with_detection: int = 0
        self.video_duration_sec: float = 0.0


def draw_dashboard(
    frame: np.ndarray,
    gait_type: str,
    angles: dict,
    latency_ms: float,
    confidence: float,
    frame_number: int,
    total_frames: int,
    gait_phase: str = "unknown"
) -> np.ndarray:
    """
    Draw a dashboard with metrics on the frame.

    Args:
        frame: Video frame
        gait_type: Detected gait type
        angles: Dictionary of joint angles
        latency_ms: Processing latency
        confidence: Classification confidence
        frame_number: Current frame number
        total_frames: Total number of frames
        gait_phase: Current gait cycle phase (swing/contact/stance/toe_off)

    Returns:
        Frame with dashboard overlay
    """
    # Create a semi-transparent overlay
    overlay = frame.copy()
    height, width = frame.shape[:2]

    # Dashboard background (top of frame) - slightly taller for phase
    dashboard_height = 210
    cv2.rectangle(overlay, (0, 0), (width, dashboard_height), (0, 0, 0), -1)

    # Blend with original frame
    alpha = 0.7
    frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

    # Text settings
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.6
    color = (255, 255, 255)
    thickness = 2
    line_height = 30

    # Progress
    progress_text = f"Frame: {frame_number}/{total_frames}"
    cv2.putText(frame, progress_text, (10, 25), font, font_scale, color, thickness)

    # Latency (color-coded: green if <150ms, yellow if <200ms, red otherwise)
    latency_color = (0, 255, 0) if latency_ms < 150 else (0, 255, 255) if latency_ms < 200 else (0, 0, 255)
    latency_text = f"Latency: {latency_ms:.1f} ms"
    cv2.putText(frame, latency_text, (10, 55), font, font_scale, latency_color, thickness)

    # Gait Phase (color-coded by phase)
    phase_colors = {
        "swing": (200, 200, 200),      # Gray
        "contact": (0, 0, 255),         # Red (critical moment!)
        "stance": (0, 255, 0),          # Green
        "toe_off": (255, 255, 0),       # Yellow
        "unknown": (128, 128, 128)
    }
    phase_color = phase_colors.get(gait_phase, (128, 128, 128))
    phase_text = f"Phase: {gait_phase.upper()}"
    cv2.putText(frame, phase_text, (10, 85), font, font_scale, phase_color, thickness)

    # Gait type
    gait_text = f"Gait: {gait_type}"
    cv2.putText(frame, gait_text, (10, 115), font, font_scale, (0, 255, 255), thickness)

    # Confidence
    confidence_text = f"Conf: {confidence:.1f}%"
    cv2.putText(frame, confidence_text, (10, 145), font, font_scale, color, thickness)

    # Angles
    y_offset = 175
    if "knee_right" in angles:
        angle_text = f"Knee: {angles['knee_right']:.1f}deg"
        cv2.putText(frame, angle_text, (10, y_offset), font, 0.5, color, 1)

    if "ankle_right" in angles:
        angle_text = f"Ankle: {angles['ankle_right']:.1f}deg"
        cv2.putText(frame, angle_text, (200, y_offset), font, 0.5, color, 1)

    if "hip_right" in angles:
        angle_text = f"Hip: {angles['hip_right']:.1f}deg"
        cv2.putText(frame, angle_text, (390, y_offset), font, 0.5, color, 1)

    return frame


def analyze_video(
    video_path: str,
    output_path: Optional[str] = None,
    mode: str = "quick",
    display_realtime: bool = True
) -> GaitAnalysisResults:
    """
    Analyze a running video for gait patterns.

    Args:
        video_path: Path to input video file
        output_path: Path to save annotated video (optional)
        mode: Analysis mode (quick, detailed, professional)
        display_realtime: Whether to display video in real-time

    Returns:
        GaitAnalysisResults object with analysis results
    """
    print(f"\n{'='*60}")
    print(f"StrideMatch - POC 1: Gait Analysis")
    print(f"{'='*60}")
    print(f"Video: {video_path}")
    print(f"Mode: {mode}")
    print(f"{'='*60}\n")

    # Open video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Failed to open video file: {video_path}")

    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration_sec = total_frames / fps if fps > 0 else 0

    print(f"Video properties:")
    print(f"  Resolution: {width}x{height}")
    print(f"  FPS: {fps:.2f}")
    print(f"  Duration: {duration_sec:.2f}s")
    print(f"  Total frames: {total_frames}\n")

    # Initialize video writer if output requested
    video_writer = None
    if output_path:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    # Initialize pose estimator and state machine
    pose_estimator = create_pose_estimator(mode=mode)
    state_machine = GaitCycleStateMachine(side="right", fps=fps)
    landmark_smoother = AdaptiveLandmarkSmoother()

    # Storage for results
    latencies = []
    angle_history = []
    current_gait_type = GaitType.UNKNOWN
    current_confidence = 0.0
    current_phase = GaitPhase.SWING

    frame_number = 0
    frames_with_detection = 0

    print("Processing video with State Machine...\n")

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame_number += 1

            # Process frame
            result = pose_estimator.process_frame(frame, frame_number)
            latencies.append(result.latency_ms)

            # Track current frame data
            current_angles = {}

            if result.detected and result.landmarks:
                frames_with_detection += 1

                # Apply smoothing to landmarks
                smoothed_landmarks = landmark_smoother.smooth_all(result.landmarks)

                # Calculate angles
                angles = calculate_biomechanical_angles(
                    smoothed_landmarks,
                    image_width=width,
                    image_height=height,
                    side="right"
                )
                angle_history.append(angles)
                current_angles = angles_to_dict(angles)

                # Update State Machine
                phase, classification = state_machine.update(
                    landmarks=smoothed_landmarks,
                    frame_number=frame_number,
                    image_width=width,
                    image_height=height
                )

                # Update current phase
                current_phase = phase

                # Update classification if we got a new one (at CONTACT)
                if classification:
                    current_gait_type = classification.gait_type
                    current_confidence = classification.confidence

                # Draw skeleton on frame
                frame = pose_estimator.draw_landmarks(
                    frame,
                    result.landmarks,
                    width,
                    height
                )

            # Draw dashboard
            frame = draw_dashboard(
                frame,
                gait_type=current_gait_type.value if current_gait_type else "unknown",
                angles=current_angles,
                latency_ms=result.latency_ms,
                confidence=current_confidence,
                frame_number=frame_number,
                total_frames=total_frames,
                gait_phase=current_phase.value if hasattr(current_phase, 'value') else "unknown"
            )

            # Write to output video
            if video_writer:
                video_writer.write(frame)

            # Display in real-time
            if display_realtime:
                cv2.imshow('StrideMatch - Gait Analysis POC', frame)

                # Press 'q' to quit
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("\nAnalysis interrupted by user.")
                    break

            # Progress indicator (every 30 frames)
            if frame_number % 30 == 0:
                progress = (frame_number / total_frames) * 100
                print(f"Progress: {progress:.1f}% ({frame_number}/{total_frames} frames)")

    finally:
        # Cleanup
        cap.release()
        if video_writer:
            video_writer.release()
        if display_realtime:
            cv2.destroyAllWindows()
        pose_estimator.close()

    # Aggregate results
    results = GaitAnalysisResults()
    results.frame_count = frame_number
    results.frames_with_detection = frames_with_detection
    results.video_duration_sec = duration_sec
    results.avg_latency_ms = np.mean(latencies) if latencies else 0.0

    # Aggregate angles
    if angle_history:
        aggregated_angles = aggregate_angles(angle_history)
        results.avg_angles = angles_to_dict(aggregated_angles)

    # Get final classification from State Machine statistics
    sm_stats = state_machine.get_statistics()
    results.gait_type = current_gait_type
    results.confidence = sm_stats.get("average_confidence", current_confidence)

    # Print State Machine statistics
    print(f"\nState Machine Statistics:")
    print(f"  Total Gait Cycles: {sm_stats['total_cycles']}")
    print(f"  Successful Classifications: {sm_stats['successful_classifications']}")
    print(f"  Success Rate: {sm_stats['success_rate']:.1f}%")
    print(f"  Average Confidence: {sm_stats['average_confidence']:.1f}%\n")

    return results


def print_results(results: GaitAnalysisResults):
    """Print analysis results in a formatted way."""
    print(f"\n{'='*60}")
    print(f"ANALYSIS RESULTS")
    print(f"{'='*60}\n")

    print(f"Gait Classification:")
    print(f"  Type: {results.gait_type.value if results.gait_type else 'unknown'}")
    print(f"  Confidence: {results.confidence:.1f}%\n")

    print(f"Biomechanical Angles (average):")
    for angle_name, angle_value in results.avg_angles.items():
        print(f"  {angle_name}: {angle_value:.2f}°")

    print(f"\nPerformance Metrics:")
    print(f"  Average Latency: {results.avg_latency_ms:.2f} ms")
    print(f"  Frames Processed: {results.frame_count}")
    print(f"  Frames with Detection: {results.frames_with_detection}")
    detection_rate = (results.frames_with_detection / results.frame_count * 100) if results.frame_count > 0 else 0
    print(f"  Detection Rate: {detection_rate:.1f}%")

    # Validation against POC criteria
    print(f"\n{'='*60}")
    print(f"POC VALIDATION")
    print(f"{'='*60}\n")

    latency_pass = results.avg_latency_ms < 150
    detection_pass = detection_rate > 85

    print(f"Criteria 1: Latency < 150ms")
    print(f"  Result: {results.avg_latency_ms:.2f} ms - {'✓ PASS' if latency_pass else '✗ FAIL'}")

    print(f"\nCriteria 2: Detection Rate > 85%")
    print(f"  Result: {detection_rate:.1f}% - {'✓ PASS' if detection_pass else '✗ FAIL'}")

    print(f"\nOverall POC Status: {'✓ SUCCESS' if (latency_pass and detection_pass) else '✗ NEEDS IMPROVEMENT'}")
    print(f"\n{'='*60}\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="StrideMatch POC 1: Running Gait Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "video",
        type=str,
        help="Path to input video file (MP4, AVI, MOV)"
    )

    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Path to save annotated video (optional)"
    )

    parser.add_argument(
        "--mode", "-m",
        type=str,
        choices=["quick", "detailed", "professional"],
        default="detailed",
        help="Analysis mode (default: detailed)"
    )

    parser.add_argument(
        "--no-display",
        action="store_true",
        help="Disable real-time video display"
    )

    args = parser.parse_args()

    # Validate input file
    video_path = Path(args.video)
    if not video_path.exists():
        print(f"Error: Video file not found: {args.video}")
        sys.exit(1)

    # Run analysis
    try:
        results = analyze_video(
            video_path=str(video_path),
            output_path=args.output,
            mode=args.mode,
            display_realtime=not args.no_display
        )

        # Print results
        print_results(results)

        # Save output path info
        if args.output:
            print(f"Annotated video saved to: {args.output}\n")

    except Exception as e:
        print(f"\nError during analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
