"""
Corridor Network Topology Definition
Represents junctions J1, J2, J3, fallback J4, and school crosswalk C1.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class Junction:
    id: str
    name: str
    description: str
    x: float
    y: float
    has_crossing: bool = False
    cross_arrival_rate: float = 0.2  # vehicles/sec arriving on cross streets
    is_blocked: bool = False
    status: str = "NORMAL"  # "NORMAL", "DELAYED", "HELD"
    hold_start_time: Optional[float] = None
    hold_end_time: Optional[float] = None

class CorridorNetwork:
    """
    Corridor topology:
    Ambulance Entry -> J1 -> J2 (School Zone) -> J3 (Hospital Exit)
    Fallback Bypass: J1 -> J4 -> J3
    """
    def __init__(self):
        self.junctions: Dict[str, Junction] = {
            "J1": Junction(
                id="J1",
                name="Corridor Entry (West)",
                description="Entry point for ambulance into arterial corridor",
                x=120,
                y=250,
                has_crossing=False,
                cross_arrival_rate=0.20
            ),
            "J2": Junction(
                id="J2",
                name="School Zone Crossing",
                description="High pedestrian volume intersection with marked crosswalk C1",
                x=380,
                y=250,
                has_crossing=True,
                cross_arrival_rate=0.25
            ),
            "J3": Junction(
                id="J3",
                name="Hospital Approach (East)",
                description="Exit node connecting corridor to emergency trauma center",
                x=640,
                y=250,
                has_crossing=False,
                cross_arrival_rate=0.18
            ),
            "J4": Junction(
                id="J4",
                name="North Bypass (Fallback)",
                description="Auxiliary bypass node used if J2 is obstructed",
                x=380,
                y=110,
                has_crossing=False,
                cross_arrival_rate=0.10
            )
        }

    def get_corridor_route(self, is_j2_blocked: bool = False) -> List[str]:
        """
        Determines corridor route: primary [J1, J2, J3], or fallback [J1, J4, J3] if J2 is blocked.
        """
        if is_j2_blocked or self.junctions["J2"].is_blocked:
            return ["J1", "J4", "J3"]
        return ["J1", "J2", "J3"]

    def set_blocked_status(self, junction_id: str, blocked: bool):
        if junction_id in self.junctions:
            self.junctions[junction_id].is_blocked = blocked

    def update_junction_status(self, junction_id: str, status: str):
        if junction_id in self.junctions:
            self.junctions[junction_id].status = status

    def reset_all_statuses(self):
        for j in self.junctions.values():
            j.status = "NORMAL"
            j.hold_start_time = None
            j.hold_end_time = None
