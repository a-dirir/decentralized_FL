import json
import requests
from os import path, mkdir
from uuid import uuid4
from cryptography.hazmat.primitives import serialization

from dFL.Peer.registration import Registration
from dFL.Security.communication import SecureCommunication
from dFL.Security.files import save_peer_file
from dFL.Utils.util import c2b, hash_msg
from dFL.Utils.config import config


root_directory: str = path.normpath(config['root_directory'])
main_server_url: str = config['main_server']['url']


class MainServer:
    def __init__(self):
        signature_key_bytes = c2b(config['main_server']['signature_key'])
        self.ds_key = serialization.load_pem_public_key(signature_key_bytes).public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        encryption_key_bytes = c2b(config['main_server']['encryption_key'])
        self.ec_key = serialization.load_pem_public_key(encryption_key_bytes).public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )


class Node:
    def __init__(self, node_id=None):
        self.main_server = MainServer()
        if node_id is not None:
            self.node_id = node_id
            self.working_dir = path.join(root_directory, f'Node_{self.node_id}')
            self.secure_communication = SecureCommunication(node_id, self.working_dir)
            self.registration = Registration(self)

        else:
            self.secure_communication = SecureCommunication()
            self.registration = Registration(self)
            self.node_id = self.registration.create_node({"name": uuid4().hex})
            if self.node_id is not None:
                self.secure_communication.node_id = self.node_id
                self.working_dir = path.join(root_directory, f'Node_{self.node_id}')
                mkdir(self.working_dir)
                mkdir(path.join(self.working_dir, "Processes"))
                self.secure_communication.signer.store_keys(self.working_dir)
                self.secure_communication.encryptor.store_keys(self.working_dir)


    def send_request(self, msg: dict, pek: bytes, end_point: str, return_response=False):
        try:
            msg = self.secure_communication.outgress(msg, pek)
            response = requests.post(end_point, json=msg).json()
            if response['status_code'] == 200:
                return self.secure_communication.ingress(response["msg"], return_response)
            else:
                return None
        except Exception as e:
            return None

    def download_file(self, msg: dict, pek: bytes, psk: bytes, end_point: str, storage_directory: str, file_name: str):
        try:
            msg = self.secure_communication.outgress(msg, pek)
            response = requests.post(end_point, json=msg)
            if response.status_code == 200:
                info_cipher = json.loads(response.headers['info'].replace("'", "\""))
                info = self.secure_communication.ingress(info_cipher)

                file_hash = hash_msg(response.content)
                is_valid = self.secure_communication.signer.verify_other_signatures(c2b(info['signature']),file_hash, psk)
                if is_valid:
                    save_peer_file(response.content, storage_directory, file_name, info)
                    return info
                else:
                    return None
            else:
                return None
        except Exception as e:
            return None

