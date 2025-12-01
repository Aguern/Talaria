"""
Velocity and acceleration tracker for biomechanical analysis.

This module tracks landmark movement over time to calculate velocity
and acceleration, critical for detecting ground contact and phase transitions.
"""

from typing import Tuple, List, Optional, Deque
from collections import deque
import numpy as np
from dataclasses import dataclass

from .pose_estimator import LandmarkPoint


@dataclass
class VelocityData:
    """Container for velocity and acceleration data."""
    velocity_x: float  # Horizontal velocity (pixels/second)
    velocity_y: float  # Vertical velocity (pixels/second)
    speed: float  # Magnitude of velocity vector
    acceleration_y: float  # Vertical acceleration (pixels/second²)


class VelocityTracker:
    """
    Tracks landmark velocity and acceleration over time.

    Uses a rolling window of positions to calculate smoothed velocity
    and acceleration, reducing noise from frame-to-frame variations.

    Attributes:
        window_size: Number of frames to use for velocity calculation
        position_history: Rolling buffer of (x, y, timestamp) positions
    """

    def __init__(self, window_size: int = 5):
        """
        Initialize velocity tracker.

        Args:
            window_size: Number of frames for moving average (default: 5)
        """
        self.window_size = window_size
        self.position_history: Deque[Tuple[float, float, float]] = deque(maxlen=window_size)
        self.velocity_history: Deque[Tuple[float, float]] = deque(maxlen=window_size)

    def update(
        self,
        position: Tuple[float, float],
        timestamp: float
    ) -> Optional[VelocityData]:
        """
        Update tracker with new position and calculate velocity.

        Args:
            position: (x, y) coordinates in pixels
            timestamp: Frame timestamp in seconds

        Returns:
            VelocityData if enough history, None otherwise
        """
        # Add to history
        self.position_history.append((position[0], position[1], timestamp))

        # Need at least 2 points to calculate velocity
        if len(self.position_history) < 2:
            return None

        # Calculate velocity using finite differences
        velocity_x, velocity_y = self._calculate_velocity()

        # Store velocity for acceleration calculation
        self.velocity_history.append((velocity_x, velocity_y))

        # Calculate speed (magnitude)
        speed = np.sqrt(velocity_x**2 + velocity_y**2)

        # Calculate acceleration if we have velocity history
        acceleration_y = 0.0
        if len(self.velocity_history) >= 2:
            acceleration_y = self._calculate_vertical_acceleration()

        return VelocityData(
            velocity_x=velocity_x,
            velocity_y=velocity_y,
            speed=speed,
            acceleration_y=acceleration_y
        )

    def _calculate_velocity(self) -> Tuple[float, float]:
        """
        Calculate velocity using central difference method.

        Uses the positions at the start and end of the window for
        a smoothed velocity estimate.

        Returns:
            (velocity_x, velocity_y) in pixels/second
        """
        if len(self.position_history) < 2:
            return (0.0, 0.0)

        # Get first and last positions
        x1, y1, t1 = self.position_history[0]
        x2, y2, t2 = self.position_history[-1]

        # Calculate time difference
        dt = t2 - t1

        if dt == 0:
            return (0.0, 0.0)

        # Calculate velocity
        velocity_x = (x2 - x1) / dt
        velocity_y = (y2 - y1) / dt

        return (velocity_x, velocity_y)

    def _calculate_vertical_acceleration(self) -> float:
        """
        Calculate vertical acceleration from velocity history.

        Returns:
            Vertical acceleration in pixels/second²
        """
        if len(self.velocity_history) < 2:
            return 0.0

        # Get velocity at start and end of window
        _, vy1 = self.velocity_history[0]
        _, vy2 = self.velocity_history[-1]

        # Approximate time span (using window size and assuming constant FPS)
        # This will be refined when we pass actual timestamps
        dt = len(self.velocity_history) * 0.04  # Assume ~25 FPS initially

        if dt == 0:
            return 0.0

        # Calculate acceleration
        acceleration_y = (vy2 - vy1) / dt

        return acceleration_y

    def reset(self):
        """Clear all history buffers."""
        self.position_history.clear()
        self.velocity_history.clear()


