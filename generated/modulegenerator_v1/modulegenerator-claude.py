"""
This program is intended to be run as a script, or through the
generate_module function. Functions prefixed with a _ are for
internal processing and are not intended to be used outside of
this module (but feel free to give it a shot).

This program creates a Python module that provides a developer-friendly
API for working with Neo4j graphs, abstracting away the complexity of
Cypher queries and the Neo4j driver.

This program assumes the following dependencies have been installed
in this environment:
    - neo4j

This program accepts the following command-line inputs:
    --uri: a connection string to a neo4j instance
    --name: a name for the generated module
    --username: a username for the account that will access neo4j
    --password: a password for the account that will access neo4j
    --database: the neo4j database to query
    --output: directory to write the generated module
"""

# Python standard libraries
import os
import logging
import sys
import argparse
import datetime
import inspect
import json
from typing import Dict, List, Any, Tuple, Optional, Union

# Pip installs
# https://neo4j.com/docs/api/python-driver/current/
import neo4j
from neo4j import GraphDatabase

VERSION = (0, 1, 0)

profile = {
    'uri': 'bolt://localhost:7687',
    'database': 'neo4j',
    'username': 'neo4j',
    'password': 'neo4j-dev'
}

class Queries:
    def server_timestamp():
        text = 'RETURN datetime() AS timestamp;'
        params = None
        return text, params
    
    def node(label, **props):
        """
        Node interface cypher -- given a neo4j label (can be a multi-
        label separated by colons, e.g., Label1:Label2) and a dictionary
        of propNames and propValues, construct a parameterized Cypher query 
        to return a list of nodes with that label matching those properties.
        """        
        text = f"""MATCH 
            (n:{label} 
            {'{' if props else ''} 
            {', '.join(f"{prop}: ${prop}" for prop in props)}
            {'}' if props else ''}) 
            RETURN n;"""

        return text, props
    
    def node_labels():
        text = 'CALL db.labels() YIELD label RETURN collect(label) AS labels;'
        params = None
        return text, params
    
    def node_type_properties():
        text = """
        CALL db.schema.nodeTypeProperties() YIELD nodeLabels, propertyName, propertyTypes
        UNWIND nodeLabels AS nodeLabel
        UNWIND propertyTypes AS propertyType
        RETURN
            DISTINCT nodeLabel,
            propertyName,
            collect(propertyType) AS propertyTypes;
        """
        params = None 
        return text, params
    
    def rel_type_properties():
        text = """
        CALL db.schema.relTypeProperties() YIELD relType, propertyName, propertyTypes
        UNWIND propertyTypes AS propertyType
        RETURN
            DISTINCT relType,
            propertyName,
            collect(propertyType) AS propertyTypes;"""
        params = None
        return text, params
    
    def node_properties(label, limit=None):
        text = f"""
            MATCH 
                (n:{label}) 
            WITH n 
            {f"LIMIT {limit}" if limit is not None else ""}
            UNWIND keys(n) AS key
            RETURN DISTINCT key, apoc.meta.type(n[key]) AS type;
        """
        params = None
        return text, params
    
    def edge_types():
        text = 'CALL db.relationshipTypes() YIELD relationshipType RETURN collect(relationshipType) AS relationshipTypes;'
        params = None
        return text, params
    
    def edge_properties(type, limit=1000):
        text = f"""
            MATCH ()-[e:{type}]->()
            WITH e
            {f"LIMIT {limit}" if limit is not None else ""}
            UNWIND keys(e) AS key
            RETURN DISTINCT key, apoc.meta.type(e[key]) AS type;
        """
        params = None 
        return text, params
    
    def edge_endpoints(type, limit=1000):
        text = f"""
            MATCH (a)-[e:{type}]->(b)
            WITH a, e, b
            {f"LIMIT {limit}" if limit is not None else ""}
            RETURN DISTINCT labels(a) AS startLabels, labels(b) AS endLabels;
        """
        params = None 
        return text, params
    
    def edge(type, **props):
        """
        Edge interface cypher -- given a neo4j relationship type and a dictionary
        of propNames and propValues, construct a parameterized Cypher query 
        to return a list of relationships with that type matching those properties.
        """
        text = f"""MATCH 
            (source)-[r:{type} 
            {'{' if props else ''} 
            {', '.join(f"{prop}: ${prop}" for prop in props)}
            {'}' if props else ''}]->(target) 
            RETURN source, r, target;"""

        return text, props

