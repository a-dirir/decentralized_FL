import shutil
from os import path, mkdir, walk

from dFL.Utils.util import c2s
from dFL.Utils.config import config


root_directory: str = path.normpath(config['root_directory'])
main_server_url: str = config['main_server']['url']


class Registration:
    def __init__(self, node):
        self.node = node
    
    def create_node(self, info: dict = None):
        if info is None:
            info = {}
        msg = {
            "type": "create",
            "info": info,
            "sk": c2s(self.node.secure_communication.signer.get_public_key()),
            "ek": c2s(self.node.secure_communication.encryptor.get_public_key())
        }

        response = self.node.send_request(msg, self.node.main_server.ec_key, f"{main_server_url}/node")
        if response is not None:

            return response['node_id']
        else:
            return None

    def update_node(self, info: dict = None):
        if info is None:
            return None

        msg = {
            "type": "update",
            "info": info,
            "sk": c2s(self.node.secure_communication.signer.get_public_key()),
            "ek": c2s(self.node.secure_communication.encryptor.get_public_key())
        }

        response = self.node.send_request(msg, self.node.main_server.ec_key, f"{main_server_url}/node")
        if response is not None:
            return response
        else:
            return None

    def get_node(self, node_id: int):
        msg = {
            "type": "read",
            "node_id": node_id
        }
        response = self.node.send_request(msg, self.node.main_server.ec_key, f"{main_server_url}/node")
        if response is not None:
            return response
        else:
            return None

    def get_nodes(self):
        msg = {
            "type": "read_all"
        }
        response = self.node.send_request(msg, self.node.main_server.ec_key, f"{main_server_url}/node")
        if response is not None:
            return response
        else:
            return None

    def delete_node(self):
        msg = {"type": "delete"}
        response = self.node.send_request(msg, self.node.main_server.ec_key, f"{main_server_url}/node")
        if response is not None:
            shutil.rmtree(self.node.working_dir)
            return True
        else:
            return None

    def create_process(self, info: dict = None):
        if info is None:
            return None

        msg = {"type": "create", "info": info}
        response = self.node.send_request(msg, self.node.main_server.ec_key, f"{main_server_url}/process")
        if response is not None:
            return response["process_id"]
        else:
            return None

    def get_process(self, process_id: int):
        msg = {"type": "read", "process_id": process_id}
        response = self.node.send_request(msg, self.node.main_server.ec_key, f"{main_server_url}/process")
        if response is not None:
            return response
        else:
            return None

    def get_processes(self):
        msg = {"type": "read_all"}
        response = self.node.send_request(msg, self.node.main_server.ec_key, f"{main_server_url}/process")
        if response is not None:
            return response
        else:
            return None

    def update_process(self, process_id, info: dict = None):
        if info is None:
            return None

        msg = {"type": "update", "process_id": process_id, "info": info}

        response = self.node.send_request(msg, self.node.main_server.ec_key, f"{main_server_url}/process")
        if response is not None:
            return response
        else:
            return None

    def delete_process(self, process_id: int):
        msg = {"type": "delete", "process_id": process_id}
        response = self.node.send_request(msg, self.node.main_server.ec_key, f"{main_server_url}/process")
        if response is not None:
            for main_directory_path, node_directories, _ in walk(root_directory):
                for node_directory in node_directories:
                    process_directory = path.join(main_directory_path, node_directory, "Processes",
                                                  f"Process_{process_id}")
                    shutil.rmtree(process_directory)
                break
            return True
        else:
            return None

    def participate(self, process_id: int, end_point: str = None, info: dict = None):
        if end_point is None:
            return None
        info['ek'] = c2s(self.node.secure_communication.encryptor.get_public_key())
        info['sk'] = c2s(self.node.secure_communication.signer.get_public_key())

        msg = {"type": "participate", "process_id": process_id, "end_point": end_point, "info": info}
        response = self.node.send_request(msg, self.node.main_server.ec_key, f"{main_server_url}/process")
        if response is not None:
            if path.exists(path.join(self.node.working_dir, "Processes", f"Process_{process_id}")):
                shutil.rmtree(path.join(self.node.working_dir, "Processes", f"Process_{process_id}"))
            mkdir(path.join(self.node.working_dir, "Processes", f"Process_{process_id}"))
            mkdir(path.join(self.node.working_dir, "Processes", f"Process_{process_id}", "data"))
            return response
        else:
            return None

