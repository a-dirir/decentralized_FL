import logging
from os import path
from flask import Flask, request, jsonify

from dFL.MainServer.handlers import Handlers
from dFL.Utils.config import config
from dFL.Utils.util import get_logger


logger = get_logger(__name__)


class ControlServer:
    def __init__(self):
        self.app = Flask(__name__)
        self.request_handler = Handlers(path.join(path.dirname(path.realpath(__file__)), 'keys'))
        self.routes()

        self.app.logger.disabled = True
        log = logging.getLogger('werkzeug')
        log.disabled = True

        logger.info('Control Server is up and running')
        self.app.run(host=config['main_server']['ip'], port=config['main_server']['port'])

    def routes(self):
        @self.app.route('/node', methods=['POST'])
        def node():
            request_msg = request.get_json()

            response_msg, response_status_code = self.request_handler.handle(request_msg, 'node')

            return jsonify(msg=response_msg, status_code=response_status_code)


        @self.app.route('/process', methods=['POST'])
        def process():
            request_msg = request.get_json()

            response_msg, response_status_code = self.request_handler.handle(request_msg, 'process')

            return jsonify(msg=response_msg, status_code=response_status_code)


        @self.app.route('/fl', methods=['POST'])
        def fl():
            request_msg = request.get_json()

            response_msg, response_status_code = self.request_handler.handle(request_msg, 'fl')

            return jsonify(msg=response_msg, status_code=response_status_code)