###############################################################################
# _internal functions
# These make the public functions work. While they can be called directly,
# they are not designed for that use and may not be as easy to work with as
# the public functions.
###############################################################################

def _append(filename, text):
    """
    Appends text to the end of the specified file with a newline.

    Parameters
    ----------
    filename: str
        The path to the file to append to

    text: str, list(str)
        Text to write to the module.
        Can be a single string to append or a list of strings.

    Returns
    -------
    None
    """
    with open(filename, 'a+') as outfile:
        outfile.write(f'{text}\n')
        
def _append_imports(filename, imports):
    """
    Appends imports to the beginning of the file.

    Parameters
    ----------
    filename: str
        The path to the file to append to
        
    imports: list(str)
        A list of imports to be written to the top of the file.

    Returns
    -------
    None
    """
    for module in imports:
        _append(filename, f'import {module}')

def _authenticated_driver(uri=profile['uri'], username=profile['username'], password=profile['password']):
    """
    Internal method to set up an authenticated driver.

    Parameters
    ----------
    uri: str
        neo4j connection string
    username: str
        username for the neo4j account
    password: str
        password for the neo4j account
    
    Returns
    -------
    neo4j.GraphDatabase.Driver instance to connect to the database.
    """
    return GraphDatabase.driver(uri, auth=(username, password))

###############################################################################
# _schema calls
# These make the public functions work. While they can be called directly,
# they are not designed for that use and may not be as easy to work with as
# the public functions.
###############################################################################

def _get_edge_endpoints(type):
    """
    Returns a list of endpoint labels for the given type.
    
    Parameters
    ----------
    type: str
        The relationship type to get endpoints for
        
    Returns
    -------
    Tuple[List[str], List[str]]:
        A tuple containing (startLabels, endLabels)
    """
    text, params = Queries.edge_endpoints(type)
    results = _query(text, params)
    # Collect all possible combinations of start and end labels
    startLabels = set()
    endLabels = set()
    
    for result in results:
        for start in result['startLabels']:
            startLabels.add(start)
        for end in result['endLabels']:
            endLabels.add(end)
            
    return list(startLabels), list(endLabels)

def _get_edge_types():
    """
    Returns a list of relationship types in use by the database.

    Parameters
    ----------
    None

    Returns
    -------
    list(str):
        A list of Neo4j edge types in use by the database.
    """
    text, params = Queries.edge_types()
    results = _query(text, params)
    return results[0]['relationshipTypes']

def _get_edge_properties(type):
    """
    Returns the properties and their types for a given edge type.
    
    Parameters
    ----------
    type: str
        The relationship type to get properties for
        
    Returns
    -------
    Dict[str, str]:
        A dictionary mapping property names to their types
    """
    text, params = Queries.edge_properties(type)
    results = _query(text, params)
    properties = {}
    
    for result in results:
        properties[result['key']] = result['type']
        
    return properties

def _get_edge_type_properties():
    """
    Uses db.schema.relTypeProperties() to compile metadata.

    Parameters
    ----------
    None

    Returns
    -------
    dict()
        Keys are edge types, values are lists of dictionaries:
        propertyName: the name of the property on the edge
        propertyTypes: any neo4j types associated with this property
    """
    text, params = Queries.rel_type_properties()
    results = _query(text, params)
    props = dict()
    for result in results:
        relType = result['relType'].strip(':').strip('`')
        if relType not in props:
            props[relType] = []
        props[relType].append({
            'propertyName': result['propertyName'], 
            'propertyTypes': result['propertyTypes']
        })
    return props

def _get_node(label, **props):
    """
    Searches for specific nodes in the database by label and property value.

    Parameters
    ----------
    label: str
        A neo4j label (may be a multilabel, separated by colons)
    props: dict
        Optional key-value pairs for property searches. If none are
        provided, all nodes with the given label are returned.
    """
    text, params = Queries.node(label=label, **props)
    results = _query(text, params)
    return list(map(lambda result: _neo4j_node_to_dict(result['n']), results))

