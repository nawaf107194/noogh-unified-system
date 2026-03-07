from typing import List

from pydantic import BaseModel, Field


class PluginToolRef(BaseModel):
    name: str
    type: str  # "skill" or "tool"


class PluginManifest(BaseModel):
    name: str
    version: str
    entrypoint: str  # e.g. "plugin.py:register"
    capabilities: List[str]
    tools: List[PluginToolRef] = Field(default_factory=list)
