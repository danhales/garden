# Notebook 8: Lists and Tuples

## Learning Objectives

By the end of this notebook, you will be able to:
1. Understand how the Module Generator uses lists and tuples to manage collections of data
2. Analyze the implementation of sequence operations in the generated code
3. Recognize when to use lists versus tuples in graph operations
4. Apply effective collection processing strategies to graph data
5. Implement your own collection-based operations for Neo4j data

## 1. Introduction to Collections in Python

Python provides several collection types for managing groups of related items. In the Module Generator, lists and tuples play crucial roles in managing Neo4j data and generating code.

### 1.1 Lists and Tuples Overview

Lists and tuples are sequence types with important distinctions:

- **Lists** are mutable collections (can be modified after creation)
- **Tuples** are immutable collections (cannot be modified after creation)

Both support common operations:
- Indexing: `collection[0]`
- Slicing: `collection[1:3]`
- Length: `len(collection)`
- Iteration: `for item in collection`
- Membership testing: `item in collection`

The choice between lists and tuples often reflects the semantic intent of the collection.

### 1.2 Collections in the Module Generator

The Module Generator uses collections for several purposes:

1. **Metadata Organization**: Storing schema information
2. **Query Results**: Processing database query responses
3. **Code Generation**: Assembling pieces of generated code
4. **Result Transformation**: Converting between Neo4j and Python formats

Understanding these applications provides insights into effective collection management.

## 2. Lists for Dynamic Collections

The Module Generator uses lists extensively for collections that may change size or content.

### 2.1 Collecting Schema Information

When gathering metadata, the Module Generator collects schema information into lists:

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

This function:
1. Executes a query to retrieve node labels
2. Accesses the 'labels' field of the first result
3. Returns a list of strings representing the labels

The returned list will dynamically reflect the labels present in the database.

### 2.2 Building Code Fragments

During code generation, the Module Generator builds lists of code fragments:

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
        # ... generate function code ...
        functions.append(function_code)
    
    return "\n".join(functions)
```

This function:
1. Initializes an empty list `functions`
2. Appends a code fragment for each node label
3. Joins the fragments with newlines to form a complete code block

Using a list allows the number of functions to match the number of node labels, which varies by database.

### 2.3 List Comprehensions for Transformation

The Module Generator uses list comprehensions for concise transformations:

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

The expression `', '.join(f"{prop}: ${prop}" for prop in props)` is a list comprehension combined with a join operation:
1. It creates a formatted string for each property
2. It joins these strings with commas
3. The result is a properly formatted property constraint list

This approach is more concise and readable than building the string incrementally.

### 2.4 Converting Query Results

In the generated code, list comprehensions transform query results:

```python
# Construct and execute the query
query, params = Queries.node(label="Person", **search_props)
results = _query(query, params)
return [_neo4j_node_to_dict(result['n']) for result in results]
```

This list comprehension:
1. Applies the `_neo4j_node_to_dict` function to each node in the results
2. Creates a new list containing the transformed nodes
3. Returns the list as the function's result

This pattern efficiently converts Neo4j objects to a more convenient Python representation.

## 3. Tuples for Fixed Collections

The Module Generator uses tuples when the structure of a collection is fixed.

### 3.1 Query Construction

The Module Generator returns queries and parameters as tuples:

```python
def server_timestamp():
    text = 'RETURN datetime() AS timestamp;'
    params = None
    return text, params
```

This function returns a 2-element tuple containing:
1. The query text
2. The query parameters (or None if there are no parameters)

Using a tuple communicates that this is a fixed structure with a specific meaning for each position.

### 3.2 Relationship Patterns

In the generated code, relationship patterns are represented as tuples:

```python
def knows(uuid=None, **props):
    """
    Find relationships of type KNOWS matching the given properties.
    
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
    """
    # ... implementation ...
    return [(_neo4j_node_to_dict(r['source']), 
             _neo4j_relationship_to_dict(r['r']), 
             _neo4j_node_to_dict(r['target'])) for r in results]
