from os import path
from time import sleep
import numpy as np
import multiprocessing


from dFL.Peer.node import Node
from dFL.Peer.server import Server
from dFL.Utils.util import c2b, get_time_difference, hash_msg, get_logger
from dFL.Utils.config import config
from dFL.Security.files import save_file, read_file


root_directory: str = path.normpath(config['root_directory'])
main_server_url: str = config['main_server']['url']
logger = get_logger(__name__)


class Client:
    def __init__(self, node_id: int, process_id: int):
        self.node_id = node_id
        self.process_id = process_id
        self.node = Node(node_id=node_id)
        self.process_path = path.join(self.node.working_dir, "Processes", f"Process_{process_id}", "data")

        self.info, self.participants = self.load_info()
        self.file_extension = self.info['file_extension']

        self.state = {}
        self.lookup = self.build_lookup()

        self.shape_blocks = {}

    def load_info(self):
        response = self.node.registration.get_process(self.process_id)
        if response is not None:
            logger.info(f"Node_{self.node_id} -> Downloaded the configurations for process {self.process_id}")
            return response['process']['process_info'], response['process']['participants']
        else:
            logger.error(f"Node_{self.node_id} -> Unable to download the configurations for process {self.process_id}")
            return None

    def build_lookup(self):
        lookup = {}
        for index, participant in enumerate(self.participants):
            lookup[participant['node_id']] = {
                "index": index,
                "psk": c2b(participant['info']['sk']),
                "pek": c2b(participant['info']['ek']),
                "end_point": participant['end_point']
            }
        return lookup

    def store_blocks(self, blocks: list):
        for block_num, block in enumerate(blocks):
            self.shape_blocks[block_num] = block.shape
            save_file(block.tobytes(), self.process_path,
                      f'Node_{self.node_id}_Block_{block_num}.{self.file_extension}', self.node)

            logger.info(f"Node_{self.node_id} -> Saved block {block_num} for process {self.process_id}")


    def get_blocks(self, ms_msg: dict, ms_signature: bytes) -> None:
        for block_num in ms_msg['blocks']:
            if self.state.get(block_num) is None:
                self.state[block_num] = {"senders": [self.node_id], "aggregation_hash": ""}

            for sender in ms_msg['blocks'][block_num]:
                if sender == self.node.node_id:
                    continue

                msg = {'block_num': block_num, 'ms_msg': ms_msg, 'ms_signature': ms_signature}
                if block_num < 1000:
                    file_name = f"Node_{sender}_Block_{block_num}.{self.file_extension}"
                else:
                    file_name = f"Block_{block_num}.{self.file_extension}"

                response = self.node.download_file(msg, self.lookup[sender]['pek'],
                                                   self.lookup[sender]['psk'],
                                                   self.lookup[sender]['end_point'],
                                                   self.process_path, file_name)
                if response is not None:
                    self.state[block_num]['senders'] += [sender]
                    logger.info(f"Node_{self.node_id} -> Downloaded block {block_num} from {sender}")
                else:
                    logger.error(f"Node_{self.node_id} -> Unable tp download block {block_num} from {sender}")

    def aggregate_blocks(self) -> None:
        for block_num in self.state:
            flag = True
            for sender in self.state[block_num]["senders"]:
                filename = f"Node_{sender}_Block_{block_num}.{self.file_extension}"
                block_bytes, _ = read_file(self.process_path, filename)
                block_data = np.frombuffer(block_bytes, dtype=np.float32)
                block_data = np.reshape(block_data, self.shape_blocks[block_num]) * 1000000

                if flag:
                    aggregation_result = np.array(block_data, dtype=np.int32)
                    flag = False
                else:
                    aggregation_result += np.array(block_data, dtype=np.int32)

            aggregation_result = aggregation_result / (1000000*len(self.state[block_num]["senders"]))
            aggregation_result = np.array(aggregation_result, dtype=np.float32)

            self.state[block_num]["aggregation_hash"] = hash_msg(aggregation_result.tobytes()).hex()

            save_file(aggregation_result.tobytes(), self.process_path,
                      f"Block_{block_num+1000}.{self.file_extension}", self.node)

            logger.info(f"Node_{self.node_id} -> Aggregated and saved block {block_num}")

    def load_aggregated_blocks(self):
        blocks = []
        for block_num in range(self.info['num_blocks']):
            filename = f"Block_{block_num+1000}.{self.file_extension}"
            block_bytes, _ = read_file(self.process_path, filename)
            block_data = np.frombuffer(block_bytes, dtype=np.float32)
            block_data = np.reshape(block_data, self.shape_blocks[block_num])
            blocks += [block_data]

            logger.info(f"Node_{self.node_id} -> Loaded block {block_num}")

        return blocks

    def run(self, wait_interval: int = 60) -> list:
        remaining_time = get_time_difference(self.info['start'])
        if remaining_time > 0:
            sleep(remaining_time)

        # Run the FL server to serve blocks to nodes
        fl_sever = multiprocessing.Process(target=Server, args=(self.node_id, (5001+self.node_id)), daemon=True)
        fl_sever.start()
        sleep(10)

        while True:
            msg = {"process_id": self.process_id, "status": self.state}
            response = self.node.send_request(msg, self.node.main_server.ec_key, f"{main_server_url}/fl", True)

            if response is None or response[0]['stage'] == -1:
                logger.error(f"Node_{self.node_id} -> Error in running the process")
                fl_sever.terminate()
                return []

            if response[0]['stage'] == 1:
                self.get_blocks(response[0], response[1]['signature'])

            elif response[0]['stage'] == 2:
                self.aggregate_blocks()

            elif response[0]['stage'] == 3:
                self.get_blocks(response[0], response[1]['signature'])
                sleep(wait_interval)
                fl_sever.terminate()
                logger.info(f"Node_{self.node_id} -> Done work in all blocks")
                return self.load_aggregated_blocks()

