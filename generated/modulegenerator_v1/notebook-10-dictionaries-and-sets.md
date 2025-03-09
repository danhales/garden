# Notebook 10: Dictionaries and Sets

## Learning Objectives

By the end of this notebook, you will be able to:
1. Understand how the Module Generator uses dictionaries to organize metadata
2. Apply dictionary and set operations for efficient data management
3. Implement graph traversal using dictionaries for relationship mapping
4. Design effective data structures for Neo4j schema representation
5. Create your own dictionary-based utilities for graph operations

## 1. Introduction to Dictionaries and Sets in Python

Dictionaries and sets are fundamental data structures in Python that provide efficient ways to organize and access data. In the Module Generator, these structures play crucial roles in managing Neo4j schema information.

### 1.1 Dictionary and Set Overview

Dictionaries and sets offer distinct capabilities:

- **Dictionaries** are key-value collections that provide rapid lookup by key
- **Sets** are unordered collections of unique items with efficient membership testing

Both are implemented using hash tables, which enable O(1) average case performance for common operations.

### 1.2 Dictionaries and Sets in the Module Generator

The Module Generator uses dictionaries and sets for several purposes:

1. **Schema Organization**: Storing structured metadata about the database
2. **Parameter Management**: Handling query parameters securely
3. **Unique Value Collection**: Ensuring uniqueness of labels and properties
4. **Configuration**: Managing connection and generation settings
5. **Type Mapping**: Translating between Neo4j and Python types

Understanding these applications provides insights into effective data structure selection.

## 2. Dictionary Operations in the Module Generator

The Module Generator employs various dictionary operations to manage complex data effectively.

### 2.1 Metadata Organization

The central data structure in the Module Generator is the metadata dictionary:

```python
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
```

This function creates a nested dictionary structure:
1. Top-level keys for different types of metadata
2. Values that are lists (for simple collections) or nested dictionaries (for label-specific data)
3. A hierarchical organization that reflects the database schema

This approach makes it easy to access specific information through key-based lookup.

### 2.2 Property Collection

The Module Generator collects properties for each node label:

```python
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
```

This function:
1. Initializes an empty dictionary
2. Populates it with property names and types from query results
3. Returns a mapping that associates each property with its type

This dictionary makes it efficient to look up type information for a specific property.

### 2.3 Type Mapping

The Module Generator uses dictionaries for type mapping:

```python
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
    
    # ... generate type checking code ...
```

This dictionary:
1. Maps Neo4j type names to Python type names
2. Provides a default value ('object') for unknown types
3. Enables consistent type translation across the module

Using a dictionary for this mapping makes the code more maintainable than a series of if-else statements.

### 2.4 Configuration Management

The Module Generator manages configuration through dictionaries:

```python
profile = {
    'uri': 'bolt://localhost:7687',
    'database': 'neo4j',
    'username': 'neo4j',
    'password': 'neo4j-dev'
}

# ... later in the code ...

# Set up the authentication parameters
if uri is not None:
    profile['uri'] = uri
if username is not None:
    profile['username'] = username
if password is not None:
    profile['password'] = password
```

This approach:
1. Provides default values for configuration parameters
2. Allows selective override of specific parameters
3. Keeps related configuration together in a single structure

Using a dictionary for configuration simplifies parameter management and makes defaults explicit.

## 3. Dictionary Access and Manipulation

The Module Generator employs various techniques for accessing and manipulating dictionaries.

### 3.1 Safe Dictionary Access

The Module Generator uses the `get` method for safe dictionary access:

```python
python_type = type_mapping.get(property_type, 'object')
```

This approach:
1. Retrieves the value for the given key if it exists
2. Returns a default value ('object') if the key is not present
3. Avoids KeyError exceptions for missing keys

Safe access is particularly important when working with data derived from the database, which may contain unexpected values.

### 3.2 Dictionary Construction

The Module Generator constructs dictionaries from Neo4j entities:

```python
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
        # ... error handling ...
```

This function:
1. Converts a Neo4j Node to a dictionary using `dict(node.items())`
2. Extracts specific values from this dictionary
3. Creates a new dictionary with a standardized structure

This approach transforms Neo4j-specific objects into a consistent Python representation.

### 3.3 Dictionary Merging

The Module Generator merges dictionaries for parameter handling:

```python
def person(uuid=None, **props):
    """
    Find nodes with label Person matching the given properties.
    
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
    """
    search_props = props.copy()
    if uuid is not None:
        search_props['uuid'] = uuid
    
    # ... additional processing ...
```

