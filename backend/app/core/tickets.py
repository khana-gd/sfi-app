import uuid
import threading
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict

class WSTicketStore:
    def __init__(self):
        self._tickets: Dict[str, dict] = {}
        self._lock = threading.Lock()

    def generate_ticket(self, user_id: int, role: str, expiry_seconds: int = 30) -> str:
        ticket_id = str(uuid.uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expiry_seconds)
        
        with self._lock:
            self._tickets[ticket_id] = {
                "user_id": user_id,
                "role": role,
                "expires_at": expires_at
            }
        return ticket_id

    def consume_ticket(self, ticket_id: str) -> Optional[dict]:
        now = datetime.now(timezone.utc)
        with self._lock:
            # Clean up expired tickets during lookup to free memory
            self._cleanup_expired(now)

            if ticket_id not in self._tickets:
                return None
            
            ticket_data = self._tickets[ticket_id]
            # Immediately delete to ensure single-use
            del self._tickets[ticket_id]

            if now > ticket_data["expires_at"]:
                return None # Expired

            return {
                "user_id": ticket_data["user_id"],
                "role": ticket_data["role"]
            }

    def _cleanup_expired(self, now: datetime) -> None:
        expired_keys = [k for k, v in self._tickets.items() if now > v["expires_at"]]
        for k in expired_keys:
            del self._tickets[k]

# Global singleton ticket store
ticket_store = WSTicketStore()