```

This function returns a list of 3-element tuples, where each tuple represents a complete relationship pattern:
1. The source node
2. The relationship
3. The target node

Using tuples ensures that the components maintain their relative positions, which is crucial for unpacking:

```python
# Example usage of the returned data
for source, relationship, target in knows(since=2010):
    print(f"{source['props']['name']} knows {target['props']['name']} since {relationship['props']['since']}")
```

### 3.3 Edge Endpoints

The Module Generator uses tuples to represent the valid endpoints of relationships:

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

This function returns a 2-element tuple containing:
1. A list of valid start node labels
2. A list of valid end node labels

The tuple structure ensures that these two collections maintain their distinct meanings.

## 4. Collection Processing Techniques

The Module Generator employs several techniques for processing collections effectively.

### 4.1 Collection Building with Sets

When uniqueness matters, the Module Generator uses sets before converting to lists:

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
2. Adds labels to the sets, automatically eliminating duplicates
3. Converts the sets to lists before returning them

This approach efficiently ensures uniqueness without explicit duplicate checking.

### 4.2 Dictionary Grouping

The Module Generator organizes metadata using dictionaries with lists or dictionaries as values:

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

This function creates a nested structure:
1. A top-level dictionary with keys for different types of metadata
2. Lists for simple collections like labels and edge types
3. Nested dictionaries for properties and endpoints, keyed by label or type

This organization makes it easy to access specific information by navigating the structure.

### 4.3 Iteration and Filtering

The Module Generator processes collections through iteration and filtering:

```python
# Add type checking for each property
for prop_name, prop_type in properties.items():
    function_code += _generate_type_checking_code(prop_name, prop_type)
```

This pattern:
1. Iterates through the items in a dictionary
2. Applies a transformation to each item
3. Accumulates the results

The Module Generator often combines iteration with conditional logic:

```python
# Generate the type checking code
if property_type.startswith('LIST<') and property_type.endswith('>'):
    # Handle typed lists
    item_type = property_type[5:-1]
    # ... generate list-specific code ...
else:
    # Handle scalar types
    # ... generate scalar-specific code ...
```

This approach allows for different processing based on collection characteristics.

### 4.4 Joining Collections

The Module Generator joins collections of strings to form code blocks:

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
        # ... generate function code ...
        functions.append(function_code)
    
    return "\n".join(functions)
```

The `"\n".join(functions)` operation:
1. Takes a list of strings (function definitions)
2. Inserts a newline character between each string
3. Returns a single string with all functions properly separated

This approach maintains readability in the generated code.

## 5. Lists vs. Tuples: Making the Right Choice

The Module Generator's use of lists and tuples provides insights into when to use each collection type.

### 5.1 When to Use Lists

The Module Generator uses lists when:

1. **The collection size is variable**: 
   ```python
   metadata['node_labels'] = _get_node_labels()  # Number of labels varies by database
   ```

2. **The collection needs to be built incrementally**:
   ```python
   functions = []
   for label in metadata['node_labels']:
       # ... generate function code ...
       functions.append(function_code)
   ```

3. **The collection may need modification**:
   ```python
   # Convert node labels to valid Python identifiers
   function_names = []
   for label in node_labels:
       name = label.lower().replace(':', '_').replace('-', '_')
       function_names.append(name)
   ```

4. **Items share a common type and purpose**:
   ```python
   # All items are node labels
   node_labels = ['Person', 'Movie', 'Company']
   ```

### 5.2 When to Use Tuples

The Module Generator uses tuples when:

1. **The collection structure is fixed**:
   ```python
   return text, params  # Always a query string and parameters
   ```

2. **Items have different types with specific meanings**:
   ```python
   # (source_node, relationship, target_node)
   return [(_neo4j_node_to_dict(r['source']), 
            _neo4j_relationship_to_dict(r['r']), 
            _neo4j_node_to_dict(r['target'])) for r in results]
   ```

