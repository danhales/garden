"""
Meta-Pattern Discovery Engine (M-PDE)

A semantic intelligence middleware for graph data exploration and interpretation.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Callable

# Core graph analysis libraries
import networkx as nx
import numpy as np

class MetaPatternDiscoveryEngine:
    """
    A comprehensive graph analysis middleware designed for flexible 
    semantic pattern discovery and network interpretation.
    """

    def __init__(self, graph_module=None, logger=None):
        """
        Initialize the Meta-Pattern Discovery Engine.

        Parameters
        ----------
        graph_module : module, optional
            Generated graph module from the Module Generator
        logger : logging.Logger, optional
            Custom logger instance
        """
        self.graph_module = graph_module
        self.logger = logger or logging.getLogger('M-PDE')
        self.logger.setLevel(logging.INFO)

        # Configurable analysis strategies
        self.pattern_strategies = {
            'hub_and_spoke': self._detect_hub_and_spoke,
            'core_periphery': self._detect_core_periphery,
            'community_structure': self._detect_communities
        }

    def extract_graph_network(self) -> nx.MultiDiGraph:
        """
        Convert the graph module's data into a NetworkX multi-digraph.
        
        Returns
        -------
        nx.MultiDiGraph
            A NetworkX graph representation of the database
        """
        if not self.graph_module:
            raise ValueError("No graph module provided for network extraction")

        G = nx.MultiDiGraph()
        
        # Dynamically extract all node types
        for label in self.graph_module.METADATA['node_labels']:
            # Get all nodes of this label
            nodes = getattr(self.graph_module.nodes, label.lower().replace(':', '_'))()
            
            for node in nodes:
                # Add node with all its properties
                G.add_node(
                    node['uuid'], 
                    labels=node['labels'], 
                    **node['props']
                )
        
        # Extract relationships
        for rel_type in self.graph_module.METADATA['edge_types']:
            # Get all relationships of this type
            edges = getattr(self.graph_module.edges, rel_type.lower().replace(':', '_'))()
            
            for source, relationship, target in edges:
                G.add_edge(
                    source['uuid'], 
                    target['uuid'], 
                    type=relationship['relType'],
                    **relationship['props']
                )
        
        return G

    def analyze_network_topology(self, G: nx.MultiDiGraph) -> Dict[str, Any]:
        """
        Perform comprehensive network topology analysis.
        
        Parameters
        ----------
        G : nx.MultiDiGraph
            Input graph network
        
        Returns
        -------
        Dict[str, Any]
            Comprehensive topology analysis results
        """
        try:
            topology_analysis = {
                'basic_metrics': {
                    'total_nodes': G.number_of_nodes(),
                    'total_edges': G.number_of_edges(),
                    'node_labels': list(set(label for node, data in G.nodes(data=True) for label in data.get('labels', []))),
                    'edge_types': list(set(data.get('type', '') for _, _, data in G.edges(data=True)))
                },
                'centrality_measures': {
                    'degree_centrality': dict(nx.degree_centrality(G)),
                    'betweenness_centrality': dict(nx.betweenness_centrality(G)),
                    'closeness_centrality': dict(nx.closeness_centrality(G))
                },
                'structural_characteristics': {
                    'diameter': nx.diameter(G.to_undirected()) if nx.is_connected(G.to_undirected()) else None,
                    'average_clustering_coefficient': nx.average_clustering(G),
                    'connected_components': nx.number_connected_components(G.to_undirected())
                }
            }
            
            return topology_analysis
        except Exception as e:
            self.logger.error(f"Topology analysis failed: {e}")
            return {}

    def identify_semantic_patterns(self, G: nx.MultiDiGraph) -> Dict[str, Any]:
        """
        Identify and classify semantic patterns in the graph.
        
        Parameters
        ----------
        G : nx.MultiDiGraph
            Input graph network
        
        Returns
        -------
        Dict[str, Any]
            Semantic pattern classification results
        """
        semantic_patterns = {}
        for name, strategy in self.pattern_strategies.items():
            try:
                semantic_patterns[name] = strategy(G)
            except Exception as e:
                self.logger.warning(f"Pattern detection failed for {name}: {e}")
        
        return semantic_patterns

    def _detect_hub_and_spoke(self, G: nx.MultiDiGraph) -> Dict[str, Any]:
        """
        Detect hub and spoke network structures.
        """
        degree_centrality = nx.degree_centrality(G)
        sorted_centrality = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)
        
        # Identify potential hubs (top 5% by degree centrality)
        hub_threshold = np.percentile(list(degree_centrality.values()), 95)
        hubs = [node for node, centrality in sorted_centrality if centrality >= hub_threshold]
        
        hub_details = {}
        for hub in hubs:
            hub_connections = list(G.neighbors(hub))
            hub_details[hub] = {
                'total_connections': len(hub_connections),
                'connected_nodes': hub_connections
            }
        
        return {
            'hubs': hub_details,
            'hub_threshold': hub_threshold
        }

    def _detect_core_periphery(self, G: nx.MultiDiGraph) -> Dict[str, Any]:
        """
        Identify core and periphery structures in the network.
        """
        # K-core decomposition
        k_cores = {}
        for k in range(1, max(dict(G.degree()).values()) + 1):
            k_core = nx.k_core(G, k)
            if k_core.nodes():
                k_cores[k] = list(k_core.nodes())
        
        return {
            'k_cores': k_cores,
            'max_k_core': max(k_cores.keys()) if k_cores else 0
        }

    def _detect_communities(self, G: nx.MultiDiGraph) -> Dict[str, Any]:
        """
        Detect community structures using Louvain method.
        """
        try:
            import community as community_louvain
            
            # Convert to undirected for community detection
            undirected_G = G.to_undirected()
            partition = community_louvain.best_partition(undirected_G)
            
            # Aggregate community information
            communities = {}
            for node, community_id in partition.items():
                if community_id not in communities:
                    communities[community_id] = []
                communities[community_id].append(node)
            
            return {
                'total_communities': len(communities),
                'community_distribution': {
                    cid: len(nodes) for cid, nodes in communities.items()
                },
                'modularity': community_louvain.modularity(partition, undirected_G)
            }
        except ImportError:
            self.logger.warning("Community detection requires 'python-louvain' package")
            return {}

    def register_pattern_strategy(self, name: str, strategy: Callable[[nx.MultiDiGraph], Dict[str, Any]]):
        """
        Register a custom pattern detection strategy.

        Parameters
        ----------
        name : str
            Unique name for the strategy
        strategy : Callable
            Function to detect a specific pattern in the graph
        """
        if name in self.pattern_strategies:
            self.logger.warning(f"Overwriting existing strategy: {name}")
        
        self.pattern_strategies[name] = strategy

    def generate_comprehensive_analysis(self, G: nx.MultiDiGraph = None) -> Dict[str, Any]:
        """
        Generate a comprehensive analysis of the graph network.

        Parameters
        ----------
        G : nx.MultiDiGraph, optional
            Input graph network. If not provided, extracts from graph module.

        Returns
        -------
        Dict[str, Any]
            Comprehensive graph analysis
        """
        # If no graph provided, extract from module
        if G is None:
            G = self.extract_graph_network()

        return {
            'topology': self.analyze_network_topology(G),
            'semantic_patterns': self.identify_semantic_patterns(G)
        }

def create_mpde_flask_blueprint(graph_module=None):
    """
    Create a Flask blueprint for M-PDE integration.

    Parameters
    ----------
    graph_module : module, optional
        Generated graph module from the Module Generator

    Returns
    -------
    Flask blueprint
        Configured blueprint for graph analysis endpoints
    """
    from flask import Blueprint, jsonify, request

    mpde_blueprint = Blueprint('mpde', __name__)
    mpde = MetaPatternDiscoveryEngine(graph_module)

    @mpde_blueprint.route('/analyze/topology', methods=['GET'])
    def analyze_topology():
        """
        Endpoint for comprehensive network topology analysis.
        """
        try:
            G = mpde.extract_graph_network()
            topology_analysis = mpde.analyze_network_topology(G)
            return jsonify(topology_analysis)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @mpde_blueprint.route('/analyze/semantic-patterns', methods=['GET'])
    def analyze_semantic_patterns():
        """
        Endpoint for semantic pattern discovery.
        """
        try:
            G = mpde.extract_graph_network()
            semantic_patterns = mpde.identify_semantic_patterns(G)
            return jsonify(semantic_patterns)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @mpde_blueprint.route('/analyze/comprehensive', methods=['GET'])
    def comprehensive_analysis():
        """
        Endpoint for generating comprehensive graph analysis.
        """
        try:
            G = mpde.extract_graph_network()
            comprehensive_analysis = mpde.generate_comprehensive_analysis(G)
            return jsonify(comprehensive_analysis)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return mpde_blueprint

# Optional: Provide a command-line interface for direct analysis
def main():
    import sys
    import importlib

    if len(sys.argv) < 2:
        print("Usage: python mpde.py <graph_module_name>")
        sys.exit(1)

    try:
        graph_module = importlib.import_module(sys.argv[1])
        mpde = MetaPatternDiscoveryEngine(graph_module)
        G = mpde.extract_graph_network()
        
        # Print comprehensive analysis
        analysis = mpde.generate_comprehensive_analysis(G)
        print(json.dumps(analysis, indent=2))
    except ImportError:
        print(f"Could not import graph module: {sys.argv[1]}")
        sys.exit(1)

if __name__ == '__main__':
    main()