def _get_edge(type, **props):
    """
    Searches for specific edges in the database by type and property value.
    
    Parameters
    ----------
    type: str
        A neo4j relationship type
    props: dict
        Optional key-value pairs for property searches
        
    Returns
    -------
    List[Tuple[Dict, Dict, Dict]]:
        A list of (source_node, edge, target_node) tuples
    """
    text, params = Queries.edge(type=type, **props)
    results = _query(text, params)
    return [(_neo4j_node_to_dict(r['source']), 
             _neo4j_relationship_to_dict(r['r']), 
             _neo4j_node_to_dict(r['target'])) for r in results]

def _neo4j_node_to_dict(node):
    """
    Convert a neo4j Node or dictionary to a standardized Python dictionary.
    
    Parameters
    ----------
    node: neo4j.Node or dict
        The Neo4j node or dictionary to convert
        
    Returns
    -------
    Dict:
        A dictionary with keys 'uuid', 'labels', and 'props'
    """
    # Handle case where node is already a dictionary
    if isinstance(node, dict):
        # If it has the expected structure, just return it
        if 'uuid' in node and 'labels' in node and 'props' in node:
            return node
            
        # Otherwise, attempt to extract the necessary information
        props = node
        uuid = props.get('uuid', None)
        labels = props.get('labels', [])
        
        # If there's a special 'elementId' field, it's a Neo4j result dictionary
        # which might have labels under a different form
        if '_labels' in props:
            labels = props['_labels']
        elif 'labels' in props and isinstance(props['labels'], list):
            labels = props['labels']
            
        return {
            'uuid': uuid,
            'labels': labels,
            'props': props
        }
    
    # Handle Neo4j Node objects
    try:
        # Create a dictionary from the node
        props = dict(node.items())
        # Get the uuid (if it exists)
        uuid = props.get('uuid', None)
        # Get the labels
        labels = list(node.labels)
        
        return {
            'uuid': uuid,
            'labels': labels,
            'props': props
        }
    except (AttributeError, TypeError):
        # As a last resort, if neither approach works
        return {
            'uuid': None,
            'labels': [],
            'props': {} if not isinstance(node, dict) else node
        }

def _neo4j_relationship_to_dict(rel):
    """
    Convert a neo4j Relationship to a standardized Python dictionary.

    Unlike nodes, relationships in neo4j can only have a single type.
    
    Parameters
    ----------
    rel: neo4j.Relationship
        The Neo4j relationship to convert
        
    Returns
    -------
    Dict:
        A dictionary with keys 'uuid', 'type', and 'props'
    """

    # Handle case where rel is already a dictionary
    if isinstance(rel, dict):
        # If it has the expected structure, just return it
        if 'uuid' in rel and 'type' in rel and 'props' in rel:
            return rel
        
        # Otherwise, attempt to extract the necessary information
        props = rel 
        uuid = props.get('uuid', None)
        reltype = props.get('relationshipType', '')

        # If there's a special elementId field, it's a Neo4j result dictionary
        # which might have labels under a different form
        if '_type' in props:
            rel_type = props['_type']

        return {
            'uuid': uuid,
            'relType': rel_type,
            'props': props
        }
    
    try:
        # Create a dictionary from the relationship
        props = dict(rel.items())
        # Get the uuid (if it exists)
        uuid = props.get('uuid', None)
        # Get the type
        type = rel.type
        
        return {
            'uuid': uuid,
            'relType': type,
            'props': props
        }
    except (AttributeError, TypeError):
        # As a last resort, if neither approach works
        return {
            'uuid': None,
            'relType': '',
            'props': {} if not isinstance(rel, dict) else rel
        }

def _get_node_labels():
    """
    Returns a list of labels in use by the database.

    Parameters
    ----------
    None

    Returns
    -------
    list(str):
        A list of Neo4j labels in use by the database.
    """
    text, params = Queries.node_labels()
    results = _query(text, params)
    return results[0]['labels']

def _get_node_properties(label):
    """
    Returns the properties and their types for a given node label.
    
    Parameters
    ----------
    label: str
        The node label to get properties for
        
    Returns
    -------
    Dict[str, str]:
        A dictionary mapping property names to their types
    """
    text, params = Queries.node_properties(label)
    results = _query(text, params)
    properties = {}
    
    for result in results:
        properties[result['key']] = result['type']
        
    return properties

