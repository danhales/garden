# Notebook 4: Type Mapping and Validation

## Learning Objectives

By the end of this notebook, you will be able to:
1. Understand the differences between Neo4j and Python type systems
2. Implement effective type mapping strategies between database and application types
3. Generate type validation code for Neo4j properties
4. Handle type conversion and error cases gracefully
5. Extend the Module Generator's type system with custom mappings

## 1. Introduction to Type Systems

A type system defines the categories of values that can be manipulated in a programming language or database. Effective integration between Neo4j and Python requires mapping between their respective type systems.

### 1.1 The Neo4j Type System

Neo4j's type system includes the following basic types:

- **String**: Textual data
- **Integer**: Whole numbers
- **Float**: Decimal numbers
- **Boolean**: True/false values
- **Point**: Spatial coordinates
- **Date**: Calendar date without time
- **Time**: Time of day without date
- **DateTime**: Combined date and time
- **Duration**: Time intervals
- **List**: Ordered collection of values
- **Map**: Key-value collection

### 1.2 The Python Type System

Python's type system includes corresponding types:

- **str**: Textual data
- **int**: Whole numbers
- **float**: Decimal numbers
- **bool**: True/false values
- **datetime.date**: Calendar date
- **datetime.time**: Time of day
- **datetime.datetime**: Combined date and time
- **list**: Ordered collection
- **dict**: Key-value collection
- **set**: Unordered collection of unique values
- **tuple**: Immutable ordered collection

### 1.3 The Type Mapping Challenge

Creating a seamless integration between these type systems requires addressing several challenges:

1. **Semantic Equivalence**: Ensuring that mapped types preserve the same meaning
2. **Conversion Fidelity**: Maintaining accuracy during type conversions
3. **Default Values**: Handling missing or null values appropriately
4. **Collection Contents**: Managing types within collections
5. **Validation**: Confirming type correctness before database operations

Let's examine how the Module Generator addresses these challenges.

## 2. The Module Generator's Type Mapping Strategy

The Module Generator employs a comprehensive strategy for mapping between Neo4j and Python types.

### 2.1 The Core Type Mapping

The foundation of this strategy is the type mapping dictionary:

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

This mapping establishes the correspondence between Neo4j types (as identified by the `apoc.meta.type()` function) and their Python equivalents.

### 2.2 Type Discovery Through Introspection

The Module Generator doesn't rely on static type declarations. Instead, it examines actual data in the database to infer types:

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

This approach captures the actual types in use, which may vary from theoretical declarations or documentation.

### 2.3 Handling Special Types

Some Neo4j types require special handling:

#### Temporal Types

Neo4j's temporal types (Date, Time, DateTime, Duration) are mapped to Python's datetime module types:

```python
'DATE': 'datetime.date',
'DATETIME': 'datetime.datetime',
```

#### Collection Types

Neo4j's List and Map types are mapped to Python's list and dict types:

```python
'LIST': 'list',
'MAP': 'dict',
```

However, this simple mapping doesn't capture the types of items within the collections, which may require additional validation.

#### Default Fallback

For any unknown or unrecognized Neo4j type, the Module Generator defaults to Python's generic `object` type:

```python
python_type = type_mapping.get(property_type, 'object')
```

This ensures that the generated code can handle any property, even if its type isn't explicitly recognized.

## 3. Generating Type Validation Code

The Module Generator doesn't just map types—it generates code to enforce these types at runtime.

### 3.1 Basic Type Validation

The core of the type validation logic is the `isinstance` check:

```python
if not isinstance(props["{property_name}"], {python_type}):
```

This check verifies that the provided value matches the expected Python type.

### 3.2 Type Conversion Attempts

If the value doesn't match the expected type, the Module Generator attempts to convert it:

```python
try:
    # Attempt to convert
    props["{property_name}"] = {python_type}(props["{property_name}"])
except:
    raise TypeError(f"Property {property_name} must be of type {python_type}, got {{type(props['{property_name}']).__name__}}")
```

This approach handles common conversion scenarios, such as strings to numbers or numbers to strings.

### 3.3 Error Reporting

If conversion fails, the Module Generator raises a clear error message that identifies:
- The property name
- The expected type
- The actual type

This detailed error reporting helps developers quickly identify and fix type mismatches.

### 3.4 Handling Null Values

The Module Generator carefully handles null values:

```python
if "{property_name}" in props and props["{property_name}"] is not None:
```

This condition ensures that:
1. Type checking only applies to properties actually present in the input
2. Null values (None in Python) bypass type checking

This approach allows for optional properties and null values, which are common in graph databases.

## 4. Type Validation in Generated Functions

The type validation code is integrated into the generated node and relationship interface functions.

### 4.1 Node Interface Functions

For node interface functions, type validation is applied to each known property:

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

The generated function includes:
1. Type checking for each known property
2. Query construction with validated properties
3. Query execution
4. Result conversion

### 4.2 Relationship Interface Functions

A similar approach is applied to relationship interface functions:

```python
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