3. **The collection represents a composite value**:
   ```python
   # Start and end labels form a meaningful pair
   return list(startLabels), list(endLabels)
   ```

4. **The collection shouldn't be modified after creation**:
   ```python
   # Fixed set of utility functions to copy
   utility_functions = (
       '_authenticated_driver',
       '_query',
       '_server_timestamp'
   )
   ```

### 5.3 Design Implications

The choice between lists and tuples has implications beyond mutability:

1. **API Design**: Tuples in return values signal fixed structure to callers
2. **Error Prevention**: Immutable tuples prevent accidental modifications
3. **Performance**: Tuples can be slightly more efficient due to immutability
4. **Readability**: The choice can signal intent to other developers

## 6. Working with Neo4j Collections

Neo4j has its own collection types that must be mapped to Python collections.

### 6.1 Neo4j Lists

Neo4j supports list properties, which the Module Generator maps to Python lists:

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
```

When handling Neo4j lists, the Module Generator generates appropriate validation code:

```python
# Example of handling a list property (not from the actual code)
if property_type == 'LIST':
    return f"""
    # Type check {property_name} (expected list)
    if "{property_name}" in props and props["{property_name}"] is not None:
        if not isinstance(props["{property_name}"], list):
            try:
                # Attempt to convert to list
                props["{property_name}"] = list(props["{property_name}"])
            except:
                raise TypeError(f"Property {property_name} must be a list, got {{type(props['{property_name}']).__name__}}")
"""
```

### 6.2 Cypher Collection Operations

Cypher, Neo4j's query language, includes operations for working with collections. The Module Generator generates Cypher queries that use these operations:

```python
def node_labels():
    text = 'CALL db.labels() YIELD label RETURN collect(label) AS labels;'
    params = None
    return text, params
```

The `collect()` function in Cypher:
1. Aggregates individual values into a list
2. Similar to Python's `list()` function on an iterator
3. Commonly used to create lists from query results

### 6.3 Collection Parameters in Queries

The Module Generator supports passing collections as query parameters:

```python
def nodes_with_labels(labels):
    """
    Find nodes that have all the specified labels.
    """
    labels_param = ':'.join(labels)
    text = f"""
    MATCH (n:{labels_param})
    RETURN n;
    """
    params = None
    return text, params
```

This function:
1. Takes a list of labels as input
2. Joins them with colons to form a multi-label pattern
3. Uses the joined string in a Cypher query

For more complex cases, collections can be passed as parameters:

```python
def nodes_with_any_label(labels):
    """
    Find nodes that have any of the specified labels.
    """
    text = """
    MATCH (n)
    WHERE any(label IN $labels WHERE label IN labels(n))
    RETURN n;
    """
    params = {'labels': labels}
    return text, params
```

This approach:
1. Passes the entire list as a parameter
2. Uses Cypher's `any()` function for collection testing
3. Keeps the query parameterized for security and performance

## 7. Collection Processing in Generated Interfaces

The interfaces generated by the Module Generator process collections in various ways.

### 7.1 Query Result Transformation

The generated node interface functions transform query results into collections of dictionaries:

```python
# Construct and execute the query
query, params = Queries.node(label="Person", **search_props)
results = _query(query, params)
return [_neo4j_node_to_dict(result['n']) for result in results]
```

This pattern:
1. Executes a query to get raw results
2. Applies a transformation function to each result
3. Returns a list of transformed results

### 7.2 Relationship Pattern Representation

The generated relationship interface functions represent complete patterns as tuples:

```python
return [(_neo4j_node_to_dict(r['source']), 
         _neo4j_relationship_to_dict(r['r']), 
         _neo4j_node_to_dict(r['target'])) for r in results]
