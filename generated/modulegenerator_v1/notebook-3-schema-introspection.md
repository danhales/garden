# Notebook 3: Database Schema Introspection

## Learning Objectives

By the end of this notebook, you will be able to:
1. Understand how the Module Generator discovers and analyzes Neo4j database structures
2. Implement schema introspection queries using Cypher
3. Process and organize metadata from introspection results
4. Identify strategies for handling schema evolution and variations
5. Build a comprehensive schema representation for code generation

## 1. Introduction to Schema Introspection

Schema introspection is the process of programmatically examining a database to discover its structure, including entities, relationships, and properties. In the Module Generator, this introspection serves as the foundation for generating type-specific code that mirrors the database's organization.

### 1.1 The Role of Introspection in Code Generation

Before generating code, the Module Generator must understand what it's working with. It needs to know:

- What node labels exist in the database
- What relationship types connect these nodes
- What properties are available on each node label and relationship type
- What data types these properties use
- What connections exist between different node types

This information determines what classes and functions to generate, what parameters they should accept, and what type checking to include.

### 1.2 The Introspection Process

The Module Generator's introspection process follows a systematic approach:

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

This function orchestrates the entire introspection process, calling specialized functions to gather specific metadata and organizing the results into a comprehensive structure.

## 2. Node Label Introspection

The first step in understanding a Neo4j database is discovering what node labels exist. These labels categorize nodes and often correspond to entity types in the domain model.

### 2.1 Discovering Node Labels

The Module Generator uses Neo4j's system procedures to retrieve all node labels:

```python
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
```

The underlying Cypher query is concise but powerful:

```python
def node_labels():
    text = 'CALL db.labels() YIELD label RETURN collect(label) AS labels;'
    params = None
    return text, params
```

This query:
1. Calls the `db.labels()` system procedure, which yields rows containing a `label` field
2. Uses `collect()` to aggregate the labels into a list
3. Returns the list as a single field named `labels`

The result is a comprehensive list of all node labels present in the database.

### 2.2 Discovering Node Properties and Types

Once the labels are known, the Module Generator examines the properties associated with each label:

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

The underlying Cypher query is more complex:

```python
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
```

This query:
1. Matches nodes with the specified label
2. Optionally limits the number of nodes to examine
3. Uses `UNWIND` to expand the keys of each node into separate rows
4. Returns distinct property names and their types

The `apoc.meta.type()` function is particularly valuable, as it determines the actual data type of each property value, which will inform type checking in the generated code.

### 2.3 Alternative Approaches to Node Metadata

The Module Generator also implements an alternative approach using Neo4j's schema information:

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

The underlying Cypher query leverages an advanced system procedure:

```python
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
```

This approach provides more comprehensive type information but requires Neo4j 4.x or later with the APOC library installed.

## 3. Relationship Introspection

After discovering node labels, the Module Generator examines the relationships that connect these nodes.

### 3.1 Discovering Relationship Types

The Module Generator retrieves all relationship types using another system procedure:

```python
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
```

The underlying Cypher query is similar to the node label query:

```python
def edge_types():
    text = 'CALL db.relationshipTypes() YIELD relationshipType RETURN collect(relationshipType) AS relationshipTypes;'
    params = None
    return text, params
```

This query returns a comprehensive list of all relationship types present in the database.

### 3.2 Discovering Relationship Properties and Types

For each relationship type, the Module Generator examines associated properties:

```python
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
```

The underlying Cypher query follows a similar pattern to the node properties query:

```python
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
```

### 3.3 Discovering Relationship Endpoints

A crucial aspect of relationship introspection is understanding what node types can be connected by each relationship type:

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

The underlying Cypher query examines existing relationships to determine valid connections:

```python
def edge_endpoints(type, limit=1000):
    text = f"""
        MATCH (a)-[e:{type}]->(b)
        WITH a, e, b
        {f"LIMIT {limit}" if limit is not None else ""}
        RETURN DISTINCT labels(a) AS startLabels, labels(b) AS endLabels;
    """
    params = None 
    return text, params
```

This query:
1. Matches relationship patterns of the specified type
2. Optionally limits the number of relationships to examine
3. Returns the labels of the start and end nodes

The result is a comprehensive map of what node types can be connected by each relationship type, which is crucial for generating type-safe interface methods.

## 4. Processing Introspection Results

After collecting raw metadata, the Module Generator processes and organizes it into a structured format suitable for code generation.

### 4.1 Building a Comprehensive Metadata Structure

The `_collect_metadata` function assembles all the introspection results into a single, comprehensive structure:

