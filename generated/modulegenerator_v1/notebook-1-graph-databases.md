# Notebook 1: Introduction to Graph Databases and Neo4j

## Learning Objectives

By the end of this notebook, you will be able to:
1. Understand the fundamental concepts of graph databases
2. Recognize the key components of the Neo4j graph data model
3. Write basic Cypher queries for data retrieval and manipulation
4. Connect to a Neo4j database using Python
5. Understand how the Module Generator interfaces with Neo4j

## 1. Graph Database Fundamentals

### 1.1 What Are Graph Databases?

Graph databases represent a paradigm shift from traditional relational databases. Rather than organizing data in tables with rows and columns, graph databases use graph structures consisting of nodes (entities) and edges (relationships) to represent and store data. This approach excels at managing highly connected data and analyzing relationships.

The key advantages of graph databases include:

- **Relationship-centric**: They prioritize connections between entities
- **Performance**: Queries that would require expensive joins in relational databases are often more efficient
- **Flexibility**: The schema can evolve without disrupting existing queries
- **Intuitive modeling**: Many real-world domains naturally map to graph structures

### 1.2 The Property Graph Model

Neo4j implements the property graph model, which consists of:

- **Nodes**: Entities with properties (key-value pairs)
- **Relationships**: Connections between nodes with their own properties
- **Labels**: Categories for nodes
- **Relationship Types**: Categories for relationships

Let's examine how the Module Generator interprets this model through its internal functions:

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
```

This function demonstrates how Neo4j nodes are represented programmatically. It handles two distinct cases:

1. When a node is already represented as a Python dictionary
2. When a node is a native Neo4j Node object

In both cases, it extracts three fundamental components:
- A unique identifier (`uuid`)
- The node's labels (categories)
- The node's properties (key-value pairs)

Similarly, relationships are processed by a companion function:

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
```

Note the important distinction highlighted in the docstring: unlike nodes, which can have multiple labels, relationships in Neo4j can only have a single type. This fundamental constraint shapes how graph models are designed.

## 2. Introduction to Neo4j

### 2.1 Neo4j Architecture

Neo4j is a native graph database platform with several key components:

- **Core Database Engine**: The native graph storage and processing engine
- **Cypher Query Language**: A declarative language for querying and manipulating graphs
- **Bolt Protocol**: A binary protocol for efficient client-server communication
- **Procedures**: Built-in and user-defined extensions to Cypher functionality

The Module Generator interfaces with Neo4j primarily through the Bolt protocol via the official Neo4j Python driver, as shown in the connection function:

```python
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
```

This function creates an authenticated connection to the Neo4j database using the Bolt protocol (typically on port 7687, as indicated by the default URI `bolt://localhost:7687`).

### 2.2 The Cypher Query Language

Cypher is Neo4j's declarative query language, designed specifically for working with graph data. Its syntax is visually representative of the graph patterns being queried, making it intuitive for many users.

The Module Generator contains numerous examples of Cypher queries within its `Queries` class:

```python
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

        return text, params
    
    def node_labels():
        text = 'CALL db.labels() YIELD label RETURN collect(label) AS labels;'
        params = None
        return text, params
```

Let's break down the key Cypher patterns demonstrated here:

1. `RETURN datetime() AS timestamp;`
   - Uses a built-in function to return the current timestamp
   - Demonstrates aliasing with `AS`

2. ```
   MATCH 
      (n:{label} 
      {props}) 
      RETURN n;
   ```
   - `MATCH` specifies a pattern to find in the graph
   - `(n:{label})` represents a node with a specific label
   - `{props}` filters nodes based on property values
   - `RETURN n` returns the matching nodes

3. `CALL db.labels() YIELD label RETURN collect(label) AS labels;`
   - `CALL` executes a procedure (in this case, a system procedure)
   - `YIELD` specifies which outputs from the procedure to use
   - `collect()` aggregates values into a list

The Module Generator also contains more complex Cypher queries for introspecting the database schema:

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

This query:
1. Calls a system procedure to retrieve schema information
2. Uses `UNWIND` to expand collections into individual rows
3. Uses `DISTINCT` to eliminate duplicates
4. Aggregates with `collect()` to group property types

### 2.3 Executing Cypher Queries from Python

The Module Generator uses a dedicated function to execute Cypher queries:

```python
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
```

This function demonstrates the typical pattern for executing Cypher queries from Python:

1. Establish a connection and create a session
2. Run the query with parameters
3. Convert the results to a Python data structure

Note the use of parameterized queries, which is a critical security practice to prevent Cypher injection attacks (similar to SQL injection in relational databases).

## 3. Graph Data Modeling

### 3.1 Designing Graph Data Models

Graph data modeling focuses on identifying:
- Entities (which become nodes)
- Relationships between entities
- Properties for both nodes and relationships
- Appropriate labels and relationship types

The Module Generator examines existing graph models by querying the database schema:

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

This function builds a comprehensive picture of the graph model by examining:
1. All node labels (entity types)
2. Properties associated with each node label
3. All relationship types
4. Properties associated with each relationship type
5. Valid connections between different node types

### 3.2 Common Graph Patterns

Several common graph patterns appear in many graph database applications:

1. **Node-Relationship-Node**: The fundamental building block
   ```
   (Person)-[:KNOWS]->(Person)
   ```

2. **Property Container**: Using nodes to represent complex objects with properties
   ```
   (Customer {name: "John", age: 30})
   ```

3. **Hyperedge**: Representing many-to-many relationships
   ```
   (Person)-[:ATTENDED]->(Event)<-[:ATTENDED]-(Person)
   ```