This generated function:
1. Creates a copy of the input properties dictionary
2. Adds the UUID to this dictionary if provided
3. Uses the merged dictionary for query construction

Dictionary merging allows for flexible parameter handling without modifying the original input.

### 3.4 Nested Dictionary Access

The Module Generator navigates nested dictionaries to access specific metadata:

```python
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
        # ... function generation ...
```

This function:
1. Accesses a list of node labels from the metadata dictionary
2. For each label, retrieves the corresponding properties dictionary
3. Uses safe access with a default empty dictionary

Nested dictionary access enables organized data retrieval from complex structures.

## 4. Set Operations in the Module Generator

The Module Generator uses sets for efficient unique value management.

### 4.1 Collecting Unique Labels

When analyzing relationship endpoints, the Module Generator uses sets to collect unique labels:

```python
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
```

This function:
1. Initializes empty sets for start and end labels
2. Adds labels to these sets, automatically eliminating duplicates
3. Converts the sets to lists before returning them

Using sets ensures that each label is included only once, regardless of how many relationships use it.

### 4.2 Eliminating Duplicate Properties

While not explicitly shown in the code, the Module Generator effectively eliminates duplicate properties through dictionary construction:

```python
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
```

Because dictionaries cannot contain duplicate keys, this approach automatically ensures uniqueness of property names.

### 4.3 Set Membership Testing

The Module Generator implicitly uses set membership testing in dictionary operations:

```python
if nodeLabel not in props:
    props[nodeLabel] = []
```

This pattern:
1. Checks if a key exists in the dictionary
2. Creates an empty list for that key if it doesn't exist
3. Leverages the O(1) average case performance of hash-based lookups

Set membership testing (whether explicit with sets or implicit with dictionary keys) provides efficient existence checking.

## 5. Combining Dictionaries and Sets

The Module Generator combines dictionaries and sets to solve complex problems.

### 5.1 Schema Analysis

When analyzing node type properties, the Module Generator combines dictionaries and sets:

```python
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
```

This function:
1. Creates a dictionary mapping node labels to property information
2. For each result, checks if the label exists in the dictionary
3. Appends property details to the list for that label

This combination of dictionary organization and set-like existence checking enables efficient schema analysis.

### 5.2 Type Inference

The Module Generator uses dictionary lookup to infer Python types from Neo4j types:

```python
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
```

This approach:
1. Defines a mapping between Neo4j and Python types
2. Uses dictionary lookup to find the corresponding Python type
3. Provides a default type for unknown Neo4j types

The dictionary structure provides a clean, maintainable way to define the mapping.

## 6. Dictionary-Based Data Structures

The Module Generator uses dictionaries to create custom data structures.

### 6.1 Function Registry

While not explicitly implemented in the Module Generator, it could use a dictionary-based function registry:

```python
# Example of a function registry (not from the actual code)
def _create_function_registry():
    """
    Create a registry of generator functions.
    """
    registry = {}
    
    # Register node interface generator
    registry['node_interface'] = _generate_node_interface_functions
    
    # Register edge interface generator
    registry['edge_interface'] = _generate_edge_interface_functions
    
    # Register utility generator
    registry['utilities'] = _generate_utility_functions
    
    return registry
```

This approach:
1. Creates a mapping between function names and actual functions
2. Enables dynamic function lookup by name
3. Provides a central registry for all generator functions

Dictionary-based registries are a common pattern for organizing related functions.

### 6.2 Named Parameter Handling

The Module Generator uses dictionaries for named parameter handling:

```python
# Generate the module
generate_module(
    uri=profile['uri'],
    username=profile['username'],
    password=profile['password'],
    graph=graph,
    output_directory=output_directory
)
```

Under the hood, Python converts these named parameters to a dictionary, which is then unpacked in the function definition:

```python
def generate_module(uri=None, username=None, password=None, graph=None, output_directory=os.environ['PWD']):
    # ... implementation ...
```

This pattern:
1. Provides clear parameter names at the call site
2. Allows for default values in the function definition
3. Enables flexible parameter ordering

Named parameters are essentially a dictionary-based calling convention.

### 6.3 Query Parameters

The Module Generator uses dictionaries for query parameters:

```python
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

    return text, params
```

The query parameters are passed as a dictionary, where:
1. Keys are parameter names referenced in the query with `$`
2. Values are the actual parameter values
3. The dictionary structure prevents injection attacks

This approach separates query structure from parameter values, enhancing security and performance.

