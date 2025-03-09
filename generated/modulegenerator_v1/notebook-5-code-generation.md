# Notebook 5: Code Generation Techniques

## Learning Objectives

By the end of this notebook, you will be able to:
1. Understand the principles of template-based code generation
2. Implement string manipulation for dynamic code creation
3. Apply code organization techniques for generated modules
4. Generate properly documented code with docstrings
5. Build your own custom code generator for Neo4j

## 1. Introduction to Code Generation

Code generation is the process of creating source code programmatically rather than writing it manually. In the context of the Module Generator, code generation transforms database schema information into a functional Python API.

### 1.1 Why Generate Code?

Code generation offers several advantages:

1. **Consistency**: Generated code follows consistent patterns and conventions
2. **Reduced Repetition**: Eliminates the need to write boilerplate code for similar entities
3. **Synchronization**: Keeps code in sync with the database schema
4. **Type Safety**: Enforces type checking based on actual database types
5. **Documentation**: Automatically includes documentation based on schema information

### 1.2 Code Generation Approaches

The Module Generator employs several code generation techniques:

1. **String Templates**: Using f-strings to inject variables into code templates
2. **Function Composition**: Building complex code by composing smaller generator functions
3. **Incremental Assembly**: Building modules piece by piece rather than all at once
4. **Inspection-based Generation**: Using Python's `inspect` module to copy existing functions

Let's examine these techniques in detail.

## 2. String Templates for Code Generation

The most fundamental technique in the Module Generator is the use of string templates to create code.

### 2.1 Basic String Templates with F-Strings

Python's f-strings provide a powerful way to inject variables into string templates:

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

This function demonstrates several key aspects of string templates:

1. **Variable Interpolation**: Inserting `property_name` and `python_type` into the template
2. **Nested Templates**: Using inner f-strings for dynamic error messages
3. **Multi-line Strings**: Using triple quotes for readable multi-line templates
4. **Indentation Control**: Managing indentation to match the target code structure

### 2.2 Handling String Escaping

When generating code with string literals, proper escaping is crucial:

```python
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
    # ... implementation ...
"""
```

Notice the escaped quotes (`\"\"\"`) in the docstring. This prevents the triple quotes from closing the outer string prematurely.

### 2.3 Conditional Code Generation

The Module Generator uses conditional expressions to adapt the generated code to different scenarios:

```python
text = f"""MATCH 
    (n:{label} 
    {'{' if props else ''} 
    {', '.join(f"{prop}: ${prop}" for prop in props)}
    {'}' if props else ''}) 
    RETURN n;"""
```

This example demonstrates:
1. Conditional inclusion of braces based on whether properties are present
2. Using list comprehensions and `join` to create comma-separated property expressions
3. Maintaining consistent formatting regardless of the conditions

### 2.4 Template Composition

Larger code blocks are composed from smaller templates:

```python
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
```

This approach:
1. Starts with a basic function template
2. Dynamically adds type checking code for each property
3. Appends the query execution and result processing code
4. Maintains proper indentation throughout

## 3. Generating Module Structure

The Module Generator creates entire Python modules, not just individual functions. This requires careful organization of the generated code.

### 3.1 Module Header

The module starts with a comprehensive header that includes documentation and imports:

```python
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
```

This sets up:
1. Module-level documentation with generation metadata
2. Required imports for the module to function

### 3.2 Configuration Section

The module includes a configuration section with connection details:

```python
# Connection details
_log('Adding connection details')
_append(filename, f'''
# Neo4j connection details
NEO4J_URI = "{profile['uri']}"
NEO4J_USERNAME = "{profile['username']}"
NEO4J_PASSWORD = "{profile['password']}"
NEO4J_DATABASE = "{profile['database']}"
''')
```

This encapsulates the connection parameters in module-level constants.

### 3.3 Utility Functions

Next, the module includes utility functions copied from the generator:

```python
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
```

This uses Python's `inspect.getsource()` function to copy the source code of existing functions, ensuring that the generated module has all the necessary supporting code.

### 3.4 Metadata Repository

