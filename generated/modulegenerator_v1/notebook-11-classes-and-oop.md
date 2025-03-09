# Notebook 11: Classes and Object-Oriented Programming

## Learning Objectives

By the end of this notebook, you will be able to:
1. Understand how the Module Generator uses classes to organize code
2. Analyze the object-oriented design principles in the generated modules
3. Implement your own class-based interfaces for Neo4j
4. Apply encapsulation, abstraction, and interface design techniques
5. Design effective class hierarchies for graph data representation

## 1. Introduction to Object-Oriented Programming in Python

Object-oriented programming (OOP) is a programming paradigm that organizes code around data (objects) rather than functions and logic. In the Module Generator, OOP principles guide both the generator's design and the structure of the generated code.

### 1.1 OOP Core Concepts

Object-oriented programming revolves around several key concepts:

- **Classes**: Blueprints for creating objects that define attributes and methods
- **Objects**: Instances of classes that contain data and behavior
- **Encapsulation**: Bundling of data and methods that operate on that data
- **Abstraction**: Hiding implementation details and exposing only relevant interfaces
- **Inheritance**: Creating new classes based on existing classes
- **Polymorphism**: Providing a unified interface to different types of objects

The Module Generator employs these concepts to create maintainable, extensible code.

### 1.2 Classes in the Module Generator

The Module Generator uses classes in two primary ways:

1. **As Organizational Units**: The `Queries` class organizes related query-building functions
2. **In Generated Code**: The `Nodes` and `Edges` classes provide structured interfaces to graph data

Understanding these class structures provides insights into effective OOP design for Neo4j applications.

## 2. The Queries Class

The Module Generator uses the `Queries` class to organize query generation functions.

### 2.1 Class Structure

The `Queries` class serves as a container for related functions:

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
    
    # ... additional query methods ...
```

This class:
1. Groups related query generation functions under a common namespace
2. Provides a consistent interface for building different types of queries
3. Separates query construction from query execution

Although the functions are static (no `self` parameter), the class structure enhances organization and discoverability.

### 2.2 Static Method Pattern

The `Queries` class uses a static method pattern, where methods don't depend on instance state:

```python
def node_labels():
    text = 'CALL db.labels() YIELD label RETURN collect(label) AS labels;'
    params = None
    return text, params
```

This method:
1. Doesn't include a `self` parameter (it's implicitly static)
2. Can be called directly on the class without creating an instance
3. Focuses on a single responsibility (generating a specific query)

While not fully utilizing OOP capabilities, this pattern provides organizational benefits without the overhead of instance management.

### 2.3 Method Consistency

The `Queries` class maintains consistent method signatures:

```python
def server_timestamp():
    text = 'RETURN datetime() AS timestamp;'
    params = None
    return text, params
```

```python
def node(label, **props):
    # ... query construction ...
    return text, params
```

All methods:
1. Return a tuple of (query_text, query_params)
2. Accept parameters specific to their query type
3. Focus on query construction, not execution

This consistency creates a predictable interface across all query types.

## 3. Generated Classes in Output Modules

The Module Generator creates class-based interfaces in the generated modules.

### 3.1 The Nodes Class

The generated `Nodes` class provides entity-specific interfaces:

```python
class Nodes:
    """
    Interface for working with nodes in the Neo4j graph.
    Each method corresponds to a node label in the graph.
    """
    def person(self, uuid=None, **props):
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
        
    # ... methods for other node labels ...
```

This class:
1. Provides a method for each node label in the database
2. Handles parameter validation and type checking
3. Abstracts query construction and execution details

The class structure organizes node-related functionality in a logical, discoverable way.

### 3.2 The Edges Class

Similarly, the `Edges` class provides relationship-specific interfaces:

```python
class Edges:
    """
    Interface for working with relationships in the Neo4j graph.
    Each method corresponds to a relationship type in the graph.
    """
    def knows(self, uuid=None, **props):
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
        
    # ... methods for other relationship types ...
