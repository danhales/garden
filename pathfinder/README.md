# 🧭 Pathfinder

Pathfinder is a context-aware graph navigation application in the G.A.R.D.E.N. ecosystem that bridges the conceptual gap between metadata/data-oriented exploration and advanced graph intelligence.

## Core Concept: Context-Aware Graph Navigation

Traditional graph exploration tools treat all data equally, forcing users to maintain their own mental contexts. Pathfinder recognizes that humans naturally switch between different perspectives when exploring complex data. By formalizing these contexts, Pathfinder helps users maintain cognitive coherence while navigating complex information networks.

### Key Features

- **Context Management**: Create, store, and switch between different views of your graph data
- **Priority-Based Navigation**: Records interaction patterns and prioritizes nodes based on context
- **Path Recording**: Capture sequences of exploration for later review or sharing
- **Cognitive Transition Support**: Carry relevant nodes between contexts when switching perspectives
- **Accessibility-First Design**: Multiple visual themes optimized for different cognitive preferences

## Architecture

Pathfinder introduces several architectural innovations that extend the G.A.R.D.E.N. philosophy:

```
┌───────────────────────┐
│     Flask App Layer   │ ← REST endpoints for web integration
└───────────┬───────────┘
            │
┌───────────┴───────────┐
│  Context Management   │ ← Manages multiple views of the graph
└───────────┬───────────┘
            │
┌───────────┴───────────┐
│   Accessibility UI    │ ← Multiple visual themes for different needs  
└───────────┬───────────┘
            │
┌───────────┴───────────┐
│    Module Generator   │ ← Generated Neo4j interface
└───────────┬───────────┘
            │
┌───────────┴───────────┐
│   Neo4j Database      │ ← Underlying graph data
└───────────────────────┘
```

## Bridging the Ecosystem

Pathfinder serves as a natural progression in the G.A.R.D.E.N. ecosystem:

- **From Grassroots**: Extends schema-oriented exploration by adding the dimension of context
- **From Grasshopper**: Enriches entity-focused navigation with prioritization and memory
- **Toward Intelligence Systems**: Paves the way for advanced analytics and machine learning

## Use Cases

- **Complex Research**: Navigate multi-dimensional research data without losing your place
- **Enterprise Knowledge Management**: Allow different departments to maintain their own views
- **Educational Exploration**: Guide students through different perspectives on complex domains
- **Expert Systems**: Create specialized views for domain experts to navigate within their comfort zone
- **Collaborative Analysis**: Record exploration paths to share with colleagues

## Three Interaction Modes

Pathfinder supports three powerful ways to explore your graph:

1. **Context Mode**: Create separate exploration contexts for different perspectives or tasks
2. **Path Mode**: Record sequences of exploration steps for later analysis or sharing
3. **Comparison Mode**: Compare different contexts to identify similarities and differences

## Design Philosophy

Pathfinder's design leverages several key cognitive principles:

1. **Context Switching Cost Reduction**: Formalize mental contexts to reduce cognitive load
2. **Selective Attention Support**: Focus on relevant data in each context
3. **Memory Externalization**: Store exploration paths rather than keeping them in memory
4. **Visual Preference Adaptation**: Provide themes that accommodate different visual processing needs

## Getting Started

```bash
# Installation
git clone https://github.com/danhales/garden.git
cd garden/pathfinder
pip install -r requirements.txt

# Run Pathfinder
export FLASK_APP=pathfinder.app:create_app
export FLASK_ENV=development
flask run --host=0.0.0.0 --port=5000
```

## Learning Path

Pathfinder serves as an excellent stepping stone for developers interested in:

1. **Architectural Patterns**: Learn layered architecture and factory patterns
2. **Flask Applications**: Create advanced Flask applications with blueprints
3. **Graph Data Management**: Work with Neo4j and graph data structures
4. **Accessibility Design**: Implement visual themes and accessibility features
5. **Context Management**: Understand state management techniques

## Future Directions

Pathfinder opens paths to several exciting future directions:

- **Machine Learning Integration**: Train models to suggest relevant contexts
- **Collaborative Exploration**: Share contexts and paths among teams
- **Semantic Context Detection**: Automatically identify potential contexts
- **Multi-Modal Navigation**: Add voice and gesture-based context navigation

## Contributing

Pathfinder welcomes contributions, particularly in these areas:

- Enhanced visualization techniques
- Additional accessibility themes
- Integration with other data sources
- Path analysis algorithms
- Context suggestion mechanisms

## License

This project is licensed under the MIT License - see the LICENSE file for details.