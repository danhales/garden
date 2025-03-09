# Notebook 0: Prerequisites for Module Generator

## Introduction

This notebook provides a concise review of core Python programming concepts necessary for understanding the G.A.R.D.E.N. Module Generator. Each section addresses a fundamental concept with an example drawn directly from the Module Generator source code. Understanding these building blocks will enable you to effectively analyze and extend the Module Generator in subsequent notebooks.

## 1. Introduction to Computers and Programming

Programming fundamentally involves instructing computers to perform tasks through carefully crafted instructions. The Module Generator exemplifies this by creating structured, reusable code that translates database queries into Python objects.

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
```

This function represents the core purpose of the Module Generator: to transform instructions (parameters) into a complete Python module through a series of computational steps. It demonstrates how programming abstracts complex operations into reusable components with defined inputs and outputs.

## 2. Input, Processing, and Output

The Input-Processing-Output (IPO) model forms the foundation of most computational tasks. The Module Generator extensively utilizes this paradigm to gather database information, transform it into code, and produce usable Python modules.

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

This function demonstrates the IPO model through:
- **Input**: Accepts a filename and text content
- **Processing**: Opens the specified file in append mode
- **Output**: Writes the processed text to the file system

The operation transforms initial inputs into a meaningful output (modified file) through a defined sequence of operations, demonstrating how programs manage data flow.

## 3. Simple Functions

Functions encapsulate reusable logic, accepting inputs, performing operations, and returning results. They form the building blocks of modular code.

```python
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
```

This function exemplifies a well-defined, single-purpose operation that:
1. Calls another function to obtain query components
2. Executes the query through the `_query` function
3. Extracts the timestamp from the result
4. Formats and returns it as an ISO-formatted string

The function maintains a clear responsibility boundary, demonstrating the principle of encapsulation while providing a simple interface for obtaining server timestamps.

## 4. Decision Structures and Boolean Logic

Decision structures enable programs to execute different code paths based on conditional expressions, creating dynamic behavior governed by Boolean logic.

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

This function demonstrates multiple layers of decision logic:
1. It first checks if the input is already a dictionary
2. If so, it evaluates whether it has the expected structure
3. If not, it attempts extraction with additional conditional checks
4. As an alternative path, it tries to handle Neo4j Node objects
5. It provides fallback behavior for exceptional cases

The nested conditionals and Boolean expressions create a robust algorithm capable of standardizing different input formats into a consistent output structure, highlighting how decision structures enable adaptive program behavior.

## 5. Repetition Structures

Repetition structures (loops) allow programs to execute operations multiple times, either with a predetermined count or until a condition is met.

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

This function showcases nested repetition structures:
1. The outer loop iterates through each result in the query response
2. For each result, inner loops process start and end labels
3. The loops populate sets to eliminate duplicates

This pattern efficiently transforms a collection of database results into consolidated, unique lists of node labels, demonstrating how repetition structures enable systematic data processing and aggregation.

## 6. Value-Returning Functions and Modules

Value-returning functions process inputs and produce outputs, while modules organize related functions into cohesive units that can be imported and reused across programs.

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

This function demonstrates:
1. A complex value-returning operation that orchestrates multiple database queries
2. The composition of results from other specialized functions
3. The construction of a structured data object (dictionary) as the return value

The Module Generator itself exemplifies the module concept as a self-contained unit of functionality with a clearly defined public interface (`generate_module`) supported by private internal functions (denoted with `_`).

## 7. Files and Exceptions

File operations enable programs to persist and retrieve data, while exception handling provides mechanisms for managing errors and unexpected conditions.

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

This function demonstrates:
1. Resource management through the `with` statement, ensuring proper session handling
2. Implicit exception propagation (any errors in query execution will be passed up the call stack)

The Module Generator uses file operations extensively to generate output modules, while employing exception handling to gracefully manage database connection issues, schema inconsistencies, and other potential errors.

## 8. Lists and Tuples

Lists and tuples provide ordered collection capabilities, with lists offering mutability for dynamic operations and tuples ensuring immutability for fixed structures.

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

This function demonstrates:
1. The use of tuples for unpacking multiple return values from a function call
2. Accessing and returning a list retrieved from a database query result

The function returns a list of labels that will be used for further processing in the Module Generator, showcasing how collections facilitate the handling of multiple related values as a single unit.

## 9. More About Strings

Strings enable text manipulation, with Python providing extensive capabilities for formatting, concatenation, and pattern-based operations.

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

This function showcases advanced string manipulation:
1. F-strings for embedding variables within template text
2. Multi-line string literals for complex code generation
3. Nested string interpolation to create dynamic Python code
4. Escaping of special characters within string literals

The Module Generator relies extensively on string operations to transform database schema information into functional Python code, demonstrating how strings serve as both data and program components.

## 10. Dictionaries and Sets

Dictionaries provide key-value mapping capabilities, while sets offer unique collection functionality with mathematical set operations.

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

This function demonstrates:
1. Dictionary initialization with `dict()`
2. Conditional key existence checking and dynamic key creation
3. Construction of nested data structures (dictionaries containing lists of dictionaries)
4. Dictionary aggregation based on a common property

The Module Generator uses dictionaries extensively to organize and transform schema information, leveraging their efficient key-based lookup capabilities for data organization and retrieval.

## 11. Classes and Object-Oriented Programming

Object-oriented programming organizes code into classes with attributes (data) and methods (functions), enabling encapsulation, inheritance, and polymorphism.

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
    
    # Other methods omitted for brevity
```

