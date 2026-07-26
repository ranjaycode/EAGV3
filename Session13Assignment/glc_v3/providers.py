import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class ProviderSlot:
    name: str
    api_key: str
    is_active: bool = True
    usage_count: int = 0
    error_count: int = 0


class ProviderRouter:
    """Manages multi-slot Gemini API provider routing without leaking credentials."""
    def __init__(self):
        self.slots: Dict[str, ProviderSlot] = {}
        self._load_slots()
        self._current_index: int = 0

    def _load_slots(self):
        # Check for GEMINI_API_KEY_1..5 or single GEMINI_API_KEY
        for i in range(1, 6):
            key = os.getenv(f"GEMINI_API_KEY_{i}") or os.getenv(f"GEMINI_KEY_{i}")
            if key:
                slot_name = f"gemini_{i}"
                self.slots[slot_name] = ProviderSlot(name=slot_name, api_key=key)

        # Fallback if no numbered keys found
        if not self.slots:
            default_key = os.getenv("GEMINI_API_KEY", "mock_gemini_key_synthetic")
            for i in range(1, 6):
                slot_name = f"gemini_{i}"
                self.slots[slot_name] = ProviderSlot(name=slot_name, api_key=f"{default_key}_slot_{i}")

    def acquire_slot(self, preferred_role: str = "") -> ProviderSlot:
        active_slots = [slot for slot in self.slots.values() if slot.is_active]
        if not active_slots:
            raise RuntimeError("No active Gemini API key slots available")

        # Round robin selection
        slot = active_slots[self._current_index % len(active_slots)]
        self._current_index += 1
        slot.usage_count += 1
        return slot

    def record_error(self, slot_name: str):
        if slot_name in self.slots:
            self.slots[slot_name].error_count += 1

    def get_slot_status(self) -> List[Dict[str, Any]]:
        return [
            {
                "slot": slot.name,
                "is_active": slot.is_active,
                "usage_count": slot.usage_count,
                "error_count": slot.error_count
            }
            for slot in self.slots.values()
        ]