The module includes the collected metadata as a JSON string:

```python
# Add metadata as a JSON string
_log('Adding metadata')
_append(filename, f'''
# Metadata about the Neo4j graph
METADATA = {json.dumps(metadata, indent=4)}
''')
```

This embeds the schema information directly in the module, enabling runtime introspection without querying the database.

### 3.5 Class Definitions

The core of the module consists of two classes, `Nodes` and `Edges`, with dynamically generated methods:

```python
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
```

This approach:
1. Creates class structures with detailed docstrings
2. Delegates method generation to specialized functions
3. Indents the generated methods appropriately

### 3.6 Module-Level Interfaces

Finally, the module provides convenient module-level interfaces:

```python
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
```

This provides:
1. Pre-instantiated class instances for immediate use
2. Convenience functions for common operations
3. Detailed documentation for each interface

## 4. Incremental File Building

Rather than generating the entire module in memory and writing it all at once, the Module Generator builds the file incrementally.

### 4.1 The Append Function

The core of this approach is the `_append` function:

```python
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
```

This function:
1. Opens the file in append mode
2. Writes the provided text with a trailing newline
3. Automatically closes the file when done

### 4.2 Specialized Append Functions

For certain types of content, specialized append functions are used:

```python
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
```

This ensures consistent formatting for specific types of content.

### 4.3 File Initialization

Before appending content, the Module Generator initializes the file:

```python
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
```

This ensures a clean slate for the new module.

### 4.4 Progress Logging

Throughout the generation process, the Module Generator logs its progress:

```python
def _log(msg):
    with open('modulegenerator.out', '+a') as log:
        log.write(f'{datetime.datetime.now()}: {msg}\n')
```

This provides visibility into the generation process and helps with debugging.

## 5. Generating Documented Code

One of the key features of the Module Generator is its ability to generate well-documented code.

### 5.1 Function Docstrings

Each generated function includes a comprehensive docstring:

```python
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
    # ... implementation ...
"""
```

The docstring follows the NumPy documentation style with:
1. A concise description of the function's purpose
2. Parameter descriptions with types and optional status
3. Return value description with type information

### 5.2 Class Docstrings

Similarly, classes include descriptive docstrings:

```python
_append(filename, f'''
class Nodes:
    """
    Interface for working with nodes in the Neo4j graph.
    Each method corresponds to a node label in the graph.
    """
{_generate_node_interface_functions(metadata)}
''')
```

These docstrings explain the purpose and organization of the class.

### 5.3 Code Comments

Generated code includes comments to explain implementation details:

```python
# Type check {property_name} (expected {python_type})
if "{property_name}" in props and props["{property_name}"] is not None:
    # ... implementation ...
    
# Construct and execute the query
query, params = Queries.node(label="{label}", **search_props)
```

These comments make the generated code more maintainable and easier to understand.

## 6. Building a Custom Code Generator

Now that we've examined the Module Generator's techniques, let's explore how to build a custom code generator.

### 6.1 Design Principles

Effective code generators follow several key principles:

1. **Separation of Concerns**: Divide the generation process into distinct phases
2. **Modularity**: Create small, focused generator functions that can be composed
3. **Adaptability**: Make the generator flexible enough to handle variations
4. **Clarity**: Generate code that is readable and well-documented
5. **Maintainability**: Organize the generator itself in a maintainable way

### 6.2 A Generator Framework

A simple generator framework might look like this:

```python
class CodeGenerator:
    def __init__(self, output_file):
        self.output_file = output_file
        self.ensure_clean_file()
        
    def ensure_clean_file(self):
        """Initialize an empty output file."""
        if os.path.exists(self.output_file):
            os.remove(self.output_file)
        
    def append(self, text):
        """Append text to the output file."""
        with open(self.output_file, 'a+') as file:
            file.write(f'{text}\n')
    
    def generate_header(self, module_name, description):
        """Generate a module header with documentation."""
        self.append(f'''"""
{module_name} - {description}

Generated on: {datetime.datetime.now().isoformat()}
"""''')
    
    def generate_imports(self, imports):
        """Generate import statements."""
        for module in imports:
            self.append(f'import {module}')
    
    def generate_class(self, name, docstring, methods):
        """Generate a class with methods."""
        self.append(f'''
class {name}:
    """
    {docstring}
    """
''')
        for method in methods:
            self.append(f'    {method}')
    
    def generate_function(self, name, params, body, docstring):
        """Generate a function with parameters and docstring."""
        param_str = ', '.join(params)
        self.append(f'''
def {name}({param_str}):
    """
    {docstring}
    """
{body}
''')
```

