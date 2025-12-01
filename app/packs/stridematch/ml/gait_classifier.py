"""
Gait pattern classifier for running biomechanics.

This module classifies the type of foot strike (heel, midfoot, forefoot)
using heuristic rules and biomechanical analysis from pose landmarks.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np

from .pose_estimator import LandmarkPoint


class GaitType(str, Enum):
    """Enumeration of gait strike patterns."""
    HEEL_STRIKE = "heel_strike"
    MIDFOOT_STRIKE = "midfoot_strike"
    FOREFOOT_STRIKE = "forefoot_strike"
    UNKNOWN = "unknown"


@dataclass
class GaitClassification:
    """Result of gait classification."""
    gait_type: GaitType
    confidence: float  # 0-100
    strike_angle: Optional[float] = None  # Ankle angle at contact
    vertical_ratio: Optional[float] = None  # Heel vs toe vertical position
    reasoning: str = ""  # Human-readable explanation


class GaitClassifier:
    """
    Classifier for running gait patterns based on foot strike.

    This classifier uses biomechanical heuristics to determine whether
    a runner has a heel strike, midfoot strike, or forefoot strike pattern.

    The primary method is analyzing the vertical position of heel vs toe
    at the moment of ground contact.
    """

    # Thresholds for classification (tuned based on biomechanics research)
    HEEL_STRIKE_THRESHOLD = 0.98  # Heel is at or below toe level
    FOREFOOT_STRIKE_THRESHOLD = 0.85  # Toe significantly below heel

    def __init__(self):
        """Initialize the gait classifier."""
        self.classifications_history: List[GaitClassification] = []

    def classify_frame(
        self,
        landmarks: Dict[str, LandmarkPoint],
        side: str = "right"
    ) -> GaitClassification:
        """
        Classify gait pattern from a single frame's landmarks.

        Args:
            landmarks: Dictionary of pose landmarks
            side: Which leg to analyze ("right" or "left")

        Returns:
            GaitClassification with detected pattern and confidence
        """
        # Select landmarks based on side
        heel_key = f"{side}_heel"
        toe_key = f"{side}_foot_index"
        ankle_key = f"{side}_ankle"

        # Check if required landmarks are available
        if not all(k in landmarks for k in [heel_key, toe_key, ankle_key]):
            return GaitClassification(
                gait_type=GaitType.UNKNOWN,
                confidence=0.0,
                reasoning="Missing required landmarks"
            )

        heel = landmarks[heel_key]
        toe = landmarks[toe_key]
        ankle = landmarks[ankle_key]

        # Check landmark visibility
        min_visibility = 0.5
        if heel.visibility < min_visibility or toe.visibility < min_visibility:
            return GaitClassification(
                gait_type=GaitType.UNKNOWN,
                confidence=0.0,
                reasoning="Low landmark visibility"
            )

        # METHOD 1: Vertical position analysis (primary method)
        # In normalized coordinates, higher Y = lower on screen
        # So if heel.y > toe.y, heel is lower (more toward ground)

        vertical_ratio = heel.y / toe.y if toe.y > 0 else 1.0

        # Determine gait type based on vertical ratio
        if vertical_ratio >= self.HEEL_STRIKE_THRESHOLD:
            gait_type = GaitType.HEEL_STRIKE
            confidence = min(95.0, 70.0 + (vertical_ratio - self.HEEL_STRIKE_THRESHOLD) * 200)
            reasoning = f"Heel at or below toe level (ratio: {vertical_ratio:.3f})"

        elif vertical_ratio <= self.FOREFOOT_STRIKE_THRESHOLD:
            gait_type = GaitType.FOREFOOT_STRIKE
            confidence = min(95.0, 70.0 + (self.FOREFOOT_STRIKE_THRESHOLD - vertical_ratio) * 200)
            reasoning = f"Toe significantly below heel (ratio: {vertical_ratio:.3f})"

        else:
            gait_type = GaitType.MIDFOOT_STRIKE
            confidence = 60.0  # Medium confidence for midfoot
            reasoning = f"Balanced foot position (ratio: {vertical_ratio:.3f})"

        return GaitClassification(
            gait_type=gait_type,
            confidence=confidence,
            vertical_ratio=vertical_ratio,
            reasoning=reasoning
        )

    def classify_from_angles(
        self,
        ankle_angle: float,
        knee_angle: float
    ) -> GaitClassification:
        """
        Alternative classification method using joint angles.

        This method analyzes ankle and knee angles to infer strike pattern.

        Args:
            ankle_angle: Ankle flexion angle in degrees
            knee_angle: Knee flexion angle in degrees

        Returns:
            GaitClassification result
        """
        # Heel strike typically has:
        # - More dorsiflexed ankle (larger angle, ~100-110°)
        # - More extended knee (larger angle, ~160-170°)

        # Forefoot strike typically has:
        # - More plantarflexed ankle (smaller angle, ~70-85°)
        # - More flexed knee (smaller angle, ~140-150°)

        if ankle_angle > 95 and knee_angle > 155:
            return GaitClassification(
                gait_type=GaitType.HEEL_STRIKE,
                confidence=75.0,
                strike_angle=ankle_angle,
                reasoning=f"Extended ankle ({ankle_angle:.1f}°) and knee ({knee_angle:.1f}°)"
            )

        elif ankle_angle < 85 and knee_angle < 155:
            return GaitClassification(
                gait_type=GaitType.FOREFOOT_STRIKE,
                confidence=75.0,
                strike_angle=ankle_angle,
                reasoning=f"Flexed ankle ({ankle_angle:.1f}°) and knee ({knee_angle:.1f}°)"
            )

        else:
            return GaitClassification(
                gait_type=GaitType.MIDFOOT_STRIKE,
                confidence=60.0,
                strike_angle=ankle_angle,
                reasoning=f"Moderate angles: ankle {ankle_angle:.1f}°, knee {knee_angle:.1f}°"
            )

    def classify_video_sequence(
        self,
        landmark_sequence: List[Dict[str, LandmarkPoint]],
        side: str = "right"
    ) -> GaitClassification:
        """
        Classify gait pattern from a sequence of frames.

        This aggregates classifications across multiple frames to get
        a more robust result.

        Args:
            landmark_sequence: List of landmark dictionaries from consecutive frames
            side: Which leg to analyze

        Returns:
            Aggregated GaitClassification
        """
        classifications = []

        for landmarks in landmark_sequence:
            classification = self.classify_frame(landmarks, side)
            if classification.gait_type != GaitType.UNKNOWN:
                classifications.append(classification)

        if not classifications:
            return GaitClassification(
                gait_type=GaitType.UNKNOWN,
                confidence=0.0,
                reasoning="No valid frames for classification"
            )

        # Count gait types
        gait_counts = {
            GaitType.HEEL_STRIKE: 0,
            GaitType.MIDFOOT_STRIKE: 0,
            GaitType.FOREFOOT_STRIKE: 0,
        }

        total_confidence = 0.0
        for c in classifications:
            gait_counts[c.gait_type] += 1
            total_confidence += c.confidence

        # Determine most common gait type
        most_common_gait = max(gait_counts.items(), key=lambda x: x[1])[0]

        # Calculate confidence based on consensus
        consensus_ratio = gait_counts[most_common_gait] / len(classifications)
        avg_confidence = total_confidence / len(classifications)
        final_confidence = min(95.0, avg_confidence * consensus_ratio)

        return GaitClassification(
            gait_type=most_common_gait,
            confidence=final_confidence,
            reasoning=f"Consensus from {len(classifications)} frames ({consensus_ratio*100:.1f}% agreement)"
        )

    def detect_contact_phase(
        self,
        landmarks: Dict[str, LandmarkPoint],
        side: str = "right",
        previous_landmarks: Optional[Dict[str, LandmarkPoint]] = None
    ) -> bool:
        """
        Detect if the foot is in contact phase (ground contact).

        This uses vertical ankle position and velocity to estimate contact.

        Args:
            landmarks: Current frame landmarks
            side: Which leg to analyze
            previous_landmarks: Previous frame landmarks for velocity calculation

        Returns:
            True if foot appears to be in contact with ground
        """
        ankle_key = f"{side}_ankle"
        heel_key = f"{side}_heel"

        if ankle_key not in landmarks or heel_key not in landmarks:
            return False

        ankle = landmarks[ankle_key]
        heel = landmarks[heel_key]

        # Simple heuristic: if ankle/heel are in lower part of frame
        # (higher Y value in normalized coordinates)
        # Consider them in contact phase
        contact_threshold = 0.7  # Lower 30% of frame

        is_low = ankle.y > contact_threshold or heel.y > contact_threshold

        # If we have previous frame, check for low velocity (sign of contact)
        if previous_landmarks and ankle_key in previous_landmarks:
            prev_ankle = previous_landmarks[ankle_key]
            vertical_velocity = abs(ankle.y - prev_ankle.y)

            # Low vertical movement suggests contact
            velocity_threshold = 0.02
            is_stable = vertical_velocity < velocity_threshold

            return is_low and is_stable

        return is_low


def majority_vote_gait_type(
    classifications: List[GaitClassification]
) -> GaitType:
    """
    Determine gait type by majority vote from multiple classifications.

    Args:
        classifications: List of GaitClassification results

    Returns:
        Most common GaitType
    """
    if not classifications:
        return GaitType.UNKNOWN

    # Filter out unknown classifications
    valid_classifications = [c for c in classifications if c.gait_type != GaitType.UNKNOWN]

    if not valid_classifications:
        return GaitType.UNKNOWN

    # Count occurrences
    gait_counts = {}
    for c in valid_classifications:
        gait_counts[c.gait_type] = gait_counts.get(c.gait_type, 0) + 1

    # Return most common
    return max(gait_counts.items(), key=lambda x: x[1])[0]


def calculate_stride_frequency(
    landmark_sequence: List[Dict[str, LandmarkPoint]],
    fps: float = 30.0,
    side: str = "right"
) -> Optional[float]:
    """
    Calculate stride frequency (cadence) from a video sequence.

    This detects peaks in vertical ankle movement to count strides.

    Args:
        landmark_sequence: Sequence of landmarks from video
        fps: Frames per second of the video
        side: Which leg to analyze

    Returns:
        Cadence in steps per minute, or None if cannot calculate
    """
    ankle_key = f"{side}_ankle"

    # Extract ankle vertical positions
    ankle_positions = []
    for landmarks in landmark_sequence:
        if ankle_key in landmarks:
            ankle_positions.append(landmarks[ankle_key].y)

    if len(ankle_positions) < 30:  # Need at least 1 second of data
        return None

    # Detect peaks (low points in Y coordinate = high points in space)
    # Since Y increases downward, we look for local minima
    from scipy.signal import find_peaks

    # Invert signal to find peaks (since we want local minima)
    inverted_signal = [-y for y in ankle_positions]

    peaks, _ = find_peaks(inverted_signal, distance=int(fps * 0.3))  # Min 0.3s between steps

    if len(peaks) < 2:
        return None

    # Calculate frequency
    num_strides = len(peaks)
    duration_sec = len(ankle_positions) / fps
    steps_per_second = num_strides / duration_sec
    steps_per_minute = steps_per_second * 60

    return steps_per_minute
