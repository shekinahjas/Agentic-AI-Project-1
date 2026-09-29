"""
Hold-Time Cap & Human-In-The-Loop (HITL) Controller
Enforces Rule 1 (Hold-Time Cap) & Rule 2 (Human Approval To Extend).
"""
import time
from typing import Dict, Optional

class HoldController:
    """
    Rule 1 — Hold-Time Cap:
    Maximum hold = 60 seconds. After 60 seconds, the system cannot hold traffic
    indefinitely without human intervention.
    
    Rule 2 — Human Approval To Extend:
    If hold needs to continue, a fresh human click is required.
    AI cannot continuously extend the hold by itself.
    User selected: +30 seconds per human click.
    """
    DEFAULT_MAX_CAP: int = 60
    EXTENSION_STEP: int = 30

    def __init__(self):
        self.is_holding: bool = False
        self.hold_start_timestamp: Optional[float] = None
        self.simulated_elapsed_seconds: int = 0
        self.current_cap: int = self.DEFAULT_MAX_CAP
        self.human_approvals_granted: int = 0
        self.gate_visible: bool = False
        self.status: str = "IDLE"  # "IDLE", "HOLDING", "CAP_REACHED_AWAITING_HUMAN", "RELEASED"

    def start_hold(self):
        """Initiates a corridor hold."""
        self.is_holding = True
        self.hold_start_timestamp = time.time()
        self.simulated_elapsed_seconds = 0
        self.current_cap = self.DEFAULT_MAX_CAP
        self.human_approvals_granted = 0
        self.gate_visible = False
        self.status = "HOLDING"

    def set_elapsed_seconds(self, elapsed: int) -> Dict:
        """
        Updates simulated or wall-clock elapsed hold time and verifies cap invariant.
        """
        if not self.is_holding:
            return {"status": self.status, "gate_visible": False, "elapsed": 0}

        self.simulated_elapsed_seconds = elapsed

        if self.simulated_elapsed_seconds >= self.current_cap:
            # Rule 1: Max hold cap reached
            # Rule 2: Cannot auto-extend, requires human approval
            self.gate_visible = True
            self.status = "CAP_REACHED_AWAITING_HUMAN"
        else:
            self.gate_visible = False
            self.status = "HOLDING"

        return {
            "status": self.status,
            "gate_visible": self.gate_visible,
            "elapsed": self.simulated_elapsed_seconds,
            "cap": self.current_cap,
            "approvals": self.human_approvals_granted
        }

    def human_extend_click(self) -> Dict:
        """
        Rule 2: A fresh human click is required to extend.
        Extends the cap by +30 seconds.
        """
        if self.status != "CAP_REACHED_AWAITING_HUMAN":
            return {
                "success": False,
                "message": "Hold cap has not been reached or hold is not active."
            }

        self.human_approvals_granted += 1
        self.current_cap += self.EXTENSION_STEP
        self.gate_visible = False
        self.status = "HOLDING"

        return {
            "success": True,
            "new_cap": self.current_cap,
            "message": f"Human approval verified! Hold extended by +{self.EXTENSION_STEP}s (New Cap: {self.current_cap}s)."
        }

    def release_hold(self) -> Dict:
        """Releases the corridor hold and restores standard signal cycles."""
        self.is_holding = False
        self.gate_visible = False
        self.status = "RELEASED"
        return {
            "success": True,
            "message": "Corridor released. Normal cycling restored."
        }