## 7. Implementing Graph Operations with Dictionaries

The Module Generator creates interfaces that use dictionaries to work with graph data.

### 7.1 Node Representation

The generated code represents nodes as dictionaries:

```python
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
    # ... implementation ...
    return {
        'uuid': uuid,
        'labels': labels,
        'props': props
    }
```

This representation:
1. Provides a consistent structure for all nodes
2. Includes a unique identifier, labels, and properties
3. Makes node data accessible through standard dictionary operations

Dictionary-based representation simplifies interaction with Neo4j entities.

### 7.2 Relationship Representation

Similarly, relationships are represented as dictionaries:

```python
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
    # ... implementation ...
    return {
        'uuid': uuid,
        'relType': type,
        'props': props
    }
```

This representation follows the same pattern as nodes, providing a consistent interface.

### 7.3 Relational Data Access

The generated code returns relational data as tuples of dictionaries:

```python
return [(_neo4j_node_to_dict(r['source']), 
         _neo4j_relationship_to_dict(r['r']), 
         _neo4j_node_to_dict(r['target'])) for r in results]
```

This approach:
1. Represents each relationship pattern as a tuple of (source, relationship, target)
2. Uses dictionaries for each element in the tuple
3. Creates a consistent structure for working with graph patterns

Dictionary-based representation makes it easy to access and manipulate graph data.

## 8. Utilities for Dictionary Manipulation

Though not implemented in the Module Generator, several utilities could enhance dictionary manipulation for graph data.

### 8.1 Graph Traversal

A dictionary-based graph traversal function could efficiently navigate relationships:

```python
def traverse_graph(start_node, relationship_type=None, direction='OUTGOING', max_depth=1):
    """
    Traverse the graph starting from a node.
    
    Parameters
    ----------
    start_node: Dict
        The starting node dictionary
    relationship_type: str, optional
        The type of relationship to traverse
    direction: str, optional
        The direction of traversal ('OUTGOING', 'INCOMING', or 'BOTH')
    max_depth: int, optional
        The maximum traversal depth
        
    Returns
    -------
    List[Dict]:
        The nodes reached through traversal
    """
    # Implementation using dictionaries for tracking visited nodes
    visited = {start_node['uuid']: start_node}
    queue = [(start_node, 0)]  # (node, depth)
    
    while queue:
        current, depth = queue.pop(0)
        
        if depth >= max_depth:
            continue
        
        # Get relationships based on direction
        relationships = []
        if direction in ('OUTGOING', 'BOTH'):
            # Get outgoing relationships
            # ... query database ...
            relationships.extend(outgoing)
        
        if direction in ('INCOMING', 'BOTH'):
            # Get incoming relationships
            # ... query database ...
            relationships.extend(incoming)
        
        # Filter by relationship type if specified
        if relationship_type:
            relationships = [r for r in relationships if r[1]['relType'] == relationship_type]
        
        # Process relationships
        for source, rel, target in relationships:
            target_uuid = target['uuid']
            if target_uuid not in visited:
                visited[target_uuid] = target
                queue.append((target, depth + 1))
    
    return list(visited.values())
```

This function:
1. Uses a dictionary to track visited nodes by UUID
2. Implements breadth-first traversal with a queue
3. Filters relationships by type and direction
4. Returns a list of reached nodes

Dictionary-based tracking provides efficient duplicate avoidance during traversal.

### 8.2 Node Indexing

A dictionary-based indexing function could create efficient lookups:

```python
def index_nodes_by_property(nodes, property_name):
    """
    Create an index of nodes by a specific property.
    
    Parameters
    ----------
    nodes: List[Dict]
        List of node dictionaries
    property_name: str
        The property to index by
        
    Returns
    -------
    Dict[Any, List[Dict]]:
        A dictionary mapping property values to nodes
    """
    index = {}
    
    for node in nodes:
        value = node['props'].get(property_name)
        
        if value is not None:
            if value not in index:
                index[value] = []
            index[value].append(node)
    
    return index
```

This function:
1. Creates a dictionary mapping property values to nodes
2. Handles multiple nodes with the same property value
3. Ignores nodes without the specified property

Dictionary-based indexing enables efficient lookup by property value.

### 8.3 Property Aggregation

A dictionary-based aggregation function could summarize property values:

