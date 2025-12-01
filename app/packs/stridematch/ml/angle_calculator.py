"""
Biomechanical angle calculator for gait analysis.

This module provides functions to calculate joint angles from pose landmarks,
critical for analyzing running biomechanics and gait patterns.
"""

import numpy as np
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass

from .pose_estimator import LandmarkPoint


@dataclass
class BiomechanicalAngles:
    """Container for biomechanical joint angles."""
    knee_right: Optional[float] = None  # Right knee angle (degrees)
    knee_left: Optional[float] = None   # Left knee angle (degrees)
    ankle_right: Optional[float] = None  # Right ankle angle (degrees)
    ankle_left: Optional[float] = None   # Left ankle angle (degrees)
    hip_right: Optional[float] = None    # Right hip angle (degrees)
    hip_left: Optional[float] = None     # Left hip angle (degrees)
    trunk: Optional[float] = None        # Trunk lean angle (degrees)


def calculate_angle(
    point_a: Tuple[float, float],
    point_b: Tuple[float, float],
    point_c: Tuple[float, float]
) -> float:
    """
    Calculate the angle formed by three points (A-B-C) where B is the vertex.

    The angle is calculated using the arctangent of the vectors BA and BC.
    This is a standard biomechanical angle calculation method.

    Args:
        point_a: First point (x, y) coordinates
        point_b: Vertex point (x, y) coordinates - the joint
        point_c: Third point (x, y) coordinates

    Returns:
        Angle in degrees (0-180)

    Example:
        For knee angle:
        - point_a = hip position
        - point_b = knee position (vertex)
        - point_c = ankle position
    """
    # Convert points to numpy arrays
    a = np.array(point_a)
    b = np.array(point_b)
    c = np.array(point_c)

    # Calculate vectors
    ba = a - b  # Vector from B to A
    bc = c - b  # Vector from B to C

    # Calculate angle using dot product and arctangent
    # cos(θ) = (ba · bc) / (||ba|| * ||bc||)
    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))

    # Clamp to [-1, 1] to avoid numerical errors
    cosine_angle = np.clip(cosine_angle, -1.0, 1.0)

    # Calculate angle in radians then convert to degrees
    angle_radians = np.arccos(cosine_angle)
    angle_degrees = np.degrees(angle_radians)

    return float(angle_degrees)


def calculate_angle_alternative(
    point_a: Tuple[float, float],
    point_b: Tuple[float, float],
    point_c: Tuple[float, float]
) -> float:
    """
    Alternative angle calculation using arctangent method.

    This method uses atan2 to calculate the angle between two vectors,
    which can be more robust in some edge cases.

    Args:
        point_a: First point (x, y) coordinates
        point_b: Vertex point (x, y) coordinates
        point_c: Third point (x, y) coordinates

    Returns:
        Angle in degrees (0-180)
    """
    a = np.array(point_a)
    b = np.array(point_b)
    c = np.array(point_c)

    # Calculate angles of the two vectors relative to horizontal
    radians_a = np.arctan2(a[1] - b[1], a[0] - b[0])
    radians_c = np.arctan2(c[1] - b[1], c[0] - b[0])

    # Calculate the difference
    angle = np.abs(radians_a - radians_c)

    # Convert to degrees
    angle = np.degrees(angle)

    # Ensure angle is in [0, 180] range
    if angle > 180.0:
        angle = 360.0 - angle

    return float(angle)


def extract_point_2d(
    landmark: LandmarkPoint,
    image_width: int = 1,
    image_height: int = 1
) -> Tuple[float, float]:
    """
    Extract 2D coordinates from a landmark.

    Args:
        landmark: LandmarkPoint object
        image_width: Image width for scaling (default 1 for normalized)
        image_height: Image height for scaling (default 1 for normalized)

    Returns:
        Tuple of (x, y) coordinates
    """
    x = landmark.x * image_width
    y = landmark.y * image_height
    return (x, y)


