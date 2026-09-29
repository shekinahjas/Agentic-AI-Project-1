"""
Side-Effect Delay Calculator
Quantifies the delay imposed on cross-traffic and non-emergency vehicles
during corridor holding.
"""
from typing import List, Dict

class DelayCalculator:
    """
    Computes vehicular queue buildup and side-effect delay.
    When a junction is held for T seconds, cross-traffic arrivals accumulate.
    Average additional delay per stopped vehicle = T / 2.
    For a 50-second hold, the average extra delay to normal traffic = 25 sec.
    """
    def __init__(self, default_arrival_rate: float = 0.20):
        # Default 0.20 veh/sec (12 vehicles/minute per cross approach)
        self.default_arrival_rate = default_arrival_rate

    def calculate_delay(self, held_junction_ids: List[str], hold_duration_seconds: float) -> Dict:
        """
        Calculates side-effect delay metrics for a given hold duration.
        """
        if hold_duration_seconds <= 0 or not held_junction_ids:
            return {
                "hold_duration_sec": 0,
                "avg_extra_delay_per_vehicle_sec": 0,
                "total_queued_vehicles": 0,
                "total_network_delay_veh_sec": 0,
                "held_junctions": held_junction_ids,
                "summary_display": "Normal traffic flow (0 sec delay)"
            }

        # Average extra delay experienced by a vehicle waiting at the held cross-street
        # Since vehicles arrive uniformly during the hold window [0, T],
        # the average wait time imposed is T / 2.
        avg_extra_delay = round(hold_duration_seconds / 2.0, 1)

        total_queued = 0
        total_veh_sec = 0.0

        for j_id in held_junction_ids:
            # Assume 0.20 vehicles/sec on each cross approach
            queued = round(self.default_arrival_rate * hold_duration_seconds, 1)
            # Area under triangular queue accumulation: 0.5 * lambda * T^2
            delay_for_junction = 0.5 * self.default_arrival_rate * (hold_duration_seconds ** 2)

            total_queued += queued
            total_veh_sec += delay_for_junction

        return {
            "hold_duration_sec": hold_duration_seconds,
            "avg_extra_delay_per_vehicle_sec": avg_extra_delay,
            "total_queued_vehicles": round(total_queued),
            "total_network_delay_veh_sec": round(total_veh_sec, 1),
            "held_junctions": held_junction_ids,
            "summary_display": f"{int(avg_extra_delay)} sec extra delay to normal traffic"
        }
