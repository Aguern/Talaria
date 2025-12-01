"""
MediaPipe Pose Estimator for gait analysis.

This module provides a wrapper around MediaPipe Pose for extracting
biomechanical landmarks from video frames with latency tracking.
"""

import time
from typing import Optional, Dict, List, Tuple, Any
import mediapipe as mp
import cv2
import numpy as np
from dataclasses import dataclass


@dataclass
class LandmarkPoint:
    """Represents a single body landmark point."""
    x: float  # Normalized x coordinate (0-1)
    y: float  # Normalized y coordinate (0-1)
    z: float  # Depth coordinate
    visibility: float  # Visibility score (0-1)


@dataclass
class PoseEstimationResult:
    """Result of pose estimation on a single frame."""
    landmarks: Optional[Dict[str, LandmarkPoint]]  # Keyed by landmark name
    frame_number: int
    latency_ms: float  # Processing latency in milliseconds
    detected: bool  # Whether pose was successfully detected


class MediaPipePoseEstimator:
    """
    Wrapper for MediaPipe Pose estimation optimized for gait analysis.

    This class manages the MediaPipe Pose model lifecycle and provides
    methods to extract biomechanical landmarks from video frames.

    Attributes:
        model_complexity: Model complexity (0, 1, or 2). Higher = more accurate but slower
        min_detection_confidence: Minimum confidence for detection
        min_tracking_confidence: Minimum confidence for tracking
    """

    # MediaPipe landmark indices for key body points
    LANDMARK_INDICES = {
        "nose": mp.solutions.pose.PoseLandmark.NOSE.value,
        "left_eye_inner": mp.solutions.pose.PoseLandmark.LEFT_EYE_INNER.value,
        "left_eye": mp.solutions.pose.PoseLandmark.LEFT_EYE.value,
        "left_eye_outer": mp.solutions.pose.PoseLandmark.LEFT_EYE_OUTER.value,
        "right_eye_inner": mp.solutions.pose.PoseLandmark.RIGHT_EYE_INNER.value,
        "right_eye": mp.solutions.pose.PoseLandmark.RIGHT_EYE.value,
        "right_eye_outer": mp.solutions.pose.PoseLandmark.RIGHT_EYE_OUTER.value,
        "left_ear": mp.solutions.pose.PoseLandmark.LEFT_EAR.value,
        "right_ear": mp.solutions.pose.PoseLandmark.RIGHT_EAR.value,
        "mouth_left": mp.solutions.pose.PoseLandmark.MOUTH_LEFT.value,
        "mouth_right": mp.solutions.pose.PoseLandmark.MOUTH_RIGHT.value,
        "left_shoulder": mp.solutions.pose.PoseLandmark.LEFT_SHOULDER.value,
        "right_shoulder": mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER.value,
        "left_elbow": mp.solutions.pose.PoseLandmark.LEFT_ELBOW.value,
        "right_elbow": mp.solutions.pose.PoseLandmark.RIGHT_ELBOW.value,
        "left_wrist": mp.solutions.pose.PoseLandmark.LEFT_WRIST.value,
        "right_wrist": mp.solutions.pose.PoseLandmark.RIGHT_WRIST.value,
        "left_hip": mp.solutions.pose.PoseLandmark.LEFT_HIP.value,
        "right_hip": mp.solutions.pose.PoseLandmark.RIGHT_HIP.value,
        "left_knee": mp.solutions.pose.PoseLandmark.LEFT_KNEE.value,
        "right_knee": mp.solutions.pose.PoseLandmark.RIGHT_KNEE.value,
        "left_ankle": mp.solutions.pose.PoseLandmark.LEFT_ANKLE.value,
        "right_ankle": mp.solutions.pose.PoseLandmark.RIGHT_ANKLE.value,
        "left_heel": mp.solutions.pose.PoseLandmark.LEFT_HEEL.value,
        "right_heel": mp.solutions.pose.PoseLandmark.RIGHT_HEEL.value,
        "left_foot_index": mp.solutions.pose.PoseLandmark.LEFT_FOOT_INDEX.value,
        "right_foot_index": mp.solutions.pose.PoseLandmark.RIGHT_FOOT_INDEX.value,
    }

    def __init__(
        self,
        model_complexity: int = 1,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ):
        """
        Initialize the MediaPipe Pose estimator.

        Args:
            model_complexity: Model complexity (0=fastest, 2=most accurate)
            min_detection_confidence: Minimum confidence for initial detection
            min_tracking_confidence: Minimum confidence for tracking between frames
        """
        self.model_complexity = model_complexity
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence

        # Initialize MediaPipe Pose
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        # Create pose instance (context manager)
        self.pose = None
        self._initialize_pose()

    def _initialize_pose(self):
        """Initialize the MediaPipe Pose model."""
        self.pose = self.mp_pose.Pose(
            model_complexity=self.model_complexity,
            min_detection_confidence=self.min_detection_confidence,
            min_tracking_confidence=self.min_tracking_confidence,
            enable_segmentation=False,  # Disable segmentation for performance
            smooth_landmarks=True,  # Enable landmark smoothing
        )

    def process_frame(
        self,
        frame: np.ndarray,
        frame_number: int = 0
    ) -> PoseEstimationResult:
        """
        Process a single video frame to extract pose landmarks.

        Args:
            frame: BGR image as numpy array (OpenCV format)
            frame_number: Frame number for tracking

        Returns:
            PoseEstimationResult containing landmarks and metadata
        """
        # Convert BGR to RGB
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False  # Improve performance

        # Measure latency
        start_time = time.time()
        results = self.pose.process(image)
        latency_ms = (time.time() - start_time) * 1000

        image.flags.writeable = True

        # Extract landmarks if detected
        landmarks_dict = None
        detected = False

        if results.pose_landmarks:
            detected = True
            landmarks_dict = self._extract_landmarks(results.pose_landmarks)

        return PoseEstimationResult(
            landmarks=landmarks_dict,
            frame_number=frame_number,
            latency_ms=latency_ms,
            detected=detected
        )

    def _extract_landmarks(
        self,
        pose_landmarks
    ) -> Dict[str, LandmarkPoint]:
        """
        Extract landmarks from MediaPipe results into a structured dictionary.

        Args:
            pose_landmarks: MediaPipe pose_landmarks object

        Returns:
            Dictionary mapping landmark names to LandmarkPoint objects
        """
        landmarks = {}

        for name, idx in self.LANDMARK_INDICES.items():
            landmark = pose_landmarks.landmark[idx]
            landmarks[name] = LandmarkPoint(
                x=landmark.x,
                y=landmark.y,
                z=landmark.z,
                visibility=landmark.visibility
            )

        return landmarks

    def draw_landmarks(
        self,
        frame: np.ndarray,
        landmarks: Dict[str, LandmarkPoint],
        image_width: int,
        image_height: int
    ) -> np.ndarray:
        """
        Draw skeleton landmarks on a frame.

        Args:
            frame: BGR image as numpy array
            landmarks: Dictionary of landmarks
            image_width: Image width in pixels
            image_height: Image height in pixels

        Returns:
            Annotated frame with skeleton overlay
        """
        # Convert landmarks dict back to MediaPipe format for drawing
        mp_landmarks = self._landmarks_to_mp_format(landmarks)

        # Draw pose landmarks
        self.mp_drawing.draw_landmarks(
            frame,
            mp_landmarks,
            self.mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style()
        )

        return frame

    def _landmarks_to_mp_format(
        self,
        landmarks: Dict[str, LandmarkPoint]
    ):
        """
        Convert our LandmarkPoint dict back to MediaPipe landmark format.

        Args:
            landmarks: Dictionary of LandmarkPoint objects

        Returns:
            MediaPipe landmark object
        """
        # Create a landmark list
        from mediapipe.framework.formats import landmark_pb2

        landmark_list = landmark_pb2.NormalizedLandmarkList()

        # Add landmarks in the correct order (by index)
        index_to_name = {v: k for k, v in self.LANDMARK_INDICES.items()}
        for idx in range(33):  # MediaPipe has 33 landmarks
            landmark = landmark_list.landmark.add()
            if idx in index_to_name:
                name = index_to_name[idx]
                lm = landmarks.get(name)
                if lm:
                    landmark.x = lm.x
                    landmark.y = lm.y
                    landmark.z = lm.z
                    landmark.visibility = lm.visibility
                else:
                    # Default values if landmark not available
                    landmark.x = 0.0
                    landmark.y = 0.0
                    landmark.z = 0.0
                    landmark.visibility = 0.0
            else:
                # For indices not in our mapping, use defaults
                landmark.x = 0.0
                landmark.y = 0.0
                landmark.z = 0.0
                landmark.visibility = 0.0

        return landmark_list

    def get_pixel_coordinates(
        self,
        landmark: LandmarkPoint,
        image_width: int,
        image_height: int
    ) -> Tuple[int, int]:
        """
        Convert normalized landmark coordinates to pixel coordinates.

        Args:
            landmark: LandmarkPoint with normalized coordinates
            image_width: Image width in pixels
            image_height: Image height in pixels

        Returns:
            Tuple of (x_pixel, y_pixel)
        """
        x_pixel = int(landmark.x * image_width)
        y_pixel = int(landmark.y * image_height)
        return (x_pixel, y_pixel)

    def close(self):
        """Release resources."""
        if self.pose:
            self.pose.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def create_pose_estimator(
    mode: str = "quick"
) -> MediaPipePoseEstimator:
    """
    Factory function to create a pose estimator with preset configurations.

    Args:
        mode: Preset mode ("quick", "detailed", "professional")

    Returns:
        Configured MediaPipePoseEstimator instance
    """
    configs = {
        "quick": {
            "model_complexity": 0,
            "min_detection_confidence": 0.5,
            "min_tracking_confidence": 0.5,
        },
        "detailed": {
            "model_complexity": 1,
            "min_detection_confidence": 0.6,
            "min_tracking_confidence": 0.6,
        },
        "professional": {
            "model_complexity": 2,
            "min_detection_confidence": 0.7,
            "min_tracking_confidence": 0.7,
        },
    }

    config = configs.get(mode, configs["quick"])
    return MediaPipePoseEstimator(**config)