def _get_node_type_properties():
    """
    Uses db.schema.nodeTypeProperties() to compile metadata.

    Parameters
    ----------
    None

    Returns
    -------
    A dictionary containing metadata about nodes.
    """
    text, params = Queries.node_type_properties()
    results = _query(text, params)
    props = dict()
    for result in results:
        nodeLabel = result['nodeLabel'] 
        if nodeLabel not in props:
            props[nodeLabel] = []
        props[nodeLabel].append({
            'propertyName': result['propertyName'],
            'propertyTypes': result['propertyTypes']
        })
    return props

def _query(query_text=None, query_params=None):
    """
    Submits a parameterized Cypher query to Neo4j.

    Parameters
    ----------
    query_text: str
        A valid Cypher query string.
    query_params: list(str)
        A list of parameters to be passed along with the query_text.

    Returns
    -------
    A tuple of dictionaries, representing entities returned by the query.
    """
    with _authenticated_driver().session() as session:
        return session.run(query_text, query_params).data()

def _server_timestamp():
    """
    Retrieves a timestamp from the neo4j instance and prints a message 
    to the screen. 

    Parameters
    ----------
    None

    Returns
    -------
    str:
        Timestamp from server.
    """
    text, params = Queries.server_timestamp()
    return _query(query_text=text, query_params=params)[0]['timestamp'].iso_format()

def _collect_metadata(driver):
    """
    Collects comprehensive metadata about the Neo4j graph database.
    
    Parameters
    ----------
    driver: neo4j.GraphDatabase.Driver
        An authenticated driver instance
        
    Returns
    -------
    Dict:
        A dictionary containing metadata about nodes, edges, and their properties
    """
    metadata = {
        'node_labels': [],
        'node_properties': {},
        'edge_types': [],
        'edge_properties': {},
        'edge_endpoints': {}
    }
    
    # Get all node labels
    metadata['node_labels'] = _get_node_labels()
    
    # Get properties for each node label
    for label in metadata['node_labels']:
        metadata['node_properties'][label] = _get_node_properties(label)
    
    # Get all edge types
    metadata['edge_types'] = _get_edge_types()
    
    # Get properties and endpoints for each edge type
    for edge_type in metadata['edge_types']:
        metadata['edge_properties'][edge_type] = _get_edge_properties(edge_type)
        metadata['edge_endpoints'][edge_type] = _get_edge_endpoints(edge_type)
    
    return metadata

def _generate_type_checking_code(property_name, property_type):
    """
    Generates code for type checking a property value.
    
    Parameters
    ----------
    property_name: str
        The name of the property
    property_type: str
        The Neo4j type of the property
        
    Returns
    -------
    str:
        Python code to validate the property value
    """
    # Map Neo4j types to Python types
    type_mapping = {
        'STRING': 'str',
        'INTEGER': 'int',
        'FLOAT': 'float',
        'BOOLEAN': 'bool',
        'DATE': 'datetime.date',
        'DATETIME': 'datetime.datetime',
        'LIST': 'list',
        'MAP': 'dict'
    }
    
    # Get the Python type
    python_type = type_mapping.get(property_type, 'object')
    
    # Generate the type checking code
    return f"""
        # Type check {property_name} (expected {python_type})
        if "{property_name}" in props and props["{property_name}"] is not None:
            if not isinstance(props["{property_name}"], {python_type}):
                try:
                    # Attempt to convert
                    props["{property_name}"] = {python_type}(props["{property_name}"])
                except:
                    raise TypeError(f"Property {property_name} must be of type {python_type}, got {{type(props['{property_name}']).__name__}}")
    """

def _generate_node_interface_functions(metadata):
    """
    Generates interface functions for each node label.
    
    Parameters
    ----------
    metadata: Dict
        The metadata dictionary
        
    Returns
    -------
    str:
        Python code defining the node interface functions
    """
    functions = []
    
    for label in metadata['node_labels']:
        properties = metadata['node_properties'].get(label, {})
        function_name = label.lower().replace(':', '_').replace('-', '_')
        
        function_code = f"""
    def {function_name}(uuid=None, **props):
        \"\"\"
        Find nodes with label {label} matching the given properties.
        
        Parameters
        ----------
        uuid: str, optional
            The UUID of the node to find
        **props: Dict
            Additional properties to search for
            
        Returns
        -------
        List[Dict]:
            A list of matching nodes as dictionaries with keys 'uuid', 'labels', and 'props'
        \"\"\"
        search_props = props.copy()
        if uuid is not None:
            search_props['uuid'] = uuid
            
        # Type checking for known properties
"""
        
        # Add type checking for each property
        for prop_name, prop_type in properties.items():
            function_code += _generate_type_checking_code(prop_name, prop_type)
        
        function_code += f"""
        # Construct and execute the query
        query, params = Queries.node(label="{label}", **search_props)
        results = _query(query, params)
        return [_neo4j_node_to_dict(result['n']) for result in results]
"""
        
        functions.append(function_code)
    
    return "\n".join(functions)

