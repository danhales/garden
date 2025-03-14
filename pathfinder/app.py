"""
Flask application factory for Pathfinder
"""

import sys
import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path as PathLib

# Initialize logging
logger = logging.getLogger('pathfinder.app')

def create_app(config: Optional[Dict[str, Any]] = None):
    """
    Create and configure a Flask application
    """
    # Import Flask here to avoid requiring it for non-web usage
    try:
        from flask import Flask, Blueprint, request, jsonify, render_template, send_from_directory
    except ImportError:
        logger.error("Flask is not installed. Please install Flask to use the web application.")
        return None
    
    # Create and configure the app
    app = Flask(__name__, static_folder='static', template_folder='templates')
    
    # Apply default configuration
    app.config.update({
        'SECRET_KEY': os.environ.get('SECRET_KEY', 'dev'),
        'PATHFINDER_NEO4J_URI': os.environ.get('PATHFINDER_NEO4J_URI', 'bolt://localhost:7687'),
        'PATHFINDER_NEO4J_USER': os.environ.get('PATHFINDER_NEO4J_USER', 'neo4j'),
        'PATHFINDER_NEO4J_PASSWORD': os.environ.get('PATHFINDER_NEO4J_PASSWORD', 'neo4j'),
        'PATHFINDER_NEO4J_DATABASE': os.environ.get('PATHFINDER_NEO4J_DATABASE', 'neo4j'),
    })
    
    # Override with any provided configuration
    if config:
        app.config.update(config)
    
    # Initialize Pathfinder
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from __init__ import Pathfinder
    pathfinder = Pathfinder(
        neo4j_uri=app.config['PATHFINDER_NEO4J_URI'],
        username=app.config['PATHFINDER_NEO4J_USER'],
        password=app.config['PATHFINDER_NEO4J_PASSWORD'],
        database=app.config['PATHFINDER_NEO4J_DATABASE']
    )
    
    # Access the context manager and theme manager
    context_manager = pathfinder.context_manager
    theme_manager = pathfinder.theme_manager
    
    # Import the accessibility helper
    from ui.accessibility import AccessibilityHelper
    
    # Create a blueprint
    bp = Blueprint('pathfinder', __name__, url_prefix='/pathfinder')
    
    @bp.route('/')
    def index():
        """Render the main application interface"""
        # Get current theme
        theme = theme_manager.get_current_theme()
        css = theme["css"]
        
        # Render the template
        return render_template('index.html', css=css)
    
    # Add API routes
    @bp.route('/info', methods=['GET'])
    def info():
        """Get basic information about Pathfinder"""
        return jsonify({
            "name": "Pathfinder",
            "description": "Context-aware graph navigation",
            "contexts": len(context_manager.contexts),
            "paths": len(context_manager.paths),
            "current_context": context_manager.current_context_id,
            "current_theme": theme_manager.current_theme,
            "version": "1.0.0"
        })
    
    @bp.route('/contexts', methods=['GET'])
    def list_contexts():
        """List all contexts"""
        current_id = context_manager.current_context_id
        
        contexts = []
        for ctx_id, ctx in context_manager.contexts.items():
            contexts.append({
                "id": ctx_id,
                "name": ctx.name,
                "description": ctx.description,
                "node_count": len(ctx.nodes),
                "last_accessed": ctx.last_accessed,
                "is_current": ctx_id == current_id
            })
        
        # Sort by last accessed (most recent first)
        contexts.sort(key=lambda x: x["last_accessed"], reverse=True)
        
        return jsonify({"contexts": contexts})
    
    @bp.route('/contexts', methods=['POST'])
    def create_context():
        """Create a new context"""
        data = request.json
        context = context_manager.create_context(
            name=data.get('name', 'New Context'),
            description=data.get('description', '')
        )

        # Save data after creating context
        context_manager.save_data()

        return jsonify({
            "id": context.id,
            "name": context.name,
            "description": context.description
        })
    
    @bp.route('/contexts/<context_id>', methods=['GET'])
    def get_context(context_id):
        """Get details about a specific context"""
        if context_id not in context_manager.contexts:
            return jsonify({"error": "Context not found"}), 404
        
        ctx = context_manager.contexts[context_id]
        return jsonify({
            "id": ctx.id,
            "name": ctx.name,
            "description": ctx.description,
            "node_count": len(ctx.nodes),
            "focus_nodes": ctx.focus_nodes,
            "last_accessed": ctx.last_accessed,
            "priority_scheme": ctx.priority_scheme.name,
            "tags": list(ctx.tags),
            "accessibility_description": ctx.accessibility_description
        })
    
    @bp.route('/contexts/switch/<context_id>', methods=['POST'])
    def switch_context(context_id):
        """Switch to a different context"""
        data = request.json or {}
        context = context_manager.switch_context(
            context_id=context_id,
            reason=data.get('reason', 'API switch'),
            carry_nodes=data.get('carry_nodes', [])
        )
        return jsonify({
            "id": context.id,
            "name": context.name,
            "message": f"Switched to context: {context.name}"
        })
    
    @bp.route('/contexts/focus/<node_id>', methods=['POST'])
    def focus_node(node_id):
        """Add a node to the focus list in the current context"""
        if not context_manager.current_context_id:
            return jsonify({"error": "No active context"}), 400
            
        context = context_manager.contexts[context_manager.current_context_id]
        if node_id not in context.nodes:
            return jsonify({"error": "Node not found in current context"}), 404
            
        # Add to focus nodes if not already there
        if node_id not in context.focus_nodes:
            context.focus_nodes.append(node_id)
            context_manager.save_data()
        
        return jsonify({"message": f"Node {node_id} added to focus"})
    
    @bp.route('/test-data', methods=['POST'])
    def create_test_data():
        """Create some test data for visualization"""
        if not context_manager.current_context_id:
            return jsonify({"error": "No active context"}), 400
            
        context = context_manager.contexts[context_manager.current_context_id]
        
        # Create sample nodes
        nodes = []
        for i in range(5):
            node_id = str(uuid.uuid4())
            node = ContextualNode(
                uuid=node_id,
                labels=["TestNode"],
                properties={"name": f"Node {i+1}", "value": i*10}
            )
            context.add_node(node)
            nodes.append(node_id)
        
        # Create relationships between nodes
        for i in range(len(nodes)-1):
            context.add_relationship(
                source_id=nodes[i],
                target_id=nodes[i+1],
                rel_type="CONNECTS_TO"
            )
        
        # Make a cycle
        context.add_relationship(
            source_id=nodes[-1],
            target_id=nodes[0],
            rel_type="CONNECTS_TO"
        )
        
        context_manager.save_data()
        return jsonify({"message": f"Created {len(nodes)} test nodes with relationships"})
    
    @bp.route('/visualization', methods=['GET'])
    def visualize():
        """Get visualization data for a context with accessibility enhancements"""
        context_id = request.args.get('context_id', context_manager.current_context_id)
        if not context_id:
            return jsonify({"error": "No context specified"}), 400
        
        # Get raw visualization data
        viz_data = context_manager.visualize_context(context_id)
        
        # Enhance with accessibility information
        enhanced_data = AccessibilityHelper.enhance_visualization_data(viz_data)
        
        # Add keyboard navigation
        navigable_data = AccessibilityHelper.create_keyboard_navigable_graph(enhanced_data)
        
        # Generate screen reader description
        navigable_data['screen_reader_description'] = AccessibilityHelper.generate_screen_reader_text(navigable_data)
        
        return jsonify(navigable_data)
    
    @bp.route('/themes', methods=['GET'])
    def list_themes():
        """List all available themes"""
        themes = theme_manager.list_themes()
        return jsonify({"themes": themes})
    
    @bp.route('/themes/current', methods=['GET'])
    def get_current_theme():
        """Get the current theme"""
        theme = theme_manager.get_current_theme()
        return jsonify({
            "name": theme["name"],
            "description": theme["description"],
            "css_data_uri": theme_manager.get_css_data_uri()
        })
    
    @bp.route('/themes/set/<theme_name>', methods=['POST'])
    def set_theme(theme_name):
        """Set the current theme"""
        success = theme_manager.set_theme(theme_name)
        if success:
            return jsonify({"message": f"Theme set to {theme_name}"})
        else:
            return jsonify({"error": f"Theme {theme_name} not found"}), 404
    
    @bp.route('/themes/relaxed', methods=['POST'])
    def create_relaxed_theme():
        """Create a relaxed version of the current theme"""
        theme_name = theme_manager.create_relaxed_theme()
        if theme_name:
            return jsonify({
                "message": f"Created relaxed theme {theme_name}",
                "theme_name": theme_name
            })
        else:
            return jsonify({"error": "Could not create relaxed theme"}), 500
    
    @bp.route('/themes/high-contrast', methods=['POST'])
    def create_high_contrast_theme():
        """Create a high contrast version of the current theme"""
        theme_name = theme_manager.create_high_contrast_theme()
        if theme_name:
            return jsonify({
                "message": f"Created high contrast theme {theme_name}",
                "theme_name": theme_name
            })
        else:
            return jsonify({"error": "Could not create high contrast theme"}), 500
    
    @bp.route('/save', methods=['POST'])
    def save_data():
        """Save all data to disk"""
        context_manager.save_data()
        return jsonify({"message": "Data saved successfully"})
    
    @bp.route('/static/<path:filename>')
    def static_files(filename):
        """Serve static files"""
        return send_from_directory(app.static_folder, filename)
    
    # Register the blueprint
    app.register_blueprint(bp)
    
    # Create a simple index redirect
    @app.route('/')
    def root():
        return jsonify({
            "name": "Pathfinder",
            "api_endpoint": "/pathfinder",
            "ui_endpoint": "/pathfinder/"
        })
    
    return app


# Entry point for running with Flask directly
if __name__ == '__main__':
    app = create_app()
    if app:
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        print("Could not create Flask application. Please install Flask.")