# Notebook 6: Value-Returning Functions and Modules

## Learning Objectives

By the end of this notebook, you will be able to:
1. Understand the role of value-returning functions in the Module Generator
2. Analyze how functions are composed to build complex functionality
3. Apply module organization principles for maintainable code
4. Design effective interfaces that balance flexibility and simplicity
5. Implement your own value-returning functions for graph operations

## 1. Introduction to Value-Returning Functions

Value-returning functions are the building blocks of modular programming. They take inputs, perform operations, and return results that can be used by other parts of the program.

### 1.1 Function Anatomy

A typical value-returning function has four components:

1. **Name**: Identifies the function
2. **Parameters**: Define the inputs
3. **Body**: Contains the operations
4. **Return Value**: Provides the output

The Module Generator uses value-returning functions extensively to decompose complex tasks into manageable pieces.

### 1.2 Benefits of Value-Returning Functions

Using value-returning functions offers several advantages:

1. **Reusability**: Functions can be used in multiple contexts
2. **Testability**: Individual functions can be tested in isolation
3. **Maintainability**: Changes to a function's implementation don't affect its callers
4. **Readability**: Functions provide a level of abstraction that simplifies understanding

Let's examine how the Module Generator leverages these benefits.

## 2. Core Value-Returning Functions

The Module Generator includes several key value-returning functions that drive its operation.

### 2.1 The generate_module Function

The central function of the Module Generator is `generate_module`, which orchestrates the entire generation process:

```python
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

    # ... additional steps for writing the module ...

    _log(f"{filename} successfully generated.")
    return filename
```

This function:
1. Takes input parameters for configuration
2. Performs a series of operations using other functions
3. Returns a value (the filepath of the generated module)

The function's organization follows a clear progression from inputs to outputs, with each step building on the previous one.

### 2.2 The _collect_metadata Function

Another critical value-returning function is `_collect_metadata`, which gathers information about the database schema:

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

This function:
1. Takes a database driver as input
2. Creates a structured dictionary to hold the metadata
3. Populates the dictionary by calling other functions
4. Returns the completed metadata dictionary

The function decomposes the complex task of schema introspection into smaller, focused operations, delegating to specialized functions for each type of metadata.

### 2.3 The _query Function

At a lower level, the `_query` function handles database communication:

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

This function:
1. Takes a query and parameters as inputs
2. Establishes a database session
3. Executes the query
4. Returns the results as a collection of dictionaries

The function encapsulates the details of database interaction, providing a clean interface for other functions to use.

### 2.4 Conversion Functions

The Module Generator includes specialized functions for converting Neo4j entities to Python dictionaries:

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
```

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
```

These functions:
1. Take Neo4j entities as inputs
2. Apply conversions to standardize the representation
3. Return Python dictionaries with a consistent structure

The functions handle various input formats and edge cases, ensuring that the rest of the system can work with a unified representation.

## 3. Function Composition Patterns

The Module Generator employs several patterns for composing functions to build complex functionality.

### 3.1 Hierarchical Composition

Functions are organized in a hierarchical structure, with higher-level functions calling lower-level ones:

```
generate_module
  ├── _authenticated_driver
  ├── _collect_metadata
  │     ├── _get_node_labels
  │     ├── _get_node_properties
  │     ├── _get_edge_types
  │     ├── _get_edge_properties
  │     └── _get_edge_endpoints
  ├── _generate_node_interface_functions
  │     └── _generate_type_checking_code
  └── _generate_edge_interface_functions
        └── _generate_type_checking_code
```

This hierarchical composition:
1. Decomposes complex operations into simpler ones
2. Groups related functions together
3. Enables code reuse at multiple levels

### 3.2 Pipeline Composition

The Module Generator also uses a pipeline pattern, where the output of one function becomes the input to another:

```python
# Collect metadata about the graph
metadata = _collect_metadata(driver)

# Create the node and edge interface classes
_append(filename, f'''
class Nodes:
    """
    Interface for working with nodes in the Neo4j graph.
    Each method corresponds to a node label in the graph.
    """
{_generate_node_interface_functions(metadata)}
''')
```