def _generate_edge_interface_functions(metadata):
    """
    Generates interface functions for each edge type.
    
    Parameters
    ----------
    metadata: Dict
        The metadata dictionary
        
    Returns
    -------
    str:
        Python code defining the edge interface functions
    """
    functions = []
    
    for edge_type in metadata['edge_types']:
        properties = metadata['edge_properties'].get(edge_type, {})
        function_name = edge_type.lower().replace(':', '_').replace('-', '_')
        
        function_code = f"""
    def {function_name}(uuid=None, **props):
        \"\"\"
        Find relationships of type {edge_type} matching the given properties.
        
        Parameters
        ----------
        uuid: str, optional
            The UUID of the relationship to find
        **props: Dict
            Additional properties to search for
            
        Returns
        -------
        List[Tuple[Dict, Dict, Dict]]:
            A list of tuples containing (source_node, relationship, target_node)
        \"\"\"
        search_props = props.copy()
        if uuid is not None:
            search_props['uuid'] = uuid
            
        # Type checking for known properties
"""
        
        # Add type checking for each property
        for prop_name, prop_type in properties.items():
            function_code += _generate_type_checking_code(prop_name, prop_type)
        
        function_code += f"""
        # Construct and execute the query
        query, params = Queries.edge(type="{edge_type}", **search_props)
        results = _query(query, params)
        return [(_neo4j_node_to_dict(r['source']), 
                 _neo4j_relationship_to_dict(r['r']), 
                 _neo4j_node_to_dict(r['target'])) for r in results]
"""
        
        functions.append(function_code)
    
    return "\n".join(functions)

###############################################################################
# Public functions
# The purpose of this module is to expose the generate_module function.
###############################################################################

