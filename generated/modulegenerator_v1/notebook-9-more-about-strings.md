# Notebook 9: More About Strings

## Learning Objectives

By the end of this notebook, you will be able to:
1. Understand advanced string operations used in the Module Generator
2. Apply string formatting techniques for code generation
3. Implement string manipulation for Cypher query construction
4. Handle escape sequences and multiline strings effectively
5. Create your own string templates for generating code

## 1. Introduction to Advanced String Operations

Strings are fundamental to the Module Generator, serving as both data containers and the building blocks of generated code. This notebook explores advanced string operations that enable powerful code generation.

### 1.1 The Role of Strings in Code Generation

In the Module Generator, strings play several crucial roles:

1. **Templates for Generated Code**: Skeleton structures filled with dynamic content
2. **Cypher Queries**: Database operations expressed as parameterized strings
3. **Documentation**: Function and module documentation in docstrings
4. **Metadata**: Names and identifiers from the database schema
5. **Error Messages**: Clear communication of validation issues

Understanding advanced string operations is essential for effective code generation.

### 1.2 String Representation in Python

Python supports several string representations:

- **Single Quotes**: `'text'`
- **Double Quotes**: `"text"`
- **Triple Single Quotes**: `'''multiline text'''`
- **Triple Double Quotes**: `"""multiline text"""`
- **Raw Strings**: `r"text with \n literal backslashes"`
- **F-strings**: `f"formatted {variable} text"`

The Module Generator uses all of these forms for different purposes, selecting the most appropriate representation for each context.

## 2. String Formatting in the Module Generator

The Module Generator employs various string formatting techniques to create dynamic content.

### 2.1 F-Strings for Variable Interpolation

F-strings provide a concise syntax for embedding variables within strings:

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

This function demonstrates several f-string techniques:

1. **Simple Variable Insertion**: `{property_name}` and `{python_type}`
2. **Escaped Braces in Nested F-strings**: `{{type(props['{property_name}']).__name__}}`
3. **Multiline F-strings**: Using triple quotes for complex templates
4. **String Literals Within F-strings**: `"{property_name}"` creates a string literal in the generated code

F-strings provide a readable way to create dynamic strings without complex concatenation or formatting operations.

### 2.2 String Joining for Code Assembly

The Module Generator uses string joining to assemble code fragments:

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

This approach:
1. Creates a list of function definitions as strings
2. Joins them with newlines to create properly separated code
3. Returns the combined result as a single string

String joining is more efficient and readable than concatenation, especially for many fragments.

### 2.3 Conditional Formatting

The Module Generator includes conditional elements in formatted strings:

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

This function demonstrates conditional formatting:
1. `{'{' if props else ''}` includes an opening brace only if properties exist
2. `{', '.join(f"{prop}: ${prop}" for prop in props)}` creates a comma-separated list of property constraints
3. `{'}' if props else ''}` includes a closing brace only if properties exist

This approach generates correctly formatted Cypher queries for both simple and property-filtered node lookups.

## 3. String Manipulation for Query Construction

The Module Generator performs various string manipulations to construct Cypher queries.

### 3.1 Building Parameterized Queries

Parameterized queries enhance security and performance:

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

This function:
1. Includes the label directly in the query string
2. Uses parameter references (`${prop}`) for property values
3. Returns both the query text and parameter dictionary

This approach prevents Cypher injection attacks by separating query structure from data values.

### 3.2 Handling Special Characters

Cypher queries may contain special characters that need careful handling:

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

This function carefully:
1. Inserts the label directly into the query
2. Conditionally includes a LIMIT clause with proper spacing
3. Uses backticks for identifiers containing special characters (in other parts of the code)

### 3.3 Multi-Line Query Formatting

For complex queries, the Module Generator uses multi-line formatting:

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

This approach:
1. Uses triple quotes for multi-line strings
2. Structures the query with clear indentation and line breaks
3. Places each clause on a separate line for readability

Multi-line formatting makes complex queries more maintainable and easier to debug.

