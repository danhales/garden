"""
G.A.R.D.E.N. Explorer - A simple, hyperlink-driven interface for exploring Neo4j graph data

This application provides an intuitive way to navigate graph data through two complementary approaches:
1. Grassroots: Starting from schema (labels, relationship types) and drilling down to instances
2. Grasshopper: Starting from specific entities and "hopping" to connected entities

The application uses a middleware layer generated by the Module Generator to interact with Neo4j.

Note from Dan:  This should make things future-proof, allowing my continue work on the
                module generator to not break your application.

Version:        2025_03_12_0431
Version Note:   Due to rapid development of features, I am now timestamping all versions.
                I am manually entering this after reviewing the code.
"""

import os
import datetime
import inspect
from flask import Flask, render_template, redirect, url_for, request, session, flash, g

# Import the middleware generated for the movie graph
# This provides type-safe access to the Neo4j database
try:
    # Import the middleware - normally this would be generated with the Module Generator
    import newgraph as graph_db
    
    # Create a middleware adapter to handle different middleware structures
    from middleware_adapter import create_middleware_adapter
    middleware = create_middleware_adapter(graph_db)
except ImportError as e:
    print(f"Error importing middleware: {e}")
    # For demonstration purposes, we'll use a simplified mock if the real middleware isn't available
    from helpers import create_mock_middleware
    graph_db = create_mock_middleware()
    middleware = graph_db  # Mock middleware already has the right structure

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev_key_for_testing')
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour

# Simple user database - in a real application, this would come from a secure database
# Format: { username: { 'password': 'password_value', 'display_name': 'Display Name' } }
USERS = {
    'demo': {
        'password': 'demo123',
        'display_name': 'Demo User'
    }
}

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

def login_required(view_function):
    """
    Decorator that ensures a user is logged in before accessing a route.
    If not logged in, redirects to the login page.
    """
    def wrapped_view(*args, **kwargs):
        if 'username' not in session:
            # Store the requested URL for redirect after login
            session['next'] = request.url
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('login'))
        return view_function(*args, **kwargs)
    # This is needed to preserve the function name, which Flask's routing uses
    wrapped_view.__name__ = view_function.__name__
    return wrapped_view

def get_node_display_name(node):
    """
    Gets a human-readable display name for a node based on common properties.
    This helps create more user-friendly links and titles.
    """
    props = node['props']
    
    # Try common name properties in order of preference
    for prop in ['title', 'name', 'fullName', 'displayName']:
        if prop in props and props[prop]:
            return props[prop]
    
    # Fall back to UUID if no name property is found
    return f"Node {node['uuid'][:8]}..."

def format_property_value(value, max_length=100):
    """
    Format a property value for display, handling different types appropriately.
    """
    if value is None:
        return "<empty>"
    
    # For lists, format each item
    if isinstance(value, list):
        if len(value) > 3:
            return f"List with {len(value)} items"
        return ", ".join(str(item) for item in value)
    
    # For dictionaries, summarize content
    if isinstance(value, dict):
        return f"Object with {len(value)} properties"
    
    # For strings, truncate if too long
    value_str = str(value)
    if len(value_str) > max_length:
        return value_str[:max_length] + "..."
    
    return value_str

def log_activity(activity_type, details=None):
    """
    Log user activity for audit purposes.
    In a production system, this would write to a secure log.
    """
    timestamp = datetime.datetime.now().isoformat()
    username = session.get('username', 'anonymous')
    activity = {
        'timestamp': timestamp,
        'username': username,
        'activity_type': activity_type,
        'details': details or {}
    }
    # In a real system, we'd write this to a log file or database
    print(f"ACTIVITY: {activity}")

