from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Node:
    id: str
    type: str
    params: Dict[str, Any] = field(default_factory=dict)
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    display_name: Optional[str] = None


@dataclass
class Edge:
    source: str
    target: str


@dataclass
class ModelGraph:
    nodes: List[Node] = field(default_factory=list)
    edges: List[Edge] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
