import multiprocessing
import shutil
import pymongo
from os import path, mkdir
from time import time, sleep


import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.datasets import mnist


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
                "timeout": 600,
                "file_extension": "csv"
            })

        node.registration.participate(process_id, f"http://127.0.0.1:{5001+i}", {'id': i})
        nodes += [node]

    return nodes


class DigitClassification:
    def __init__(self, node_index: int, num_nodes: int):
        self.ds_train, self.ds_val, self.ds_test = DigitClassification.load_data(node_index, num_nodes)
        self.model = DigitClassification.build_model()
        self.load_the_model()

    @staticmethod
    def load_data(node_index: int, num_nodes: int):
        (x_train, y_train), (x_test, y_test) = mnist.load_data()

        # Prepare training data
        size_train = int(x_train.shape[0] / num_nodes)
        start_train = node_index * size_train
        x_train = x_train[start_train: (start_train + size_train)]
        y_train = y_train[start_train: (start_train + size_train)]

        # Prepare validation data
        size_val = int(x_test.shape[0] / num_nodes * 0.25)
        start_val = node_index * size_val
        x_val = x_test[start_val: (start_val + size_val)]
        y_val = y_test[start_val: (start_val + size_val)]

        # Prepare testing data
        size_test = int(x_test.shape[0] / num_nodes * 0.75)
        start_test = start_val + size_val
        x_test = x_test[start_test: (start_test + size_test)]
        y_test = y_test[start_test: (start_test + size_test)]

        return (x_train, y_train), (x_val, y_val), (x_test, y_test)

    @staticmethod
    def build_model():
        model = tf.keras.models.Sequential([
            tf.keras.layers.Flatten(input_shape=(28, 28)),
            tf.keras.layers.Dense(128, activation='relu'),
            tf.keras.layers.Dense(128, activation='relu'),
            tf.keras.layers.Dense(10)
        ])

        model.compile(
            optimizer=tf.keras.optimizers.Adam(0.001),
            loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
            metrics=[tf.keras.metrics.SparseCategoricalAccuracy()],
        )

        return model

    def train_model(self, epochs: int = 1):
        self.model.fit(x=self.ds_train[0], y=self.ds_train[1], epochs=epochs, validation_data=self.ds_val)

    def get_model_parameters(self):
        return self.model.get_weights()

    def set_model_parameters(self, weights: list):
        self.model.set_weights(weights)

    def save_model(self):
        self.model.save('models')

    def load_the_model(self):
        self.model = load_model(path.join(path.dirname(path.realpath(__file__)), 'models'))

    def test_model(self):
        loss, acc = self.model.evaluate(x=self.ds_test[0], y=self.ds_test[1])
        return loss, acc


class FederatedLearning:
    def __init__(self, node_id, process_id):
        self.client = Client(node_id, process_id)
        node_index = self.client.lookup[node_id]['index']
        num_nodes = len(self.client.lookup)
        self.classifier = DigitClassification(node_index, num_nodes)
        self.train()
        sleep(10)
        self.start_fl()

    def train(self):
        self.classifier.train_model(20)
        data = self.classifier.get_model_parameters()
        self.client.store_blocks(data)

    def start_fl(self):
        loss_old, acc_old = self.classifier.test_model()
        model_updates = self.client.run()
        self.classifier.set_model_parameters(model_updates)
        loss_new, acc_new = self.classifier.test_model()
        print(f"{self.client.node_id} : Old model loss {loss_old}, acc {acc_old}")
        print(f"{self.client.node_id} : New model loss {loss_new}, acc {acc_new}")


if __name__ == "__main__":
    # uncomment this for one time to create the initial model
    # ds = DigitClassification(0,10)
    # ds.save_model()
    # print()

    control_server_process = multiprocessing.Process(target=ControlServer, daemon=True)
    control_server_process.start()
    sleep(3)

    if path.exists(config['root_directory']):
        shutil.rmtree(config['root_directory'])

    mkdir(config['root_directory'])

    create_database()
    nodes_list = create_nodes(6, 6)

    processes = []
    for i in range(6):
        processes += [multiprocessing.Process(target=FederatedLearning, args=(i, 0))]
        processes[-1].start()

    for pi in processes:
        pi.join()

    control_server_process.terminate()
