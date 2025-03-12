"""
Middleware Adapter for G.A.R.D.E.N. Explorer

This module provides a consistent interface to Neo4j middleware generated by different
versions of the Module Generator. It adapts various middleware structures to a standard
interface that Garden Explorer can use consistently.

Note from Dan:  This should make things future-proof, allowing my continue work on the
                module generator to not break your application.

Version:        2025_03_12_0431
Version Note:   Due to rapid development of features, I am now timestamping all versions.
                I am manually entering this after reviewing the code.
"""

class MiddlewareAdapter:
    """
    Adapter for Neo4j middleware that provides a consistent interface
    regardless of the specific middleware implementation.
    """
    
    def __init__(self, middleware):
        """
        Initialize the adapter with the middleware module.
        
        Parameters
        ----------
        middleware:
            The imported middleware module
        """
        self.middleware = middleware
    
    def get_node_labels(self):
        """
        Get all node labels from the database.
        
        Returns
        -------
        List[str]:
            List of node labels
        """
        if hasattr(self.middleware, 'METADATA'):
            return self.middleware.METADATA.get('node_labels', [])
        return []
    
    def get_relationship_types(self):
        """
        Get all relationship types from the database.
        
        Returns
        -------
        List[str]:
            List of relationship types
        """
        if hasattr(self.middleware, 'METADATA'):
            return self.middleware.METADATA.get('edge_types', [])
        return []
    
    def get_nodes_by_label(self, label):
        """
        Get all nodes with a specific label.
        
        Parameters
        ----------
        label: str
            The node label to query
            
        Returns
        -------
        List[Dict]:
            List of nodes with the specified label
        """
        # Try to get the nodes using different approaches
        try:
            # Approach 1: Using nodes.label_name() method
            if hasattr(self.middleware, 'nodes'):
                func_name = label.lower().replace(':', '_').replace('-', '_')
                node_func = getattr(self.middleware.nodes, func_name, None)
                if node_func and callable(node_func):
                    return node_func()
            
            # Approach 2: Direct query using execute_query
            if hasattr(self.middleware, 'execute_query'):
                results = self.middleware.execute_query(f"MATCH (n:{label}) RETURN n")
                return [self._process_node_result(result['n']) for result in results]
            
            # Approach 3: Try a different direct query format
            query_func = getattr(self.middleware, '_query', None)
            if query_func and callable(query_func):
                query_text = f"MATCH (n:{label}) RETURN n"
                results = query_func(query_text)
                return [self._process_node_result(result['n']) for result in results]
            
            # No approach worked
            return []
        except Exception as e:
            print(f"Error getting nodes by label {label}: {e}")
            return []
    
    def get_node_by_id(self, label, node_id):
        """
        Get a specific node by its ID.
        
        Parameters
        ----------
        label: str
            The node label
        node_id: str
            The node ID
            
        Returns
        -------
        Dict or None:
            The node if found, None otherwise
        """
        try:
            # Approach 1: Using nodes.label_name() method with uuid parameter
            if hasattr(self.middleware, 'nodes'):
                func_name = label.lower().replace(':', '_').replace('-', '_')
                node_func = getattr(self.middleware.nodes, func_name, None)
                if node_func and callable(node_func):
                    nodes = node_func(uuid=node_id)
                    if nodes:
                        return nodes[0]
            
            # Approach 2: Direct query using execute_query
            if hasattr(self.middleware, 'execute_query'):
                results = self.middleware.execute_query(
                    f"MATCH (n:{label}) WHERE n.uuid = $uuid RETURN n", 
                    {"uuid": node_id}
                )
                if results:
                    return self._process_node_result(results[0]['n'])
            
            # No approach worked
            return None
        except Exception as e:
            print(f"Error getting node by ID {node_id}: {e}")
            return None
    
    def get_incoming_relationships(self, node_id):
        """
        Get all relationships where the specified node is the target.
        
        Parameters
        ----------
        node_id: str
            The node ID
            
        Returns
        -------
        List[Dict]:
            List of relationship information
        """
        incoming = []
        
        try:
            # Try all relationship types
            for rel_type in self.get_relationship_types():
                # Approach 1: Using edges.rel_type() method
                if hasattr(self.middleware, 'edges'):
                    func_name = rel_type.lower().replace(':', '_').replace('-', '_')
                    rel_func = getattr(self.middleware.edges, func_name, None)
                    if rel_func and callable(rel_func):
                        rels = rel_func(end_node_uuid=node_id)
                        for source, rel, target in rels:
                            incoming.append({
                                'source': source,
                                'relationship': rel,
                                'target': target,
                                'type': rel_type
                            })
                
                # Approach 2: Direct query
                elif hasattr(self.middleware, 'execute_query'):
                    results = self.middleware.execute_query(
                        f"MATCH (source)-[r:{rel_type}]->(target) WHERE target.uuid = $uuid RETURN source, r, target",
                        {"uuid": node_id}
                    )
                    for result in results:
                        incoming.append({
                            'source': self._process_node_result(result['source']),
                            'relationship': self._process_relationship_result(result['r']),
                            'target': self._process_node_result(result['target']),
                            'type': rel_type
                        })
        except Exception as e:
            print(f"Error getting incoming relationships for node {node_id}: {e}")
        
        return incoming
    
    def get_outgoing_relationships(self, node_id):
        """
        Get all relationships where the specified node is the source.
        
        Parameters
        ----------
        node_id: str
            The node ID
            
        Returns
        -------
        List[Dict]:
            List of relationship information
        """
        outgoing = []
        
        try:
            # Try all relationship types
            for rel_type in self.get_relationship_types():
                # Approach 1: Using edges.rel_type() method
                if hasattr(self.middleware, 'edges'):
                    func_name = rel_type.lower().replace(':', '_').replace('-', '_')
                    rel_func = getattr(self.middleware.edges, func_name, None)
                    if rel_func and callable(rel_func):
                        rels = rel_func(start_node_uuid=node_id)
                        for source, rel, target in rels:
                            outgoing.append({
                                'source': source,
                                'relationship': rel,
                                'target': target,
                                'type': rel_type
                            })
                
                # Approach 2: Direct query
                elif hasattr(self.middleware, 'execute_query'):
                    results = self.middleware.execute_query(
                        f"MATCH (source)-[r:{rel_type}]->(target) WHERE source.uuid = $uuid RETURN source, r, target",
                        {"uuid": node_id}
                    )
                    for result in results:
                        outgoing.append({
                            'source': self._process_node_result(result['source']),
                            'relationship': self._process_relationship_result(result['r']),
                            'target': self._process_node_result(result['target']),
                            'type': rel_type
                        })
        except Exception as e:
            print(f"Error getting outgoing relationships for node {node_id}: {e}")
        
        return outgoing
    
    def _process_node_result(self, node):
        """
        Process a node result from a query to ensure it has the expected structure.
        
        Parameters
        ----------
        node: Any
            The node result from a query
            
        Returns
        -------
        Dict:
            A dictionary with keys 'uuid', 'labels', and 'props'
        """
        # If the middleware has a node conversion function, use it
        if hasattr(self.middleware, '_neo4j_node_to_dict'):
            return self.middleware._neo4j_node_to_dict(node)
        
        # Otherwise, try to create a compatible structure
        if isinstance(node, dict):
            # If it already has the expected structure, return it
            if 'uuid' in node and 'labels' in node and 'props' in node:
                return node
            
            # Otherwise, try to create the structure
            props = node
            uuid = props.get('uuid', '')
            
            # Try to extract labels
            labels = []
            if 'labels' in props and isinstance(props['labels'], list):
                labels = props['labels']
            elif hasattr(node, 'labels'):
                labels = list(node.labels)
            
            return {
                'uuid': uuid,
                'labels': labels,
                'props': props
            }
        
        # Last resort, return an empty structure
        return {
            'uuid': '',
            'labels': [],
            'props': {}
        }
    
    def _process_relationship_result(self, rel):
        """
        Process a relationship result from a query to ensure it has the expected structure.
        
        Parameters
        ----------
        rel: Any
            The relationship result from a query
            
        Returns
        -------
        Dict:
            A dictionary with keys 'uuid', 'relType', and 'props'
        """
        # If the middleware has a relationship conversion function, use it
        if hasattr(self.middleware, '_neo4j_relationship_to_dict'):
            return self.middleware._neo4j_relationship_to_dict(rel)
        
        # Otherwise, try to create a compatible structure
        if isinstance(rel, dict):
            # If it already has the expected structure, return it
            if 'uuid' in rel and 'relType' in rel and 'props' in rel:
                return rel
            
            # Otherwise, try to create the structure
            props = rel
            uuid = props.get('uuid', '')
            rel_type = props.get('type', '')
            
            if not rel_type and hasattr(rel, 'type'):
                rel_type = rel.type
            
            return {
                'uuid': uuid,
                'relType': rel_type,
                'props': props
            }
        
        # Last resort, return an empty structure
        return {
            'uuid': '',
            'relType': '',
            'props': {}
        }

def create_middleware_adapter(middleware):
    """
    Create a middleware adapter for the specified middleware module.
    
    Parameters
    ----------
    middleware:
        The imported middleware module
        
    Returns
    -------
    MiddlewareAdapter:
        An adapter that provides a consistent interface to the middleware
    """
    return MiddlewareAdapter(middleware)