```

This class follows the same pattern as the `Nodes` class, providing a parallel structure for working with relationships.

### 3.3 Module-Level Interface

The generated module includes pre-instantiated class instances:

```python
# Create the interface instances
nodes = Nodes()
edges = Edges()
```

This approach:
1. Provides immediate access to the class methods without explicit instantiation
2. Creates a clean, intuitive interface for users of the module
3. Follows the singleton pattern for shared functionality

Users can simply import the module and access the methods through these instances.

## 4. OOP Design Principles in the Module Generator

The Module Generator's use of classes reflects several OOP design principles.

### 4.1 Single Responsibility Principle

Each class has a well-defined responsibility:

- `Queries`: Generating parameterized Cypher queries
- `Nodes`: Finding and manipulating nodes
- `Edges`: Finding and manipulating relationships

This separation of concerns enhances maintainability and testability.

### 4.2 Interface Segregation

The generated classes provide segregated interfaces:

- `Nodes`: Methods specifically for node operations
- `Edges`: Methods specifically for relationship operations

This segregation allows users to focus on the relevant interface for their task.

### 4.3 Open/Closed Principle

The Module Generator's design is open for extension but closed for modification:

- New query types can be added to the `Queries` class without changing existing queries
- New node or relationship types automatically generate new methods without changing the class structure

This extensibility accommodates evolving database schemas.

### 4.4 Dependency Inversion

While not fully implemented, the Module Generator shows elements of dependency inversion:

- Higher-level node and relationship methods depend on abstract query interfaces
- Database details are abstracted behind utility functions

This approach reduces coupling between components.

## 5. Class Generation in the Module Generator

The Module Generator uses string templates to create classes in the generated modules.

### 5.1 Class Template Generation

The framework for class generation is straightforward:

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
```

This code:
1. Creates a class definition with appropriate documentation
2. Delegates method generation to a specialized function
3. Embeds the generated methods within the class

The template provides a consistent structure for all generated classes.

### 5.2 Method Generation

The methods within each class are generated based on schema metadata:

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
    def {function_name}(self, uuid=None, **props):
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

This function:
1. Iterates through all node labels in the metadata
2. Generates a method for each label with appropriate documentation
3. Adds type checking for each property
4. Completes the method with query execution and result processing
5. Joins all methods into a single string

This approach dynamically generates methods based on the database schema.

### 5.3 Indentation Management

When generating classes, the Module Generator carefully manages indentation:

```python
function_code = f"""
    def {function_name}(self, uuid=None, **props):
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
```

Notice that:
1. The method definition is indented with four spaces (inside the class)
2. Method body lines are indented with eight spaces
3. Docstring content maintains appropriate indentation

Proper indentation ensures that the generated code is syntactically correct and readable.

## 6. Object Models for Graph Data

While the Module Generator doesn't fully implement object models for graph data, we can explore how such models might be designed.

### 6.1 Node and Relationship Classes

A more object-oriented approach might define explicit classes for nodes and relationships:

```python
class Node:
    """
    Represents a node in the Neo4j graph.
    """
    def __init__(self, uuid=None, labels=None, props=None):
        self.uuid = uuid
        self.labels = labels or []
        self.props = props or {}
    
    def __getitem__(self, key):
        return self.props.get(key)
    
    def __setitem__(self, key, value):
        self.props[key] = value
    
    def save(self):
        """Save changes to the database."""
        # Implementation
    
    def delete(self):
        """Delete this node from the database."""
        # Implementation
    
    @classmethod
    def find(cls, label, **props):
        """Find nodes matching the criteria."""
        # Implementation
```

```python
class Relationship:
    """
    Represents a relationship in the Neo4j graph.
    """
    def __init__(self, uuid=None, type=None, props=None, start_node=None, end_node=None):
        self.uuid = uuid
        self.type = type
        self.props = props or {}
        self.start_node = start_node
        self.end_node = end_node
    
    def __getitem__(self, key):
        return self.props.get(key)
    
    def __setitem__(self, key, value):
        self.props[key] = value
    
    def save(self):
        """Save changes to the database."""
        # Implementation
    
    def delete(self):
        """Delete this relationship from the database."""
        # Implementation
    
    @classmethod
    def find(cls, type, **props):
        """Find relationships matching the criteria."""
        # Implementation
```

