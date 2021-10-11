from time import time
from dFL.Processes.fl import FL
from dFL.MainServer.models import Process


class FLHandler:
    def __init__(self):
        self.processes = {}

    def handle_request(self, request, node_id):
        process_id = request['process_id']
        if self.processes.get(process_id) is None:
            process = Process.objects(process_id=int(process_id))[0]
            info = process.process_info
            nodes = [participant['node_id'] for participant in process.participants]
            if node_id not in nodes or info['start'] > time():
                return {}, 400
            elif node_id in nodes and info['start'] <= time():
                self.processes[process_id] = FL(process_id, info, nodes)

        return self.processes[process_id].update_status(node_id, request['status']), 200

