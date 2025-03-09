"""
Flask application factory for Pathfinder
"""

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
        from flask import Flask, Blueprint, request, jsonify, render_template_string, send_from_directory
    except ImportError:
        logger.error("Flask is not installed. Please install Flask to use the web application.")
        return None
    
    # Create and configure the app
    app = Flask(__name__, static_folder='static')
    
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
    from . import Pathfinder
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
    from .ui.accessibility import AccessibilityHelper
    
    # Create a blueprint
    bp = Blueprint('pathfinder', __name__, url_prefix='/pathfinder')
    
    @bp.route('/')
    def index():
        """Render the main application interface"""
        # Get current theme
        theme = theme_manager.get_current_theme()
        css = theme["css"]
        
        # Basic HTML template with accessibility features
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Pathfinder - Context-Aware Graph Navigation</title>
            <style>{{ css }}</style>
        </head>
        <body class="pathfinder-container">
            <!-- Skip link for keyboard navigation -->
            <a href="#main-content" class="skip-link">Skip to main content</a>
            
            <header role="banner">
                <h1 class="pathfinder-header">Pathfinder</h1>
                <div role="navigation" aria-label="Main navigation">
                    <div class="navigation-links">
                        <a href="#contexts">Contexts</a>
                        <a href="#visualization">Visualization</a>
                        <a href="#focus-panel">Focus Panel</a>
                    </div>
                </div>
            </header>
            
            <main id="main-content" role="main">
                <div id="loading" aria-live="polite">Loading Pathfinder...</div>
                
                <div id="app" style="display: none;">
                    <div class="app-layout">
                        <!-- Left panel -->
                        <section id="contexts" aria-label="Contexts" class="panel-section">
                            <h2>Contexts</h2>
                            <div id="context-list" role="list" aria-label="Available contexts"></div>
                        </section>
                        
                        <!-- Main panel -->
                        <section id="visualization" aria-label="Graph visualization" class="main-panel">
                            <h2>Visualization</h2>
                            <div id="graph-container" role="img" aria-label="Graph visualization"></div>
                            <div id="graph-description" class="sr-only" aria-live="polite"></div>
                        </section>
                        
                        <!-- Right panel -->
                        <section id="focus-panel" aria-label="Focus panel" class="panel-section">
                            <h2>Focus Items</h2>
                            <div id="focus-list" role="list" aria-label="Focus nodes"></div>
                        </section>
                    </div>
                    
                    <!-- Path controls -->
                    <div id="path-controls" role="region" aria-label="Path recording controls">
                        <h2>Path Recording</h2>
                        <div id="path-buttons" role="toolbar" aria-label="Recording controls"></div>
                    </div>
                </div>
            </main>
            
            <footer role="contentinfo">
                <div id="theme-controls">
                    <h2>Theme Selection</h2>
                    <div id="theme-selector" role="radiogroup" aria-label="Theme selection"></div>
                    
                    <div class="theme-buttons">
                        <button id="focus-theme-btn" class="pathfinder-button" aria-label="Data focus theme">
                            Data Focus Mode
                        </button>
                        <button id="low-contrast-theme-btn" class="pathfinder-button" aria-label="Low contrast theme">
                            Low Contrast Mode
                        </button>
                        <button id="high-contrast-theme-btn" class="pathfinder-button" aria-label="High contrast theme">
                            High Contrast
                        </button>
                    </div>
                </div>
                
                <div id="accessibility-info">
                    <h2>Accessibility</h2>
                    <p>Pathfinder is designed to be accessible to all users, including screen reader users and those with sensory sensitivities.</p>
                    <button id="toggle-sr-descriptions" class="pathfinder-button" aria-label="Toggle screen reader descriptions">
                        Toggle Descriptions
                    </button>
                </div>
            </footer>
            
            <script>
            // Basic script to toggle between loading and app display
            document.addEventListener('DOMContentLoaded', function() {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('app').style.display = 'block';
                
                // Add responsive layout classes
                document.querySelector('.app-layout').classList.add('responsive-layout');
                
                // Fetch app data and contexts
                fetchData();
                
                // Setup theme buttons
                document.getElementById('focus-theme-btn').addEventListener('click', function() {
                    setTheme('focus');
                });
                
                document.getElementById('low-contrast-theme-btn').addEventListener('click', function() {
                    setTheme('low_contrast');
                });
                
                document.getElementById('high-contrast-theme-btn').addEventListener('click', function() {
                    setTheme('high_contrast_default');
                });
                
                // Toggle screen reader descriptions
                document.getElementById('toggle-sr-descriptions').addEventListener('click', function() {
                    const description = document.getElementById('graph-description');
                    if (description.classList.contains('sr-only')) {
                        description.classList.remove('sr-only');
                        this.textContent = 'Hide Descriptions';
                    } else {
                        description.classList.add('sr-only');
                        this.textContent = 'Show Descriptions';
                    }
                });
            });
            
            async function fetchData() {
                try {
                    // Fetch contexts
                    const contextsResponse = await fetch('/pathfinder/contexts');
                    const contextsData = await contextsResponse.json();
                    renderContexts(contextsData.contexts || []);
                    
                    // Fetch themes
                    const themesResponse = await fetch('/pathfinder/themes');
                    const themesData = await themesResponse.json();
                    renderThemes(themesData.themes || []);
                    
                    // Fetch current visualization if a context is active
                    const infoResponse = await fetch('/pathfinder/info');
                    const infoData = await infoResponse.json();
                    
                    if (infoData.current_context) {
                        const vizResponse = await fetch(`/pathfinder/visualization?context_id=${infoData.current_context}`);
                        const vizData = await vizResponse.json();
                        renderVisualization(vizData);
                    }
                } catch (error) {
                    console.error('Error fetching data:', error);
                    document.getElementById('app').innerHTML = `<p>Error loading data: ${error.message}</p>`;
                }
            }
            
            function renderContexts(contexts) {
                const contextList = document.getElementById('context-list');
                contextList.innerHTML = '';
                
                contexts.forEach(context => {
                    const contextItem = document.createElement('div');
                    contextItem.className = `pathfinder-context ${context.is_current ? 'active' : 'inactive'}`;
                    contextItem.setAttribute('role', 'listitem');
                    contextItem.setAttribute('tabindex', '0');
                    contextItem.setAttribute('aria-selected', context.is_current ? 'true' : 'false');
                    contextItem.setAttribute('aria-label', `${context.name}: ${context.description}`);
                    
                    contextItem.innerHTML = `
                        <h3>${context.name}</h3>
                        <p>${context.description}</p>
                        <p>${context.node_count || 0} nodes</p>
                    `;
                    
                    contextItem.addEventListener('click', () => switchContext(context.id));
                    contextItem.addEventListener('keydown', (e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                            switchContext(context.id);
                        }
                    });
                    
                    contextList.appendChild(contextItem);
                });
                
                // Add create new context button
                const newBtn = document.createElement('button');
                newBtn.className = 'pathfinder-button';
                newBtn.textContent = 'New Context';
                newBtn.setAttribute('aria-label', 'Create new context');
                newBtn.addEventListener('click', createNewContext);
                
                contextList.appendChild(newBtn);
            }
            
            function renderThemes(themes) {
                const themeSelector = document.getElementById('theme-selector');
                themeSelector.innerHTML = '';
                
                themes.forEach(theme => {
                    const themeItem = document.createElement('div');
                    themeItem.className = `theme-option ${theme.is_current ? 'current' : ''}`;
                    
                    const radio = document.createElement('input');
                    radio.type = 'radio';
                    radio.name = 'theme';
                    radio.id = `theme-${theme.name}`;
                    radio.value = theme.name;
                    radio.checked = theme.is_current;
                    radio.setAttribute('aria-label', `Switch to theme: ${theme.description}`);
                    
                    const label = document.createElement('label');
                    label.htmlFor = `theme-${theme.name}`;
                    label.textContent = theme.name.replace(/_/g, ' ');
                    
                    themeItem.appendChild(radio);
                    themeItem.appendChild(label);
                    
                    radio.addEventListener('change', () => {
                        if (radio.checked) {
                            setTheme(theme.name);
                        }
                    });
                    
                    themeSelector.appendChild(themeItem);
                });
            }
            
            function renderVisualization(vizData) {
                const graphContainer = document.getElementById('graph-container');
                graphContainer.innerHTML = '<p>Graph visualization would render here</p>';
                
                // Update screen reader description
                const description = document.getElementById('graph-description');
                description.textContent = vizData.screen_reader_description || 
                    vizData.context.accessibility_description || 
                    `Context ${vizData.context.name} with ${vizData.nodes.length} nodes and ${vizData.links.length} links`;
                
                // Render focus items
                renderFocusItems(vizData);
            }
            
            function renderFocusItems(vizData) {
                const focusList = document.getElementById('focus-list');
                focusList.innerHTML = '';
                
                // Get focus nodes
                const focusNodeIds = vizData.context.focus_nodes || [];
                const focusNodes = vizData.nodes.filter(node => focusNodeIds.includes(node.id));
                
                if (focusNodes.length === 0) {
                    focusList.innerHTML = '<p>No focus items</p>';
                    return;
                }
                
                // Sort by priority
                focusNodes.sort((a, b) => b.priority - a.priority);
                
                focusNodes.forEach(node => {
                    const focusItem = document.createElement('div');
                    focusItem.className = 'focus-item';
                    focusItem.setAttribute('role', 'listitem');
                    focusItem.setAttribute('tabindex', '0');
                    focusItem.setAttribute('aria-label', node.aria_label || node.name);
                    
                    focusItem.innerHTML = `
                        <h3>${node.name}</h3>
                        <p>Priority: ${node.priority.toFixed(2)}</p>
                    `;
                    
                    focusList.appendChild(focusItem);
                });
            }
            
            // API interaction functions
            async function switchContext(contextId) {
                try {
                    const response = await fetch(`/pathfinder/contexts/switch/${contextId}`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    });
                    
                    if (response.ok) {
                        // Refresh the UI
                        fetchData();
                    } else {
                        console.error('Error switching context');
                    }
                } catch (error) {
                    console.error('Error:', error);
                }
            }
            
            async function createNewContext() {
                const name = prompt('Enter context name:');
                if (!name) return;
                
                const description = prompt('Enter context description:');
                
                try {
                    const response = await fetch('/pathfinder/contexts', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            name,
                            description: description || ''
                        })
                    });
                    
                    if (response.ok) {
                        // Refresh the UI
                        fetchData();
                    } else {
                        console.error('Error creating context');
                    }
                } catch (error) {
                    console.error('Error:', error);
                }
            }
            
            async function setTheme(themeName) {
                try {
                    const response = await fetch(`/pathfinder/themes/set/${themeName}`, {
                        method: 'POST'
                    });
                    
                    if (response.ok) {
                        // Refresh the page to apply the theme
                        window.location.reload();
                    } else {
                        console.error('Error setting theme');
                    }
                } catch (error) {
                    console.error('Error:', error);
                }
            }
            </script>
            
            <style>
            /* Responsive layout */
            .responsive-layout {
                display: grid;
                grid-template-columns: 1fr 2fr 1fr;
                gap: 1rem;
            }
            
            @media (max-width: 1024px) {
                .responsive-layout {
                    grid-template-columns: 1fr 2fr;
                }
                
                #focus-panel {
                    grid-column: 1 / -1;
                }
            }
            
            @media (max-width: 768px) {
                .responsive-layout {
                    grid-template-columns: 1fr;
                }
                
                .panel-section, .main-panel {
                    grid-column: 1;
                }
            }
            
            /* Ensure spacing between elements */
            .panel-section, .main-panel {
                margin-bottom: 2rem;
            }
            
            /* Theme buttons */
            .theme-buttons {
                display: flex;
                flex-wrap: wrap;
                gap: 0.5rem;
                margin-top: 1rem;
            }
            </style>
        </body>
        </html>
        """
        
        # Render the template
        return render_template_string(html, css=css)
    
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