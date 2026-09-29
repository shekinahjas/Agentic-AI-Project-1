"""
Unit & Integration Verification Tests for School-Zone and Ambulance Corridor Agent
"""
import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
from corridor_agent import CorridorAgent

def run_all_tests():
    print("=================================================================")
    print("STARTING TEST SUITE: School-Zone & Ambulance Corridor Agent")
    print("=================================================================")

    agent = CorridorAgent()

    # TEST 1: Baseline Pedestrian Green (Demo 1 Baseline)
    print("\n--- TEST 1: Baseline Pedestrian Green ---")
    res_normal = agent.process_school_bell(force_bell=False)
    assert res_normal["normal_pedestrian_green"] == "20 sec"
    assert res_normal["active_pedestrian_green"] == "20 sec"
    assert res_normal["school_bell_detected"] is False
    print("[OK] Normal Pedestrian Green = 20 sec confirmed.")

    # TEST 2: School Bell Detected (Demo 1 Bell Trigger)
    print("\n--- TEST 2: School Bell Detected (Demo 1) ---")
    res_bell = agent.process_school_bell(force_bell=True)
    assert res_bell["school_bell_detected"] is True
    assert res_bell["active_pedestrian_green"] == "40 sec"
    print("[OK] School Bell Detected! Pedestrian Green = 40 sec confirmed.")

    # TEST 3: Ambulance Request & Corridor Hold (Demo 2 Standard Run)
    print("\n--- TEST 3: Ambulance Request & Corridor Hold (Demo 2) ---")
    res_amb = agent.request_ambulance_corridor(eta_seconds=120.0, is_j2_blocked=False)
    assert res_amb["route"] == ["J1", "J2", "J3"]
    assert res_amb["holding_junctions"] == ["J1", "J2", "J3"]
    assert res_amb["extra_delay_to_normal_traffic"] == "25 sec"
    print(f"[OK] Route: {res_amb['route_display']}")
    print(f"[OK] Holding: {', '.join(res_amb['holding_junctions'])}")
    print(f"[OK] Extra delay to normal traffic: {res_amb['extra_delay_to_normal_traffic']}")

    # TEST 4: Fallback Routing when J2 is Blocked
    print("\n--- TEST 4: Fallback Route Planner ---")
    res_fallback = agent.request_ambulance_corridor(eta_seconds=120.0, is_j2_blocked=True)
    assert res_fallback["route"] == ["J1", "J4", "J3"]
    assert res_fallback["holding_junctions"] == ["J1", "J4", "J3"]
    assert res_fallback["is_fallback_active"] is True
    print(f"[OK] Blocked node detection successful. Fallback route: {res_fallback['route_display']}")

    # TEST 5: Rule 1 — Hold-Time Cap (60 seconds)
    print("\n--- TEST 5: Rule 1 — Hold-Time Cap (60s) ---")
    # Hold for 30s: Safe holding
    hold_30 = agent.update_hold_simulation(30)
    assert hold_30["gate_visible"] is False
    assert hold_30["hold_controller_state"]["status"] == "HOLDING"
    print("[OK] 30s elapsed: within safe cap, gate not visible.")

    # Hold reaches 60s: Cap reached!
    hold_60 = agent.update_hold_simulation(60)
    assert hold_60["gate_visible"] is True
    assert hold_60["hold_controller_state"]["status"] == "CAP_REACHED_AWAITING_HUMAN"
    print("[OK] 60s elapsed: Rule 1 Enforced! Hold cap reached, Gate Visible.")

    # TEST 6: Rule 2 — Human Approval To Extend (+30s)
    print("\n--- TEST 6: Rule 2 — Human Approval To Extend ---")
    # Operator clicks extend
    extend_res = agent.approve_human_extension()
    assert extend_res["success"] is True
    assert extend_res["new_cap"] == 90
    print(f"[OK] Fresh human click processed: {extend_res['message']}")
    
    # Check updated state at 70s (now within the 90s extended cap)
    hold_70 = agent.update_hold_simulation(70)
    assert hold_70["gate_visible"] is False
    assert hold_70["hold_controller_state"]["cap"] == 90
    print("[OK] 70s elapsed: within extended cap (90s), holding continues safely.")

    # TEST 7: Mandatory Invariant — Never Steal Pedestrian Crossing Time
    print("\n--- TEST 7: Mandatory Invariant — Crossing Protection ---")
    agent.school_zone.trigger_pedestrian_crossing(bell_active=True)
    preempt_res = agent.school_zone.request_ambulance_preemption()
    assert preempt_res["permitted"] is False
    assert preempt_res["action"] == "HOLD_EMERGENCY_AT_UPSTREAM"
    print("[OK] Crossing Invariant Verified: Stealing time from active crossing is strictly blocked!")

    print("\n=================================================================")
    print("ALL 7 CRITICAL AGENT TESTS PASSED SUCCESSFULLY!")
    print("=================================================================")

if __name__ == "__main__":
    run_all_tests()
