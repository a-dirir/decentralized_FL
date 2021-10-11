import logging
import pickle
from flask import send_file, request, Flask, make_response
from os import path

from dFL.Peer.node import Node
from dFL.Security.files import read_file
from dFL.Utils.config import config


root_directory: str = path.normpath(config['root_directory'])


class Server:
    def __init__(self, node_id: int, port: int, host: str = "127.0.0.1"):
        self.node = Node(node_id)

        self.app = Flask(__name__)
        self.routes()
        self.app.logger.disabled = True
        log = logging.getLogger('werkzeug')
        log.disabled = True
        self.app.run(port=port, host=host)

    def routes(self):
        @self.app.route('/', methods=["POST"])
        def get_block():
            request_msg = request.get_json()

            try:
                requester_id = request_msg['node_id']

                msg = self.node.secure_communication.ingress(request_msg)
                if msg is None:
                    return {"Error": "Authentication Fails"}, 400

                block_num = msg['block_num']
                process_id = msg['ms_msg']['process_id']

                if not self.node.secure_communication.signer.verify_other_signatures(msg["ms_signature"],
                                                                                     pickle.dumps(msg['ms_msg']),
                                                                                     self.node.main_server.ds_key):
                    return make_response(f"Main Server Signature is not valid", 401)

                if requester_id != msg['ms_msg']['requester_id']:
                    return make_response(f"node id and authorized id do not match", 402)

                if msg['ms_msg']['blocks'].get(block_num) is None or self.node.node_id not in msg['ms_msg']['blocks'][block_num]:
                    return make_response(f"You are not authorized for this block {block_num}", 403)


                file_extension = msg['ms_msg']['file_extension']
                file_path = path.join(self.node.working_dir, "Processes", f"Process_{process_id}", "data")
                if block_num < 1000:
                    file_name = f"Node_{self.node.node_id}_Block_{block_num}.{file_extension}"
                else:
                    file_name = f"Block_{block_num}.{file_extension}"

                response = make_response(send_file(path.join(file_path,file_name)))
                info = read_file(file_path, file_name, info_only=True)
                response.headers['info'] = self.node.secure_communication.outgress(info, request_msg['ek'])
                return response
            except Exception as e:
                return make_response(f"{e}", 404)