```

This representation:
1. Captures the source node, relationship, and target node as a unit
2. Maintains the structural relationships between elements
3. Allows for easy unpacking in client code

### 7.3 Collection Property Handling

The generated code includes special handling for collection properties:

```python
# Example handling for list properties (not from the actual code)
if "tags" in props and props["tags"] is not None:
    if not isinstance(props["tags"], list):
        try:
            # Attempt to convert to list
            props["tags"] = list(props["tags"])
        except:
            raise TypeError(f"Property tags must be a list, got {type(props['tags']).__name__}")
    
    # Check items in the list (if needed)
    for i, item in enumerate(props["tags"]):
        if not isinstance(item, str):
            try:
                props["tags"][i] = str(item)
            except:
                raise TypeError(f"Item {i} in tags must be a string, got {type(item).__name__}")
```

This approach:
1. Validates the property's type as a list
2. Attempts conversion if necessary
3. Optionally validates the types of items within the list

## 8. Exercises

Now that we've explored the use of lists and tuples in the Module Generator, let's apply this knowledge with some exercises.

### Exercise 1: Enhanced Collection Handling

Extend the Module Generator's type system to support typed collections with validation:

```python
# Map Neo4j types to Python types with collection support
type_mapping = {
    'STRING': 'str',
    'INTEGER': 'int',
    'FLOAT': 'float',
    'BOOLEAN': 'bool',
    'DATE': 'datetime.date',
    'DATETIME': 'datetime.datetime',
    'LIST<STRING>': ('list', 'str'),   # List of strings
    'LIST<INTEGER>': ('list', 'int'),  # List of integers
    'LIST<FLOAT>': ('list', 'float'),  # List of floats
    'LIST<BOOLEAN>': ('list', 'bool'), # List of booleans
    'MAP': 'dict'
}
```

Then modify the `_generate_type_checking_code` function to handle these typed collections.

### Exercise 2: Path Processing

Create a function that processes path results from Neo4j and represents them as a list of alternating nodes and relationships:

```python
def find_paths(start_label, end_label, max_depth=3):
    """
    Find paths between nodes of the specified labels.
    
    Parameters
    ----------
    start_label: str
        The label of the start nodes
    end_label: str
        The label of the end nodes
    max_depth: int, optional
        Maximum path length
        
    Returns
    -------
    List[List[Dict]]:
        A list of paths, where each path is a list of alternating nodes and relationships
    """
    # Implementation here
```

### Exercise 3: Collection-Based Query Builder

Design a query builder that uses collections to construct complex Cypher queries:

```python
def build_query(node_labels=None, relationship_types=None, properties=None, limit=None):
    """
    Build a Cypher query based on the specified criteria.
    
    Parameters
    ----------
    node_labels: List[str], optional
        Node labels to include in the query
    relationship_types: List[str], optional
        Relationship types to include in the query
    properties: Dict[str, Any], optional
        Properties to match in the query
    limit: int, optional
        Maximum number of results to return
        
    Returns
    -------
    Tuple[str, Dict]:
        The Cypher query and parameters
    """
    # Implementation here
```

## 9. Summary

In this notebook, we've explored how the Module Generator uses lists and tuples to work with collections of data. We've seen how:

1. Lists provide flexibility for variable-size collections and incremental building
2. Tuples represent fixed structures with specific meaning for each position
3. Collection processing techniques like comprehensions and joins streamline operations
4. The choice between lists and tuples reflects design intent and constraints
5. Neo4j collections map to Python collections with appropriate validation

Understanding these patterns enables effective management of graph data and code generation for Neo4j interfaces.

## 10. Further Reading

- [Python Lists and Tuples](https://docs.python.org/3/tutorial/datastructures.html)
- [Python List Comprehensions](https://docs.python.org/3/tutorial/datastructures.html#list-comprehensions)
- [Neo4j Lists and Maps](https://neo4j.com/docs/cypher-manual/current/values-and-types/lists/)
- [Cypher Collection Functions](https://neo4j.com/docs/cypher-manual/current/functions/list/)
- [Python Collection Processing Patterns](https://realpython.com/python-data-structures/)