These classes:
1. Provide consistent interfaces for working with graph entities
2. Support dictionary-like property access
3. Include methods for persistence operations
4. Offer class methods for entity retrieval

This approach creates a more object-oriented representation of graph data.

### 6.2 Label-Specific Node Classes

Taking the object model further, we could generate label-specific node classes:

```python
class Person(Node):
    """
    Represents a Person node in the Neo4j graph.
    """
    def __init__(self, uuid=None, props=None):
        super().__init__(uuid, ['Person'], props)
    
    @property
    def name(self):
        return self.props.get('name')
    
    @name.setter
    def name(self, value):
        self.props['name'] = value
        
    @property
    def age(self):
        return self.props.get('age')
    
    @age.setter
    def age(self, value):
        if not isinstance(value, int) or value < 0:
            raise ValueError("Age must be a non-negative integer")
        self.props['age'] = value
    
    @classmethod
    def find(cls, **props):
        """Find Person nodes matching the criteria."""
        # Implementation
```

This approach:
1. Uses inheritance for shared behavior
2. Provides property accessors with validation
3. Specializes search methods for specific node types
4. Enforces type constraints at the object level

Label-specific classes provide an even more tailored interface for working with graph data.

### 6.3 Relationship Navigation

The object model could include methods for traversing relationships:

```python
class Person(Node):
    # ... other methods ...
    
    def knows(self):
        """Find people this person knows."""
        # Implementation to find KNOWS relationships
        # Return Person objects for the related nodes
    
    def works_for(self):
        """Find companies this person works for."""
        # Implementation to find WORKS_FOR relationships
        # Return Company objects for the related nodes
```

This approach:
1. Provides natural navigational methods based on relationship types
2. Returns appropriate typed objects for related nodes
3. Creates an intuitive API for graph traversal

Relationship navigation methods make graph operations more intuitive and domain-focused.

## 7. Extending the Generated Classes

The Module Generator produces classes that can be extended for additional functionality.

### 7.1 Adding Custom Methods

Users can add custom methods to the generated classes:

```python
# Extending the generated Nodes class
class CustomNodes(Nodes):
    def find_by_property(self, property_name, property_value):
        """
        Find nodes with a specific property value, regardless of label.
        
        Parameters
        ----------
        property_name: str
            The name of the property to search
        property_value: Any
            The value to search for
            
        Returns
        -------
        List[Dict]:
            A list of matching nodes
        """
        query = f"""
        MATCH (n)
        WHERE n.{property_name} = $value
        RETURN n
        """
        params = {'value': property_value}
        results = _query(query, params)
        return [_neo4j_node_to_dict(result['n']) for result in results]
    
    def find_connected(self, start_node, relationship_type=None, max_depth=1):
        """
        Find nodes connected to the start node.
        
        Parameters
        ----------
        start_node: Dict
            The starting node
        relationship_type: str, optional
            The type of relationship to traverse
        max_depth: int, optional
            The maximum traversal depth
            
        Returns
        -------
        List[Dict]:
            The connected nodes
        """
        # Implementation
```

This approach:
1. Inherits all generated methods from the base class
2. Adds custom methods for additional functionality
3. Creates a specialized interface for specific application needs

Extension through inheritance preserves the generated code while adding custom capabilities.

### 7.2 Method Override

Users can override generated methods for customized behavior:

```python
class CustomNodes(Nodes):
    def person(self, uuid=None, **props):
        """
        Enhanced version of the person finder with caching.
        """
        # Check cache first
        cache_key = f"person_{uuid}_{hash(frozenset(props.items()))}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Call the original method if not in cache
        results = super().person(uuid, **props)
        
        # Store in cache
        self._cache[cache_key] = results
        
        return results
    
    def __init__(self):
        super().__init__()
        self._cache = {}
    
    def clear_cache(self):
        """Clear the result cache."""
        self._cache = {}
```