This framework provides a foundation for building custom code generators.

### 6.3 Example: Generating a Custom Neo4j Interface

Using this framework, we could create a specialized generator for Neo4j graph analytics:

```python
def generate_graph_analytics_module(database_uri, username, password, output_file):
    """Generate a module for Neo4j graph analytics."""
    # Create the generator
    generator = CodeGenerator(output_file)
    
    # Generate header and imports
    generator.generate_header("GraphAnalytics", "Neo4j Graph Analytics Utilities")
    generator.generate_imports([
        "neo4j",
        "datetime",
        "pandas as pd",
        "matplotlib.pyplot as plt",
        "networkx as nx"
    ])
    
    # Connect to the database and gather metadata
    driver = GraphDatabase.driver(database_uri, auth=(username, password))
    with driver.session() as session:
        # Get node counts by label
        result = session.run("CALL db.labels() YIELD label RETURN label")
        labels = [record["label"] for record in result]
        
        # Generate centrality analysis functions
        for label in labels:
            # Generate a function for analyzing node centrality
            function_name = f"analyze_{label.lower()}_centrality"
            params = ["limit=100", "centrality_type='degree'"]
            docstring = f"Analyze the centrality of {label} nodes in the graph.\n\n" \
                        f"Parameters:\n" \
                        f"    limit: The maximum number of nodes to analyze\n" \
                        f"    centrality_type: The type of centrality to calculate ('degree', 'betweenness', or 'closeness')\n\n" \
                        f"Returns:\n" \
                        f"    A pandas DataFrame with centrality metrics"
            
            # Function body with Cypher query and processing
            body = f"""    # Validate centrality type
    valid_types = ['degree', 'betweenness', 'closeness']
    if centrality_type not in valid_types:
        raise ValueError(f"centrality_type must be one of {{valid_types}}, got {{centrality_type}}")
    
    # Construct the query based on centrality type
    if centrality_type == 'degree':
        query = \"\"\"
            MATCH (n:{label})
            WITH n, size((n)--()) AS degree
            RETURN n.name AS name, degree
            ORDER BY degree DESC
            LIMIT $limit
        \"\"\"
    elif centrality_type == 'betweenness':
        query = \"\"\"
            CALL gds.betweenness.stream('{{label}}')
            YIELD nodeId, score
            MATCH (n) WHERE id(n) = nodeId AND n:{label}
            RETURN n.name AS name, score
            ORDER BY score DESC
            LIMIT $limit
        \"\"\"
    else:  # closeness
        query = \"\"\"
            CALL gds.closeness.stream('{{label}}')
            YIELD nodeId, score
            MATCH (n) WHERE id(n) = nodeId AND n:{label}
            RETURN n.name AS name, score
            ORDER BY score DESC
            LIMIT $limit
        \"\"\"
    
    # Execute the query
    with GraphDatabase.driver("{database_uri}", auth=("{username}", "{password}")) as driver:
        with driver.session() as session:
            result = session.run(query, {{"limit": limit}})
            data = [record for record in result]
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Create a visualization
    plt.figure(figsize=(10, 6))
    plt.bar(df['name'], df['degree' if centrality_type == 'degree' else 'score'])
    plt.title(f"{label} {centrality_type.capitalize()} Centrality")
    plt.xlabel("Node")
    plt.ylabel(f"{centrality_type.capitalize()} Value")
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    return df"""
            
            generator.generate_function(function_name, params, body, docstring)
        
        # Generate graph visualization function
        vis_function = """
def visualize_graph(label=None, limit=100):
    \"\"\"
    Visualize a subgraph from Neo4j.
    
    Parameters:
        label: Node label to filter by (optional)
        limit: Maximum number of nodes to include
        
    Returns:
        A NetworkX graph object
    \"\"\"
    # Construct the query
    if label:
        query = f\"\"\"
            MATCH (n:{label})-[r]-(m)
            RETURN n, r, m
            LIMIT $limit
        \"\"\"
    else:
        query = \"\"\"
            MATCH (n)-[r]-(m)
            RETURN n, r, m
            LIMIT $limit
        \"\"\"
    
    # Execute the query
    with GraphDatabase.driver("{database_uri}", auth=("{username}", "{password}")) as driver:
        with driver.session() as session:
            result = session.run(query, {"limit": limit})
            
            # Create NetworkX graph
            G = nx.Graph()
            
            # Process results
            for record in result:
                source = record["n"]
                target = record["m"]
                relationship = record["r"]
                
                # Add nodes
                G.add_node(id(source), label=list(source.labels)[0], name=source.get("name", f"Node {id(source)}"))
                G.add_node(id(target), label=list(target.labels)[0], name=target.get("name", f"Node {id(target)}"))
                
                # Add edge
                G.add_edge(id(source), id(target), type=relationship.type)
    
    # Visualize
    plt.figure(figsize=(12, 12))
    pos = nx.spring_layout(G)
    
    # Draw nodes
    node_labels = {node_id: G.nodes[node_id]["name"] for node_id in G.nodes}
    nx.draw_networkx_nodes(G, pos, node_size=700, node_color="lightblue")
    nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=8)
    
    # Draw edges
    edge_labels = {(source, target): G.edges[source, target]["type"] for source, target in G.edges}
    nx.draw_networkx_edges(G, pos, width=1.0, alpha=0.7)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=6)
    
    plt.axis("off")
    plt.tight_layout()
    plt.show()
    
    return G
"""
        generator.append(vis_function)
    
    # Close the driver
    driver.close()
    
    return output_file
```

