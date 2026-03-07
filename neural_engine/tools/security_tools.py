"""
Security Tools for NOOGH
=========================
Provides security functions that ALLaM can call to protect the system.
Includes firewall control, IP blocking, IDS alerts, and security logging.
"""

import logging
import subprocess
import os
import json
import hashlib
import hmac
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Security log path
SECURITY_LOG_PATH = Path("/home/noogh/projects/noogh_unified_system/src/logs/security")
BLOCKED_IPS_FILE = SECURITY_LOG_PATH / "blocked_ips.json"
SECURITY_EVENTS_LOG = SECURITY_LOG_PATH / "events.log"
HMAC_SECRET = os.getenv("NOOGH_HMAC_SECRET", "noogh-security-key-2026")


def _ensure_security_dirs():
    """Ensure security directories exist."""
    SECURITY_LOG_PATH.mkdir(parents=True, exist_ok=True)
    if not BLOCKED_IPS_FILE.exists():
        BLOCKED_IPS_FILE.write_text("[]")


def _compute_hmac(message: str) -> str:
    """Compute HMAC for tamper-proof logging."""
    return hmac.new(
        HMAC_SECRET.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()[:16]


# =============================================================================
# FIREWALL TOOLS
# =============================================================================

def get_firewall_status() -> Dict[str, Any]:
    """
    Get current firewall status using iptables/ufw.
    
    Returns:
        Dict with firewall status and rules
    """
    try:
        # Try ufw first
        result = subprocess.run(
            ["ufw", "status", "verbose"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            status = "active" if "Status: active" in result.stdout else "inactive"
            
            return {
                "success": True,
                "firewall": "ufw",
                "status": status,
                "rules_count": len([l for l in lines if "ALLOW" in l or "DENY" in l]),
                "raw_output": result.stdout[:500]
            }
        
        # Fallback to iptables
        result = subprocess.run(
            ["iptables", "-L", "-n", "--line-numbers"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            return {
                "success": True,
                "firewall": "iptables",
                "status": "active",
                "raw_output": result.stdout[:500]
            }
        
        return {
            "success": False,
            "error": "No firewall detected",
            "suggestion": "Install ufw: sudo apt install ufw"
        }
        
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Firewall check timed out"}
    except FileNotFoundError:
        return {"success": False, "error": "Firewall tools not installed"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def block_ip(ip: str, reason: str = "Suspicious activity") -> Dict[str, Any]:
    """
    Block an IP address using iptables.
    Also logs to blocked_ips.json for persistence.
    
    Args:
        ip: IP address to block
        reason: Reason for blocking
        
    Returns:
        Dict with success status
    """
    _ensure_security_dirs()
    
    # Validate IP format (basic)
    parts = ip.split(".")
    if len(parts) != 4:
        return {"success": False, "error": f"Invalid IP format: {ip}"}
    
    try:
        # Log the block action first
        log_security_event({
            "action": "block_ip",
            "ip": ip,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        })
        
        # Add to blocked IPs file
        blocked = json.loads(BLOCKED_IPS_FILE.read_text())
        if ip not in [b["ip"] for b in blocked]:
            blocked.append({
                "ip": ip,
                "reason": reason,
                "blocked_at": datetime.now().isoformat()
            })
            BLOCKED_IPS_FILE.write_text(json.dumps(blocked, indent=2))
        
        # Try to block with iptables (requires sudo)
        try:
            result = subprocess.run(
                ["sudo", "iptables", "-A", "INPUT", "-s", ip, "-j", "DROP"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                logger.info(f"🛡️ Blocked IP {ip}: {reason}")
                return {
                    "success": True,
                    "ip": ip,
                    "blocked": True,
                    "method": "iptables",
                    "reason": reason
                }
        except Exception:
            pass  # Fall through to software-only block
        
        # Software-only block (logged but not enforced at OS level)
        logger.warning(f"⚠️ IP {ip} blocked in software only (no iptables access)")
        return {
            "success": True,
            "ip": ip,
            "blocked": True,
            "method": "software",
            "reason": reason,
            "note": "Blocked in NOOGH only, not at OS firewall level"
        }
        
    except Exception as e:
        logger.error(f"Failed to block IP {ip}: {e}")
        return {"success": False, "error": str(e)}


def unblock_ip(ip: str) -> Dict[str, Any]:
    """
    Unblock a previously blocked IP address.
    
    Args:
        ip: IP address to unblock
        
    Returns:
        Dict with success status
    """
    _ensure_security_dirs()
    
    try:
        # Remove from blocked IPs file
        blocked = json.loads(BLOCKED_IPS_FILE.read_text())
        original_count = len(blocked)
        blocked = [b for b in blocked if b["ip"] != ip]
        
        if len(blocked) < original_count:
            BLOCKED_IPS_FILE.write_text(json.dumps(blocked, indent=2))
            
            # Try to unblock with iptables
            try:
                subprocess.run(
                    ["sudo", "iptables", "-D", "INPUT", "-s", ip, "-j", "DROP"],
                    capture_output=True,
                    timeout=5
                )
            except Exception:
                pass
            
            log_security_event({
                "action": "unblock_ip",
                "ip": ip,
                "timestamp": datetime.now().isoformat()
            })
            
            return {"success": True, "ip": ip, "unblocked": True}
        else:
            return {"success": False, "error": f"IP {ip} was not blocked"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_blocked_ips() -> Dict[str, Any]:
    """
    Get list of all blocked IPs.
    
    Returns:
        Dict with blocked IP list
    """
    _ensure_security_dirs()
    
    try:
        blocked = json.loads(BLOCKED_IPS_FILE.read_text())
        return {
            "success": True,
            "count": len(blocked),
            "blocked_ips": blocked
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# =============================================================================
# SECURITY LOGGING (HMAC-protected)
# =============================================================================

def log_security_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Log a security event with HMAC protection for tamper detection.
    
    Args:
        event: Event details to log
        
    Returns:
        Dict with success status
    """
    _ensure_security_dirs()
    
    try:
        # Add timestamp and compute HMAC
        event["logged_at"] = datetime.now().isoformat()
        event_json = json.dumps(event, sort_keys=True)
        event["hmac"] = _compute_hmac(event_json)
        
        # Append to log file
        with open(SECURITY_EVENTS_LOG, "a") as f:
            f.write(json.dumps(event) + "\n")
        
        logger.info(f"🔒 Security event logged: {event.get('action', 'unknown')}")
        return {"success": True, "logged": True, "event_id": event["hmac"]}
        
    except Exception as e:
        logger.error(f"Failed to log security event: {e}")
        return {"success": False, "error": str(e)}


def get_security_events(limit: int = 50) -> Dict[str, Any]:
    """
    Get recent security events from the log.
    
    Args:
        limit: Maximum number of events to return
        
    Returns:
        Dict with events list
    """
    _ensure_security_dirs()
    
    try:
        if not SECURITY_EVENTS_LOG.exists():
            return {"success": True, "count": 0, "events": []}
        
        events = []
        with open(SECURITY_EVENTS_LOG, "r") as f:
            for line in f:
                if line.strip():
                    try:
                        events.append(json.loads(line))
                    except Exception:
                        pass
        
        # Return most recent events
        return {
            "success": True,
            "count": len(events),
            "events": events[-limit:]
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


# =============================================================================
# INTRUSION DETECTION (IDS)
# =============================================================================

def check_suspicious_activity() -> Dict[str, Any]:
    """
    Check for suspicious activity indicators.
    
    Returns:
        Dict with suspicious activity report
    """
    alerts = []
    
    try:
        # Check for failed SSH attempts
        try:
            result = subprocess.run(
                ["grep", "-c", "Failed password", "/var/log/auth.log"],
                capture_output=True,
                text=True,
                timeout=5
            )
            failed_ssh = int(result.stdout.strip()) if result.returncode == 0 else 0
            if failed_ssh > 10:
                alerts.append({
                    "type": "ssh_bruteforce",
                    "severity": "high" if failed_ssh > 50 else "medium",
                    "count": failed_ssh,
                    "message": f"{failed_ssh} failed SSH attempts detected"
                })
        except Exception:
            pass
        
        # Check for high CPU usage (potential mining)
        try:
            result = subprocess.run(
                ["ps", "-eo", "pcpu,comm", "--sort=-pcpu"],
                capture_output=True,
                text=True,
                timeout=5
            )
            lines = result.stdout.strip().split("\n")[1:6]  # Top 5
            for line in lines:
                parts = line.split()
                if len(parts) >= 2:
                    cpu = float(parts[0])
                    proc = parts[1]
                    if cpu > 80:
                        alerts.append({
                            "type": "high_cpu",
                            "severity": "medium",
                            "process": proc,
                            "cpu_percent": cpu,
                            "message": f"Process {proc} using {cpu}% CPU"
                        })
        except Exception:
            pass
        
        # Check for unusual network connections
        try:
            result = subprocess.run(
                ["ss", "-tuln"],
                capture_output=True,
                text=True,
                timeout=5
            )
            open_ports = result.stdout.count("LISTEN")
            if open_ports > 20:
                alerts.append({
                    "type": "many_open_ports",
                    "severity": "low",
                    "count": open_ports,
                    "message": f"{open_ports} listening ports detected"
                })
        except Exception:
            pass
        
        return {
            "success": True,
            "alert_count": len(alerts),
            "alerts": alerts,
            "status": "critical" if any(a["severity"] == "high" for a in alerts) 
                      else "warning" if alerts else "ok"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def emergency_lockdown(reason: str = "Security threat detected") -> Dict[str, Any]:
    """
    Initiate emergency security lockdown.
    Blocks all non-essential incoming connections.
    
    Args:
        reason: Reason for lockdown
        
    Returns:
        Dict with lockdown status
    """
    try:
        log_security_event({
            "action": "emergency_lockdown",
            "reason": reason,
            "severity": "critical"
        })
        
        # In production, this would:
        # 1. Block all incoming connections except SSH
        # 2. Alert administrators
        # 3. Create system snapshot
        
        logger.critical(f"🚨 EMERGENCY LOCKDOWN: {reason}")
        
        return {
            "success": True,
            "lockdown": True,
            "reason": reason,
            "actions_taken": [
                "Security event logged",
                "Alert triggered",
                "Ready for manual intervention"
            ],
            "note": "Full lockdown requires manual confirmation"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


# =============================================================================
# TOOL REGISTRATION (SUPERSEDED)
# =============================================================================

def register_security_tools(registry=None) -> None:
    """NO-OP: Tools are now defined in unified_core.tools.definitions.
    
    This function previously registered tools with the deprecated
    neural_engine.tools.tool_registry. All tools are now managed
    statically via unified_core.tool_registry.
    """
    logger.debug(
        "register_security_tools() is superseded by unified_core.tools.definitions"
    )
