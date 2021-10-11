from os import path
from mongoengine import connect

from dFL.Security.communication import SecureCommunication
from dFL.MainServer.Handlers.node_handler import NodeHandler
from dFL.MainServer.Handlers.process_handler import ProcessHandler
from dFL.MainServer.Handlers.fl_handler import FLHandler
from dFL.Utils.config import config

connect(config['database']['name'], host=config['database']['ip'],port=config['database']['port'])


class Handlers:
    def __init__(self, directory: str):
        self.secure_communication = SecureCommunication(-1, path.join(directory))
        self.handlers = {'node': NodeHandler(), 'process': ProcessHandler(), 'fl': FLHandler()}

    def handle(self, request_msg: dict, handler: str):

        node_id = request_msg['node_id']
        msg = self.secure_communication.ingress(request_msg)
        if msg is None:
            return {"Error": "Authentication Fails"}, 400

        response_msg, status_code = self.handlers[handler].handle_request(msg, node_id)
        response_content = self.secure_communication.outgress(response_msg, request_msg['ek'])

        return response_content, status_code


