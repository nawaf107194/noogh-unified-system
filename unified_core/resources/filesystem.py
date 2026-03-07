"""
Secure File System Access
Sandboxed file operations with audit logging
"""
import logging
import os
import shutil
import hashlib
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from enum import Enum

logger = logging.getLogger("unified_core.resources.filesystem")


class FileOperation(Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    CREATE = "create"
    MOVE = "move"
    COPY = "copy"
    CHMOD = "chmod"


@dataclass
class FileAuditEntry:
    """Audit log entry for file operation."""
    operation: FileOperation
    path: str
    agent_id: str
    timestamp: datetime
    success: bool
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class FileAccessResult:
    """Result of file operation."""
    success: bool
    path: str
    operation: FileOperation
    data: Optional[bytes] = None
    content: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class SecureFileSystem:
    """
    Sandboxed file system access with audit logging.
    Restricts access to allowed paths and logs all operations.
    """
    
    # Paths that are always blocked
    BLOCKED_PATHS = {
        "/etc/shadow", "/etc/passwd", "/etc/sudoers",
        "/root", "/boot", "/proc/kcore", "/dev/mem"
    }
    
    # Sensitive file patterns
    SENSITIVE_PATTERNS = {
        "*.key", "*.pem", "*.env", "*password*", "*secret*",
        "id_rsa*", "*.p12", "*.pfx"
    }
    
    def __init__(
        self,
        allowed_roots: List[str],
        audit_enabled: bool = True,
        max_file_size_mb: float = 100.0
    ):
        self.allowed_roots = [Path(p).resolve() for p in allowed_roots]
        self.audit_enabled = audit_enabled
        self.max_file_size_mb = max_file_size_mb
        
        self._audit_log: List[FileAuditEntry] = []
        self._access_cache: Dict[str, bool] = {}
        self._blocked_extensions: Set[str] = {".exe", ".dll", ".so", ".sh", ".bat"}
    
    def is_path_allowed(self, path: str) -> bool:
        """Check if path is within allowed roots."""
        try:
            resolved = Path(path).resolve()
            
            # Check blocked paths
            for blocked in self.BLOCKED_PATHS:
                if str(resolved).startswith(blocked):
                    return False
            
            # Check allowed roots
            for root in self.allowed_roots:
                try:
                    resolved.relative_to(root)
                    return True
                except ValueError:
                    continue
            
            return False
            
        except Exception:
            return False
    
    def _validate_access(self, path: str, operation: FileOperation) -> Optional[str]:
        """Validate access and return error message if denied."""
        if not self.is_path_allowed(path):
            return f"Access denied: Path {path} is outside allowed roots"
        
        resolved = Path(path).resolve()
        
        # Check blocked paths explicitly
        for blocked in self.BLOCKED_PATHS:
            if str(resolved).startswith(blocked):
                return f"Access denied: {blocked} is a protected path"
        
        # Check sensitive patterns for write operations
        if operation in (FileOperation.WRITE, FileOperation.DELETE):
            import fnmatch
            filename = resolved.name
            for pattern in self.SENSITIVE_PATTERNS:
                if fnmatch.fnmatch(filename.lower(), pattern.lower()):
                    return f"Access denied: {filename} matches sensitive pattern {pattern}"
        
        # Check blocked extensions for write
        if operation == FileOperation.WRITE:
            if resolved.suffix.lower() in self._blocked_extensions:
                return f"Access denied: Cannot write {resolved.suffix} files"
        
        return None
    
    def _audit(
        self,
        operation: FileOperation,
        path: str,
        agent_id: str,
        success: bool,
        details: Dict = None,
        error: str = None
    ):
        """Record audit entry."""
        if not self.audit_enabled:
            return
        
        entry = FileAuditEntry(
            operation=operation,
            path=path,
            agent_id=agent_id,
            timestamp=datetime.now(),
            success=success,
            details=details or {},
            error=error
        )
        self._audit_log.append(entry)
        
        # Keep manageable size
        if len(self._audit_log) > 10000:
            self._audit_log = self._audit_log[-5000:]
        
        # Log to standard logger
        log_msg = f"[{agent_id}] {operation.value} {path}"
        if success:
            logger.info(log_msg)
        else:
            logger.warning(f"{log_msg} - FAILED: {error}")
    
    def read_file(
        self,
        path: str,
        agent_id: str = "system",
        binary: bool = False
    ) -> FileAccessResult:
        """Read file contents."""
        error = self._validate_access(path, FileOperation.READ)
        if error:
            self._audit(FileOperation.READ, path, agent_id, False, error=error)
            return FileAccessResult(
                success=False, path=path, operation=FileOperation.READ, error=error
            )
        
        try:
            resolved = Path(path).resolve()
            
            if not resolved.exists():
                error = f"File not found: {path}"
                self._audit(FileOperation.READ, path, agent_id, False, error=error)
                return FileAccessResult(
                    success=False, path=path, operation=FileOperation.READ, error=error
                )
            
            # Check file size
            size_mb = resolved.stat().st_size / (1024 * 1024)
            if size_mb > self.max_file_size_mb:
                error = f"File too large: {size_mb:.1f}MB > {self.max_file_size_mb}MB"
                self._audit(FileOperation.READ, path, agent_id, False, error=error)
                return FileAccessResult(
                    success=False, path=path, operation=FileOperation.READ, error=error
                )
            
            mode = "rb" if binary else "r"
            with open(resolved, mode) as f:
                data = f.read()
            
            # Calculate hash for audit
            file_hash = hashlib.sha256(
                data if binary else data.encode()
            ).hexdigest()[:16]
            
            self._audit(
                FileOperation.READ, path, agent_id, True,
                details={"size_bytes": len(data), "hash": file_hash}
            )
            
            if binary:
                return FileAccessResult(
                    success=True, path=path, operation=FileOperation.READ,
                    data=data, metadata={"size": len(data), "hash": file_hash}
                )
            else:
                return FileAccessResult(
                    success=True, path=path, operation=FileOperation.READ,
                    content=data, metadata={"size": len(data), "hash": file_hash}
                )
                
        except Exception as e:
            error = str(e)
            self._audit(FileOperation.READ, path, agent_id, False, error=error)
            return FileAccessResult(
                success=False, path=path, operation=FileOperation.READ, error=error
            )
    
    def write_file(
        self,
        path: str,
        content: str,
        agent_id: str = "system",
        append: bool = False,
        create_dirs: bool = True
    ) -> FileAccessResult:
        """Write content to file."""
        error = self._validate_access(path, FileOperation.WRITE)
        if error:
            self._audit(FileOperation.WRITE, path, agent_id, False, error=error)
            return FileAccessResult(
                success=False, path=path, operation=FileOperation.WRITE, error=error
            )
        
        try:
            resolved = Path(path).resolve()
            
            if create_dirs:
                resolved.parent.mkdir(parents=True, exist_ok=True)
            
            mode = "a" if append else "w"
            with open(resolved, mode) as f:
                f.write(content)
            
            file_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
            
            self._audit(
                FileOperation.WRITE, path, agent_id, True,
                details={
                    "size_bytes": len(content),
                    "hash": file_hash,
                    "append": append
                }
            )
            
            return FileAccessResult(
                success=True, path=path, operation=FileOperation.WRITE,
                metadata={"size": len(content), "hash": file_hash}
            )
            
        except Exception as e:
            error = str(e)
            self._audit(FileOperation.WRITE, path, agent_id, False, error=error)
            return FileAccessResult(
                success=False, path=path, operation=FileOperation.WRITE, error=error
            )
    
    def delete_file(
        self,
        path: str,
        agent_id: str = "system"
    ) -> FileAccessResult:
        """Delete a file."""
        error = self._validate_access(path, FileOperation.DELETE)
        if error:
            self._audit(FileOperation.DELETE, path, agent_id, False, error=error)
            return FileAccessResult(
                success=False, path=path, operation=FileOperation.DELETE, error=error
            )
        
        try:
            resolved = Path(path).resolve()
            
            if not resolved.exists():
                error = f"File not found: {path}"
                self._audit(FileOperation.DELETE, path, agent_id, False, error=error)
                return FileAccessResult(
                    success=False, path=path, operation=FileOperation.DELETE, error=error
                )
            
            if resolved.is_dir():
                error = "Cannot delete directory with delete_file"
                self._audit(FileOperation.DELETE, path, agent_id, False, error=error)
                return FileAccessResult(
                    success=False, path=path, operation=FileOperation.DELETE, error=error
                )
            
            resolved.unlink()
            
            self._audit(FileOperation.DELETE, path, agent_id, True)
            return FileAccessResult(
                success=True, path=path, operation=FileOperation.DELETE
            )
            
        except Exception as e:
            error = str(e)
            self._audit(FileOperation.DELETE, path, agent_id, False, error=error)
            return FileAccessResult(
                success=False, path=path, operation=FileOperation.DELETE, error=error
            )
    
    def list_directory(
        self,
        path: str,
        agent_id: str = "system",
        recursive: bool = False
    ) -> FileAccessResult:
        """List directory contents."""
        error = self._validate_access(path, FileOperation.READ)
        if error:
            return FileAccessResult(
                success=False, path=path, operation=FileOperation.READ, error=error
            )
        
        try:
            resolved = Path(path).resolve()
            
            if not resolved.is_dir():
                return FileAccessResult(
                    success=False, path=path, operation=FileOperation.READ,
                    error=f"Not a directory: {path}"
                )
            
            if recursive:
                items = list(resolved.rglob("*"))
            else:
                items = list(resolved.iterdir())
            
            file_list = []
            for item in items[:1000]:  # Limit
                file_list.append({
                    "name": item.name,
                    "path": str(item),
                    "is_dir": item.is_dir(),
                    "size": item.stat().st_size if item.is_file() else 0
                })
            
            return FileAccessResult(
                success=True, path=path, operation=FileOperation.READ,
                content=None,
                metadata={"files": file_list, "count": len(file_list)}
            )
            
        except Exception as e:
            return FileAccessResult(
                success=False, path=path, operation=FileOperation.READ, error=str(e)
            )
    
    def get_audit_log(
        self,
        agent_id: Optional[str] = None,
        operation: Optional[FileOperation] = None,
        last_n: int = 100
    ) -> List[FileAuditEntry]:
        """Get filtered audit log entries."""
        entries = self._audit_log
        
        if agent_id:
            entries = [e for e in entries if e.agent_id == agent_id]
        if operation:
            entries = [e for e in entries if e.operation == operation]
        
        return entries[-last_n:]
    
    def add_allowed_root(self, path: str):
        """Add an allowed root path at runtime."""
        resolved = Path(path).resolve()
        if resolved not in self.allowed_roots:
            self.allowed_roots.append(resolved)
            logger.info(f"Added allowed root: {resolved}")
    
    def block_extension(self, ext: str):
        """Block an additional file extension."""
        if not ext.startswith("."):
            ext = f".{ext}"
        self._blocked_extensions.add(ext.lower())