## 4. Docstring Generation

The Module Generator creates docstrings for all generated functions, providing clear documentation.

### 4.1 Docstring Structure

Generated functions include comprehensive docstrings:

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

This docstring follows the NumPy documentation format:
1. A concise description in the first line
2. Parameter descriptions with types and optional status
3. Return value description with type information

The escaped triple quotes (`\"\"\"`) prevent conflicts with the outer triple quotes.

### 4.2 Dynamic Docstring Content

Docstrings include dynamic content based on schema information:

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

The label from the database schema is included in the function description, providing context-specific documentation.

### 4.3 Module-Level Documentation

The Module Generator also creates module-level documentation:

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
```

This documentation includes:
1. A description of the module's purpose
2. Generation metadata (timestamp, version)
3. Dependency information

This documentation helps users understand the origin and purpose of the generated code.

## 5. String Escaping and Special Characters

The Module Generator handles various string escaping scenarios to ensure correct code generation.

### 5.1 Escaping in String Literals

When generating string literals, the Module Generator handles escaping:

```python
# Type check {property_name} (expected {python_type})
if "{property_name}" in props and props["{property_name}"] is not None:
    # ... type checking code ...
```

The generated code includes a string literal with the property name, properly escaped with quotes.

### 5.2 Nested String Formatting

The Module Generator uses nested string formatting for complex scenarios:

```python
raise TypeError(f"Property {property_name} must be of type {python_type}, got {{type(props['{property_name}']).__name__}}")
```

This generated code includes:
1. An outer f-string with `{property_name}` and `{python_type}` substitutions from the generator
2. An inner f-string with `{type(props['{property_name}']).__name__}` for runtime evaluation
3. Double braces `{{` and `}}` to escape the inner braces

Nested formatting enables dynamic content at both generation time and runtime.

### 5.3 Handling Special Characters in Identifiers

The Module Generator handles special characters in database identifiers:

```python
function_name = label.lower().replace(':', '_').replace('-', '_')
```

This code:
1. Converts labels to lowercase for Python naming conventions
2. Replaces colons and hyphens with underscores for valid Python identifiers

This approach ensures that database labels can be translated to valid Python function names.

## 6. String Templates for Code Generation

The Module Generator employs string templates to create consistent code patterns.

### 6.1 Function Templates

Function generation follows a consistent template:

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
1. Starts with a function skeleton including signature and docstring
2. Dynamically adds type checking code for each property
3. Completes the function with query execution and result processing

The template ensures consistent structure across all generated functions.

### 6.2 Class Templates

Class generation also follows a template:

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
1. Creates class skeletons with docstrings
2. Delegates method generation to specialized functions
3. Indents the generated methods appropriately

The template ensures that classes have consistent structure and documentation.

### 6.3 Template Composition

The Module Generator composes templates to build complex structures:

```python
# Module structure
_append(filename, module_header)
_append_imports(filename, imports)
_append(filename, connection_details)
_append(filename, utility_functions)
_append(filename, queries_class)
_append(filename, metadata_json)
_append(filename, nodes_class)
_append(filename, edges_class)
_append(filename, module_interfaces)
```

This approach:
1. Breaks the module into logical sections
2. Assembles the sections in a specific order
3. Creates a cohesive final module

Template composition enables complex structures to be built from simpler components.

## 7. String Representation of Generated Code

The Module Generator ensures that generated code is correctly formatted and indented.

### 7.1 Indentation Management

Proper indentation is crucial for Python code:

```python
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

This function:
1. Includes appropriate indentation in the template string
2. Ensures that the generated code will have correct indentation when inserted into the function body

Proper indentation makes the generated code readable and syntactically correct.

### 7.2 Whitespace Management

The Module Generator manages whitespace for clean code presentation:

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

This function carefully manages whitespace:
1. Adds appropriate spacing around operators and punctuation
2. Inserts newlines and indentation for query readability
3. Conditionally adjusts spacing based on whether properties are present

These details ensure that the generated code and queries are clean and readable.