This pipeline approach:
1. Establishes a clear flow of data through the system
2. Makes dependencies between functions explicit
3. Allows for intermediate results to be inspected or modified

### 3.3 Function Factory Pattern

The Module Generator employs a function factory pattern for generating type-specific interfaces:

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
        # ... generate function for this label ...
        functions.append(function_code)
    
    return "\n".join(functions)
```

This pattern:
1. Creates multiple similar functions based on a template
2. Customizes each function according to specific requirements
3. Returns the combined result as a unified piece of code

## 4. Module Organization

Beyond individual functions, the Module Generator demonstrates effective module organization principles.

### 4.1 Public vs. Private Functions

The Module Generator distinguishes between public and private functions using the underscore convention:

```python
# Public function (part of the module's API)
def generate_module(uri=None, username=None, password=None, graph=None, output_directory=os.environ['PWD']):
    # ...

# Private function (internal implementation detail)
def _authenticated_driver(uri=profile['uri'], username=profile['username'], password=profile['password']):
    # ...
```

This convention:
1. Clarifies which functions are meant for external use
2. Encapsulates implementation details
3. Provides guidance to users of the module

### 4.2 Function Grouping

Functions are grouped logically by their purpose:

1. **Schema Introspection**: `_get_node_labels`, `_get_edge_types`, etc.
2. **Code Generation**: `_generate_node_interface_functions`, `_generate_edge_interface_functions`, etc.
3. **File Management**: `_append`, `_append_imports`, etc.
4. **Utility Functions**: `_authenticated_driver`, `_query`, etc.

This organization:
1. Makes the code easier to navigate
2. Highlights relationships between functions
3. Enables focused testing and maintenance

### 4.3 Configuration Management

The Module Generator uses a centralized approach to configuration:

```python
profile = {
    'uri': 'bolt://localhost:7687',
    'database': 'neo4j',
    'username': 'neo4j',
    'password': 'neo4j-dev'
}

# Update configuration from function parameters
if uri is not None:
    profile['uri'] = uri
if username is not None:
    profile['username'] = username
if password is not None:
    profile['password'] = password
```

This approach:
1. Provides default values for configuration
2. Allows for overrides through function parameters
3. Centralizes configuration in one place

### 4.4 Error Handling

The Module Generator includes error handling to manage exceptional cases:

```python
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

This error handling:
1. Anticipates potential issues
2. Provides graceful degradation rather than crashing
3. Returns sensible default values when possible

## 5. Interface Design Principles

The Module Generator demonstrates several principles for designing effective interfaces.

### 5.1 Consistent Parameter Ordering

Functions that perform similar operations use consistent parameter ordering:

```python
def _neo4j_node_to_dict(node):
    # ...

def _neo4j_relationship_to_dict(rel):
    # ...
```

Both functions take a single parameter representing the entity to convert, making the interface predictable and easy to remember.

### 5.2 Default Parameters

Functions provide sensible defaults for optional parameters:

```python
def generate_module(uri=None, username=None, password=None, graph=None, output_directory=os.environ['PWD']):
    # ...
```

This allows users to specify only the parameters they want to customize, while accepting defaults for the rest.

### 5.3 Named Parameters

The Module Generator uses named parameters for clarity:

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

This approach:
1. Makes the purpose of each argument explicit
2. Allows for parameters to be specified in any order
3. Improves code readability

### 5.4 Parameter Validation

Generated functions include validation for their parameters:

```python
# Type check {property_name} (expected {python_type})
if "{property_name}" in props and props["{property_name}"] is not None:
    if not isinstance(props["{property_name}"], {python_type}):
        try:
            # Attempt to convert
            props["{property_name}"] = {python_type}(props["{property_name}"])
        except:
            raise TypeError(f"Property {property_name} must be of type {python_type}, got {{type(props['{property_name}']).__name__}}")
```

This validation:
1. Ensures that parameters meet the expected requirements
2. Provides helpful error messages when validation fails
3. Attempts to convert parameters to the correct type when possible

## 6. Generated Module Structure

The Module Generator produces modules with their own value-returning functions and organization.

### 6.1 Node Interface Functions

