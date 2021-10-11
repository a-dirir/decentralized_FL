import multiprocessing
import shutil
import pymongo
from os import path, mkdir
from time import time, sleep
import numpy as np

from dFL.Peer.client import Client
from dFL.Peer.node import Node
from dFL.utils.config import config
from dFL.MainServer.api import ControlServer

# Create the database for the main server if the database does not exist
def create_database():
    name = config['database']['name']
    ip = config['database']['ip']
    port = config['database']['port']
    db_client = pymongo.MongoClient(f"mongodb://{ip}/{port}")

    if name not in db_client.list_database_names():
        my_db = db_client[name]
    else:
        db_client.drop_database(name)
        my_db = db_client[name]

    my_db.create_collection("Nodes")
    my_db.create_collection("Processes")

    db_client.close()


# Create nodes and a process
def create_nodes(num_nodes, num_blocks):
    nodes: list = []
    process_id = 0
    for i in range(num_nodes):
        node = Node()
        if i == 0:
            # Create new FL Process
            process_id = node.registration.create_process({
                "num_blocks": num_blocks,
                "start": time(),
                "timeout": 60,
                "file_extension": "csv"
            })

        node.registration.participate(process_id, f"http://127.0.0.1:{5001+i}", {'id': i})
        nodes += [node]

    return nodes



class DistributedComputation:
    def __init__(self, node_id, process_id):
        self.client = Client(node_id, process_id)
        self.train(node_id, self.client.info['num_blocks'])
        self.start_fl()

    def train(self, node_id, num_blocks):
        data = np.ones((num_blocks, 1), dtype=np.float32) * (node_id + 1)
        self.client.store_blocks(data)

    def start_fl(self):
        aggregated_blocks = self.client.run()
        print(f"{self.client.node_id} : Aggregation result is {aggregated_blocks}")


if __name__ == "__main__":
    control_server_process = multiprocessing.Process(target=ControlServer, daemon=True)
    control_server_process.start()
    sleep(3)

    if path.exists(config['root_directory']):
        shutil.rmtree(config['root_directory'])

    mkdir(config['root_directory'])

    create_database()
    nodes_list = create_nodes(10, 10)


    processes = []
    for i in range(10):
        processes += [multiprocessing.Process(target=DistributedComputation, args=(i, 0))]
        processes[-1].start()

    for pi in processes:
        pi.join()

    control_server_process.terminate()
