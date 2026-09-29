"""
School Zone Controller & Timetable Engine
Manages pedestrian crossing duration at marked school crosswalk C1 (at J2).
Enforces the mandatory safety invariant: NEVER steal time from a marked crossing to save cars.
"""
from dataclasses import dataclass
from typing import List, Dict, Optional
import datetime

@dataclass
class TimetableEntry:
    name: str
    start_time: str  # "HH:MM:SS"
    end_time: str    # "HH:MM:SS"

class SchoolZoneController:
    """
    Manages school bell detection and pedestrian green interval.
    Normal pedestrian green: 20s
    School bell pedestrian green: 40s
    """
    NORMAL_PED_GREEN: int = 20
    BELL_PED_GREEN: int = 40

    def __init__(self):
        # Default mock timetable
        self.timetable: List[TimetableEntry] = [
            TimetableEntry("Morning Arrival Bell", "08:15:00", "08:45:00"),
            TimetableEntry("Mid-day Kindergarten Bell", "11:45:00", "12:15:00"),
            TimetableEntry("Afternoon Dismissal Bell", "15:00:00", "15:30:00")
        ]
        self.manual_bell_override: bool = False
        self.pedestrian_phase_active: bool = False
        self.pedestrian_time_remaining: int = 0
        self.current_ped_green_setting: int = self.NORMAL_PED_GREEN

    def is_bell_active(self, current_time_str: Optional[str] = None) -> bool:
        """
        Determines whether the school bell window is active via timetable or manual demo trigger.
        """
        if self.manual_bell_override:
            return True

        if current_time_str:
            try:
                cur_t = datetime.datetime.strptime(current_time_str, "%H:%M:%S").time()
                for entry in self.timetable:
                    start_t = datetime.datetime.strptime(entry.start_time, "%H:%M:%S").time()
                    end_t = datetime.datetime.strptime(entry.end_time, "%H:%M:%S").time()
                    if start_t <= cur_t <= end_t:
                        return True
            except ValueError:
                pass
        return False

    def evaluate_crossing_policy(self, bell_active: bool) -> Dict:
        """
        Evaluates green time based on bell status.
        Returns policy details.
        """
        if bell_active:
            self.current_ped_green_setting = self.BELL_PED_GREEN
            reason = "School bell detected! Foot traffic prioritized."
        else:
            self.current_ped_green_setting = self.NORMAL_PED_GREEN
            reason = "Standard school zone cycle."

        return {
            "bell_detected": bell_active,
            "pedestrian_green_sec": self.current_ped_green_setting,
            "normal_baseline_sec": self.NORMAL_PED_GREEN,
            "reason": reason
        }

    def trigger_pedestrian_crossing(self, bell_active: bool):
        """
        Starts active pedestrian crossing countdown.
        """
        self.pedestrian_phase_active = True
        self.current_ped_green_setting = self.BELL_PED_GREEN if bell_active else self.NORMAL_PED_GREEN
        self.pedestrian_time_remaining = self.current_ped_green_setting

    def request_ambulance_preemption(self) -> Dict:
        """
        Enforces Mandatory Safety Invariant:
        'Never steal time from a marked crossing to save cars.'
        If pedestrian phase is active, emergency preemption CANNOT cancel or truncate it.
        """
        if self.pedestrian_phase_active and self.pedestrian_time_remaining > 0:
            return {
                "permitted": False,
                "action": "HOLD_EMERGENCY_AT_UPSTREAM",
                "message": (
                    f"SAFETY INVARIANT ENFORCED: Pedestrian crossing active at J2 "
                    f"({self.pedestrian_time_remaining}s remaining). "
                    f"Time will NOT be stolen from marked crossing. "
                    f"Ambulance corridor held at J1 until crossing clears."
                ),
                "safe_clearance_seconds": self.pedestrian_time_remaining
            }
        return {
            "permitted": True,
            "action": "LOCK_CORRIDOR",
            "message": "Crossing clear. Corridor lock permitted."
        }
