"""
School-Zone and Ambulance Corridor Agent
The core agent that coordinates the corridor signals based on:
1. School Timetable & Crosswalk Priority
2. Inbound Ambulance Telemetry & Route / Fallback Planning
3. Hold-time Cap and Human Approval Gate
4. Quantifying Side-Effect Traffic Delay
"""
from dataclasses import dataclass
from typing import Dict, List, Optional
from corridor_network import CorridorNetwork
from school_zone import SchoolZoneController
from delay_calculator import DelayCalculator
from hold_controller import HoldController

@dataclass
class AmbulanceRequest:
    request_id: str
    eta_seconds: float
    is_active: bool = True
    speed_kmh: float = 65.0
    destination: str = "Regional Trauma Hospital"

class CorridorAgent:
    """
    Agentic coordinator implementing:
    - Bell window pedestrian extension (20s -> 40s)
    - Ambulance corridor listing, hold scheduling, fallback if blocked
    - Side-effect delay printing on card
    - Max hold cap (60s) + HITL approval gate
    - Mandatory safety invariant: Never steal pedestrian time
    """
    def __init__(self):
        self.network = CorridorNetwork()
        self.school_zone = SchoolZoneController()
        self.delay_calculator = DelayCalculator(default_arrival_rate=0.20)
        self.hold_controller = HoldController()
        self.active_ambulance: Optional[AmbulanceRequest] = None
        self.log_messages: List[str] = []

    def log(self, message: str):
        self.log_messages.append(message)

    # -------------------------------------------------------------
    # DEMO 1: School Bell Handling
    # -------------------------------------------------------------
    def process_school_bell(self, force_bell: Optional[bool] = None, current_time: Optional[str] = None) -> Dict:
        """
        Demo 1 execution logic:
        Checks bell window. If bell detected, lengthens pedestrian green from 20s to 40s.
        """
        if force_bell is not None:
            self.school_zone.manual_bell_override = force_bell

        bell_active = self.school_zone.is_bell_active(current_time)
        policy = self.school_zone.evaluate_crossing_policy(bell_active)

        if bell_active:
            self.log("🔔 [SCHOOL ZONE] School bell detected! Pedestrian green extended to 40s.")
        else:
            self.log("ℹ️ [SCHOOL ZONE] Normal baseline cycle: Pedestrian green 20s.")

        return {
            "normal_pedestrian_green": "20 sec",
            "school_bell_detected": bell_active,
            "active_pedestrian_green": f"{policy['pedestrian_green_sec']} sec",
            "reason": policy["reason"]
        }

    # -------------------------------------------------------------
    # DEMO 2: Ambulance Corridor & Fallback Handling
    # -------------------------------------------------------------
    def request_ambulance_corridor(self, eta_seconds: float = 120.0, is_j2_blocked: bool = False) -> Dict:
        """
        Demo 2 execution logic:
        Inbound ambulance request (~2 mins out / 120s).
        Identifies route, fallback if blocked, holds junctions, and calculates extra delay.
        """
        self.active_ambulance = AmbulanceRequest(
            request_id="AMB-911-ALPHA",
            eta_seconds=eta_seconds,
            is_active=True
        )

        # Set network blockage state
        self.network.set_blocked_status("J2", is_j2_blocked)

        # Check safety invariant: Never steal pedestrian time
        crossing_check = self.school_zone.request_ambulance_preemption()

        # Compute corridor route
        route = self.network.get_corridor_route(is_j2_blocked)
        held_junctions = list(route)

        # Update junction statuses in shared map
        self.network.reset_all_statuses()
        for j_id in held_junctions:
            self.network.update_junction_status(j_id, "HELD")

        # Flag other connected nodes as delayed
        if is_j2_blocked:
            self.network.update_junction_status("J2", "DELAYED")

        # Start hold controller
        self.hold_controller.start_hold()

        # Compute initial side-effect delay for demonstration (50s hold benchmark produces 25s extra delay)
        demo_hold_time = 50.0  # seconds
        delay_info = self.delay_calculator.calculate_delay(held_junctions, demo_hold_time)

        self.log(f"🚑 [AMBULANCE] Request received. Inbound corridor: {' → '.join(route)}.")
        self.log(f"🛑 [HOLD] Holding junctions: {', '.join(held_junctions)}.")
        self.log(f"⏱️ [DELAY] Side-effect extra delay to normal traffic: {delay_info['summary_display']}.")

        return {
            "request_id": self.active_ambulance.request_id,
            "eta_seconds": eta_seconds,
            "route": route,
            "route_display": " → ".join(route),
            "holding_junctions": held_junctions,
            "is_fallback_active": is_j2_blocked,
            "fallback_note": "Fallback bypass via J4 active because J2 is blocked." if is_j2_blocked else "Primary path active.",
            "crossing_safety_check": crossing_check,
            "extra_delay_to_normal_traffic": f"{int(delay_info['avg_extra_delay_per_vehicle_sec'])} sec",
            "total_delay_metrics": delay_info
        }

    def update_hold_simulation(self, elapsed_seconds: int) -> Dict:
        """
        Advances the hold timer to test Rule 1 (Hold cap) and Rule 2 (Human approval).
        """
        route = self.network.get_corridor_route()
        held_junctions = list(route)

        cap_info = self.hold_controller.set_elapsed_seconds(elapsed_seconds)
        delay_info = self.delay_calculator.calculate_delay(held_junctions, float(elapsed_seconds))

        if cap_info["gate_visible"]:
            self.log(f"⚠️ [HOLD CAP] Maximum hold of {cap_info['cap']}s reached! AI cannot extend. Human approval required.")

        return {
            "elapsed_seconds": elapsed_seconds,
            "hold_controller_state": cap_info,
            "delay_metrics": delay_info,
            "gate_visible": cap_info["gate_visible"]
        }

    def approve_human_extension(self) -> Dict:
        """Operator clicks 'Extend Hold (+30s)'."""
        res = self.hold_controller.human_extend_click()
        if res["success"]:
            self.log(f"✅ [HUMAN APPROVAL] Fresh human click received. {res['message']}")
        return res

    def clear_corridor(self) -> Dict:
        """Releases corridor holds back to normal cycle."""
        self.network.reset_all_statuses()
        self.hold_controller.release_hold()
        self.active_ambulance = None
        self.log("🏁 [CORRIDOR] Ambulance cleared. Signals released to normal cycles.")
        return {"status": "NORMAL"}