def inspect_middleware(middleware_module):
    """
    Inspect the structure of the middleware module to help with debugging.
    
    This function examines the middleware module to determine its structure,
    which helps diagnose issues with middleware integration.
    
    Parameters
    ----------
    middleware_module:
        The imported middleware module
        
    Returns
    -------
    Dict:
        Information about the middleware structure
    """
    info = {
        'has_nodes_attr': hasattr(middleware_module, 'nodes'),
        'has_edges_attr': hasattr(middleware_module, 'edges'),
        'has_execute_query': hasattr(middleware_module, 'execute_query'),
        'has_metadata': hasattr(middleware_module, 'METADATA'),
        'types': {}
    }
    
    if info['has_nodes_attr']:
        info['types']['nodes'] = type(middleware_module.nodes).__name__
        
        # Check if nodes has methods
        if hasattr(middleware_module.nodes, '__dict__'):
            info['nodes_methods'] = [m for m in dir(middleware_module.nodes) 
                                    if not m.startswith('_') and callable(getattr(middleware_module.nodes, m))]
    
    if info['has_edges_attr']:
        info['types']['edges'] = type(middleware_module.edges).__name__
        
        # Check if edges has methods
        if hasattr(middleware_module.edges, '__dict__'):
            info['edges_methods'] = [m for m in dir(middleware_module.edges) 
                                   if not m.startswith('_') and callable(getattr(middleware_module.edges, m))]
    
    if info['has_metadata']:
        info['metadata_keys'] = list(middleware_module.METADATA.keys())
        
    return info

