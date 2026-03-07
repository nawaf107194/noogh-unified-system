import pytest
from neural_engine.autonomy.safety_policy import SafetyPolicy

class TestSafetyPolicy:
    def setup_method(self):
        self.policy = SafetyPolicy()

    @pytest.mark.parametrize("command, expected", [
        ("ls /home/user/documents", {"allowed": True, "requires_confirmation": False, "reason": "Path access OK", "permission_level": PermissionLevel.READ}),
        ('echo "/var/log/syslog"', {"allowed": False, "requires_confirmation": False, "reason": "Protected path: /var/log/syslog", "permission_level": PermissionLevel.ADMIN}),
        ("cat /etc/passwd", {"allowed": True, "requires_confirmation": False, "reason": "Path access OK", "permission_level": PermissionLevel.READ}),
        ("rm -rf /home/user/temp", {"allowed": True, "requires_confirmation": False, "reason": "Path access OK", "permission_level": PermissionLevel.READ})
    ])
    def test_check_path_access(self, command, expected):
        result = self.policy._check_path_access(command)
        assert result == expected

    @pytest.mark.parametrize("command, expected", [
        ("", {"allowed": True, "requires_confirmation": False, "reason": "Path access OK", "permission_level": PermissionLevel.READ}),
        (None, {"allowed": True, "requires_confirmation": False, "reason": "Path access OK", "permission_level": PermissionLevel.READ})
    ])
    def test_check_path_access_empty_or_none(self, command, expected):
        result = self.policy._check_path_access(command)
        assert result == expected

    @pytest.mark.parametrize("command, expected", [
        ("ls /home/user/documents/invalid", {"allowed": True, "requires_confirmation": False, "reason": "Path access OK", "permission_level": PermissionLevel.READ}),
        ('echo "/var/log/syslog" with invalid syntax', {"allowed": True, "requires_confirmation": False, "reason": "Path access OK", "permission_level": PermissionLevel.READ})
    ])
    def test_check_path_access_invalid_paths(self, command, expected):
        result = self.policy._check_path_access(command)
        assert result == expected

    @pytest.mark.parametrize("command, expected", [
        ("ls /home/user/documents & echo 'Done'", {"allowed": True, "requires_confirmation": False, "reason": "Path access OK", "permission_level": PermissionLevel.READ}),
        ('echo "/var/log/syslog" | tee output.txt', {"allowed": False, "requires_confirmation": False, "reason": "Protected path: /var/log/syslog", "permission_level": PermissionLevel.ADMIN})
    ])
    def test_check_path_access_with_shell_commands(self, command, expected):
        result = self.policy._check_path_access(command)
        assert result == expected