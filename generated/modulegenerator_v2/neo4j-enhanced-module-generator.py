"""
Enhanced Neo4j Module Generator with Generic Database Operations
"""

import os
import inspect
import datetime
import json
import argparse
import typing
import neo4j
from neo4j import GraphDatabase
from typing import Dict, List, Any, Optional, Union

VERSION = (0, 2, 0)

def generate_module(
    uri='bolt://localhost:7687', 
    username='neo4j', 
    password='neo4j', 
    database='neo4j',
    output_directory=None
):
    """
    Generate a comprehensive Neo4j interface module.
    
    Parameters
    ----------
    uri : str, optional
        Neo4j connection URI
    username : str, optional
        Neo4j username
    password : str, optional
        Neo4j password
    database : str, optional
        Neo4j database name
    output_directory : str, optional
        Directory to write the generated module
    
    Returns
    -------
    str
        Path to the generated module file
    """
    # Module generation
    module_name = f"{database.lower()}graph"
    filename = os.path.join(
        output_directory or os.getcwd(), 
        f"{module_name}.py"
    )
    
    with open(filename, 'w') as f:
        # Module header and core functionality
        f.write(f'''"""
{module_name}.py - Enhanced Neo4j Graph Database Interface

Generated: {datetime.datetime.now().isoformat()}
Neo4j Driver Version: {neo4j.__version__}
"""

import neo4j
from neo4j import GraphDatabase
from typing import Dict, List, Any, Optional, Union

# Connection Configuration
NEO4J_CONFIG = {{
    'uri': '{uri}',
    'username': '{username}',
    'password': '{"*" * len(password)}',
    'database': '{database}'
}}

def get_driver():
    """
    Create a new authenticated Neo4j driver.
    
    Returns
    -------
    neo4j.Driver
        Authenticated Neo4j driver
    """
    return GraphDatabase.driver(**NEO4J_CONFIG)

def execute_query(query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict]:
    """
    Execute a raw Cypher query.
    
    Parameters
    ----------
    query : str
        Cypher query to execute
    params : Dict, optional
        Query parameters
    
    Returns
    -------
    List[Dict]
        Query results
    """
    with get_driver().session() as session:
        result = session.run(query, params or {{}})
        return [dict(record) for record in result]

class DatabaseOperations:
    @staticmethod
    def create_node(label: str, properties: Dict[str, Any]) -> Dict:
        """
        Create a new node with given label and properties.
        
        Parameters
        ----------
        label : str
            Node label
        properties : Dict
            Node properties
        
        Returns
        -------
        Dict
            Created node details
        """
        query = f"""
        CREATE (n:{label})
        SET n = $properties
        RETURN n
        """
        
        with get_driver().session() as session:
            result = session.run(query, {{'properties': properties}})
            return _neo4j_node_to_dict(result.single()[0])
    
    @staticmethod
    def update_node(label: str, match_properties: Dict[str, Any], update_properties: Dict[str, Any]) -> List[Dict]:
        """
        Update nodes matching specific properties.
        
        Parameters
        ----------
        label : str
            Node label
        match_properties : Dict
            Properties to match nodes
        update_properties : Dict
            Properties to update
        
        Returns
        -------
        List[Dict]
            Updated nodes
        """
        query = f"""
        MATCH (n:{label})
        WHERE all(key in keys($match) WHERE n[key] = $match[key])
        SET n += $update
        RETURN n
        """
        
        with get_driver().session() as session:
            result = session.run(query, {{
                'match': match_properties, 
                'update': update_properties
            }})
            return [_neo4j_node_to_dict(record['n']) for record in result]
    
    @staticmethod
    def delete_node(label: str, match_properties: Dict[str, Any], detach: bool = False) -> int:
        """
        Delete nodes matching specific properties.
        
        Parameters
        ----------
        label : str
            Node label
        match_properties : Dict
            Properties to match nodes
        detach : bool, optional
            If True, removes relationships before deleting nodes
        
        Returns
        -------
        int
            Number of nodes deleted
        """
        query = f"""
        MATCH (n:{label})
        WHERE all(key in keys($match) WHERE n[key] = $match[key])
        {'DETACH ' if detach else ''}DELETE n
        RETURN count(n) as deleted_count
        """
        
        with get_driver().session() as session:
            result = session.run(query, {{'match': match_properties}})
            return result.single()['deleted_count']
    
    @staticmethod
    def create_relationship(
        start_label: str, 
        start_match: Dict[str, Any], 
        end_label: str, 
        end_match: Dict[str, Any], 
        rel_type: str, 
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict:
        """
        Create a relationship between two nodes.
        
        Parameters
        ----------
        start_label : str
            Label of the start node
        start_match : Dict
            Properties to match start node
        end_label : str
            Label of the end node
        end_match : Dict
            Properties to match end node
        rel_type : str
            Relationship type
        properties : Dict, optional
            Relationship properties
        
        Returns
        -------
        Dict
            Created relationship details
        """
        query = f"""
        MATCH (start:{start_label}), (end:{end_label})
        WHERE all(key in keys($start_match) WHERE start[key] = $start_match[key])
        AND all(key in keys($end_match) WHERE end[key] = $end_match[key])
        CREATE (start)-[r:{rel_type} $rel_props]->(end)
        RETURN start, r, end
        """
        
        with get_driver().session() as session:
            result = session.run(query, {{
                'start_match': start_match,
                'end_match': end_match,
                'rel_props': properties or {{}}
            }})
            record = result.single()
            return {{
                'source': _neo4j_node_to_dict(record['start']),
                'relationship': _neo4j_relationship_to_dict(record['r']),
                'target': _neo4j_node_to_dict(record['end'])
            }}
    
    @staticmethod
    def delete_relationship(
        start_label: str, 
        start_match: Dict[str, Any], 
        end_label: str, 
        end_match: Dict[str, Any], 
        rel_type: str
    ) -> int:
        """
        Delete relationships between nodes.
        
        Parameters
        ----------
        start_label : str
            Label of the start node
        start_match : Dict
            Properties to match start node
        end_label : str
            Label of the end node
        end_match : Dict
            Properties to match end node
        rel_type : str
            Relationship type to delete
        
        Returns
        -------
        int
            Number of relationships deleted
        """
        query = f"""
        MATCH (start:{start_label})-[r:{rel_type}]->(end:{end_label})
        WHERE all(key in keys($start_match) WHERE start[key] = $start_match[key])
        AND all(key in keys($end_match) WHERE end[key] = $end_match[key])
        DELETE r
        RETURN count(r) as deleted_count
        """
        
        with get_driver().session() as session:
            result = session.run(query, {{
                'start_match': start_match,
                'end_match': end_match
            }})
            return result.single()['deleted_count']
    
    @staticmethod
    def find_nodes(
        label: str, 
        match_properties: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Find nodes matching specific properties.
        
        Parameters
        ----------
        label : str
            Node label to search
        match_properties : Dict, optional
            Properties to match
        limit : int, optional
            Maximum number of nodes to return
        
        Returns
        -------
        List[Dict]
            Matching nodes
        """
        match_properties = match_properties or {{}}
        
        query = f"""
        MATCH (n:{label})
        WHERE all(key in keys($match) WHERE n[key] = $match[key])
        {'LIMIT $limit' if limit is not None else ''}
        RETURN n
        """
        
        with get_driver().session() as session:
            result = session.run(query, {{
                'match': match_properties,
                'limit': limit
            }})
            return [_neo4j_node_to_dict(record['n']) for record in result]

def _neo4j_node_to_dict(node):
    """
    Convert a Neo4j Node to a standardized dictionary.
    
    Parameters
    ----------
    node : neo4j.Node
        Neo4j node to convert
    
    Returns
    -------
    Dict
        Standardized node representation
    """
    try:
        props = dict(node.items())
        return {{
            'uuid': props.get('uuid'),
            'labels': list(node.labels),
            'props': props
        }}
    except:
        return {{
            'uuid': None,
            'labels': [],
            'props': {{}}
        }}

def _neo4j_relationship_to_dict(rel):
    """
    Convert a Neo4j Relationship to a standardized dictionary.
    
    Parameters
    ----------
    rel : neo4j.Relationship
        Neo4j relationship to convert
    
    Returns
    -------
    Dict
        Standardized relationship representation
    """
    try:
        props = dict(rel.items())
        return {{
            'uuid': props.get('uuid'),
            'relType': rel.type,
            'props': props
        }}
    except:
        return {{
            'uuid': None,
            'relType': '',
            'props': {{}}
        }}
''')
    
    return filename

def main():
    """
    Command-line interface for module generation
    """
    parser = argparse.ArgumentParser(description='Neo4j Module Generator')
    parser.add_argument('-u', '--uri', default='bolt://localhost:7687', help='Neo4j connection URI')
    parser.add_argument('-U', '--username', default='neo4j', help='Neo4j username')
    parser.add_argument('-p', '--password', default='neo4j', help='Neo4j password')
    parser.add_argument('-d', '--database', default='neo4j', help='Neo4j database name')
    parser.add_argument('-o', '--output', help='Output directory')
    
    args = parser.parse_args()
    
    output_file = generate_module(
        uri=args.uri,
        username=args.username,
        password=args.password,
        database=args.database,
        output_directory=args.output
    )
    
    print(f"Generated module: {output_file}")

if __name__ == '__main__':
    main()
""")
