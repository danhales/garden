"""
Core data models for Pathfinder
"""

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Set, Optional, Any, Callable, Union

class PriorityType(Enum):
    """Types of priority schemes for ranking nodes in a context"""
    RECENCY = auto()     # Most recently accessed nodes
    FREQUENCY = auto()   # Most frequently accessed nodes
    RELEVANCE = auto()   # Nodes with highest relevance score
    CENTRALITY = auto()  # Nodes with highest centrality in current view
    CUSTOM = auto()      # User-defined priority function


@dataclass
class ContextualNode:
    """
    A Neo4j node wrapped with contextual metadata
    
    Attributes:
        uuid: Unique identifier of the node
        labels: Neo4j labels for the node
        properties: Dictionary of node properties
        access_count: Number of times this node has been accessed
        last_accessed: Timestamp of last access
        relevance_score: Custom relevance score (0.0-1.0)
        notes: List of user notes about this node
        flags: Set of flags/tags for this node
        priority: Calculated priority value
        alt_text: Accessibility description
    """
    uuid: str
    labels: List[str]
    properties: Dict[str, Any]
    # Contextual metadata
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    relevance_score: float = 0.0
    notes: List[str] = field(default_factory=list)
    flags: Set[str] = field(default_factory=set)
    priority: float = 0.0
    alt_text: str = ""  # Accessibility description

    def __post_init__(self):
        """Calculate initial priority and set accessibility text"""
        self.update_priority()
        
        # Generate default alt text if none provided
        if not self.alt_text:
            name = self.get_display_name()
            label_text = ", ".join(self.labels)
            self.alt_text = f"{name}: {label_text} node"
    
    def access(self) -> None:
        """Record an access to this node"""
        self.access_count += 1
        self.last_accessed = time.time()
        self.update_priority()
    
    def update_priority(self, scheme: PriorityType = PriorityType.RECENCY) -> None:
        """Update the priority of this node based on the specified scheme"""
        if scheme == PriorityType.RECENCY:
            self.priority = self.last_accessed
        elif scheme == PriorityType.FREQUENCY:
            self.priority = self.access_count
        elif scheme == PriorityType.RELEVANCE:
            self.priority = self.relevance_score
        # Other schemes would be implemented here
    
    def add_note(self, note: str) -> None:
        """Add a note to this node"""
        self.notes.append(note)
    
    def add_flag(self, flag: str) -> None:
        """Flag this node with a marker"""
        self.flags.add(flag)
    
    def get_display_name(self) -> str:
        """Get a human-readable name for this node"""
        return self.properties.get('name', 
               self.properties.get('title', 
               f"{':'.join(self.labels)}({self.uuid[:8]}...)"))
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'uuid': self.uuid,
            'labels': self.labels,
            'properties': self.properties,
            'metadata': {
                'access_count': self.access_count,
                'last_accessed': self.last_accessed,
                'relevance_score': self.relevance_score,
                'notes': self.notes,
                'flags': list(self.flags),
                'priority': self.priority,
                'alt_text': self.alt_text
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ContextualNode':
        """Create a ContextualNode from a dictionary"""
        node = cls(
            uuid=data['uuid'],
            labels=data['labels'],
            properties=data['properties'],
            access_count=data['metadata']['access_count'],
            last_accessed=data['metadata']['last_accessed'],
            relevance_score=data['metadata']['relevance_score'],
            notes=data['metadata']['notes'],
            priority=data['metadata']['priority'],
            alt_text=data['metadata'].get('alt_text', '')
        )
        node.flags = set(data['metadata']['flags'])
        return node
    
    def __str__(self) -> str:
        """String representation of the node"""
        name = self.get_display_name()
        return f"{name} (priority: {self.priority:.2f})"


@dataclass
class Context:
    """
    Represents a specific perspective/context in the graph
    
    A context is like a dog trainer's mindset when working with a specific dog.
    Each dog has different training history, priorities, and relevant cues.
    
    Attributes:
        id: Unique identifier
        name: Human-readable name
        description: Longer description of this context
        nodes: Dictionary of nodes in this context
        relationships: Dictionary of relationships between nodes
        focus_nodes: List of node IDs that are currently in focus
        created_at: Creation timestamp
        last_accessed: Last access timestamp
        priority_scheme: How nodes are prioritized in this context
        custom_priority_function: Optional custom priority function
        tags: Set of tags/categories for this context
        accessibility_description: Detailed description for screen readers
    """
    id: str
    name: str
    description: str
    nodes: Dict[str, ContextualNode] = field(default_factory=dict)
    relationships: Dict[str, Dict[str, List[Dict]]] = field(default_factory=dict)
    focus_nodes: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    priority_scheme: PriorityType = PriorityType.RECENCY
    custom_priority_function: Optional[Callable] = None
    tags: Set[str] = field(default_factory=set)
    accessibility_description: str = ""
    
    def __post_init__(self):
        """Initialize with default accessibility description if none provided"""
        if not self.accessibility_description:
            self.accessibility_description = (
                f"Context: {self.name}. {self.description}. "
                f"Contains {len(self.nodes)} nodes with {len(self.focus_nodes)} focus nodes."
            )
    
    def add_node(self, node: ContextualNode) -> None:
        """Add a node to this context"""
        self.nodes[node.uuid] = node
        
        # Update accessibility description
        self.update_accessibility_description()
    
    def add_relationship(self, source_id: str, target_id: str, rel_type: str, 
                        properties: Dict = None, rel_id: str = None) -> None:
        """Add a relationship between two nodes in this context"""
        if source_id not in self.relationships:
            self.relationships[source_id] = {}
        
        if rel_type not in self.relationships[source_id]:
            self.relationships[source_id][rel_type] = []
        
        # Generate a relationship ID if not provided
        if not rel_id:
            rel_id = str(uuid.uuid4())
        
        self.relationships[source_id][rel_type].append({
            'id': rel_id,
            'target': target_id,
            'properties': properties or {},
            'alt_text': self._generate_relationship_alt_text(source_id, target_id, rel_type)
        })
        
        # Update accessibility description
        self.update_accessibility_description()
    
    def _generate_relationship_alt_text(self, source_id: str, target_id: str, rel_type: str) -> str:
        """Generate alt text for a relationship"""
        source_node = self.nodes.get(source_id)
        target_node = self.nodes.get(target_id)
        
        if source_node and target_node:
            source_name = source_node.get_display_name()
            target_name = target_node.get_display_name()
            return f"{source_name} {rel_type} {target_name}"
        
        return f"Relationship of type {rel_type}"
    
    def get_node(self, node_id: str) -> Optional[ContextualNode]:
        """Get a node by ID and record the access"""
        node = self.nodes.get(node_id)
        if node:
            node.access()
            self.last_accessed = time.time()
        return node
    
    def set_focus(self, node_ids: List[str]) -> None:
        """Set the current focus nodes"""
        self.focus_nodes = node_ids
        self.update_accessibility_description()
    
    def update_accessibility_description(self) -> None:
        """Update the accessibility description based on current state"""
        focus_names = []
        for node_id in self.focus_nodes:
            node = self.nodes.get(node_id)
            if node:
                focus_names.append(node.get_display_name())
        
        focus_text = ", ".join(focus_names) if focus_names else "none"
        
        self.accessibility_description = (
            f"Context: {self.name}. {self.description}. "
            f"Contains {len(self.nodes)} nodes with {len(self.focus_nodes)} focus nodes. "
            f"Focus nodes: {focus_text}."
        )
    
    def top_nodes(self, n: int = 10) -> List[ContextualNode]:
        """Get the top N nodes by priority"""
        # Update all priorities first
        for node in self.nodes.values():
            node.update_priority(self.priority_scheme)
        
        # Use a heap to efficiently get top N
        return heapq.nlargest(n, self.nodes.values(), key=lambda x: x.priority)
    
    def set_priority_scheme(self, scheme: PriorityType, custom_function: Optional[Callable] = None) -> None:
        """Set the priority scheme for this context"""
        self.priority_scheme = scheme
        if scheme == PriorityType.CUSTOM:
            if custom_function is None:
                raise ValueError("Custom priority scheme requires a custom function")
            self.custom_priority_function = custom_function
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'nodes': {k: v.to_dict() for k, v in self.nodes.items()},
            'relationships': self.relationships,
            'focus_nodes': self.focus_nodes,
            'created_at': self.created_at,
            'last_accessed': self.last_accessed,
            'priority_scheme': self.priority_scheme.name,
            'tags': list(self.tags),
            'accessibility_description': self.accessibility_description
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Context':
        """Create a Context from a dictionary"""
        context = cls(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            focus_nodes=data['focus_nodes'],
            created_at=data['created_at'],
            last_accessed=data['last_accessed'],
            priority_scheme=PriorityType[data['priority_scheme']],
            tags=set(data.get('tags', [])),
            accessibility_description=data.get('accessibility_description', '')
        )
        
        # Reconstruct nodes
        for node_id, node_data in data['nodes'].items():
            context.nodes[node_id] = ContextualNode.from_dict(node_data)
        
        # Reconstruct relationships
        context.relationships = data['relationships']
        
        return context
    
    def __str__(self) -> str:
        """String representation of the context"""
        return f"Context: {self.name} ({len(self.nodes)} nodes, {len(self.focus_nodes)} focus nodes)"


@dataclass
class ContextTransition:
    """
    Records a transition between contexts
    
    Attributes:
        from_context_id: ID of the source context (can be None)
        to_context_id: ID of the destination context
        timestamp: When the transition occurred
        reason: Reason for the transition
        carried_nodes: List of node IDs carried between contexts
        notes: Additional notes about this transition
    """
    from_context_id: Optional[str]
    to_context_id: str
    timestamp: float = field(default_factory=time.time)
    reason: str = "Manual switch"
    carried_nodes: List[str] = field(default_factory=list)
    notes: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'from_context_id': self.from_context_id,
            'to_context_id': self.to_context_id,
            'timestamp': self.timestamp,
            'reason': self.reason,
            'carried_nodes': self.carried_nodes,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ContextTransition':
        """Create a ContextTransition from a dictionary"""
        return cls(
            from_context_id=data['from_context_id'],
            to_context_id=data['to_context_id'],
            timestamp=data['timestamp'],
            reason=data['reason'],
            carried_nodes=data['carried_nodes'],
            notes=data['notes']
        )


@dataclass
class PathRoute:  # Renamed from Path to avoid collision with pathlib.Path
    """
    Records a sequence of context transitions
    
    Like a training plan that works across multiple dogs, tracking progress
    and transitions between different training contexts.
    
    Attributes:
        id: Unique identifier
        name: Human-readable name
        description: Longer description
        transitions: List of transitions in this path
        created_at: Creation timestamp
        last_updated: Last update timestamp
        tags: Set of tags/categories for this path
        accessibility_description: Detailed description for screen readers
    """
    id: str
    name: str
    description: str
    transitions: List[ContextTransition] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)
    tags: Set[str] = field(default_factory=set)
    accessibility_description: str = ""
    
    def __post_init__(self):
        """Initialize with default accessibility description if none provided"""
        if not self.accessibility_description:
            self.accessibility_description = (
                f"Path: {self.name}. {self.description}. "
                f"Contains {len(self.transitions)} transitions."
            )
    
    def add_transition(self, transition: ContextTransition) -> None:
        """Add a transition to this path"""
        self.transitions.append(transition)
        self.last_updated = time.time()
        
        # Update accessibility description
        self.accessibility_description = (
            f"Path: {self.name}. {self.description}. "
            f"Contains {len(self.transitions)} transitions."
        )
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'transitions': [t.to_dict() for t in self.transitions],
            'created_at': self.created_at,
            'last_updated': self.last_updated,
            'tags': list(self.tags),
            'accessibility_description': self.accessibility_description
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PathRoute':
        """Create a PathRoute from a dictionary"""
        path = cls(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            created_at=data['created_at'],
            last_updated=data['last_updated'],
            tags=set(data.get('tags', [])),
            accessibility_description=data.get('accessibility_description', '')
        )
        
        # Reconstruct transitions
        for transition_data in data['transitions']:
            path.transitions.append(ContextTransition.from_dict(transition_data))
        
        return path


# Import missing modules needed by the code
import heapq  # Added at the end to avoid circular imports