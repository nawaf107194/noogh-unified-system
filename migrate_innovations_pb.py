import json
import os
import sys
import time
from pathlib import Path

# Fix python path for proto generated files
sys.path.append(str(Path(__file__).parent.parent))
from proto_generated.evolution import learning_pb2
from proto_generated.common import types_pb2

def json_to_proto(json_inno):
    """Convert dict from JSONL to Protobuf Innovation"""
    p = learning_pb2.Innovation()
    
    # Map ID
    inno_id = json_inno.get('_id')
    if not inno_id:
        # Fallback ID generation same as innovation_applier
        timestamp = json_inno.get('timestamp', time.time())
        inno_type = json_inno.get('innovation_type', 'unknown')
        inno_id = f"{inno_type}_{timestamp}"
    p.id = str(inno_id)

    # Basic string fields mapping
    p.description = json_inno.get('rationale', '')
    p.reasoning = json_inno.get('rationale', '')
    p.trigger_event = str(json_inno.get('triggered_by', ''))

    # Type Enum Mapping
    str_type = json_inno.get('innovation_type', '').lower()
    p.context['original_type'] = str_type
    
    if 'security' in str_type:
        p.innovation_type = learning_pb2.INNOVATION_TYPE_FEATURE
    elif 'optimize' in str_type or 'parallel' in str_type or 'async' in str_type:
        p.innovation_type = learning_pb2.INNOVATION_TYPE_PERFORMANCE
    elif 'refactor' in str_type or 'architecture' in str_type:
        p.innovation_type = learning_pb2.INNOVATION_TYPE_REFACTOR
    else:
        p.innovation_type = learning_pb2.INNOVATION_TYPE_UNSPECIFIED

    # Status Enum Mapping
    str_status = json_inno.get('status', '').lower()
    if str_status == 'suggested':
        p.status = learning_pb2.INNOVATION_STATUS_SUGGESTED
    elif str_status == 'applied':
        p.status = learning_pb2.INNOVATION_STATUS_APPLIED
    else:
        p.status = learning_pb2.INNOVATION_STATUS_UNSPECIFIED
        
    # Priority
    priority = json_inno.get('priority', 'medium')
    if isinstance(priority, str):
        priority_map = {'high': 1, 'medium': 5, 'low': 9}
        p.priority = priority_map.get(priority.lower(), 5)
    else:
        p.priority = int(priority)
        
    # Context
    tags = json_inno.get('source_tags', [])
    if tags:
        p.context['tags'] = ",".join(tags)
    
    # Timestamps
    ts = json_inno.get('timestamp')
    if ts:
        p.suggested_at.seconds = int(ts)
        p.suggested_at.nanos = int((ts - int(ts)) * 1e9)
        
    # Applied At
    applied_ts = json_inno.get('applied_at')
    if applied_ts:
        p.applied_at.seconds = int(applied_ts)
        p.applied_at.nanos = int((applied_ts - int(applied_ts)) * 1e9)

    # Files
    files = json_inno.get('target_files', [])
    if files:
        p.affected_files.extend(files)
        
    return p

def run_migration_and_benchmark():
    home = str(Path.home())
    json_path = os.path.join(home, ".noogh", "learning_innovations.jsonl")
    pb_path = os.path.join(home, ".noogh", "innovations.pb")

    print(f"Reading {json_path}")
    if not os.path.exists(json_path):
        print("File doesn't exist, creating some dummy innovations for benchmark")
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        with open(json_path, 'w') as f:
            for i in range(100): # Create 100 fake items
                dummy = {
                    "innovation_type": "optimize_memory_queries",
                    "status": "suggested",
                    "rationale": "Queries are slow in large blocks",
                    "triggered_by": "time_series_anomaly",
                    "timestamp": time.time(),
                    "priority": "high",
                    "target_files": ["file1.py", "file2.py"],
                    "source_tags": ["db", "latency"]
                }
                f.write(json.dumps(dummy) + "\\n")
    
    # 1. Read JSON
    start_json_read = time.time()
    dict_innovations = []
    with open(json_path, 'r') as f:
        for line in f:
            try:
                dict_innovations.append(json.loads(line.strip()))
            except:
                pass
    json_read_time = time.time() - start_json_read
    
    # Convert all
    proto_innovations = [json_to_proto(d) for d in dict_innovations]
    
    # Save PB
    start_pb_write = time.time()
    with open(pb_path, 'wb') as f:
        # Write length-prefixed stream
        for p in proto_innovations:
            data = p.SerializeToString()
            size_bytes = len(data).to_bytes(4, byteorder='little')
            f.write(size_bytes)
            f.write(data)
    pb_write_time = time.time() - start_pb_write
    
    # Load PB back to benchmark
    start_pb_read = time.time()
    loaded_protos = []
    with open(pb_path, 'rb') as f:
        while True:
            size_bytes = f.read(4)
            if not size_bytes:
                break
            size = int.from_bytes(size_bytes, byteorder='little')
            data = f.read(size)
            p = learning_pb2.Innovation()
            p.ParseFromString(data)
            loaded_protos.append(p)
    pb_read_time = time.time() - start_pb_read
    
    # File sizes
    json_size = os.path.getsize(json_path)
    pb_size = os.path.getsize(pb_path)
    
    print("\n" + "="*50)
    print("MIGRATION & BENCHMARK REPORT")
    print("="*50)
    print(f"Total Innovations Migrated: {len(loaded_protos)}")
    print(f"\n[Size Comparison]")
    print(f"JSONL Size: {json_size/1024:.2f} KB")
    print(f"Protobuf Size: {pb_size/1024:.2f} KB")
    print(f"Compression: {json_size/pb_size:.2f}x smaller")
    
    print(f"\n[Read Speed Comparison]")
    print(f"JSONL Read Time: {json_read_time*1000:.2f} ms")
    print(f"Protobuf Read Time: {pb_read_time*1000:.2f} ms")
    speedup = json_read_time / pb_read_time if pb_read_time > 0 else float('inf')
    print(f"Speedup: {speedup:.2f}x faster")
    print("="*50)

if __name__ == '__main__':
    run_migration_and_benchmark()