# -----------------------------------------------------------------------------
# Authentication Routes
# -----------------------------------------------------------------------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user login with a simple form.
    GET: Display the login form
    POST: Process the login form submission
    """
    error = None
    
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        
        if username in USERS and USERS[username]['password'] == password:
            # Successful login
            session['username'] = username
            session['display_name'] = USERS[username]['display_name']
            session.permanent = True
            
            log_activity('login_success')
            
            # Redirect to the original requested URL or the dashboard
            next_url = session.pop('next', url_for('index'))
            return redirect(next_url)
        else:
            # Failed login
            error = "Invalid username or password"
            log_activity('login_failure', {'username': username})
    
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    """
    Handle user logout by clearing the session.
    """
    log_activity('logout')
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

# -----------------------------------------------------------------------------
# Grassroots Routes (Schema-First Navigation)
# -----------------------------------------------------------------------------

@app.route('/')
@login_required
def index():
    """
    Main dashboard that serves as the entry point for both Grassroots and Grasshopper approaches.
    """
    log_activity('view_dashboard')
    
    # Get the schema information for the Grassroots approach
    node_labels = middleware.get_node_labels()
    
    # For the Grasshopper approach, we'll prepare curated entry points
    # These are examples from the movie graph
    featured_movies = []
    featured_people = []
    
    try:
        # Get some featured movies
        movies = middleware.get_nodes_by_label('Movie')
        if movies:
            featured_movies = movies[:5]  # First 5 movies
        
        # Get some featured people
        people = middleware.get_nodes_by_label('Person')
        if people:
            featured_people = people[:5]  # First 5 people
    except Exception as e:
        flash(f"Error loading featured content: {str(e)}", "error")
    
    return render_template(
        'dashboard.html',
        node_labels=node_labels,
        featured_movies=featured_movies,
        featured_people=featured_people,
        get_node_display_name=get_node_display_name
    )

@app.route('/schema')
@login_required
def schema_overview():
    """
    Provide an overview of the database schema (Grassroots entry point).
    Shows all node labels and relationship types.
    """
    log_activity('view_schema')
    
    node_labels = middleware.get_node_labels()
    relationship_types = middleware.get_relationship_types()
    
    # Count instances of each label
    label_counts = {}
    for label in node_labels:
        try:
            nodes = middleware.get_nodes_by_label(label)
            label_counts[label] = len(nodes)
        except Exception:
            label_counts[label] = "Error"
    
    return render_template(
        'schema.html',
        node_labels=node_labels,
        relationship_types=relationship_types,
        label_counts=label_counts
    )

@app.route('/labels/<label>')
@login_required
def list_nodes(label):
    """
    List all nodes with a specific label (Grassroots navigation).
    """
    log_activity('list_nodes', {'label': label})
    
    try:
        nodes = middleware.get_nodes_by_label(label)
        
        # Get properties for display
        if nodes:
            # Use the first node to determine which properties to show
            display_properties = list(nodes[0]['props'].keys())[:5]  # First 5 properties
        else:
            display_properties = []
        
        return render_template(
            'nodes_list.html',
            label=label,
            nodes=nodes,
            display_properties=display_properties,
            get_node_display_name=get_node_display_name,
            format_property_value=format_property_value
        )
    except Exception as e:
        flash(f"Error listing nodes: {str(e)}", "error")
        return redirect(url_for('index'))

# -----------------------------------------------------------------------------
# Grasshopper Routes (Entity-First Navigation)
# -----------------------------------------------------------------------------

@app.route('/nodes/<label>/<node_id>')
@login_required
def view_node(label, node_id):
    """
    View details of a specific node and its relationships (Grasshopper navigation).
    This is the heart of the "hopping" navigation pattern.
    """
    log_activity('view_node', {'label': label, 'node_id': node_id})
    
    try:
        # Find the specific node by ID
        node = middleware.get_node_by_id(label, node_id)
        
        if not node:
            flash(f"Node not found: {node_id}", "error")
            return redirect(url_for('index'))
        
        # Find all relationships connected to this node
        incoming_relationships = middleware.get_incoming_relationships(node_id)
        outgoing_relationships = middleware.get_outgoing_relationships(node_id)
        
        return render_template(
            'node_detail.html',
            node=node,
            label=label,
            incoming_relationships=incoming_relationships,
            outgoing_relationships=outgoing_relationships,
            get_node_display_name=get_node_display_name,
            format_property_value=format_property_value
        )
    
    except Exception as e:
        flash(f"Error viewing node: {str(e)}", "error")
        return redirect(url_for('index'))

@app.route('/search', methods=['GET'])
@login_required
def search():
    """
    Simple search functionality to find nodes by property values.
    """
    query = request.args.get('query', '').strip()
    
    if not query:
        return render_template('search.html', results=None, query=None)
    
    log_activity('search', {'query': query})
    
    results = {}
    
    try:
        # Search across all node labels
        for label in middleware.get_node_labels():
            nodes = middleware.get_nodes_by_label(label)
            
            # Simple client-side filtering - in a real application, this would use a proper search query
            label_results = []
            for node in nodes:
                for prop, value in node['props'].items():
                    if isinstance(value, str) and query.lower() in value.lower():
                        label_results.append(node)
                        break
            
            if label_results:
                results[label] = label_results
        
        return render_template(
            'search.html',
            results=results,
            query=query,
            get_node_display_name=get_node_display_name
        )
    
    except Exception as e:
        flash(f"Error performing search: {str(e)}", "error")
        return render_template('search.html', results=None, query=query)

# -----------------------------------------------------------------------------
# Debug Routes
# -----------------------------------------------------------------------------

@app.route('/debug/middleware')
@login_required
def debug_middleware():
    """
    Debug route to examine the middleware structure.
    This is helpful for understanding middleware integration issues.
    """
    try:
        middleware_info = inspect_middleware(graph_db)
        return render_template('debug_middleware.html', info=middleware_info)
    except Exception as e:
        return f"Error inspecting middleware: {str(e)}"

# -----------------------------------------------------------------------------
# Error Handlers
# -----------------------------------------------------------------------------

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors with a user-friendly page."""
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors with a user-friendly page."""
    return render_template('500.html'), 500

# -----------------------------------------------------------------------------
# Middleware Helper Functions
# -----------------------------------------------------------------------------

def get_relationship_display(relationship):
    """
    Creates a user-friendly display string for a relationship.
    """
    rel_type = relationship.get('type', '')
    props = relationship.get('relationship', {}).get('props', {})
    
    # Add key properties to the display if they exist
    property_text = ''
    for key_prop in ['since', 'role', 'year']:
        if key_prop in props:
            property_text = f" ({key_prop}: {props[key_prop]})"
            break
    
    return f"{rel_type}{property_text}"

# Make helper functions available to all templates
app.jinja_env.globals.update(
    get_relationship_display=get_relationship_display
)

# -----------------------------------------------------------------------------
# Application Entry Point
# -----------------------------------------------------------------------------

if __name__ == '__main__':
    print(f"Starting G.A.R.D.E.N. Explorer...")
    print(f"Open your browser and go to: http://localhost:5000")
    app.run(debug=True)