This example demonstrates a custom generator that:
1. Connects to a Neo4j database
2. Discovers node labels through introspection
3. Generates specialized functions for centrality analysis of each node type
4. Creates a general graph visualization function
5. Organizes the generated code into a cohesive module

## 7. Exercises

Now that we've explored the code generation techniques of the Module Generator, let's apply this knowledge with some exercises.

### Exercise 1: Enhanced Docstring Generator

Extend the Module Generator to create more detailed docstrings that include:
- Examples of how to use each function
- Descriptions of common errors and how to handle them
- References to related functions for cross-navigation

### Exercise 2: Custom Template Engine

Create a more sophisticated template engine for code generation that:
- Supports named placeholders (e.g., `{{property_name}}`)
- Handles conditional sections (e.g., `{{#if has_properties}}...{{/if}}`)
- Includes template inheritance for common patterns

### Exercise 3: Code Generator for Graph Algorithms

Design a code generator that creates specialized functions for common graph algorithms:
- Shortest path calculation
- Community detection
- Centrality measures
- Pattern matching

## 8. Summary

In this notebook, we've explored the code generation techniques employed by the Module Generator. We've seen how:

1. String templates with f-strings provide a powerful foundation for code generation
2. Incremental file building enables efficient module creation
3. Proper documentation is integrated into the generation process
4. Custom generators can be built for specialized needs
5. Code generation reduces repetition and ensures consistency

These techniques enable the Module Generator to create type-safe, well-documented interfaces for Neo4j databases, enhancing developer productivity and reducing errors.

## 9. Further Reading

- [Python String Formatting](https://realpython.com/python-f-strings/)
- [Python inspect Module](https://docs.python.org/3/library/inspect.html)
- [Code Generation Patterns](https://en.wikipedia.org/wiki/Code_generation_(compiler))
- [Template Engines in Python](https://realpython.com/primer-on-jinja-templating/)
- [Neo4j Python Driver API](https://neo4j.com/docs/api/python-driver/current/api.html)