This approach:
1. Calls the original method using `super()`
2. Adds functionality before or after the original behavior
3. Maintains the same interface while changing the implementation

Method override enables customization of specific behaviors while keeping the overall interface consistent.

### 7.3 Composition Instead of Inheritance

Alternatively, users can employ composition to extend functionality:

```python
class GraphService:
    def __init__(self):
        self.nodes = Nodes()
        self.edges = Edges()
        self._cache = {}
    
    def find_person(self, uuid=None, **props):
        """
        Find person nodes with caching.
        """
        # Check cache first
        cache_key = f"person_{uuid}_{hash(frozenset(props.items()))}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Call the original method if not in cache
        results = self.nodes.person(uuid, **props)
        
        # Store in cache
        self._cache[cache_key] = results
        
        return results
    
    def find_connected_people(self, person):
        """
        Find people connected to the given person.
        """
        # Use the edges interface to find connections
        knows_relationships = self.edges.knows(start_node_uuid=person['uuid'])
        # Extract and return the target nodes
        return [target for _, _, target in knows_relationships]
    
    def clear_cache(self):
        """Clear the result cache."""
        self._cache = {}
```

This approach:
1. Contains the generated classes as components
2. Delegates to their methods as needed
3. Adds new functionality that coordinates between components

Composition provides flexibility in how the generated interfaces are used and extended.

## 8. Exercises

Now that we've explored classes and OOP in the Module Generator, let's apply this knowledge with some exercises.

### Exercise 1: Entity Class Generator

Create a function that generates entity classes for Neo4j nodes:

```python
def generate_entity_classes(metadata):
    """
    Generate entity classes for Neo4j nodes.
    
    Parameters
    ----------
    metadata: Dict
        The metadata dictionary
        
    Returns
    -------
    str:
        Python code defining entity classes
    """
    class_code = """
class Entity:
    """Base class for Neo4j entities."""
    def __init__(self, uuid=None, props=None):
        self.uuid = uuid
        self.props = props or {}
    
    def __getitem__(self, key):
        return self.props.get(key)
    
    def __setitem__(self, key, value):
        self.props[key] = value
        
    @classmethod
    def from_dict(cls, data):
        """Create an entity from a dictionary."""
        instance = cls(uuid=data.get('uuid'))
        instance.props = data.get('props', {})
        return instance
"""
    
    # Generate entity classes for each node label
    for label in metadata['node_labels']:
        properties = metadata['node_properties'].get(label, {})
        class_name = ''.join(word.capitalize() for word in label.split('_'))
        
        class_code += f"""
class {class_name}(Entity):
    """Represents a {label} node in the Neo4j graph."""
    def __init__(self, uuid=None, props=None):
        super().__init__(uuid, props)
"""
        
        # Add property accessors for each known property
        for prop_name, prop_type in properties.items():
            python_type = _get_python_type(prop_type)
            property_code = f"""
    @property
    def {prop_name}(self):
        return self.props.get('{prop_name}')
    
    @{prop_name}.setter
    def {prop_name}(self, value):
        # Validate type
        if value is not None and not isinstance(value, {python_type}):
            try:
                value = {python_type}(value)
            except:
                raise TypeError(f"{prop_name} must be of type {python_type}")
        self.props['{prop_name}'] = value
"""
            class_code += property_code
        
        # Add a find method
        class_code += f"""
    @classmethod
    def find(cls, uuid=None, **props):
        """Find {label} nodes matching the criteria."""
        # Query database
        query, params = Queries.node(label="{label}", **{{'uuid': uuid} if uuid else {{}}, **props})
        results = _query(query, params)
        # Convert results to entities
        return [cls.from_dict(_neo4j_node_to_dict(result['n'])) for result in results]
"""
    
    return class_code
```

### Exercise 2: Relationship Method Generator

Create a function that adds relationship navigation methods to entity classes:

