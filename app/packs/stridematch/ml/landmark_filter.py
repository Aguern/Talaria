"""
Landmark filtering and smoothing for noise reduction.

MediaPipe Pose landmarks can be noisy frame-to-frame. This module provides
filtering techniques to smooth landmark positions over time, improving
stability of biomechanical calculations.
"""

from typing import Dict, Deque
from collections import deque
import numpy as np
from dataclasses import dataclass

from .pose_estimator import LandmarkPoint


@dataclass
class SmoothedLandmark:
    """Landmark with smoothed coordinates."""
    x: float
    y: float
    z: float
    visibility: float
    raw_x: float  # Original unsmoothed x
    raw_y: float  # Original unsmoothed y


class LandmarkSmoother:
    """
    Smooths landmark positions using exponential moving average.

    This filter reduces frame-to-frame jitter while maintaining
    responsiveness to actual movement.

    Attributes:
        alpha: Smoothing factor (0-1). Higher = more responsive, more noise
        landmark_history: Rolling buffer of recent landmark positions
    """

    def __init__(self, alpha: float = 0.3, window_size: int = 5):
        """
        Initialize landmark smoother.

        Args:
            alpha: Smoothing factor (0.1-0.5 recommended)
                   0.1 = very smooth, slow response
                   0.5 = balanced
            window_size: Number of frames for moving average fallback
        """
        self.alpha = alpha
        self.window_size = window_size

        # History for each landmark
        self.landmark_histories: Dict[str, Deque[LandmarkPoint]] = {}

        # Current smoothed values
        self.smoothed_values: Dict[str, SmoothedLandmark] = {}

    def smooth(
        self,
        landmark_name: str,
        landmark: LandmarkPoint
    ) -> SmoothedLandmark:
        """
        Smooth a landmark using exponential moving average.

        Args:
            landmark_name: Name of the landmark (e.g., "right_ankle")
            landmark: Raw landmark from MediaPipe

        Returns:
            SmoothedLandmark with filtered coordinates
        """
        # Initialize history for this landmark if needed
        if landmark_name not in self.landmark_histories:
            self.landmark_histories[landmark_name] = deque(maxlen=self.window_size)
            # First frame: use raw value
            smoothed = SmoothedLandmark(
                x=landmark.x,
                y=landmark.y,
                z=landmark.z,
                visibility=landmark.visibility,
                raw_x=landmark.x,
                raw_y=landmark.y
            )
            self.smoothed_values[landmark_name] = smoothed
            self.landmark_histories[landmark_name].append(landmark)
            return smoothed

        # Get previous smoothed value
        prev_smoothed = self.smoothed_values[landmark_name]

        # Apply exponential moving average
        # new_smoothed = alpha * raw + (1 - alpha) * prev_smoothed
        smoothed_x = self.alpha * landmark.x + (1 - self.alpha) * prev_smoothed.x
        smoothed_y = self.alpha * landmark.y + (1 - self.alpha) * prev_smoothed.y
        smoothed_z = self.alpha * landmark.z + (1 - self.alpha) * prev_smoothed.z

        # Smooth visibility more aggressively to avoid flickering
        smoothed_visibility = 0.2 * landmark.visibility + 0.8 * prev_smoothed.visibility

        # Create smoothed landmark
        smoothed = SmoothedLandmark(
            x=smoothed_x,
            y=smoothed_y,
            z=smoothed_z,
            visibility=smoothed_visibility,
            raw_x=landmark.x,
            raw_y=landmark.y
        )

        # Update history and current smoothed value
        self.landmark_histories[landmark_name].append(landmark)
        self.smoothed_values[landmark_name] = smoothed

        return smoothed

    def smooth_all(
        self,
        landmarks: Dict[str, LandmarkPoint]
    ) -> Dict[str, LandmarkPoint]:
        """
        Smooth all landmarks in a dictionary.

        Args:
            landmarks: Dictionary of raw landmarks

        Returns:
            Dictionary of smoothed landmarks (as LandmarkPoint for compatibility)
        """
        smoothed_landmarks = {}

        for name, landmark in landmarks.items():
            smoothed = self.smooth(name, landmark)

            # Convert back to LandmarkPoint for compatibility
            smoothed_landmarks[name] = LandmarkPoint(
                x=smoothed.x,
                y=smoothed.y,
                z=smoothed.z,
                visibility=smoothed.visibility
            )

        return smoothed_landmarks

    def reset(self):
        """Clear all smoothing history."""
        self.landmark_histories.clear()
        self.smoothed_values.clear()