```python
def aggregate_property(nodes, property_name, aggregation='count'):
    """
    Aggregate property values across nodes.
    
    Parameters
    ----------
    nodes: List[Dict]
        List of node dictionaries
    property_name: str
        The property to aggregate
    aggregation: str, optional
        The type of aggregation ('count', 'sum', 'avg', 'min', 'max')
        
    Returns
    -------
    Dict[str, Any]:
        A dictionary with aggregation results
    """
    values = []
    
    for node in nodes:
        value = node['props'].get(property_name)
        if value is not None:
            values.append(value)
    
    result = {
        'property': property_name,
        'count': len(values)
    }
    
    if values:
        if aggregation in ('sum', 'avg') and all(isinstance(v, (int, float)) for v in values):
            result['sum'] = sum(values)
            result['avg'] = result['sum'] / result['count']
        
        if aggregation in ('min', 'max') and values:
            result['min'] = min(values)
            result['max'] = max(values)
    
    return result
```

This function:
1. Collects property values from nodes
2. Performs various aggregations on these values
3. Returns a dictionary with aggregation results

Dictionary-based aggregation provides comprehensive summary statistics.

## 9. Exercises

Now that we've explored dictionaries and sets in the Module Generator, let's apply this knowledge with some exercises.

### Exercise 1: Enhanced Metadata Collection

Extend the Module Generator's metadata collection to include additional information:

```python
def _collect_enhanced_metadata(driver):
    """
    Collect enhanced metadata about the Neo4j graph database.
    
    Parameters
    ----------
    driver: neo4j.GraphDatabase.Driver
        An authenticated driver instance
        
    Returns
    -------
    Dict:
        An enhanced metadata dictionary
    """
    # Start with the basic metadata
    metadata = _collect_metadata(driver)
    
    # Add node counts
    metadata['node_counts'] = {}
    for label in metadata['node_labels']:
        # Query for count
        # Add to metadata
    
    # Add relationship counts
    metadata['edge_counts'] = {}
    for edge_type in metadata['edge_types']:
        # Query for count
        # Add to metadata
    
    # Add property statistics
    metadata['property_stats'] = {}
    # Collect statistics for property values
    
    return metadata
```

### Exercise 2: Graph Path Finder

Create a function that finds paths between nodes using dictionaries for tracking:

```python
def find_paths(start_label, end_label, relationship_types=None, max_length=3):
    """
    Find paths between nodes with the specified labels.
    
    Parameters
    ----------
    start_label: str
        The label of the start nodes
    end_label: str
        The label of the end nodes
    relationship_types: List[str], optional
        Types of relationships to consider
    max_length: int, optional
        Maximum path length
        
    Returns
    -------
    List[List[Dict]]:
        A list of paths, where each path is a list of dictionaries
    """
    # Implementation using dictionaries for path tracking
```

### Exercise 3: Schema Comparison

Develop a function that compares two metadata dictionaries to identify schema changes:

```python
def compare_schemas(old_metadata, new_metadata):
    """
    Compare two schema metadata dictionaries to identify changes.
    
    Parameters
    ----------
    old_metadata: Dict
        The original metadata dictionary
    new_metadata: Dict
        The new metadata dictionary
        
    Returns
    -------
    Dict:
        A dictionary of changes categorized by type
    """
    changes = {
        'new_labels': [],
        'removed_labels': [],
        'new_edge_types': [],
        'removed_edge_types': [],
        'new_properties': {},
        'removed_properties': {},
        'changed_property_types': {}
    }
    
    # Compare node labels
    # ... implementation ...
    
    # Compare edge types
    # ... implementation ...
    
    # Compare properties
    # ... implementation ...
    
    return changes
```

## 10. Summary

In this notebook, we've explored how the Module Generator uses dictionaries and sets to manage Neo4j schema information. We've seen how:

1. Dictionaries provide efficient organization of metadata with hierarchical structure
2. Sets enable collection of unique values like labels and property names
3. Dictionary operations support safe access, merging, and nested navigation
4. Dictionary-based representations create consistent interfaces for graph entities
5. Advanced utilities can leverage dictionaries for graph operations like traversal and indexing

Understanding these techniques enables effective management of graph data and schema information in your own applications.

## 11. Further Reading

- [Python Dictionaries](https://docs.python.org/3/tutorial/datastructures.html#dictionaries)
- [Python Sets](https://docs.python.org/3/tutorial/datastructures.html#sets)
- [Dictionary and Set Implementations](https://docs.python.org/3/library/stdtypes.html#mapping-types-dict)
- [Neo4j Data Structures](https://neo4j.com/docs/python-manual/current/data-types/)
- [Efficient Dictionary Patterns](https://realpython.com/python-dicts/)