```python
metadata = {
    'node_labels': [],
    'node_properties': {},
    'edge_types': [],
    'edge_properties': {},
    'edge_endpoints': {}
}
```

This structure is carefully designed to support the code generation process, providing quick access to all the information needed to generate type-specific interfaces.

### 4.2 Type Mapping and Conversion

A critical aspect of processing the introspection results is mapping Neo4j data types to Python types:

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
```

This function not only maps types but also generates code to enforce these types at runtime, ensuring that the generated interfaces provide type safety.

### 4.3 Handling Schema Variations

Neo4j's schema-flexible nature means that nodes with the same label might have different properties. The Module Generator handles this by examining a sample of nodes to discover all possible properties:

```python
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
```

By using `DISTINCT`, this query ensures that each property is only reported once, regardless of how many nodes have it.

## 5. Storing and Using Metadata

Once collected and processed, the metadata serves as the foundation for code generation.

### 5.1 Embedding Metadata in the Generated Module

The Module Generator embeds the collected metadata directly in the generated module:

```python
# Add metadata as a JSON string
_log('Adding metadata')
_append(filename, f'''
# Metadata about the Neo4j graph
METADATA = {json.dumps(metadata, indent=4)}
''')
```

This approach makes the schema information available at runtime, enabling introspection and reflection capabilities in the generated code.

### 5.2 Utilizing Metadata for Code Generation

The metadata drives the generation of type-specific interfaces:

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
```

This function demonstrates how the metadata directly shapes the generated code, with each node label producing a corresponding function with appropriate type checking for its properties.

## 6. Advanced Introspection Techniques

Beyond the basic introspection capabilities, the Module Generator employs several advanced techniques to enhance its understanding of the database.

### 6.1 Handling Multi-Label Nodes

Neo4j allows nodes to have multiple labels, which can complexify introspection. The Module Generator handles this by preserving all labels during conversion:

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
    # ... implementation details ...
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
    # ... error handling ...
```

By preserving all labels, the generated code can work with nodes that have multiple classifications.

### 6.2 Handling Schema Evolution

Databases evolve over time, and the Module Generator needs to handle changes to the schema. It addresses this by regenerating the module when the schema changes:

```python
if __name__ == '__main__':
    # ... argument parsing ...
    
    # Generate the module
    generate_module(
        uri=profile['uri'],
        username=profile['username'],
        password=profile['password'],
        graph=graph,
        output_directory=output_directory
    )
```

By running the generator whenever the schema changes, the code stays synchronized with the database structure.

### 6.3 Type Inference and Validation

The Module Generator employs the APOC library's type inference capabilities to determine property types:

```python
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
```

The `apoc.meta.type()` function examines the actual values stored in the database to determine their types, which is more reliable than relying on schema declarations or assumptions.

## 7. Exercises

Now that we've explored the schema introspection capabilities of the Module Generator, let's apply this knowledge with some exercises.

### Exercise 1: Enhanced Property Type Inference

Extend the Module Generator's type inference capabilities to handle arrays of specific types, such as `LIST<STRING>` or `LIST<INTEGER>`. Modify the `_generate_type_checking_code` function to generate appropriate validation code for these compound types.

### Exercise 2: Schema Documentation Generator

Create a new function that uses the collected metadata to generate comprehensive documentation of the database schema. The documentation should include:
- Node labels and their properties
- Relationship types and their properties
- Valid connections between different node types
- Sample Cypher queries for common operations

### Exercise 3: Schema Comparison Tool

Develop a function that compares two metadata dictionaries (perhaps from different points in time) and identifies changes to the schema, such as:
- Added or removed node labels
- Added or removed relationship types
- Changed property types
- New or removed connections between node types

## 8. Summary

In this notebook, we've explored the schema introspection capabilities of the Module Generator, which form the foundation of its code generation process. We've seen how:

1. The Module Generator discovers node labels and relationship types using system procedures
2. It examines the properties and types associated with each label and relationship type
3. It maps Neo4j types to Python types for validation
4. It handles schema variations and multi-label nodes
5. It embeds the collected metadata in the generated module for runtime introspection

These introspection capabilities enable the Module Generator to create type-specific interfaces that mirror the database structure, enhancing type safety and developer productivity.

## 9. Further Reading

- [Neo4j Schema Inspection](https://neo4j.com/docs/cypher-manual/current/administration/indexes-for-schema-optimization/)
- [APOC Library Documentation](https://neo4j.com/docs/apoc/current/)
- [Neo4j Type System](https://neo4j.com/docs/cypher-manual/current/values-and-types/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Dynamic Code Generation in Python](https://realpython.com/instance-class-and-static-methods-demystified/)