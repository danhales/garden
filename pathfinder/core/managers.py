"""
Manager classes for Pathfinder
"""

import os
import json
import time
import uuid
import logging
import collections
import importlib.util
from typing import Dict, List, Set, Tuple, Optional, Any, Callable, Union
from pathlib import Path

from .models import ContextualNode, Context, ContextTransition, PathRoute, PriorityType

# Initialize logging
logger = logging.getLogger('pathfinder.managers')

class ContextManager:
    """
    Manages multiple contexts and transitions between them
    
    Like a dog trainer who works with multiple dogs, keeping track
    of each dog's training status and transitioning between them.
    """
    def __init__(self, module_generator=None, storage_dir=None):
        """Initialize the context manager"""
        self.contexts: Dict[str, Context] = {}
        self.paths: Dict[str, PathRoute] = {}  # Using PathRoute instead of Path
        self.current_context_id: Optional[str] = None
        self.active_path_id: Optional[str] = None
        self.module_generator = module_generator
        self.storage_dir = storage_dir or Path.home() / '.pathfinder'
        
        # Ensure the storage directory exists
        if not isinstance(self.storage_dir, Path):
            self.storage_dir = Path(self.storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Load any existing contexts and paths
        self._load_data()
    
    def create_context(self, name: str, description: str) -> Context:
        """Create a new context"""
        context_id = str(uuid.uuid4())
        context = Context(id=context_id, name=name, description=description)
        self.contexts[context_id] = context
        logger.info(f"Created new context: {name} ({context_id})")
        return context
    
    def switch_context(self, context_id: str, reason: str = "Manual switch", 
                      carry_nodes: List[str] = None) -> Context:
        """Switch to a different context"""
        if context_id not in self.contexts:
            raise ValueError(f"Context {context_id} does not exist")
        
        # Create a transition
        transition = ContextTransition(
            from_context_id=self.current_context_id,
            to_context_id=context_id,
            reason=reason,
            carried_nodes=carry_nodes or []
        )
        
        # If we have an active path, add the transition to it
        if self.active_path_id and self.active_path_id in self.paths:
            self.paths[self.active_path_id].add_transition(transition)
        
        # Transfer carried nodes to the new context
        if carry_nodes and self.current_context_id and self.current_context_id in self.contexts:
            for node_id in carry_nodes:
                node = self.contexts[self.current_context_id].get_node(node_id)
                if node:
                    # Clone the node to the new context
                    self.contexts[context_id].add_node(node)
        
        # Update current context
        prev_context_id = self.current_context_id
        self.current_context_id = context_id
        self.contexts[context_id].last_accessed = time.time()
        
        logger.info(f"Switched context: {prev_context_id} -> {context_id}")
        return self.contexts[context_id]
    
    def create_path(self, name: str, description: str) -> PathRoute:
        """Create a new path"""
        path_id = str(uuid.uuid4())
        path = PathRoute(id=path_id, name=name, description=description)  # Using PathRoute instead of Path
        self.paths[path_id] = path
        logger.info(f"Created new path: {name} ({path_id})")
        return path
    
    def start_recording_path(self, path_id: str) -> None:
        """Start recording transitions to the specified path"""
        if path_id not in self.paths:
            raise ValueError(f"Path {path_id} does not exist")
        self.active_path_id = path_id
        logger.info(f"Started recording to path: {path_id}")
    
    def stop_recording_path(self) -> None:
        """Stop recording transitions"""
        logger.info(f"Stopped recording to path: {self.active_path_id}")
        self.active_path_id = None
    
    def replay_path(self, path_id: str, callback: Optional[Callable[[Context], None]] = None) -> None:
        """
        Replay a path, switching through contexts in order
        
        If a callback is provided, it will be called after each context switch
        """
        if path_id not in self.paths:
            raise ValueError(f"Path {path_id} does not exist")
        
        path = self.paths[path_id]
        logger.info(f"Replaying path: {path.name}")
        
        for transition in path.transitions:
            context = self.switch_context(
                transition.to_context_id,
                reason=f"Replaying path {path.name}"
            )
            
            if callback:
                callback(context)
            
            # Pause briefly between transitions
            time.sleep(0.5)
    
    def get_recent_contexts(self, n: int = 5) -> List[Context]:
        """Get the N most recently accessed contexts"""
        sorted_contexts = sorted(
            self.contexts.values(),
            key=lambda c: c.last_accessed,
            reverse=True
        )
        return sorted_contexts[:n]
    
    def analyze_context_patterns(self) -> Dict:
        """
        Analyze patterns in context transitions
        
        Returns insights like common transitions, frequently accessed contexts,
        and cyclical patterns.
        """
        if not self.paths:
            return {"message": "No paths available for analysis"}
        
        # Count transitions between contexts
        transition_counts = collections.defaultdict(int)
        for path in self.paths.values():
            for i in range(len(path.transitions) - 1):
                from_ctx = path.transitions[i].to_context_id
                to_ctx = path.transitions[i + 1].to_context_id
                transition_counts[(from_ctx, to_ctx)] += 1
        
        # Find common transition pairs
        common_transitions = sorted(
            [{"from": k[0], "to": k[1], "count": v} for k, v in transition_counts.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:10]
        
        # Find frequently visited contexts
        context_visits = collections.defaultdict(int)
        for path in self.paths.values():
            for transition in path.transitions:
                context_visits[transition.to_context_id] += 1
        
        frequent_contexts = sorted(
            [{"id": k, "visits": v} for k, v in context_visits.items()],
            key=lambda x: x["visits"],
            reverse=True
        )[:10]
        
        # Detect cycles in paths
        cycles = []
        for path in self.paths.values():
            context_sequence = [t.to_context_id for t in path.transitions]
            # Look for repeating sequences (simple cycle detection)
            for length in range(2, min(10, len(context_sequence) // 2 + 1)):
                for i in range(len(context_sequence) - length * 2 + 1):
                    if context_sequence[i:i+length] == context_sequence[i+length:i+length*2]:
                        cycle = {
                            "path_id": path.id,
                            "path_name": path.name,
                            "cycle_length": length,
                            "contexts": context_sequence[i:i+length]
                        }
                        cycles.append(cycle)
                        break
        
        return {
            "common_transitions": common_transitions,
            "frequent_contexts": frequent_contexts,
            "cycles": cycles
        }
    
    def save_data(self) -> None:
        """Save all contexts and paths to disk"""
        # Save contexts
        contexts_file = self.storage_dir / 'contexts.json'
        contexts_data = {k: v.to_dict() for k, v in self.contexts.items()}
        with open(contexts_file, 'w') as f:
            json.dump(contexts_data, f, indent=2)
        
        # Save paths
        paths_file = self.storage_dir / 'paths.json'
        paths_data = {k: v.to_dict() for k, v in self.paths.items()}
        with open(paths_file, 'w') as f:
            json.dump(paths_data, f, indent=2)
        
        # Save current state
        state_file = self.storage_dir / 'state.json'
        state_data = {
            'current_context_id': self.current_context_id,
            'active_path_id': self.active_path_id,
            'last_updated': time.time()
        }
        with open(state_file, 'w') as f:
            json.dump(state_data, f, indent=2)
        
        logger.info(f"Saved {len(self.contexts)} contexts and {len(self.paths)} paths")
    
    def _load_data(self) -> None:
        """Load contexts and paths from disk"""
        # Load contexts
        contexts_file = self.storage_dir / 'contexts.json'
        if contexts_file.exists():
            with open(contexts_file, 'r') as f:
                contexts_data = json.load(f)
                for context_id, context_data in contexts_data.items():
                    self.contexts[context_id] = Context.from_dict(context_data)
        
        # Load paths
        paths_file = self.storage_dir / 'paths.json'
        if paths_file.exists():
            with open(paths_file, 'r') as f:
                paths_data = json.load(f)
                for path_id, path_data in paths_data.items():
                    self.paths[path_id] = PathRoute.from_dict(path_data)  # Using PathRoute instead of Path
        
        # Load current state
        state_file = self.storage_dir / 'state.json'
        if state_file.exists():
            with open(state_file, 'r') as f:
                state_data = json.load(f)
                self.current_context_id = state_data.get('current_context_id')
                self.active_path_id = state_data.get('active_path_id')
        
        logger.info(f"Loaded {len(self.contexts)} contexts and {len(self.paths)} paths")
    
    def import_from_graph_module(self, module_path: str, label: str, limit: int = 100) -> List[str]:
        """
        Import nodes from a generated Neo4j module
        
        Args:
            module_path: Path to the generated module
            label: Neo4j label to query
            limit: Maximum number of nodes to import
            
        Returns:
            List of node IDs that were imported
        """
        # Dynamically import the module
        spec = importlib.util.spec_from_file_location("graph_module", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Get current context
        if not self.current_context_id:
            raise ValueError("No active context")
        context = self.contexts[self.current_context_id]
        
        # Query the module for nodes
        # We're assuming the module has a structure similar to what's in modulegenerator.py
        # This is a simplification and might need adjustment based on actual module structure
        query = f"MATCH (n:{label}) RETURN n LIMIT {limit}"
        results = module._query(query)
        
        imported_ids = []
        for result in results:
            node_data = result['n']
            node_id = node_data.get('uuid', str(uuid.uuid4()))
            
            contextual_node = ContextualNode(
                uuid=node_id,
                labels=[label],
                properties=node_data.get('properties', {}),
                relevance_score=0.5  # Default middle relevance
            )
            
            context.add_node(contextual_node)
            imported_ids.append(node_id)
        
        logger.info(f"Imported {len(imported_ids)} nodes with label {label}")
        return imported_ids
    
    def visualize_context(self, context_id: str = None) -> Dict:
        """
        Generate visualization data for a context
        
        Returns a dictionary with nodes and links formatted for visualization
        with accessibility information included.
        """
        if context_id is None:
            context_id = self.current_context_id
        
        if context_id not in self.contexts:
            raise ValueError(f"Context {context_id} does not exist")
        
        context = self.contexts[context_id]
        
        # Prepare nodes
        nodes = []
        for node_id, node in context.nodes.items():
            nodes.append({
                "id": node_id,
                "label": ":".join(node.labels),
                "name": node.get_display_name(),
                "priority": node.priority,
                "size": 10 + node.access_count * 2,  # Size based on access count
                "color": "#ff9900" if node_id in context.focus_nodes else "#3388aa",
                "properties": node.properties,
                "alt_text": node.alt_text,
                "aria_label": node.alt_text  # For accessibility
            })
        
        # Prepare links
        links = []
        for source_id, rel_types in context.relationships.items():
            for rel_type, targets in rel_types.items():
                for target in targets:
                    links.append({
                        "id": target.get("id", str(uuid.uuid4())),
                        "source": source_id,
                        "target": target["target"],
                        "type": rel_type,
                        "properties": target["properties"],
                        "alt_text": target.get("alt_text", f"Relationship of type {rel_type}"),
                        "aria_label": target.get("alt_text", f"Relationship of type {rel_type}")  # For accessibility
                    })
        
        return {
            "nodes": nodes,
            "links": links,
            "context": {
                "id": context_id,
                "name": context.name,
                "description": context.description,
                "accessibility_description": context.accessibility_description
            }
        }
    
    def compare_contexts(self, context_id_1: str, context_id_2: str) -> Dict:
        """
        Compare two contexts and identify similarities and differences
        
        Returns information about shared nodes, exclusive nodes, and
        priority differences.
        """
        if context_id_1 not in self.contexts or context_id_2 not in self.contexts:
            raise ValueError("One or both contexts do not exist")
        
        ctx1 = self.contexts[context_id_1]
        ctx2 = self.contexts[context_id_2]
        
        # Find common and exclusive nodes
        nodes1 = set(ctx1.nodes.keys())
        nodes2 = set(ctx2.nodes.keys())
        
        common_nodes = nodes1.intersection(nodes2)
        only_in_ctx1 = nodes1 - nodes2
        only_in_ctx2 = nodes2 - nodes1
        
        # Compare priorities for common nodes
        priority_diffs = []
        for node_id in common_nodes:
            node1 = ctx1.nodes[node_id]
            node2 = ctx2.nodes[node_id]
            
            # Ensure both nodes have updated priorities
            node1.update_priority(ctx1.priority_scheme)
            node2.update_priority(ctx2.priority_scheme)
            
            diff = abs(node1.priority - node2.priority)
            if diff > 0.1:  # Only show significant differences
                priority_diffs.append({
                    "node_id": node_id,
                    "name": node1.get_display_name(),
                    "ctx1_priority": node1.priority,
                    "ctx2_priority": node2.priority,
                    "difference": diff
                })
        
        # Sort by difference
        priority_diffs.sort(key=lambda x: x["difference"], reverse=True)
        
        # Generate comparison summary for accessibility
        common_node_names = [ctx1.nodes[nid].get_display_name() for nid in list(common_nodes)[:5]]
        common_node_text = ", ".join(common_node_names) + ("..." if len(common_nodes) > 5 else "")
        
        accessibility_summary = (
            f"Comparing context {ctx1.name} with {ctx2.name}. "
            f"{len(common_nodes)} common nodes, "
            f"{len(only_in_ctx1)} nodes only in {ctx1.name}, "
            f"{len(only_in_ctx2)} nodes only in {ctx2.name}. "
            f"Common nodes include: {common_node_text}."
        )
        
        return {
            "context1": {
                "id": context_id_1,
                "name": ctx1.name
            },
            "context2": {
                "id": context_id_2,
                "name": ctx2.name
            },
            "common_nodes": len(common_nodes),
            "only_in_ctx1": len(only_in_ctx1),
            "only_in_ctx2": len(only_in_ctx2),
            "priority_differences": priority_diffs[:10],  # Top 10 differences
            "similarity_score": len(common_nodes) / max(1, len(nodes1.union(nodes2))),
            "accessibility_summary": accessibility_summary
        }