This class demonstrates:
1. A collection of related static methods for query generation
2. Method implementation based on common patterns (returning query text and parameters)
3. Documentation of method behavior through docstrings
4. Parameterized query construction with safeguards against injection

The Module Generator uses classes to organize related functionality, both in its internal structure and in the generated output modules, showing how object-oriented design supports code organization and encapsulation.

## 12. Inheritance

Inheritance enables the creation of class hierarchies, where derived classes inherit attributes and methods from base classes, allowing specialization and code reuse.

In cases where the Module Generator doesn't explicitly demonstrate inheritance, we'll review a canonical example at a lower complexity level.

```python
# A canonical example of inheritance (not from Module Generator)

class DatabaseConnector:
    def __init__(self, uri, username, password):
        self.uri = uri
        self.username = username
        self.password = password
    
    def connect(self):
        print(f"Connecting to {self.uri}")
    
    def disconnect(self):
        print("Disconnecting")

class Neo4jConnector(DatabaseConnector):
    def __init__(self, uri, username, password, database="neo4j"):
        super().__init__(uri, username, password)
        self.database = database
    
    def connect(self):
        super().connect()
        print(f"Using Neo4j database: {self.database}")
    
    def execute_cypher(self, query):
        print(f"Executing: {query}")
```

This example demonstrates:
1. A base class (`DatabaseConnector`) with core functionality
2. A derived class (`Neo4jConnector`) that inherits from the base class
3. Method overriding to specialize behavior (`connect`)
4. Constructor chaining with `super().__init__`
5. Extension with additional methods (`execute_cypher`)

Inheritance enables specialized behavior while maintaining common functionality, supporting the principle of "is-a" relationships between classes.

## 13. Recursion

Recursion involves functions that call themselves to solve problems through self-similar subproblems, often providing elegant solutions for tree structures, graph traversals, and divide-and-conquer algorithms.

Though the Module Generator doesn't explicitly use recursion, we can examine a canonical example at a lower complexity level.

```python
# A canonical example of recursion (not from Module Generator)

def traverse_graph(node, visited=None):
    if visited is None:
        visited = set()
    
    # Process current node
    print(f"Visiting node: {node}")
    visited.add(node)
    
    # Get connected nodes
    connections = get_connections(node)
    
    # Recursively visit unvisited connections
    for connected_node in connections:
        if connected_node not in visited:
            traverse_graph(connected_node, visited)
```

This example demonstrates:
1. A function that calls itself with modified parameters
2. A base case (when all connections have been visited)
3. Parameter accumulation through the call stack (tracking visited nodes)
4. Default parameter initialization to establish initial state

Recursion is particularly valuable for graph databases like Neo4j, where traversing relationships between nodes often follows recursive patterns.

## Resources for Further Learning

Here's a curated list of URLs to help you dive deeper into Python and Jupyter:

1. Python Official Documentation
   - https://docs.python.org/3/
   - https://docs.python.org/3/tutorial/index.html
   - https://docs.python.org/3/library/index.html

2. Jupyter Documentation
   - https://jupyter.org/documentation
   - https://jupyter-notebook.readthedocs.io/en/stable/
   - https://jupyter.org/install

3. Neo4j and Python
   - https://neo4j.com/docs/api/python-driver/current/
   - https://neo4j.com/developer/python/
   - https://neo4j.com/docs/cypher-manual/current/

4. Interactive Learning
   - https://www.python.org/shell/
   - https://jupyter.org/try
   - https://neo4j.com/sandbox/

5. Advanced Python Concepts
   - https://docs.python.org/3/reference/datamodel.html
   - https://docs.python.org/3/howto/functional.html
   - https://docs.python.org/3/library/typing.html

These resources provide official documentation and interactive environments to deepen your understanding of the concepts covered in this notebook.
