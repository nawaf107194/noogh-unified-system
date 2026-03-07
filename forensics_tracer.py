import sys
import os
import subprocess
import importlib
import time
import json
import traceback
from datetime import datetime

LOG_FILE = "/home/noogh/projects/noogh_unified_system/data/logs/forensics_trace.jsonl"

def log_event(event_type, data):
    event = {
        "timestamp": datetime.now().isoformat(),
        "type": event_type,
        "data": data
    }
    # Use ORIGINAL open to avoid recursion!
    with original_open(LOG_FILE, "a") as f:
        # Use default=str to handle non-serializable objects like _NamespacePath
        f.write(json.dumps(event, default=str) + "\n")

# A) Function Tracing
def trace_calls(frame, event, arg):
    if event != 'call':
        return
    
    code = frame.f_code
    func_name = code.co_name
    file_path = code.co_filename
    
    # Filter for project files only to avoid noise
    if "noogh_unified_system/src" in file_path:
        caller = frame.f_back
        caller_name = caller.f_code.co_name if caller else "root"
        caller_file = caller.f_code.co_filename if caller else "N/A"
        
        log_event("function_call", {
            "file": file_path,
            "function": func_name,
            "line": frame.f_lineno,
            "caller": f"{caller_name} ({caller_file})"
        })
    return trace_calls

# B) Subprocess Tracing (Monkey-patching)
original_popen = subprocess.Popen

def hooked_popen(*args, **kwargs):
    cmd = args[0] if args else kwargs.get("args")
    cwd = kwargs.get("cwd", os.getcwd())
    env = {k: "REDACTED" for k in kwargs.get("env", {}).keys()}
    
    log_event("subprocess_spawn", {
        "command": cmd,
        "cwd": cwd,
        "env_keys": list(env.keys()),
        "stack": traceback.format_stack()[:-1]
    })
    return original_popen(*args, **kwargs)

subprocess.Popen = hooked_popen

# C) Network Tracing (Socket Hooking)
import socket
original_socket = socket.socket

class HookedSocket(original_socket):
    def connect(self, address):
        log_event("network_connect", {"address": address})
        return super().connect(address)
    
    def send(self, data, flags=0):
        log_event("network_send", {"size": len(data)})
        return super().send(data, flags)

socket.socket = HookedSocket

# D) File I/O Tracing
import builtins
original_open = builtins.open

def hooked_open(file, mode='r', buffering=-1, encoding=None, errors=None, newline=None, closefd=True, opener=None):
    if 'w' in mode or 'a' in mode:
        log_event("file_write_attempt", {"file": str(file), "mode": mode})
    return original_open(file, mode, buffering, encoding, errors, newline, closefd, opener)

# builtins.open = hooked_open

# E) Import Tracing
original_import = __import__

def hooked_import(name, globals=None, locals=None, fromlist=(), level=0):
    log_event("import", {
        "module": name,
        "fromlist": fromlist,
        "level": level,
        "stack": traceback.format_stack()[-3:] # Capture recent stack
    })
    return original_import(name, globals, locals, fromlist, level)

# We can't easily monkey-patch __import__ globally without risks, 
# but we can try to hook into the meta path.
class TraceImporter:
    def find_spec(self, fullname, path, target=None):
        log_event("import_spec", {"fullname": fullname, "path": path})
        return None # Let other importers handle it

# sys.meta_path.insert(0, TraceImporter())

def start_instrumentation():
    print(f"[*] Starting Forensics Tracing. Logging to {LOG_FILE}")
    # Sys tracing and Import tracing are too verbose for production
    # log_event("info", {"message": "Instrumentation started (Limited to Subprocess & Network)"})

if __name__ == "__main__":
    start_instrumentation()
    # If run as a script, it just sits here. 
    # Better to use it as a module to be injected or preloaded.
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[*] Stopping instrumentation.")