Each node label in the database produces a corresponding interface function:

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
        
    # Type checking for known properties
    # ... type checking code ...
    
    # Construct and execute the query
    query, params = Queries.node(label="Person", **search_props)
    results = _query(query, params)
    return [_neo4j_node_to_dict(result['n']) for result in results]
```

These functions:
1. Take a UUID and additional properties as inputs
2. Validate property types
3. Construct and execute a query
4. Return a list of matching nodes

### 6.2 Relationship Interface Functions

Similarly, each relationship type produces a corresponding interface function:

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
    search_props = props.copy()
    if uuid is not None:
        search_props['uuid'] = uuid
        
    # Type checking for known properties
    # ... type checking code ...
    
    # Construct and execute the query
    query, params = Queries.edge(type="KNOWS", **search_props)
    results = _query(query, params)
    return [(_neo4j_node_to_dict(r['source']), 
             _neo4j_relationship_to_dict(r['r']), 
             _neo4j_node_to_dict(r['target'])) for r in results]
```

These functions follow a similar pattern to node interface functions but return tuples representing complete relationship patterns.

### 6.3 Utility Functions

The generated module includes utility functions for common operations:

```python
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
```

These functions provide more general capabilities that complement the type-specific interfaces.

### 6.4 Class Organization

The generated module organizes functions into classes for better organization:

```python
class Nodes:
    """
    Interface for working with nodes in the Neo4j graph.
    Each method corresponds to a node label in the graph.
    """
    # ... node interface functions ...

class Edges:
    """
    Interface for working with relationships in the Neo4j graph.
    Each method corresponds to a relationship type in the graph.
    """
    # ... relationship interface functions ...
```

This organization:
1. Groups related functions together
2. Provides a namespace for functions
3. Makes the module's structure clearer to users

The module also provides pre-instantiated instances for immediate use:

```python
# Create the interface instances
nodes = Nodes()
edges = Edges()
```

This allows users to access the functions directly without creating their own instances.

## 7. Exercises

Now that we've explored the value-returning functions and module organization of the Module Generator, let's apply this knowledge with some exercises.

### Exercise 1: Enhanced Query Function

Create an enhanced version of the `_query` function that supports additional features:
- Automatic retry for transient errors
- Performance timing
- Query logging for debugging
- Result pagination for large result sets

### Exercise 2: Node Creation Interface

Extend the generated module with functions for creating new nodes:

```python
def create_person(name, age=None, **props):
    """
    Create a new Person node with the specified properties.
    
    Parameters
    ----------
    name: str
        The name of the person (required)
    age: int, optional
        The age of the person
    **props: Dict
        Additional properties for the person
        
    Returns
    -------
    Dict:
        The created node as a dictionary
    """
    # Implementation here
```

### Exercise 3: Module Extension Framework

Design a framework that allows users to extend the generated module with custom functions without modifying the generated code directly. Your framework should:
- Allow for registering custom functions
- Preserve extensions when the module is regenerated
- Integrate extensions seamlessly with the generated code

## 8. Summary

In this notebook, we've explored the value-returning functions and module organization of the Module Generator. We've seen how:

1. Value-returning functions decompose complex operations into manageable pieces
2. Functions are composed hierarchically to build complex functionality
3. Module organization principles enhance maintainability and usability
4. Interface design choices affect how users interact with the code
5. The generated module provides a clean, organized interface to the Neo4j database

Understanding these principles enables you to work effectively with the Module Generator, extend its capabilities, and apply similar patterns in your own code.

## 9. Further Reading

- [Python Functions](https://docs.python.org/3/tutorial/controlflow.html#defining-functions)
- [Python Modules](https://docs.python.org/3/tutorial/modules.html)
- [Clean Code: A Handbook of Agile Software Craftsmanship](https://www.oreilly.com/library/view/clean-code-a/9780136083238/)
- [Design Patterns: Elements of Reusable Object-Oriented Software](https://www.oreilly.com/library/view/design-patterns-elements/0201633612/)
- [The Pragmatic Programmer](https://pragprog.com/titles/tpp20/the-pragmatic-programmer-20th-anniversary-edition/)