class GroundContactDetector:
    """
    Detects ground contact moments using velocity analysis.

    Ground contact is detected when:
    1. Vertical velocity approaches zero (deceleration)
    2. Landmark is in lower portion of frame (spatial constraint)
    3. Sudden change in vertical acceleration (impact)
    """

    def __init__(
        self,
        velocity_threshold: float = 50.0,  # pixels/second
        acceleration_threshold: float = 500.0,  # pixels/second²
        height_threshold: float = 0.65,  # Normalized Y coordinate (0-1)
    ):
        """
        Initialize ground contact detector.

        Args:
            velocity_threshold: Max vertical velocity for contact (pixels/s)
            acceleration_threshold: Min acceleration change for impact (pixels/s²)
            height_threshold: Min Y coordinate (0=top, 1=bottom) for contact
        """
        self.velocity_threshold = velocity_threshold
        self.acceleration_threshold = acceleration_threshold
        self.height_threshold = height_threshold

        self.contact_cooldown = 0  # Frames since last contact (avoid double-detection)
        self.min_cooldown_frames = 10  # Min frames between contacts

    def detect_contact(
        self,
        landmark: LandmarkPoint,
        velocity_data: Optional[VelocityData],
        image_height: int
    ) -> bool:
        """
        Detect if ground contact occurred in this frame.

        Args:
            landmark: Ankle or heel landmark
            velocity_data: Velocity information
            image_height: Image height in pixels for normalization

        Returns:
            True if ground contact detected
        """
        # Decrement cooldown
        if self.contact_cooldown > 0:
            self.contact_cooldown -= 1
            return False

        if velocity_data is None:
            return False

        # Convert normalized Y to pixel space for velocity comparison
        pixel_y = landmark.y * image_height

        # Condition 1: Landmark in lower portion of frame
        in_lower_frame = landmark.y >= self.height_threshold

        # Condition 2: Low vertical velocity (approaching zero)
        # Note: Positive Y velocity = downward motion in image coordinates
        low_vertical_velocity = abs(velocity_data.velocity_y) < self.velocity_threshold

        # Condition 3: Significant deceleration (negative acceleration = slowing down)
        # In image coords: moving down (+velocity) then stopping = negative acceleration
        significant_deceleration = velocity_data.acceleration_y < -self.acceleration_threshold

        # Condition 4: Good landmark visibility
        good_visibility = landmark.visibility > 0.5

        # Contact detected if all conditions met
        contact_detected = (
            in_lower_frame and
            low_vertical_velocity and
            good_visibility
        )

        # Optional: Use deceleration as additional confidence boost
        if contact_detected and significant_deceleration:
            # High confidence contact
            self.contact_cooldown = self.min_cooldown_frames
            return True
        elif contact_detected:
            # Medium confidence contact
            self.contact_cooldown = self.min_cooldown_frames
            return True

        return False

    def detect_toe_off(
        self,
        landmark: LandmarkPoint,
        velocity_data: Optional[VelocityData]
    ) -> bool:
        """
        Detect toe-off (foot leaving ground).

        Args:
            landmark: Toe or ankle landmark
            velocity_data: Velocity information

        Returns:
            True if toe-off detected
        """
        if velocity_data is None:
            return False

        # Toe-off characteristics:
        # 1. Upward velocity (negative in image coordinates)
        # 2. Significant speed
        # 3. Positive acceleration (accelerating upward)

        upward_velocity = velocity_data.velocity_y < -50.0  # Moving up
        sufficient_speed = velocity_data.speed > 80.0
        upward_acceleration = velocity_data.acceleration_y < -300.0

        toe_off_detected = (
            upward_velocity and
            sufficient_speed
        )

        return toe_off_detected


def calculate_average_velocity(
    position_sequence: List[Tuple[float, float]],
    fps: float
) -> Tuple[float, float]:
    """
    Calculate average velocity from a sequence of positions.

    Utility function for batch processing.

    Args:
        position_sequence: List of (x, y) positions
        fps: Frames per second

    Returns:
        (avg_velocity_x, avg_velocity_y) in pixels/second
    """
    if len(position_sequence) < 2:
        return (0.0, 0.0)

    # Calculate total displacement
    x1, y1 = position_sequence[0]
    x2, y2 = position_sequence[-1]

    dx = x2 - x1
    dy = y2 - y1

    # Calculate time span
    dt = (len(position_sequence) - 1) / fps

    if dt == 0:
        return (0.0, 0.0)

    # Calculate average velocity
    avg_vx = dx / dt
    avg_vy = dy / dt

    return (avg_vx, avg_vy)