```python
def generate_relationship_methods(metadata):
    """
    Generate relationship navigation methods for entity classes.
    
    Parameters
    ----------
    metadata: Dict
        The metadata dictionary
        
    Returns
    -------
    Dict[str, str]:
        Dictionary mapping class names to method code
    """
    methods = {}
    
    # Process each relationship type
    for rel_type in metadata['edge_types']:
        # Get endpoints
        start_labels, end_labels = metadata['edge_endpoints'][rel_type]
        
        # Convert relationship type to method name
        method_name = rel_type.lower()
        
        # For each start label, add a method to navigate to end labels
        for start_label in start_labels:
            start_class = ''.join(word.capitalize() for word in start_label.split('_'))
            
            if start_class not in methods:
                methods[start_class] = ""
            
            # Create the navigation method
            method_code = f"""
    def {method_name}(self):
        """Find {rel_type} relationships from this {start_label}."""
        query = """
            MATCH (n:{start_label})-[r:{rel_type}]->(m)
            WHERE n.uuid = $uuid
            RETURN m, r
        """
        params = {{'uuid': self.uuid}}
        results = _query(query, params)
        
        # Determine the class for each target node
        relationships = []
        for result in results:
            target_dict = _neo4j_node_to_dict(result['m'])
            rel_dict = _neo4j_relationship_to_dict(result['r'])
            
            # Create appropriate entity for the target
            target_labels = target_dict['labels']
            if not target_labels:
                target_entity = Entity.from_dict(target_dict)
            else:
                # Use the first label to determine the class
                target_class = ''.join(word.capitalize() for word in target_labels[0].split('_'))
                target_class = globals().get(target_class, Entity)
                target_entity = target_class.from_dict(target_dict)
            
            relationships.append((rel_dict, target_entity))
        
        return relationships
"""
            methods[start_class] += method_code
    
    return methods
```

### Exercise 3: Graph Repository Class

Create a repository class that provides a unified interface for graph operations:

```python
class GraphRepository:
    """
    Repository for Neo4j graph operations with entity support.
    """
    def __init__(self):
        self.nodes = Nodes()
        self.edges = Edges()
        self.entity_cache = {}
    
    def find_entity(self, label, uuid=None, **props):
        """
        Find entities by label and properties.
        
        Parameters
        ----------
        label: str
            The node label
        uuid: str, optional
            The UUID of the node to find
        **props: Dict
            Additional properties to search for
            
        Returns
        -------
        List[Entity]:
            A list of matching entities
        """
        # Implementation
    
    def save_entity(self, entity):
        """
        Save an entity to the database.
        
        Parameters
        ----------
        entity: Entity
            The entity to save
            
        Returns
        -------
        Entity:
            The saved entity
        """
        # Implementation
    
    def create_relationship(self, source_entity, relationship_type, target_entity, **props):
        """
        Create a relationship between entities.
        
        Parameters
        ----------
        source_entity: Entity
            The source entity
        relationship_type: str
            The type of relationship
        target_entity: Entity
            The target entity
        **props: Dict
            Properties for the relationship
            
        Returns
        -------
        Dict:
            The created relationship
        """
        # Implementation
```

## 9. Summary

In this notebook, we've explored how the Module Generator uses classes and object-oriented programming. We've seen how:

1. The `Queries` class organizes query generation functions within a common namespace
2. Generated `Nodes` and `Edges` classes provide structured interfaces to graph data
3. The Module Generator employs string templates to create classes dynamically
4. OOP design principles guide the Module Generator's architecture
5. Extension through inheritance or composition enables customized functionality

These OOP techniques enhance code organization, maintainability, and usability, creating a robust foundation for Neo4j application development.

## 10. Further Reading

- [Python Classes and OOP](https://docs.python.org/3/tutorial/classes.html)
- [OOP Design Principles](https://realpython.com/python3-object-oriented-programming/)
- [Neo4j Data Models](https://neo4j.com/developer/data-modeling/)
- [Design Patterns in Python](https://refactoring.guru/design-patterns/python)
- [Python Descriptors and Properties](https://docs.python.org/3/howto/descriptor.html)