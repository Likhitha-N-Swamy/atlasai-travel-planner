# backend/utils/travel_time.py
from typing import Literal

def estimate_travel_time_minutes(distance_m: float, mode: Literal["walking","driving"]="driving") -> int:
    """
    Estimate travel time in minutes from distance in meters.
    walking: 5 km/h (5000 m/h) => 83.333 m/min
    driving: 40 km/h (40000 m/h) => 666.66 m/min
    """
    if distance_m is None:
        return 0
    if mode == "walking":
        speed_m_per_min = 5000 / 60.0
    else:
        speed_m_per_min = 40000 / 60.0
    mins = distance_m / speed_m_per_min
    return int(round(mins))