class AdaptiveLandmarkSmoother(LandmarkSmoother):
    """
    Adaptive smoother that adjusts alpha based on movement speed.

    When movement is slow: use lower alpha (more smoothing)
    When movement is fast: use higher alpha (more responsive)

    This provides smooth tracking during stance phase and
    quick response during swing phase.
    """

    def __init__(
        self,
        alpha_min: float = 0.15,
        alpha_max: float = 0.5,
        window_size: int = 5
    ):
        """
        Initialize adaptive smoother.

        Args:
            alpha_min: Minimum alpha (max smoothing) for slow movement
            alpha_max: Maximum alpha (min smoothing) for fast movement
            window_size: Window for movement speed calculation
        """
        super().__init__(alpha=alpha_max, window_size=window_size)
        self.alpha_min = alpha_min
        self.alpha_max = alpha_max

    def smooth(
        self,
        landmark_name: str,
        landmark: LandmarkPoint
    ) -> SmoothedLandmark:
        """
        Smooth with adaptive alpha based on movement speed.

        Args:
            landmark_name: Name of the landmark
            landmark: Raw landmark

        Returns:
            SmoothedLandmark with adaptive filtering
        """
        # Calculate movement speed if we have history
        if landmark_name in self.landmark_histories and len(self.landmark_histories[landmark_name]) > 0:
            prev_landmark = self.landmark_histories[landmark_name][-1]

            # Calculate displacement
            dx = abs(landmark.x - prev_landmark.x)
            dy = abs(landmark.y - prev_landmark.y)
            displacement = np.sqrt(dx**2 + dy**2)

            # Adaptive alpha: higher displacement → higher alpha (less smoothing)
            # Displacement threshold: 0.01 (slow) to 0.05 (fast) in normalized coords
            displacement_factor = np.clip(displacement / 0.05, 0.0, 1.0)
            self.alpha = self.alpha_min + displacement_factor * (self.alpha_max - self.alpha_min)

        # Call parent smooth method with updated alpha
        return super().smooth(landmark_name, landmark)


class OutlierFilter:
    """
    Filters outlier landmark detections.

    Sometimes MediaPipe produces erroneous detections. This filter
    rejects landmarks that deviate significantly from recent history.
    """

    def __init__(self, max_deviation: float = 0.15):
        """
        Initialize outlier filter.

        Args:
            max_deviation: Maximum allowed deviation (normalized coords)
        """
        self.max_deviation = max_deviation
        self.landmark_histories: Dict[str, Deque[LandmarkPoint]] = {}

    def filter(
        self,
        landmark_name: str,
        landmark: LandmarkPoint,
        history_size: int = 5
    ) -> LandmarkPoint:
        """
        Filter outlier detections.

        Args:
            landmark_name: Name of the landmark
            landmark: Current landmark
            history_size: Number of frames for outlier detection

        Returns:
            Filtered landmark (original if valid, interpolated if outlier)
        """
        # Initialize history if needed
        if landmark_name not in self.landmark_histories:
            self.landmark_histories[landmark_name] = deque(maxlen=history_size)
            self.landmark_histories[landmark_name].append(landmark)
            return landmark

        history = self.landmark_histories[landmark_name]

        # Need at least 2 points for outlier detection
        if len(history) < 2:
            history.append(landmark)
            return landmark

        # Calculate median position from history
        x_values = [lm.x for lm in history]
        y_values = [lm.y for lm in history]

        median_x = np.median(x_values)
        median_y = np.median(y_values)

        # Calculate deviation from median
        dx = abs(landmark.x - median_x)
        dy = abs(landmark.y - median_y)
        deviation = np.sqrt(dx**2 + dy**2)

        # If deviation too large, use median instead (outlier rejection)
        if deviation > self.max_deviation:
            # Use median of recent history
            filtered_landmark = LandmarkPoint(
                x=median_x,
                y=median_y,
                z=np.median([lm.z for lm in history]),
                visibility=landmark.visibility * 0.5  # Reduce confidence
            )
            # Don't add outlier to history
            return filtered_landmark
        else:
            # Valid detection: add to history
            history.append(landmark)
            return landmark

    def reset(self):
        """Clear outlier filter history."""
        self.landmark_histories.clear()
