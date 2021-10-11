from dFL.MainServer.models import Node
from dFL.Utils.util import get_logger


logger = get_logger(__name__)


class NodeHandler:
    def __init__(self):
        pass

    def handle_request(self, request, node_id=None):
        if request['type'] == "create":
            return self.create_node(request)
        elif request['type'] == "read":
            return self.get_node(request)
        elif request['type'] == "read_all":
            return self.get_nodes()
        elif request['type'] == "update":
            return self.update_node(request, node_id)
        elif request['type'] == "delete":
            return self.delete_node(node_id)

    @staticmethod
    def create_node(data):
        try:
            node_id = Node.objects.count()
            Node(node_id=node_id, pek=data['ek'], psk=data['sk'], node_info=data['info']).save()
            logger.info(f"Success: Request to create new node, node_id = {node_id}")
            return {"node_id": node_id}, 200
        except Exception as e:
            logger.error(f"Error: Request to create new node, \n{e}")
            return {"Error": e}, 400

    @staticmethod
    def get_node(data):
        node_id = data['node_id']
        try:
            node = Node.objects(node_id=int(node_id))[0]
            logger.info(f"Success: Request to get info about a node, node_id = {node_id}")
            return {"node": node}, 200
        except Exception as e:
            logger.error(f"Error: Request to get info about a node, node_id = {node_id}, \n{e}")
            return {"Error": e}, 400

    @staticmethod
    def get_nodes():
        try:
            nodes = Node.objects()
            logger.info(f"Success: Request to get info about all nodes")
            return {"nodes": nodes}, 200
        except Exception as e:
            logger.error(f"Error: Request to get info about all nodes, \n{e}")
            return {"Error": e}, 400

    @staticmethod
    def update_node(data, node_id):
        try:
            node = Node.objects(node_id=int(node_id))[0]
            node.update(pek=data['ek'], psk=data['sk'], node_info=data['info'])
            logger.info(f"Success: Request to update a node, node_id = {node_id}")
            return {}, 200
        except Exception as e:
            logger.error(f"Error: Request to update a node, node_id = {node_id}, \n{e}")
            return {"Error": e}, 400

    @staticmethod
    def delete_node(node_id):
        try:
            node = Node.objects(node_id=int(node_id))[0]
            node.delete()
            logger.info(f"Success: Request to delete a node, node_id = {node_id}")
            return {"node_id": node_id}, 200
        except Exception as e:
            logger.error(f"Error: Request to delete a node, node_id = {node_id}, \n{e}")
            return {"Error": e}, 400

