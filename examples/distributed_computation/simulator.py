import cv2
import numpy as np
import math
from copy import deepcopy


# This is a simple class to resemble a node in the graph, will be used for drawing..
class Node:
    def __init__(self, x_pos, y_pos, text):
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.text = text
        self.color = (0, 255, 0)



# This class is used for drawing the dependency graph, show the interaction between nodes.
class DrawGraph:
    def __init__(self, num_nodes, height=800, width=800):
        self.height = height
        self.width = width
        self.nodes = {}
        self.num_nodes = num_nodes
        self.image = np.ones((self.height, self.width, 3), np.uint8) * 255
        self.draw_initial_graph()

    def draw_node(self, index):
        radius = 15
        thickness = 3
        image = cv2.circle(self.image, (self.nodes[index].x_pos, self.nodes[index].y_pos),
                           radius, self.nodes[index].color, thickness)
        cv2.putText(image, self.nodes[index].text,
                    (self.nodes[index].x_pos - 5, self.nodes[index].y_pos + 5),
                    cv2.FONT_HERSHEY_DUPLEX, 0.40, (0, 0, 0), 1, cv2.LINE_AA)

    def draw_connections(self, source, destination, color=(0, 255, 0)):
        image = deepcopy(self.image)
        cv2.arrowedLine(image, (source.x_pos, source.y_pos - 15),
                        (destination.x_pos, destination.y_pos + 15),
                        color, 1, tipLength=0.05)

        cv2.imshow('Graph', image)
        cv2.waitKey(200)

    def draw_initial_graph(self):
        theta = 360 // self.num_nodes
        center = (self.width // 2, self.height // 2)
        radius = self.width // 2 - 50
        for i in range(self.num_nodes):
            angle = i * theta
            x = int(center[0] + radius * math.cos(math.radians(angle)))
            y = int(center[1] + radius * math.sin(math.radians(angle)))
            self.nodes[i] = Node(x, y, f'{i}')
            self.draw_node(i)

    def draw_graph(self):
        theta = 360 // self.num_nodes
        center = (self.width // 2, self.height // 2)
        radius = self.width // 2 - 50
        for i in range(self.num_nodes):
            angle = i * theta
            x = int(center[0] + radius * math.cos(math.radians(angle)))
            y = int(center[1] + radius * math.sin(math.radians(angle)))
            self.draw_node(x, y, f'{i}')
            self.nodes[i] = Node(x, y, i)

        self.draw_connections(self.nodes[0], self.nodes[9])

        cv2.imshow('Graph', self.image)
        cv2.waitKey(5000)

    def simulate_process(self, logs):
        for event in logs:
            if event[0] == 'Download':
                source_node = event[1][0]
                destination_node = event[1][1]
                self.draw_connections(self.nodes[source_node], self.nodes[destination_node])


def process_event(event):
    event = event.replace('\n', '')
    time, msg = event.split(';')
    time = time.split(' ')[1]
    return time, msg


events = []
maximum = 0
with open('logs.log', 'r') as f:
    for line in f.readlines():
        if line.find('Downloaded block') != -1:
            time, msg = process_event(line)

            source = int(msg[5:msg.find(' ')])
            destination = int(msg[msg.find('from ') + 5])
            if destination > maximum:
                maximum = destination

            events.append(['Download', (source, destination)])


drawer = DrawGraph(maximum+1)
drawer.simulate_process(events)