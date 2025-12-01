"""
Gait Cycle State Machine for robust foot strike classification.

This module implements a biomechanically-accurate state machine that
classifies gait type ONLY at the moment of ground contact, using
temporal context and velocity analysis.
"""

from enum import Enum
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
from collections import deque
import numpy as np

from .pose_estimator import LandmarkPoint
from .velocity_tracker import VelocityTracker, GroundContactDetector, VelocityData
from .gait_classifier import GaitType


class GaitPhase(str, Enum):
    """
    Phases of the gait cycle.

    SWING: Foot is in the air, moving forward
    CONTACT: Instant of ground contact (heel strike/midfoot/forefoot)
    STANCE: Foot is on the ground, supporting body weight
    TOE_OFF: Foot is pushing off the ground
    """
    SWING = "swing"
    CONTACT = "contact"
    STANCE = "stance"
    TOE_OFF = "toe_off"


@dataclass
class GaitClassification:
    """
    Result of gait classification at ground contact.
    """
    gait_type: GaitType
    confidence: float  # 0-100
    contact_frame: int
    biomechanical_scores: Dict[str, float]  # Individual criterion scores
    reasoning: str


class GaitCycleStateMachine:
    """
    State machine for tracking gait phases and classifying foot strike.

    This machine follows the biomechanical cycle:
    SWING → CONTACT → STANCE → TOE_OFF → SWING

    Classification occurs ONLY at the CONTACT phase, ensuring
    accurate timing and context-aware analysis.

    Attributes:
        current_phase: Current gait phase
        velocity_tracker: Tracks ankle/heel velocity
        contact_detector: Detects ground contact moments
        last_classification: Most recent gait classification
    """

    def __init__(
        self,
        side: str = "right",
        fps: float = 30.0
    ):
        """
        Initialize the gait cycle state machine.

        Args:
            side: Which leg to analyze ("right" or "left")
            fps: Video frames per second
        """
        self.side = side
        self.fps = fps

        # State tracking
        self.current_phase = GaitPhase.SWING
        self.frame_in_phase = 0  # Frames spent in current phase

        # Velocity tracking
        self.velocity_tracker = VelocityTracker(window_size=5)
        self.contact_detector = GroundContactDetector(
            velocity_threshold=50.0,
            acceleration_threshold=500.0,
            height_threshold=0.65
        )

        # Classification results
        self.last_classification: Optional[GaitClassification] = None
        self.classification_history: List[GaitClassification] = []

        # Landmark history for classification
        self.landmark_buffer: deque = deque(maxlen=10)

        # Performance metrics
        self.total_cycles = 0
        self.successful_classifications = 0

    def update(
        self,
        landmarks: Dict[str, LandmarkPoint],
        frame_number: int,
        image_width: int,
        image_height: int
    ) -> Tuple[GaitPhase, Optional[GaitClassification]]:
        """
        Update state machine with new frame data.

        Args:
            landmarks: Detected pose landmarks
            frame_number: Current frame number
            image_width: Image width in pixels
            image_height: Image height in pixels

        Returns:
            (current_phase, classification) where classification is only
            available when transitioning to CONTACT phase
        """
        # Select landmarks based on side
        ankle_key = f"{self.side}_ankle"
        heel_key = f"{self.side}_heel"
        toe_key = f"{self.side}_foot_index"
        knee_key = f"{self.side}_knee"

        # Verify required landmarks are present
        if not all(k in landmarks for k in [ankle_key, heel_key, toe_key, knee_key]):
            return (self.current_phase, self.last_classification)

        ankle = landmarks[ankle_key]
        heel = landmarks[heel_key]
        toe = landmarks[toe_key]
        knee = landmarks[knee_key]

        # Store landmarks in buffer
        self.landmark_buffer.append({
            "ankle": ankle,
            "heel": heel,
            "toe": toe,
            "knee": knee,
            "frame": frame_number
        })

        # Update velocity tracker
        timestamp = frame_number / self.fps
        ankle_pos = (ankle.x * image_width, ankle.y * image_height)
        velocity_data = self.velocity_tracker.update(ankle_pos, timestamp)

        # Increment phase frame counter
        self.frame_in_phase += 1

        # State machine logic
        new_classification = None

        if self.current_phase == GaitPhase.SWING:
            # In swing phase: wait for ground contact
            if velocity_data and self.contact_detector.detect_contact(
                ankle, velocity_data, image_height
            ):
                # Transition to CONTACT phase
                self._transition_to(GaitPhase.CONTACT)

                # CLASSIFY at this instant
                new_classification = self._classify_at_contact(
                    ankle, heel, toe, knee, frame_number, image_width, image_height
                )

                if new_classification:
                    self.last_classification = new_classification
                    self.classification_history.append(new_classification)
                    self.successful_classifications += 1

        elif self.current_phase == GaitPhase.CONTACT:
            # Short phase: immediately transition to STANCE
            if self.frame_in_phase >= 2:  # Stay in CONTACT for 2 frames
                self._transition_to(GaitPhase.STANCE)

        elif self.current_phase == GaitPhase.STANCE:
            # In stance phase: wait for toe-off
            if velocity_data and self.contact_detector.detect_toe_off(toe, velocity_data):
                self._transition_to(GaitPhase.TOE_OFF)
            # Or timeout after reasonable stance duration (~15 frames at 30fps)
            elif self.frame_in_phase > 20:
                self._transition_to(GaitPhase.TOE_OFF)

        elif self.current_phase == GaitPhase.TOE_OFF:
            # Short phase: immediately return to SWING
            if self.frame_in_phase >= 2:
                self._transition_to(GaitPhase.SWING)
                self.total_cycles += 1

        return (self.current_phase, new_classification)

    def _transition_to(self, new_phase: GaitPhase):
        """
        Transition to a new gait phase.

        Args:
            new_phase: Phase to transition to
        """
        self.current_phase = new_phase
        self.frame_in_phase = 0

    def _classify_at_contact(
        self,
        ankle: LandmarkPoint,
        heel: LandmarkPoint,
        toe: LandmarkPoint,
        knee: LandmarkPoint,
        frame_number: int,
        image_width: int,
        image_height: int
    ) -> Optional[GaitClassification]:
        """
        Classify gait type at the moment of ground contact.

        Uses multiple biomechanical criteria for robust classification:
        1. Vertical position ratio (heel vs toe)
        2. Ankle angle (dorsiflexion vs plantarflexion)
        3. Horizontal foot position relative to knee
        4. Knee extension angle

        Args:
            ankle, heel, toe, knee: Landmark points
            frame_number: Frame number of contact
            image_width, image_height: Image dimensions

        Returns:
            GaitClassification with consensus result
        """
        # Convert to pixel coordinates
        heel_px = (heel.x * image_width, heel.y * image_height)
        toe_px = (toe.x * image_width, toe.y * image_height)
        ankle_px = (ankle.x * image_width, ankle.y * image_height)
        knee_px = (knee.x * image_width, knee.y * image_height)

        # Initialize scores for each criterion
        scores = {
            "vertical_position": 0.0,
            "horizontal_position": 0.0,
            "ankle_angle": 0.0,
            "knee_angle": 0.0
        }

        # CRITERION 1: Vertical Position Ratio
        # Heel lower than toe → heel strike
        # Toe lower than heel → forefoot strike
        vertical_ratio = heel_px[1] / toe_px[1] if toe_px[1] > 0 else 1.0

        if vertical_ratio >= 1.02:  # Heel significantly lower
            scores["vertical_position"] = 1.0  # Heel strike
        elif vertical_ratio <= 0.95:  # Toe significantly lower
            scores["vertical_position"] = -1.0  # Forefoot strike
        else:
            scores["vertical_position"] = 0.0  # Midfoot

        # CRITERION 2: Horizontal Position (Foot vs Knee)
        # Foot ahead of knee → extended leg → heel strike
        # Foot under/behind knee → flexed leg → forefoot strike
        horizontal_offset = toe_px[0] - knee_px[0]

        if horizontal_offset > 30:  # Foot well ahead
            scores["horizontal_position"] = 1.0  # Heel strike
        elif horizontal_offset < -20:  # Foot behind
            scores["horizontal_position"] = -1.0  # Forefoot strike
        else:
            scores["horizontal_position"] = 0.0  # Midfoot

        # CRITERION 3: Ankle Angle
        # Calculate ankle angle (simplified)
        # Large angle → dorsiflexion → heel strike
        # Small angle → plantarflexion → forefoot strike
        ankle_vector = np.array([toe_px[0] - ankle_px[0], toe_px[1] - ankle_px[1]])
        knee_ankle_vector = np.array([ankle_px[0] - knee_px[0], ankle_px[1] - knee_px[1]])

        # Angle between vectors
        cos_angle = np.dot(ankle_vector, knee_ankle_vector) / (
            np.linalg.norm(ankle_vector) * np.linalg.norm(knee_ankle_vector) + 1e-6
        )
        ankle_angle = np.degrees(np.arccos(np.clip(cos_angle, -1.0, 1.0)))

        if ankle_angle > 100:  # Extended ankle
            scores["ankle_angle"] = 1.0  # Heel strike
        elif ankle_angle < 80:  # Flexed ankle
            scores["ankle_angle"] = -1.0  # Forefoot strike
        else:
            scores["ankle_angle"] = 0.0  # Midfoot

        # CRITERION 4: Knee Extension
        # Get hip landmark if available for knee angle
        hip_key = f"{self.side}_hip"
        if len(self.landmark_buffer) > 0 and hip_key in self.landmark_buffer[-1]:
            # Calculate knee angle (simplified estimation)
            # More extended knee → heel strike
            # More flexed knee → forefoot strike
            knee_flexion_estimate = knee_px[1] - ankle_px[1]  # Simplified

            if knee_flexion_estimate > 100:  # More extended
                scores["knee_angle"] = 0.5  # Weak signal for heel strike
            elif knee_flexion_estimate < 60:  # More flexed
                scores["knee_angle"] = -0.5  # Weak signal for forefoot
            else:
                scores["knee_angle"] = 0.0

        # Aggregate scores
        total_score = sum(scores.values())
        num_criteria = len([s for s in scores.values() if s != 0.0])

        # Classify based on consensus
        if total_score > 1.5:
            gait_type = GaitType.HEEL_STRIKE
            confidence = min(95.0, 60.0 + (total_score / 4.0) * 35.0)
            reasoning = "Strong heel strike indicators across multiple criteria"
        elif total_score < -1.5:
            gait_type = GaitType.FOREFOOT_STRIKE
            confidence = min(95.0, 60.0 + (abs(total_score) / 4.0) * 35.0)
            reasoning = "Strong forefoot strike indicators across multiple criteria"
        else:
            gait_type = GaitType.MIDFOOT_STRIKE
            confidence = 50.0 + abs(total_score) * 10.0
            reasoning = "Mixed or neutral indicators suggest midfoot strike"

        # Boost confidence if multiple criteria agree
        if num_criteria >= 3:
            confidence += 10.0

        confidence = min(100.0, confidence)

        return GaitClassification(
            gait_type=gait_type,
            confidence=confidence,
            contact_frame=frame_number,
            biomechanical_scores=scores,
            reasoning=reasoning
        )

    def get_statistics(self) -> Dict:
        """
        Get performance statistics of the state machine.

        Returns:
            Dictionary with cycle counts and success rates
        """
        success_rate = (
            (self.successful_classifications / max(1, self.total_cycles)) * 100.0
        )

        avg_confidence = 0.0
        if self.classification_history:
            avg_confidence = np.mean([c.confidence for c in self.classification_history])

        return {
            "total_cycles": self.total_cycles,
            "successful_classifications": self.successful_classifications,
            "success_rate": success_rate,
            "average_confidence": avg_confidence,
            "current_phase": self.current_phase.value
        }

    def reset(self):
        """Reset the state machine to initial state."""
        self.current_phase = GaitPhase.SWING
        self.frame_in_phase = 0
        self.velocity_tracker.reset()
        self.contact_detector.contact_cooldown = 0
        self.landmark_buffer.clear()
        self.last_classification = None
