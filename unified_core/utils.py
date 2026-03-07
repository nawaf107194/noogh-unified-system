# unified_core/utils.py

from dataclasses import dataclass, asdict
import json

@dataclass
class Serializable:
    def serialize(self):
        return json.dumps(asdict(self))

def deserialize(data, cls):
    return cls(**json.loads(data))