4. **Hierarchies**: Representing tree structures
   ```
   (Department)-[:HAS_SUBDEPARTMENT]->(Department)
   ```

The Module Generator can recognize these patterns by examining the relationship endpoints:

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

This function identifies which node labels appear at the start and end of each relationship type, thereby mapping the valid connections in the graph model.

## 4. Connecting to Neo4j from Python

### 4.1 The Neo4j Python Driver

To work with Neo4j from Python, you need the official Neo4j Python driver:

```python
import neo4j
from neo4j import GraphDatabase
```

The Module Generator uses this driver for all database interactions. The connection details are stored in a profile dictionary:

```python
profile = {
    'uri': 'bolt://localhost:7687',
    'database': 'neo4j',
    'username': 'neo4j',
    'password': 'neo4j-dev'
}
```

### 4.2 Connection Management

Proper connection management is crucial for database applications. The Module Generator follows best practices by:

1. Using the `with` statement for automatic session cleanup:
   ```python
   with _authenticated_driver().session() as session:
       return session.run(query_text, query_params).data()
   ```

2. Parameterizing all user inputs to prevent injection attacks:
   ```python
   text = f"""MATCH 
       (n:{label} 
       {'{' if props else ''} 
       {', '.join(f"{prop}: ${prop}" for prop in props)}
       {'}' if props else ''}) 
       RETURN n;"""
   ```

### 4.3 Handling Results

Results from Neo4j queries can be processed in several ways:

1. Converting to Python dictionaries:
   ```python
   def _neo4j_node_to_dict(node):
       # ... processing ...
       return {
           'uuid': uuid,
           'labels': labels,
           'props': props
       }
   ```

2. Extracting specific values:
   ```python
   return _query(query_text=text, query_params=params)[0]['timestamp'].iso_format()
   ```

3. Aggregating multiple results:
   ```python
   for result in results:
       for start in result['startLabels']:
           startLabels.add(start)
   ```

## 5. The Module Generator's Approach to Neo4j

### 5.1 Schema Introspection

The Module Generator begins by introspecting the database schema to discover:

1. Node labels:
   ```python
   def _get_node_labels():
       text, params = Queries.node_labels()
       results = _query(text, params)
       return results[0]['labels']
   ```

2. Node properties:
   ```python
   def _get_node_properties(label):
       text, params = Queries.node_properties(label)
       results = _query(text, params)
       properties = {}
       
       for result in results:
           properties[result['key']] = result['type']
           
       return properties
   ```

3. Relationship types:
   ```python
   def _get_edge_types():
       text, params = Queries.edge_types()
       results = _query(text, params)
       return results[0]['relationshipTypes']
   ```

4. Relationship properties:
   ```python
   def _get_edge_properties(type):
       text, params = Queries.edge_properties(type)
       results = _query(text, params)
       properties = {}
       
       for result in results:
           properties[result['key']] = result['type']
           
       return properties
   ```

5. Valid connections:
   ```python
   def _get_edge_endpoints(type):
       # ... (shown earlier) ...
   ```

### 5.2 Code Generation Strategy

After collecting schema information, the Module Generator:

1. Creates type-specific interfaces:
   ```python
   def _generate_node_interface_functions(metadata):
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
           # ... (implementation) ...
       """
           
           functions.append(function_code)
       
       return "\n".join(functions)
   ```

2. Implements type checking:
   ```python
   def _generate_type_checking_code(property_name, property_type):
       # ... (shown earlier) ...
   ```

3. Assembles the complete module:
   ```python
   def generate_module(uri=None, username=None, password=None, graph=None, output_directory=os.environ['PWD']):
       # ... (initialization) ...
       
       # Collect metadata about the graph
       _log('Collecting metadata from Neo4j database')
       metadata = _collect_metadata(driver)
       
       # ... (file creation) ...
       
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
       
       # ... (remaining assembly) ...
       
       _log(f"{filename} successfully generated.")
       return filename
   ```

## 6. Exercises

Now that we've explored the fundamentals of graph databases and Neo4j through the lens of the Module Generator, let's apply this knowledge with some exercises.

### Exercise 1: Understanding Graph Structure

1. Using the Module Generator's schema introspection methods, write a function that would visualize the graph structure by:
   - Listing all node labels
   - For each label, listing its properties
   - Showing valid connections between different node types
   - Highlighting properties on relationships

### Exercise 2: Extending the Module Generator

2. Identify one area where the Module Generator could be extended to provide additional functionality for working with Neo4j graphs. Sketch a function that would implement this enhancement.

### Exercise 3: Analyzing Generated Code

3. Review the code generation techniques used by the Module Generator. How does it ensure type safety in the generated code? How could this approach be improved?

## 7. Summary

In this notebook, we've explored the fundamental concepts of graph databases and Neo4j, viewed through the lens of the G.A.R.D.E.N. Module Generator. We've seen how:

1. Graph databases use nodes and relationships to represent connected data
2. Neo4j implements the property graph model with labeled nodes and typed relationships
3. Cypher provides a declarative language for querying graph databases
4. The Neo4j Python driver enables programmatic interaction with the database
5. The Module Generator introspects the database schema to generate type-specific interfaces

In the next notebook, we'll delve deeper into the Module Generator's core architecture and design patterns.

## 8. Further Reading

- [Neo4j Graph Database Documentation](https://neo4j.com/docs/)
- [Cypher Query Language Reference](https://neo4j.com/docs/cypher-manual/current/)
- [Neo4j Python Driver Documentation](https://neo4j.com/docs/api/python-driver/current/)
- [Graph Data Modeling Guidelines](https://neo4j.com/developer/guide-data-modeling/)
- [Python Code Generation Techniques](https://realpython.com/code-generation-python/)