### 7.3 Comment Placement

The Module Generator includes comments to explain the generated code:

```python
# Type check {property_name} (expected {python_type})
if "{property_name}" in props and props["{property_name}"] is not None:
    # ... type checking code ...

# Construct and execute the query
query, params = Queries.node(label="{label}", **search_props)
results = _query(query, params)
```

These comments:
1. Describe the purpose of code sections
2. Provide context for understanding the implementation
3. Follow consistent placement and formatting conventions

Proper comments enhance the readability and maintainability of the generated code.

## 8. Exercises

Now that we've explored string operations in the Module Generator, let's apply this knowledge with some exercises.

### Exercise 1: Enhanced Docstring Generator

Create a function that generates enhanced function docstrings with:
- Example usage
- Common errors and solutions
- References to related functions
- Parameter constraints and valid values

```python
def generate_enhanced_docstring(function_name, description, parameters, returns, examples=None, errors=None, related=None):
    """
    Generate an enhanced docstring for a function.
    
    Parameters
    ----------
    function_name: str
        The name of the function
    description: str
        A brief description of the function
    parameters: Dict[str, Tuple[str, str, bool]]
        Dictionary mapping parameter names to tuples of (type, description, required)
    returns: Tuple[str, str]
        A tuple of (return_type, return_description)
    examples: List[Tuple[str, str]], optional
        List of (example_code, example_description) tuples
    errors: List[Tuple[str, str]], optional
        List of (error_type, error_description) tuples
    related: List[str], optional
        List of related function names
        
    Returns
    -------
    str:
        A formatted docstring
    """
    # Implementation here
```

### Exercise 2: Query Template Builder

Create a function that builds Cypher query templates for common graph patterns:

```python
def build_query_template(pattern_type, with_properties=True):
    """
    Generate a Cypher query template for a common graph pattern.
    
    Parameters
    ----------
    pattern_type: str
        The type of pattern ('node', 'relationship', 'path', 'subgraph')
    with_properties: bool, optional
        Whether to include property placeholders
        
    Returns
    -------
    str:
        A Cypher query template with placeholders
    """
    # Implementation here
```

### Exercise 3: Code Generator DSL

Design a simple domain-specific language (DSL) for code generation that makes templates more readable:

```python
def parse_template(template, context):
    """
    Parse a template with a simplified syntax and generate code.
    
    Parameters
    ----------
    template: str
        Template with placeholders like {{variable}} and control structures
    context: Dict[str, Any]
        Variables to substitute in the template
        
    Returns
    -------
    str:
        Generated code
    """
    # Example template:
    """
    def {{function_name}}({{#each params}}{{name}}{{#if default}}={{default}}{{/if}}{{#unless @last}}, {{/unless}}{{/each}}):
        \"\"\"
        {{description}}
        
        {{#if params.length}}
        Parameters
        ----------
        {{#each params}}
        {{name}}: {{type}}
            {{description}}
        {{/each}}
        {{/if}}
        
        Returns
        -------
        {{return_type}}:
            {{return_description}}
        \"\"\"
        {{body}}
    """
    # Implementation here
```

## 9. Summary

In this notebook, we've explored advanced string operations in the Module Generator. We've seen how:

1. F-strings provide powerful variable interpolation for dynamic content
2. String joining and conditional formatting enable complex code generation
3. Parameterized queries enhance security and performance
4. Proper handling of escaping and special characters ensures correct output
5. Consistent templates create predictable, maintainable code

These string techniques are essential for code generation, allowing the Module Generator to transform database schema information into functional Python interfaces.

## 10. Further Reading

- [Python F-Strings](https://docs.python.org/3/reference/lexical_analysis.html#f-strings)
- [Python String Methods](https://docs.python.org/3/library/stdtypes.html#string-methods)
- [Documentation Styles in Python](https://realpython.com/documenting-python-code/)
- [Code Generation Techniques](https://realpython.com/python-string-formatting/)
- [Template Engines in Python](https://realpython.com/primer-on-jinja-templating/)