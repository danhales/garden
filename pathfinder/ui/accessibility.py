"""
Accessibility utilities for Pathfinder
"""

import re
import json
import logging
from typing import Dict, List, Optional, Any, Union

# Initialize logging
logger = logging.getLogger('pathfinder.accessibility')

class AccessibilityHelper:
    """
    Helper class for generating accessible components and descriptions
    """
    
    @staticmethod
    def create_node_description(node: Dict[str, Any]) -> str:
        """
        Create an accessible description for a node
        
        Args:
            node: Dictionary containing node data
            
        Returns:
            String description suitable for screen readers
        """
        name = node.get('name', 'Unnamed node')
        label = node.get('label', '')
        priority = node.get('priority', 0)
        
        # Get key properties to include in description
        properties = node.get('properties', {})
        key_props = []
        for key, value in properties.items():
            if key in ('name', 'title', 'id', 'type', 'category'):
                continue  # Skip properties already covered elsewhere
            if isinstance(value, (str, int, float, bool)):
                key_props.append(f"{key}: {value}")
        
        props_text = ". ".join(key_props[:3])  # Limit to 3 properties
        priority_text = f"Priority: {priority:.2f}" if priority else ""
        
        # Build the full description
        parts = []
        if name:
            parts.append(name)
        if label:
            parts.append(f"Type: {label}")
        if priority_text:
            parts.append(priority_text)
        if props_text:
            parts.append(props_text)
        
        return ". ".join(parts)
    
    @staticmethod
    def create_relationship_description(rel: Dict[str, Any], nodes: Dict[str, Dict]) -> str:
        """
        Create an accessible description for a relationship
        
        Args:
            rel: Dictionary containing relationship data
            nodes: Dictionary of nodes indexed by ID
            
        Returns:
            String description suitable for screen readers
        """
        source_id = rel.get('source')
        target_id = rel.get('target')
        rel_type = rel.get('type', 'related to')
        
        source_node = nodes.get(source_id, {})
        target_node = nodes.get(target_id, {})
        
        source_name = source_node.get('name', 'Unknown source')
        target_name = target_node.get('name', 'Unknown target')
        
        return f"{source_name} {rel_type} {target_name}"
    
    @staticmethod
    def create_context_summary(context: Dict[str, Any]) -> str:
        """
        Create an accessible summary for a context
        
        Args:
            context: Dictionary containing context data
            
        Returns:
            String summary suitable for screen readers
        """
        name = context.get('name', 'Unnamed context')
        description = context.get('description', '')
        nodes = context.get('nodes', {})
        focus_nodes = context.get('focus_nodes', [])
        
        focus_names = []
        for node_id in focus_nodes[:3]:  # Limit to first 3 focus nodes
            node = nodes.get(node_id, {})
            node_name = node.get('name', node.get('properties', {}).get('name', 'Unnamed node'))
            focus_names.append(node_name)
        
        focus_text = ", ".join(focus_names)
        if len(focus_nodes) > 3:
            focus_text += f", and {len(focus_nodes) - 3} more"
        
        summary = f"Context: {name}. {description}"
        if focus_text:
            summary += f" Focus nodes: {focus_text}."
        
        return summary
    
    @staticmethod
    def enhance_visualization_data(viz_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance visualization data with accessibility information
        
        Args:
            viz_data: Dictionary with nodes and links for visualization
            
        Returns:
            Enhanced data with accessibility attributes
        """
        # Create a mapping of nodes by ID for easier reference
        nodes_by_id = {node['id']: node for node in viz_data.get('nodes', [])}
        
        # Enhance nodes with accessibility information
        for node in viz_data.get('nodes', []):
            if not node.get('aria_label'):
                node['aria_label'] = AccessibilityHelper.create_node_description(node)
            
            # Add tabindex for keyboard navigation
            node['tabindex'] = 0
            
            # Add ARIA roles
            node['role'] = 'button'
            
            # Add additional metadata for screen readers
            focus = 'focus' if node['id'] in viz_data.get('context', {}).get('focus_nodes', []) else ''
            node['aria_description'] = f"{node.get('aria_label')}. {focus}"
        
        # Enhance links with accessibility information
        for link in viz_data.get('links', []):
            if not link.get('aria_label'):
                link['aria_label'] = AccessibilityHelper.create_relationship_description(
                    link, nodes_by_id
                )
            
            # Add ARIA roles
            link['role'] = 'link'
        
        # Add context-level accessibility information
        context = viz_data.get('context', {})
        if context and not context.get('aria_label'):
            context['aria_label'] = AccessibilityHelper.create_context_summary(context)
        
        # Add navigation landmarks
        viz_data['landmarks'] = {
            'context_selector': {
                'role': 'navigation',
                'aria_label': 'Context selector'
            },
            'graph_view': {
                'role': 'main',
                'aria_label': 'Graph visualization'
            },
            'focus_panel': {
                'role': 'complementary',
                'aria_label': 'Focus panel'
            },
            'path_controls': {
                'role': 'toolbar',
                'aria_label': 'Path recording controls'
            }
        }
        
        # Add keyboard shortcuts information
        viz_data['keyboard_shortcuts'] = [
            {'key': 'Tab', 'description': 'Navigate between elements'},
            {'key': 'Enter/Space', 'description': 'Activate selected element'},
            {'key': 'Escape', 'description': 'Close dialogs or cancel operations'},
            {'key': 'Arrow keys', 'description': 'Navigate within graph visualization'},
            {'key': 'Ctrl+F', 'description': 'Add selected node to focus'},
            {'key': 'Ctrl+N', 'description': 'Create new note for selected node'}
        ]
        
        return viz_data
    
    @staticmethod
    def generate_screen_reader_text(visualization_data: Dict[str, Any]) -> str:
        """
        Generate comprehensive text description of visualization for screen readers
        
        Args:
            visualization_data: Dictionary with nodes and links for visualization
            
        Returns:
            Structured text description
        """
        nodes = visualization_data.get('nodes', [])
        links = visualization_data.get('links', [])
        context = visualization_data.get('context', {})
        
        # Start with context description
        text_parts = []
        context_name = context.get('name', 'Unnamed context')
        context_desc = context.get('description', '')
        
        text_parts.append(f"Context: {context_name}")
        if context_desc:
            text_parts.append(context_desc)
        
        # Add node count
        text_parts.append(f"Contains {len(nodes)} nodes and {len(links)} relationships.")
        
        # Describe focus nodes
        focus_node_ids = context.get('focus_nodes', [])
        focus_nodes = [n for n in nodes if n['id'] in focus_node_ids]
        if focus_nodes:
            focus_names = [n.get('name', 'Unnamed node') for n in focus_nodes]
            text_parts.append(f"Focus nodes: {', '.join(focus_names)}.")
        
        # Describe top nodes (up to 5)
        top_nodes = sorted(nodes, key=lambda n: n.get('priority', 0), reverse=True)[:5]
        if top_nodes:
            text_parts.append("Top priority nodes:")
            for i, node in enumerate(top_nodes):
                name = node.get('name', 'Unnamed node')
                label = node.get('label', '')
                priority = node.get('priority', 0)
                text_parts.append(f"{i+1}. {name}, {label}, priority {priority:.2f}")
        
        # Describe key relationships
        if links:
            text_parts.append("Key relationships:")
            # Create node lookup by ID
            node_lookup = {n['id']: n for n in nodes}
            
            # Group relationships by type
            rel_by_type = {}
            for link in links:
                rel_type = link.get('type', 'related')
                if rel_type not in rel_by_type:
                    rel_by_type[rel_type] = []
                rel_by_type[rel_type].append(link)
            
            # Describe each type (up to 3 examples per type)
            for rel_type, rel_links in rel_by_type.items():
                examples = rel_links[:3]
                rel_desc = []
                for link in examples:
                    source_id = link.get('source')
                    target_id = link.get('target')
                    source_name = node_lookup.get(source_id, {}).get('name', 'Unknown')
                    target_name = node_lookup.get(target_id, {}).get('name', 'Unknown')
                    rel_desc.append(f"{source_name} to {target_name}")
                
                count_text = f"({len(rel_links)} total)" if len(rel_links) > 3 else ""
                text_parts.append(f"{rel_type} relationships {count_text}: {', '.join(rel_desc)}.")
        
        # Join all parts with appropriate spacing
        return "\n\n".join(text_parts)
    
    @staticmethod
    def create_keyboard_navigable_graph(viz_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add keyboard navigation metadata to graph visualization
        
        Args:
            viz_data: Dictionary with nodes and links for visualization
            
        Returns:
            Enhanced data with keyboard navigation information
        """
        # Add navigation order to nodes
        nodes = viz_data.get('nodes', [])
        for i, node in enumerate(nodes):
            node['nav_order'] = i
            
            # Add keyboard navigation connections
            up_idx = (i - 1) % len(nodes) if len(nodes) > 0 else None
            down_idx = (i + 1) % len(nodes) if len(nodes) > 0 else None
            
            # Find left/right neighbors based on position
            # This is simplified - in a real implementation, we'd use actual coordinates
            node['keyboard_nav'] = {
                'up': nodes[up_idx]['id'] if up_idx is not None else None,
                'down': nodes[down_idx]['id'] if down_idx is not None else None,
                'tab_index': i + 1  # Start at 1 for tab index
            }
        
        # Add keyboard navigation instructions
        viz_data['keyboard_nav_instructions'] = (
            "Use Tab key to navigate between nodes. "
            "Use arrow keys to move between connected nodes. "
            "Press Enter to select a node. "
            "Press Escape to exit the current mode."
        )
        
        return viz_data