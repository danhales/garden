# Mock middleware for testing
class Nodes:
    def person(self, uuid=None, **props):
        return [{'uuid': '123', 'labels': ['Person'], 'props': {'name': 'Test Person', 'age': 30}}]
    
    def company(self, uuid=None, **props):
        return [{'uuid': '456', 'labels': ['Company'], 'props': {'name': 'Test Company'}}]

class Edges:
    def works_at(self, uuid=None, start_node_uuid=None, end_node_uuid=None, **props):
        return [(
            {'uuid': '123', 'labels': ['Person'], 'props': {'name': 'Test Person'}},
            {'uuid': '789', 'relType': 'WORKS_AT', 'props': {'since': 2020}},
            {'uuid': '456', 'labels': ['Company'], 'props': {'name': 'Test Company'}}
        )]

# Create instances
nodes = Nodes()
edges = Edges()

# Mock metadata
METADATA = {
    'node_labels': ['Person', 'Company'],
    'edge_types': ['WORKS_AT'],
    'node_properties': {
        'Person': {'name': 'STRING', 'age': 'INTEGER'},
        'Company': {'name': 'STRING'}
    },
    'edge_properties': {
        'WORKS_AT': {'since': 'INTEGER'}
    }
}