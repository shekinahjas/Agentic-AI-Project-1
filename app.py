"""
Streamlit Web Dashboard for School-Zone and Ambulance Corridor Agent
Interactive real-time visualization of:
1. Shared Corridor Map (Normal, Delayed, Held, Ambulance, School Crossing)
2. Demo 1: School Bell Pedestrian Priority (20s -> 40s)
3. Demo 2: Ambulance Corridor Request (Route, Holding, Extra Delay Card)
4. Rule 1 & Rule 2: 60s Hold-Time Cap & Fresh Human Click Gate (+30s)
5. Fallback Routing (J1 -> J4 -> J3 when J2 is blocked)
6. Strict Safety Invariants & Side-Effect Delay Telemetry
"""
import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import streamlit as st
import time
from corridor_agent import CorridorAgent

# Page Configuration
st.set_page_config(
    page_title="School-Zone & Ambulance Corridor Agent",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-End Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #1e293b, #0f172a);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 16px 20px;
        color: #f8fafc;
        box-shadow: 0 4px 12px rgba(0,0,0,0.25);
    }
    .metric-title {
        font-size: 0.82rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94a3b8;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 800;
        font-family: 'JetBrains Mono', monospace;
        color: #38bdf8;
    }
    .demo-card {
        background: #0f172a;
        border: 2px solid #38bdf8;
        border-radius: 12px;
        padding: 20px;
        margin-top: 10px;
        margin-bottom: 15px;
        box-shadow: 0 8px 24px rgba(56, 189, 248, 0.15);
    }
    .gate-card-alert {
        background: linear-gradient(135deg, #450a0a, #7f1d1d);
        border: 2px solid #ef4444;
        border-radius: 12px;
        padding: 20px;
        color: #fef2f2;
        animation: pulse-border 1.5s infinite;
    }
    @keyframes pulse-border {
        0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
        70% { box-shadow: 0 0 0 12px rgba(239, 68, 68, 0); }
        100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
    }
    .status-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
    }
    .badge-held { background: #ef4444; color: #fff; }
    .badge-delayed { background: #f59e0b; color: #000; }
    .badge-normal { background: #10b981; color: #fff; }
    .badge-school { background: #3b82f6; color: #fff; }
</style>
""", unsafe_allow_html=True)

# Session State Initialization
if "agent" not in st.session_state:
    st.session_state.agent = CorridorAgent()
if "bell_active" not in st.session_state:
    st.session_state.bell_active = False
if "ambulance_active" not in st.session_state:
    st.session_state.ambulance_active = False
if "j2_blocked" not in st.session_state:
    st.session_state.j2_blocked = False
if "elapsed_hold" not in st.session_state:
    st.session_state.elapsed_hold = 0

agent: CorridorAgent = st.session_state.agent

# Header & System Invariants Bar
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.title("🚦 School-Zone & Ambulance Corridor Agent")
    st.caption("Agentic signal coordinator balancing pedestrian bell dismissal priority with emergency preemption under strict safety caps.")
with col_h2:
    st.markdown("""
    <div style="text-align: right; padding-top: 10px;">
        <span class="status-badge" style="background: #22c55e; color: #fff; padding: 6px 12px;">🛡️ Safety First: Active</span><br>
        <span class="status-badge" style="background: #64748b; color: #fff; margin-top: 5px; padding: 6px 12px;">🧪 Sandbox (No Real Signal)</span>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# Sidebar: Interactive Demo & Scenario Controls
st.sidebar.header("🕹️ Demo & Scenario Controls")

st.sidebar.subheader("Demo 1: School Bell")
col_b1, col_b2 = st.sidebar.columns(2)
with col_b1:
    if st.button("🔔 School Bell ON", use_container_width=True, type="primary"):
        st.session_state.bell_active = True
with col_b2:
    if st.button("⚪ Normal Traffic", use_container_width=True):
        st.session_state.bell_active = False

st.sidebar.subheader("Demo 2: Ambulance Request")
col_a1, col_a2 = st.sidebar.columns(2)
with col_a1:
    if st.button("🚑 Dispatch (2m Out)", use_container_width=True, type="primary"):
        st.session_state.ambulance_active = True
        st.session_state.elapsed_hold = 50  # Demo benchmark producing 25s extra delay
with col_a2:
    if st.button("🏁 Clear Corridor", use_container_width=True):
        st.session_state.ambulance_active = False
        st.session_state.elapsed_hold = 0
        agent.clear_corridor()

st.sidebar.subheader("Node Obstruction & Fallback")
st.session_state.j2_blocked = st.sidebar.checkbox(
    "⚠️ Simulate J2 Blockage (Accident / Debris)",
    value=st.session_state.j2_blocked,
    help="When enabled, agent computes fallback corridor bypassing J2 via North Bypass J4."
)

st.sidebar.subheader("Rule 1 & 2: Hold Timer Stepper")
st.session_state.elapsed_hold = st.sidebar.slider(
    "Simulated Hold Elapsed (sec)",
    min_value=0,
    max_value=120,
    value=st.session_state.elapsed_hold,
    step=5,
    help="Move past 60s to trigger Rule 1 (Hold Cap) and Rule 2 (Human Approval Gate)."
)

if st.sidebar.button("🔄 Reset All Systems", use_container_width=True):
    st.session_state.bell_active = False
    st.session_state.ambulance_active = False
    st.session_state.j2_blocked = False
    st.session_state.elapsed_hold = 0
    agent.clear_corridor()
    st.rerun()

# Execute Agent State Updates
bell_status = agent.process_school_bell(force_bell=st.session_state.bell_active)

if st.session_state.ambulance_active:
    amb_status = agent.request_ambulance_corridor(
        eta_seconds=120.0,
        is_j2_blocked=st.session_state.j2_blocked
    )
    sim_update = agent.update_hold_simulation(st.session_state.elapsed_hold)
    active_route = amb_status["route"]
    held_nodes = amb_status["holding_junctions"]
    extra_delay_text = f"{int(sim_update['delay_metrics']['avg_extra_delay_per_vehicle_sec'])} sec"
else:
    active_route = []
    held_nodes = []
    extra_delay_text = "0 sec (Normal Flow)"
    sim_update = {"gate_visible": False, "hold_controller_state": {"cap": 60, "status": "IDLE"}}

# -------------------------------------------------------------
# RULE 3: SHARED MAP VISUALIZATION LAYER
# -------------------------------------------------------------
st.subheader("🗺️ Shared Corridor Map (Rule 3)")
st.caption("Live-updating spatial map accessible by all emergency and civil agencies. Displays: Normal, Delayed, Held, Ambulance, and School Crossing.")

# Generate SVG Map
def render_shared_map(active_route, held_nodes, is_bell_active, is_amb_active, is_j2_blocked, elapsed_hold):
    # Colors
    c_normal = "#10b981"
    c_delayed = "#f59e0b"
    c_held = "#ef4444"
    c_road = "#334155"
    c_corridor = "#38bdf8"
    
    # Node colors based on state
    def get_node_color(node_id):
        if node_id in held_nodes:
            return c_held
        if node_id == "J2" and is_j2_blocked:
            return c_delayed
        return c_normal

    col_j1 = get_node_color("J1")
    col_j2 = get_node_color("J2")
    col_j3 = get_node_color("J3")
    col_j4 = get_node_color("J4")

    # Path stroke styling
    is_fallback = "J4" in active_route
    path_main_stroke = c_corridor if (is_amb_active and not is_fallback) else c_road
    path_bypass_stroke = c_corridor if (is_amb_active and is_fallback) else "#475569"

    # Ambulance position interpolation
    if is_amb_active:
        if not is_fallback:
            amb_cx = min(680, 100 + (elapsed_hold * 8))
            amb_cy = 190
        else:
            amb_cx = min(680, 100 + (elapsed_hold * 7.5))
            amb_cy = 90 if (250 <= amb_cx <= 500) else 190
        amb_svg = f"""
        <g transform="translate({amb_cx-20}, {amb_cy-20})">
            <circle cx="20" cy="20" r="22" fill="#ef4444" opacity="0.3">
                <animate attributeName="r" values="18;26;18" dur="1s" repeatCount="indefinite"/>
            </circle>
            <rect x="2" y="8" width="36" height="24" rx="6" fill="#f8fafc" stroke="#dc2626" stroke-width="2.5"/>
            <text x="20" y="24" font-size="14" text-anchor="middle" font-weight="900" fill="#dc2626">🚑</text>
        </g>
        """
    else:
        amb_svg = ""

    # Pedestrian Crosswalk Visual at J2
    ped_green_val = "40s" if is_bell_active else "20s"
    ped_badge_col = "#3b82f6" if is_bell_active else "#10b981"
    ped_label = "BELL PRIORITY" if is_bell_active else "NORMAL CYCLE"

    svg_content = f"""
    <svg width="100%" height="320" viewBox="0 0 860 320" xmlns="http://www.w3.org/2000/svg" style="background:#090d16; border-radius:12px; border:1px solid #1e293b;">
        <!-- Arterial Main Road (J1 -> J2 -> J3) -->
        <line x1="60" y1="190" x2="800" y2="190" stroke="{c_road}" stroke-width="28" stroke-linecap="round"/>
        <line x1="60" y1="190" x2="800" y2="190" stroke="{path_main_stroke}" stroke-width="6" stroke-dasharray="8 6"/>

        <!-- North Bypass Road (J1 -> J4 -> J3) -->
        <path d="M 170 190 L 420 90 L 670 190" fill="none" stroke="{path_bypass_stroke}" stroke-width="16" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M 170 190 L 420 90 L 670 190" fill="none" stroke="{c_corridor if is_fallback else '#64748b'}" stroke-width="4" stroke-dasharray="6 6"/>

        <!-- Cross Streets with Queue Indicators -->
        <line x1="170" y1="110" x2="170" y2="270" stroke="#1e293b" stroke-width="14"/>
        <line x1="420" y1="190" x2="420" y2="290" stroke="#1e293b" stroke-width="14"/>
        <line x1="670" y1="110" x2="670" y2="270" stroke="#1e293b" stroke-width="14"/>

        <!-- School Crosswalk Stripes at J2 -->
        <g transform="translate(390, 172)">
            <rect x="0" y="0" width="8" height="36" fill="#f8fafc" rx="1"/>
            <rect x="14" y="0" width="8" height="36" fill="#f8fafc" rx="1"/>
            <rect x="28" y="0" width="8" height="36" fill="#f8fafc" rx="1"/>
            <rect x="42" y="0" width="8" height="36" fill="#f8fafc" rx="1"/>
            <rect x="56" y="0" width="8" height="36" fill="#f8fafc" rx="1"/>
        </g>
        <g transform="translate(420, 245)">
            <rect x="-65" y="-12" width="130" height="24" rx="12" fill="{ped_badge_col}" opacity="0.95"/>
            <text x="0" y="4" font-size="11" font-weight="700" fill="#ffffff" text-anchor="middle">🚸 CROSSWALK: {ped_green_val}</text>
        </g>

        <!-- Junction Nodes -->
        <!-- J1 Node -->
        <circle cx="170" cy="190" r="26" fill="{col_j1}" stroke="#ffffff" stroke-width="3"/>
        <text x="170" y="196" font-size="14" font-weight="800" fill="#ffffff" text-anchor="middle">J1</text>
        <text x="170" y="235" font-size="12" font-weight="600" fill="#94a3b8" text-anchor="middle">Corridor Entry</text>

        <!-- J4 Bypass Node -->
        <circle cx="420" cy="90" r="22" fill="{col_j4}" stroke="#ffffff" stroke-width="3"/>
        <text x="420" y="95" font-size="13" font-weight="800" fill="#ffffff" text-anchor="middle">J4</text>
        <text x="420" y="60" font-size="11" font-weight="600" fill="#94a3b8" text-anchor="middle">Bypass Alternate</text>

        <!-- J2 School Zone Node -->
        <circle cx="420" cy="190" r="26" fill="{col_j2}" stroke="#ffffff" stroke-width="3"/>
        <text x="420" y="196" font-size="14" font-weight="800" fill="#ffffff" text-anchor="middle">J2</text>
        <text x="420" y="150" font-size="12" font-weight="700" fill="#38bdf8" text-anchor="middle">School Zone</text>

        <!-- J3 Hospital Approach Node -->
        <circle cx="670" cy="190" r="26" fill="{col_j3}" stroke="#ffffff" stroke-width="3"/>
        <text x="670" y="196" font-size="14" font-weight="800" fill="#ffffff" text-anchor="middle">J3</text>
        <text x="670" y="235" font-size="12" font-weight="600" fill="#94a3b8" text-anchor="middle">Hospital Exit</text>

        <!-- Hospital Endpoint Marker -->
        <g transform="translate(760, 165)">
            <rect x="0" y="0" width="55" height="50" rx="8" fill="#1e293b" stroke="#dc2626" stroke-width="2"/>
            <text x="27" y="26" font-size="18" text-anchor="middle">🏥</text>
            <text x="27" y="42" font-size="9" font-weight="800" fill="#ef4444" text-anchor="middle">TRAUMA</text>
        </g>

        <!-- Moving Ambulance Entity -->
        {amb_svg}
    </svg>
    """
    return svg_content

st.markdown(
    render_shared_map(
        active_route=active_route,
        held_nodes=held_nodes,
        is_bell_active=st.session_state.bell_active,
        is_amb_active=st.session_state.ambulance_active,
        is_j2_blocked=st.session_state.j2_blocked,
        elapsed_hold=st.session_state.elapsed_hold
    ),
    unsafe_allow_html=True
)

# Legend Bar
col_l1, col_l2, col_l3, col_l4, col_l5 = st.columns(5)
col_l1.markdown("🟢 **Normal:** Standard Cycle")
col_l2.markdown("🟡 **Delayed:** Queued Cross-Traffic")
col_l3.markdown("🔴 **Held:** Corridor Emergency Lock")
col_l4.markdown("🚑 **Ambulance:** Priority Route")
col_l5.markdown("🚸 **School Crossing:** Foot Traffic")

st.divider()

# -------------------------------------------------------------
# DEMO OUTPUT CARDS (DEMO 1 & DEMO 2 AS REQUESTED)
# -------------------------------------------------------------
col_demo1, col_demo2 = st.columns(2)

with col_demo1:
    st.markdown("### 🔔 Demo 1 — School Bell")
    if st.session_state.bell_active:
        st.markdown(f"""
        <div class="demo-card" style="border-color: #3b82f6;">
            <div style="font-size: 0.9rem; color: #94a3b8;">Normal pedestrian green:</div>
            <div style="font-size: 1.3rem; font-weight: 700; color: #64748b; text-decoration: line-through;">20 sec</div>
            <div style="font-size: 1.1rem; font-weight: 800; color: #38bdf8; margin-top: 10px;">🔔 School bell detected!</div>
            <div style="font-size: 0.9rem; color: #94a3b8; margin-top: 5px;">Pedestrian green:</div>
            <div style="font-size: 2.2rem; font-weight: 900; color: #22c55e; font-family: monospace;">40 sec</div>
            <div style="font-size: 0.8rem; color: #cbd5e1; margin-top: 8px;">
                🛡️ <b>Safety Invariant:</b> Crossing time cannot be truncated to save cars.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="demo-card" style="border-color: #334155;">
            <div style="font-size: 0.9rem; color: #94a3b8;">Normal pedestrian green:</div>
            <div style="font-size: 2.2rem; font-weight: 800; color: #38bdf8; font-family: monospace;">20 sec</div>
            <div style="font-size: 0.85rem; color: #64748b; margin-top: 10px;">
                Standard non-bell window. Click <b>"School Bell ON"</b> in sidebar to trigger Demo 1.
            </div>
        </div>
        """, unsafe_allow_html=True)

with col_demo2:
    st.markdown("### 🚑 Demo 2 — Ambulance Request")
    if st.session_state.ambulance_active:
        route_str = " → ".join(active_route)
        holding_items = "<br>".join([f"&nbsp;&nbsp;• <b>{n}</b>" for n in held_nodes])
        st.markdown(f"""
        <div class="demo-card" style="border-color: #ef4444;">
            <div style="font-size: 1.1rem; font-weight: 800; color: #ef4444;">🚑 Ambulance request</div>
            <div style="font-size: 0.85rem; color: #94a3b8; margin-top: 6px;">Route:</div>
            <div style="font-size: 1.4rem; font-weight: 800; color: #f8fafc; font-family: monospace;">{route_str}</div>
            <div style="font-size: 0.85rem; color: #94a3b8; margin-top: 8px;">Holding:</div>
            <div style="font-size: 1.1rem; color: #fca5a5; font-family: monospace; line-height: 1.4;">
                {holding_items}
            </div>
            <div style="font-size: 0.85rem; color: #94a3b8; margin-top: 10px;">Extra delay to normal traffic:</div>
            <div style="font-size: 2.0rem; font-weight: 900; color: #f59e0b; font-family: monospace;">{extra_delay_text}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="demo-card" style="border-color: #334155;">
            <div style="font-size: 1.0rem; font-weight: 700; color: #64748b;">No Active Ambulance Request</div>
            <div style="font-size: 0.85rem; color: #64748b; margin-top: 10px;">
                Corridor is cycling under standard local timing. Click <b>"Dispatch (2m Out)"</b> in sidebar to trigger Demo 2.
            </div>
        </div>
        """, unsafe_allow_html=True)

# -------------------------------------------------------------
# RULE 1 & RULE 2: HOLD CAP & HUMAN APPROVAL GATE
# -------------------------------------------------------------
st.divider()
st.subheader("🛡️ Safety Gates & Human Approval (Rules 1 & 2)")

current_cap = sim_update["hold_controller_state"].get("cap", 60)
elapsed_val = st.session_state.elapsed_hold
gate_visible = sim_update.get("gate_visible", False)

col_g1, col_g2 = st.columns([2, 1])

with col_g1:
    st.markdown(f"**Elapsed Hold Time:** `{elapsed_val} sec` &nbsp;|&nbsp; **Maximum Cap:** `{current_cap} sec`")
    progress_pct = min(1.0, elapsed_val / float(current_cap))
    st.progress(progress_pct)

    if gate_visible:
        st.markdown("""
        <div class="gate-card-alert">
            <h3 style="margin: 0; color: #fecaca;">⚠️ RULE 1 ENFORCED: MAXIMUM HOLD REACHED (60s)!</h3>
            <p style="margin-top: 8px; font-size: 0.95rem;">
                <b>The system cannot hold traffic indefinitely.</b><br>
                The AI is strictly prohibited from auto-extending. A <b>fresh human click</b> is required to grant additional hold time.
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Rule 1 Status: Hold within safe limit. No human intervention needed yet.")

with col_g2:
    st.markdown("#### Human Gate Action")
    if gate_visible:
        if st.button("🔘 Extend Hold (+30s)", type="primary", use_container_width=True):
            res = agent.approve_human_extension()
            st.session_state.elapsed_hold = min(st.session_state.elapsed_hold, res["new_cap"] - 5)
            st.success(res["message"])
            time.sleep(0.5)
            st.rerun()
        if st.button("❌ Release Traffic Now", use_container_width=True):
            agent.clear_corridor()
            st.session_state.ambulance_active = False
            st.session_state.elapsed_hold = 0
            st.warning("Corridor released by operator. Resumed standard cycles.")
            st.rerun()
    else:
        st.button("🔘 Extend Hold (+30s)", disabled=True, use_container_width=True, help="Active only when hold cap is reached.")

# -------------------------------------------------------------
# AGENT DECISION LOG & TELEMETRY
# -------------------------------------------------------------
with st.expander("📋 Agent Event Log & Operational Rationale", expanded=False):
    for log_entry in reversed(agent.log_messages[-10:]):
        st.write(log_entry)
