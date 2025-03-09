# Date generated: 2025-03-07T02:53:37.990000000+00:00

# Generated with modulegenerator version (0, 0, 0)
# Generated with neo4j driver version 4.4.0
import neo4j
import neo4j
from neo4j import GraphDatabase

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
        As of this version (3/3/25), there is no type checking -- all
        properties are converted to Strings for ease of development.
        We will use the metadata object to validate search terms.
        """
        # Unpack individual props
        print(props)
        
        text = f"""MATCH 
            (n:{label} 
            {'' if props is None else '{'} 
            {','.join(f"{prop}: ${prop}" for prop in props)}
            {'}' if props is None else '}'}) 
            RETURN n;"""

        return text, props
    
    def node_labels():
        text = 'CALL db.labels() YIELD label RETURN collect(label) AS labels;'
        params = None
        return text, params
    
    def node_type_properties():
        text = f"""
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
    
    def rel_type_properties():
        text = f"""
        CALL db.schema.relTypeProperties() YIELD relType, propertyName, propertyTypes
        UNWIND propertyTypes AS propertyType
        RETURN
            DISTINCT relType,
            propertyName,
            collect(propertyType) AS propertyTypes;"""
        params = None
        return text, params
    
    def node_properties(label, limit=None):
        text = f"""
            MATCH 
                (n:{label}) 
            WITH n 
            {f"LIMIT {limit}" if limit is not None else ""}
            UNWIND apoc.meta.cypher.types(n) AS props
            RETURN collect(DISTINCT props) AS props;
        """
        params = None
        return text, params
    
    def edge_types():
        text = 'CALL db.relationshipTypes() YIELD relationshipType RETURN collect(relationshipType) AS relationshipTypes;'
        params = None
        return text, params
    
    def edge_properties(type, limit=1000):
        text = f"""
            MATCH (a)-[e:{type}]->(b)
            WITH a, e, b
            {f"LIMIT {limit}" if limit is not None else ""}
            UNWIND apoc.meta.cypher.types(e) AS props
            RETURN collect(DISTINCT props) as props;
        """
        params = None 
        return text, params
    
    def edge_endpoints(type, limit=1000):
        text = f"""
            MATCH (a)-[e:{type}]->(b)
            WITH a, e, b
            {f"LIMIT {limit}" if limit is not None else ""}
            RETURN DISTINCT labels(a) AS startLabels, labels(b) AS endLabels;
        """
        params = None 
        return text, params

def _authenticated_driver(uri=profile['uri'], username=profile['username'], password=profile['password']):
    """
    Internal method to set up an authenticated driver.

    Parameters
    ----------
    uri: str
        neo4j connection string
    usernname: str
        username for the neo4j account
    password: str
        password for the neo4j account
    
    Returns
    -------
    neo4j.GraphDatabase.Driver instance to connect to the database.
    """
    return GraphDatabase.driver(uri, auth=(username, password))

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

def _server_timestamp():
    """
    Retrieves a timestamp from the neo4j isntance and prints a message 
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