def generate_module(uri=None, username=None, password=None, graph=None, output_directory=os.environ['PWD']):
    """
    Assembler function collects strings containing valid Python code
    into a list, then writes the list to a new python module (a file
    ending in .py) in a single write operation.

    Parameters
    ----------
    uri: str
        A connection string for the neo4j instance.
    username: str
        The user name for the neo4j account. This account needs read access.
    password: str
        The password for the neo4j account.
    graph: str
        The name of the graph for the generated module, e.g. name="demo" 
        results in demograph.py.
    output_directory: str
        The directory to write the generated module to.

    Returns
    -------
    str:
        The filepath to the generated module.
    """

    def _log(msg):
        with open('modulegenerator.out', '+a') as log:
            log.write(f'{datetime.datetime.now()}: {msg}\n')

    # Set up the authentication parameters
    if uri is not None:
        profile['uri'] = uri
    if username is not None:
        profile['username'] = username
    if password is not None:
        profile['password'] = password

    # Get an authenticated driver
    driver = _authenticated_driver(
        uri=profile['uri'], 
        username=profile['username'], 
        password=profile['password']
    )

    # Collect metadata about the graph
    _log('Collecting metadata from Neo4j database')
    metadata = _collect_metadata(driver)

    module_name = f"{graph if graph is not None else 'new'}graph"
    if output_directory:
        os.makedirs(output_directory, exist_ok=True)
        filename = os.path.join(output_directory, f"{module_name}.py")
    else:
        filename = f"{module_name}.py"
    
    _log(f'Generating module: {filename}')

    if os.path.exists(filename):
        _log(f'Old module found; deleting.')
        os.remove(filename)

    # Boilerplate
    _log('Writing boilerplate to top of file.')
    _append(filename, f'''"""
{module_name}.py - Auto-generated Neo4j interface module

This module provides a Python interface to a Neo4j graph database,
abstracting the Cypher query language and Neo4j driver details.

Generated on: {_server_timestamp()}
Generated with: modulegenerator version {".".join(map(str, VERSION))}
Neo4j driver version: {neo4j.__version__}
"""''')

    # Imports
    _log('Adding imports')
    _append(filename, f'''
import datetime
import neo4j
from neo4j import GraphDatabase
''')

    # Connection details
    _log('Adding connection details')
    _append(filename, f'''
# Neo4j connection details
NEO4J_URI = "{profile['uri']}"
NEO4J_USERNAME = "{profile['username']}"
NEO4J_PASSWORD = "{profile['password']}"
NEO4J_DATABASE = "{profile['database']}"
''')

    # Copy the utility functions
    _log('Copying utility functions')
    utility_functions = {
        '_authenticated_driver': _authenticated_driver,
        '_query': _query,
        '_server_timestamp': _server_timestamp,
        '_neo4j_node_to_dict': _neo4j_node_to_dict,
        '_neo4j_relationship_to_dict': _neo4j_relationship_to_dict
    }
    
    for func_name, func in utility_functions.items():
        _append(filename, inspect.getsource(func))

    # Add the Queries class
    _log('Adding Queries class')
    _append(filename, inspect.getsource(Queries))

    # Add metadata as a JSON string
    _log('Adding metadata')
    _append(filename, f'''
# Metadata about the Neo4j graph
METADATA = {json.dumps(metadata, indent=4)}
''')

    # Create the node and edge interface classes
    _log('Generating node interface class')
    _append(filename, f'''
class Nodes:
    """
    Interface for working with nodes in the Neo4j graph.
    Each method corresponds to a node label in the graph.
    """
{_generate_node_interface_functions(metadata)}
''')

    _log('Generating edge interface class')
    _append(filename, f'''
class Edges:
    """
    Interface for working with relationships in the Neo4j graph.
    Each method corresponds to a relationship type in the graph.
    """
{_generate_edge_interface_functions(metadata)}
''')

    # Create the main interface
    _log('Creating main interface')
    _append(filename, f'''
# Create the interface instances
nodes = Nodes()
edges = Edges()

def connect():
    """
    Create a new authenticated driver connection to the Neo4j database.
    
    Returns
    -------
    neo4j.Driver:
        A connected Neo4j driver instance
    """
    return _authenticated_driver(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)

def execute_query(query, params=None):
    """
    Execute a raw Cypher query against the Neo4j database.
    
    Parameters
    ----------
    query: str
        The Cypher query to execute
    params: Dict, optional
        Parameters for the query
        
    Returns
    -------
    List[Dict]:
        Results from the query
    """
    return _query(query, params)

def server_timestamp():
    """
    Get the current timestamp from the Neo4j server.
    
    Returns
    -------
    str:
        ISO-formatted timestamp
    """
    return _server_timestamp()
''')

    _log(f"{filename} successfully generated.")
    return filename

if __name__ == '__main__':
    print('modulegenerator-claude.py is being run as a script.')
    
    # Configure command-line arguments
    parser = argparse.ArgumentParser(description='Utility script for generating neo4j backend code.')
    parser.add_argument('-d', '--database', help='the neo4j database to query')
    parser.add_argument('-g', '--graph', help='the <name> in <name>graph.py', action='store')
    parser.add_argument('-n', '--name', help='username for neo4j account',action='store')
    parser.add_argument('-o', '--output', help='directory to write the generated module to', action='store')
    parser.add_argument('-p', '--password', help='password for neo4j account', action='store')
    parser.add_argument('-u', '--uri', help='neo4j connection string', action='store')
    
    args = parser.parse_args()

    # Update the graph object if command-line arguments were passed
    if args.uri is not None:
        profile['uri'] = args.uri
    if args.name is not None:
        profile['username'] = args.name
    if args.password is not None:
        profile['password'] = args.password
    if args.database is not None:
        profile['database'] = args.database

    # Default output is newgraph.py
    graph = args.graph if args.graph is not None else "new"

    # If no output argument is passed, use current directory
    output_directory = args.output if args.output is not None else None
                      
    print(f'Generating: {graph}graph.py',
          f'At: {profile["uri"]}',
          f'For database: {profile["database"]}',
          f'Username: {profile["username"]}',
          f'Password: {"*" * len(profile["password"])}',
          f'Generated module will be written to: {output_directory or "current directory"}',
          sep='\n')

    # Generate the module
    generate_module(
        uri=profile['uri'],
        username=profile['username'],
        password=profile['password'],
        graph=graph,
        output_directory=output_directory
    )