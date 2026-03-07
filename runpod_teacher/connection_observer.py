from runpod_teacher.connect_brain import ConnectBrain
from runpod_teacher.architecture_base import ArchitectureBase

class ConnectionObserver:
    def __init__(self):
        self._connections = {}
        self._brain_connector = ConnectBrain()

    def register(self, architecture: ArchitectureBase):
        """Register an architecture for connection management"""
        if architecture.id not in self._connections:
            self._connections[architecture.id] = {
                'architecture': architecture,
                'is_connected': False
            }
            self._update_connection(architecture)

    def _update_connection(self, architecture: ArchitectureBase):
        """Update connection status based on architecture changes"""
        if not self._connections[architecture.id]['is_connected']:
            self._brain_connector.connect(architecture)
            self._connections[architecture.id]['is_connected'] = True

    def get_connection_status(self, architecture_id: str) -> bool:
        """Get current connection status for an architecture"""
        return self._connections.get(architecture_id, {}).get('is_connected', False)

    def disconnect(self, architecture_id: str):
        """Manually disconnect an architecture"""
        if architecture_id in self._connections:
            self._brain_connector.disconnect(self._connections[architecture_id]['architecture'])
            self._connections[architecture_id]['is_connected'] = False