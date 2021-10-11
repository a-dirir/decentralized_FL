from dFL.MainServer.models import Process
from dFL.Utils.util import get_logger


logger = get_logger(__name__)


class ProcessHandler:
    def __init__(self):
        pass

    def handle_request(self, request, node_id=None):
        if request['type'] == "create":
            return self.create_process(request, node_id)
        elif request['type'] == "read":
            return self.get_process(request)
        elif request['type'] == "read_all":
            return self.get_processes()
        elif request['type'] == "update":
            return self.update_process(request, node_id)
        elif request['type'] == "delete":
            return self.delete_process(request, node_id)
        elif request['type'] == "participate":
            return self.participate(request, node_id)

    @staticmethod
    def create_process(data, node_id):
        try:
            process_id = Process.objects.count()
            Process(process_id=process_id, process_info=data['info'], owner=node_id).save()
            logger.info(f"Success: Request to create new process, node_id = {node_id}, process_id = {process_id}")
            return {"process_id": process_id}, 200
        except Exception as e:
            logger.error(f"Error: Request to create new process,  node_id = {node_id} \n{e}")
            return {"Error": e}, 400

    @staticmethod
    def get_process(data):
        process_id = data['process_id']
        try:
            process = Process.objects(process_id=int(process_id))[0]
            logger.info(f"Success: Request to get info about a process, process_id = {process_id}")
            return {"process": process}, 200
        except Exception as e:
            logger.error(f"Error: Request to get info about a process, process_id = {process_id} \n{e}")
            return {"Error": e}, 400

    @staticmethod
    def get_processes():
        try:
            processes = Process.objects()
            logger.info(f"Success: Request to get info about all processes")
            return {"processes": processes}, 200
        except Exception as e:
            logger.error(f"Error: Request to get info about all processes \n{e}")
            return {"Error": e}, 400

    @staticmethod
    def update_process(data, node_id):
        process_id = data['process_id']
        try:
            process = Process.objects(process_id=int(process_id))[0]
            if process.owner != node_id:
                return {"Error": "You are not the owner"}, 400
            process.update(process_info=data['info'])
            logger.info(f"Success: Request to update a process, node_id = {node_id}, process_id = {process_id}")
            return {}, 200
        except Exception as e:
            logger.error(f"Error: Request to update a process, node_id = {node_id}, process_id = {process_id} \n{e}")
            return {"Error": e}, 400

    @staticmethod
    def delete_process(data, node_id):
        process_id = data['process_id']
        try:
            process = Process.objects(process_id=int(process_id))[0]
            if process.owner != node_id:
                return {"Error": "You are not the owner"}, 400
            process.delete()
            logger.info(f"Success: Request to delete a process, node_id = {node_id}, process_id = {process_id}")
            return {"process_id": process_id}, 200
        except Exception as e:
            logger.error(f"Error: Request to delete a process, node_id = {node_id}, process_id = {process_id} \n{e}")
            return {"Error": e}, 400

    @staticmethod
    def participate(data, node_id):
        process_id = data['process_id']
        try:
            process = Process.objects(process_id=int(process_id))[0]
            process.update(push__participants={
                'node_id': node_id, 'end_point': data['end_point'],'info': data['info']})
            logger.info(f"Success: Request to participate in a process, node_id = {node_id}, process_id = {process_id}")
            return {}, 200
        except Exception as e:
            logger.error(f"Error: Request to participate in a process, node_id = {node_id}, process_id = {process_id} \n{e}")
            return {"Error": e}, 400
