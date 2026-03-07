import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List


@dataclass
class Message:
    role: str  # "user" | "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Session:
    session_id: str
    messages: List[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    def add_message(self, role: str, content: str):
        self.messages.append(Message(role=role, content=content))
        self.last_updated = datetime.now()

    def get_history(self, max_messages: int = 10) -> List[Message]:
        """Get recent messages up to max_messages"""
        return self.messages[-max_messages:]

    def to_prompt(self, max_messages: int = 10) -> str:
        """Convert session history to prompt format"""
        history = self.get_history(max_messages)
        lines = []
        for msg in history:
            prefix = "User:" if msg.role == "user" else "Assistant:"
            lines.append(f"{prefix} {msg.content}")
        return "\n".join(lines)


class SessionManager:
    """Manages user sessions for conversation history"""

    def __init__(self):
        self.sessions: Dict[str, Session] = {}

    def create_session(self) -> str:
        """Create new session and return session_id"""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = Session(session_id=session_id)
        return session_id

    def get_session(self, session_id: str) -> Session:
        """Get existing session or create new one"""
        if session_id not in self.sessions:
            self.sessions[session_id] = Session(session_id=session_id)
        return self.sessions[session_id]

    def delete_session(self, session_id: str):
        """Delete session"""
        if session_id in self.sessions:
            del self.sessions[session_id]

    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Remove sessions older than max_age_hours"""
        now = datetime.now()
        to_delete = []
        for sid, session in self.sessions.items():
            age = (now - session.last_updated).total_seconds() / 3600
            if age > max_age_hours:
                to_delete.append(sid)
        for sid in to_delete:
            del self.sessions[sid]


# Global session manager instance
session_manager = SessionManager()