def calculate_biomechanical_angles(
    landmarks: Dict[str, LandmarkPoint],
    image_width: int = 1280,
    image_height: int = 720,
    side: str = "right"
) -> BiomechanicalAngles:
    """
    Calculate all biomechanical angles from pose landmarks.

    Args:
        landmarks: Dictionary of pose landmarks
        image_width: Image width in pixels
        image_height: Image height in pixels
        side: Which side to analyze ("right", "left", or "both")

    Returns:
        BiomechanicalAngles object with calculated angles
    """
    angles = BiomechanicalAngles()

    try:
        # RIGHT SIDE ANALYSIS
        if side in ["right", "both"]:
            # Right knee angle (hip - knee - ankle)
            if all(k in landmarks for k in ["right_hip", "right_knee", "right_ankle"]):
                hip = extract_point_2d(landmarks["right_hip"], image_width, image_height)
                knee = extract_point_2d(landmarks["right_knee"], image_width, image_height)
                ankle = extract_point_2d(landmarks["right_ankle"], image_width, image_height)

                angles.knee_right = calculate_angle(hip, knee, ankle)

            # Right ankle angle (knee - ankle - foot_index)
            if all(k in landmarks for k in ["right_knee", "right_ankle", "right_foot_index"]):
                knee = extract_point_2d(landmarks["right_knee"], image_width, image_height)
                ankle = extract_point_2d(landmarks["right_ankle"], image_width, image_height)
                foot = extract_point_2d(landmarks["right_foot_index"], image_width, image_height)

                angles.ankle_right = calculate_angle(knee, ankle, foot)

            # Right hip angle (shoulder - hip - knee)
            if all(k in landmarks for k in ["right_shoulder", "right_hip", "right_knee"]):
                shoulder = extract_point_2d(landmarks["right_shoulder"], image_width, image_height)
                hip = extract_point_2d(landmarks["right_hip"], image_width, image_height)
                knee = extract_point_2d(landmarks["right_knee"], image_width, image_height)

                angles.hip_right = calculate_angle(shoulder, hip, knee)

        # LEFT SIDE ANALYSIS
        if side in ["left", "both"]:
            # Left knee angle (hip - knee - ankle)
            if all(k in landmarks for k in ["left_hip", "left_knee", "left_ankle"]):
                hip = extract_point_2d(landmarks["left_hip"], image_width, image_height)
                knee = extract_point_2d(landmarks["left_knee"], image_width, image_height)
                ankle = extract_point_2d(landmarks["left_ankle"], image_width, image_height)

                angles.knee_left = calculate_angle(hip, knee, ankle)

            # Left ankle angle (knee - ankle - foot_index)
            if all(k in landmarks for k in ["left_knee", "left_ankle", "left_foot_index"]):
                knee = extract_point_2d(landmarks["left_knee"], image_width, image_height)
                ankle = extract_point_2d(landmarks["left_ankle"], image_width, image_height)
                foot = extract_point_2d(landmarks["left_foot_index"], image_width, image_height)

                angles.ankle_left = calculate_angle(knee, ankle, foot)

            # Left hip angle (shoulder - hip - knee)
            if all(k in landmarks for k in ["left_shoulder", "left_hip", "left_knee"]):
                shoulder = extract_point_2d(landmarks["left_shoulder"], image_width, image_height)
                hip = extract_point_2d(landmarks["left_hip"], image_width, image_height)
                knee = extract_point_2d(landmarks["left_knee"], image_width, image_height)

                angles.hip_left = calculate_angle(shoulder, hip, knee)

        # TRUNK ANGLE (forward lean)
        # Calculate angle between vertical and line from hip to shoulder
        if side in ["right", "both"] and all(k in landmarks for k in ["right_shoulder", "right_hip"]):
            shoulder = extract_point_2d(landmarks["right_shoulder"], image_width, image_height)
            hip = extract_point_2d(landmarks["right_hip"], image_width, image_height)

            # Create a vertical reference point directly above the hip
            vertical_point = (hip[0], hip[1] - 100)  # 100 pixels above

            # Calculate angle from vertical
            angles.trunk = calculate_angle(vertical_point, hip, shoulder)

    except Exception as e:
        # If any calculation fails, return partially filled angles
        print(f"Warning: Angle calculation error: {e}")

    return angles


def aggregate_angles(
    angle_history: List[BiomechanicalAngles]
) -> BiomechanicalAngles:
    """
    Aggregate angles from multiple frames to get average values.

    Args:
        angle_history: List of BiomechanicalAngles from different frames

    Returns:
        BiomechanicalAngles with averaged values
    """
    if not angle_history:
        return BiomechanicalAngles()

    # Collect all non-None values for each angle
    knee_right_vals = [a.knee_right for a in angle_history if a.knee_right is not None]
    knee_left_vals = [a.knee_left for a in angle_history if a.knee_left is not None]
    ankle_right_vals = [a.ankle_right for a in angle_history if a.ankle_right is not None]
    ankle_left_vals = [a.ankle_left for a in angle_history if a.ankle_left is not None]
    hip_right_vals = [a.hip_right for a in angle_history if a.hip_right is not None]
    hip_left_vals = [a.hip_left for a in angle_history if a.hip_left is not None]
    trunk_vals = [a.trunk for a in angle_history if a.trunk is not None]

    # Calculate averages
    return BiomechanicalAngles(
        knee_right=np.mean(knee_right_vals) if knee_right_vals else None,
        knee_left=np.mean(knee_left_vals) if knee_left_vals else None,
        ankle_right=np.mean(ankle_right_vals) if ankle_right_vals else None,
        ankle_left=np.mean(ankle_left_vals) if ankle_left_vals else None,
        hip_right=np.mean(hip_right_vals) if hip_right_vals else None,
        hip_left=np.mean(hip_left_vals) if hip_left_vals else None,
        trunk=np.mean(trunk_vals) if trunk_vals else None,
    )


def angles_to_dict(angles: BiomechanicalAngles) -> Dict[str, float]:
    """
    Convert BiomechanicalAngles to a dictionary for JSON serialization.

    Args:
        angles: BiomechanicalAngles object

    Returns:
        Dictionary with angle values
    """
    result = {}

    if angles.knee_right is not None:
        result["knee_right"] = round(angles.knee_right, 2)
    if angles.knee_left is not None:
        result["knee_left"] = round(angles.knee_left, 2)
    if angles.ankle_right is not None:
        result["ankle_right"] = round(angles.ankle_right, 2)
    if angles.ankle_left is not None:
        result["ankle_left"] = round(angles.ankle_left, 2)
    if angles.hip_right is not None:
        result["hip_right"] = round(angles.hip_right, 2)
    if angles.hip_left is not None:
        result["hip_left"] = round(angles.hip_left, 2)
    if angles.trunk is not None:
        result["trunk"] = round(angles.trunk, 2)

    return result
