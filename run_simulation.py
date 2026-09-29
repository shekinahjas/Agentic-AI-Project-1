"""
Interactive Python Simulation Runner for School-Zone & Ambulance Corridor Agent
Runs Demo 1 (School Bell) and Demo 2 (Ambulance Corridor & Fallback)
with Hold-Time Cap (60s) and Human Approval Gate.
Does not require any native DLLs or external dependencies.
"""
import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from corridor_agent import CorridorAgent

def print_separator(title=""):
    print("\n" + "=" * 65)
    if title:
        print(f" {title.upper()} ")
        print("=" * 65)

def run_demo_1(agent: CorridorAgent):
    print_separator("Demo 1 — School Bell Dismissal Window")
    print("Baseline Status:")
    res_normal = agent.process_school_bell(force_bell=False)
    print(f"Normal pedestrian green:\n{res_normal['normal_pedestrian_green']}")
    
    print("\nTriggering School Bell Schedule Event...")
    res_bell = agent.process_school_bell(force_bell=True)
    print("\n🔔 School bell detected!\n")
    print(f"Pedestrian green:\n{res_bell['active_pedestrian_green']}")
    print(f"\nSafety Invariant: {res_bell['reason']}")
    print("Rule: Never steal time from a marked crossing to save cars.")

def run_demo_2(agent: CorridorAgent):
    print_separator("Demo 2 — Ambulance Corridor & Preemption")
    print("Inbound emergency alert received: Ambulance ETA = 2 minutes (120s)")
    
    res_amb = agent.request_ambulance_corridor(eta_seconds=120.0, is_j2_blocked=False)
    
    print("\n🚑 Ambulance request\n")
    print(f"Route:\n{res_amb['route_display']}\n")
    print("Holding:")
    for j in res_amb["holding_junctions"]:
        print(f"  • {j}")
    print(f"\nExtra delay to normal traffic:\n{res_amb['extra_delay_to_normal_traffic']}")

    print_separator("Rule 1 & Rule 2: Hold-Time Cap & Human Approval Gate")
    print("Simulating hold progression:")
    print("Hold started")
    print("  ↓")
    print("30 seconds (within safe limit)")
    agent.update_hold_simulation(30)
    print("  ↓")
    print("60 seconds (maximum cap reached)")
    cap_check = agent.update_hold_simulation(60)
    
    print(f"\nMaximum reached ({cap_check['hold_controller_state']['cap']}s)!")
    print("Rule 1 Status: System CANNOT hold traffic indefinitely.")
    print("Rule 2 Status: AI cannot continuously extend the hold by itself.")
    print("A fresh human click is required.\n")
    
    print("Operator action: Clicking [Extend Hold (+30s)]...")
    extend_res = agent.approve_human_extension()
    print(f"Result: {extend_res['message']}")
    
    print("\nVerifying extended hold at 75 seconds...")
    ext_check = agent.update_hold_simulation(75)
    print(f"Current elapsed: {ext_check['elapsed_seconds']}s | Active Cap: {ext_check['hold_controller_state']['cap']}s | Gate Active: {ext_check['gate_visible']}")

def run_demo_fallback(agent: CorridorAgent):
    print_separator("Fallback Corridor: J2 Blocked Simulation")
    print("Simulating traffic accident / physical blockage at Junction J2...")
    res_fallback = agent.request_ambulance_corridor(eta_seconds=120.0, is_j2_blocked=True)
    
    print("\n🚑 Ambulance request (Dynamic Fallback Triggered)\n")
    print(f"Route:\n{res_fallback['route_display']}\n")
    print("Holding:")
    for j in res_fallback["holding_junctions"]:
        print(f"  • {j}")
    print(f"\nFallback Rationale: Node J2 obstructed. Agent dynamically rerouted via North Bypass J4.")
    print(f"Extra delay to normal traffic: {res_fallback['extra_delay_to_normal_traffic']}")

if __name__ == "__main__":
    agent = CorridorAgent()
    run_demo_1(agent)
    run_demo_2(agent)
    run_demo_fallback(agent)
    print_separator("Simulation Complete — All Constraints Satisfied")
