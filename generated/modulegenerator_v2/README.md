# Neo4j Module Generator

## Welcome! 👋

Ready to transform your graph database interactions? This Neo4j Module Generator creates a dynamic, type-safe Python interface that adapts to your specific graph database structure. Whether you're a beginner or an experienced developer, this tool makes working with Neo4j feel intuitive and powerful! ✨

## Dynamic Database Interaction

Instead of rigid, predefined methods, this generator creates a fully customized API based on your specific graph database:

```python
import mygraph

# Dynamically generated interfaces adapt to your graph's structure
# Find all Person nodes with name "Sarah"
people = mygraph.nodes.person(name="Sarah")

# Create a relationship between nodes
mygraph.execute_query(
    "CREATE (p:Person {name: $name})-[:WORKS_AT]->(c:Company {name: $company})",
    params={'name': 'Alice', 'company': 'TechCorp'}
)

# Flexible querying
results = mygraph.execute_query(
    "MATCH (p:Person)-[:KNOWS]->(friend:Person) RETURN p.name, friend.name"
)
```

## Key Features

🚀 **Metadata-Driven API**: 
- Automatically generates interfaces based on your graph's actual structure
- Every node label and relationship type becomes a queryable Python method
- Type-safe interactions with automatic type conversion

🔍 **Flexible Querying**:
- Execute raw Cypher queries with ease
- Dynamic method generation for nodes and relationships
- Consistent dictionary-based result format

🛡️ **Type Safety**:
- Automatic type checking and conversion
- Helpful error messages for type mismatches
- Preserves the integrity of your data during interactions

## Getting Started

### Requirements
- Python 3.6+
- Neo4j 4.x
- Neo4j Python driver

### Installation
```bash
pip install neo4j
```

### Generate Your Module
```bash
python modulegenerator-claude.py -u "bolt://localhost:7687" -n "neo4j" -p "your_password" -g "mygraph"
```

## Advanced Interactions

### Custom Querying
```python
# Complex graph traversals become simple
social_connections = mygraph.execute_query(
    """
    MATCH (p:Person)-[:KNOWS*2]->(friend:Person) 
    WHERE p.name = $name 
    RETURN DISTINCT friend.name
    """,
    params={'name': 'Alice'}
)
```

### Direct Database Operations
```python
# Create a new connection
driver = mygraph.connect()

# Execute transactions
with driver.session() as session:
    session.run(
        "CREATE (p:Person {name: $name, age: $age})",
        {'name': 'Bob', 'age': 30}
    )
```

## Why This Matters

The module generator does more than create a simple interface—it:
- Learns your database structure
- Generates type-safe methods
- Provides a consistent, Pythonic way to interact with graph data
- Serves as a learning tool for graph database concepts

## Join the Journey!

This project demonstrates the potential of adaptive, metadata-driven interfaces. We're excited to see how you'll use it to simplify your graph database workflows!

🌟 **Pro Tip**: The generated module is a powerful learning resource that shows you how to interact with complex graph databases.

## License
Open-source and ready for your next innovative project!

Happy Graphing! 🚀