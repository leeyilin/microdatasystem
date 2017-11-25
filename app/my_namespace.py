from flask_socketio import Namespace, emit, disconnect, join_room, leave_room
from datetime import datetime
import asyncio
import threading
from . import mds_data_set, global_info, process_data
from .global_info import global_server_infos


def my_namespace(socketio_obj):
    class _ClientTask(object):
        def __init__(self, name):
            self._name = name
            self._stop_task = False
            self._socketio_obj = socketio_obj
            self._keep_alive_start_time = datetime.now()

        def __repr__(self):
            return '<_ClientTask>'

        def receive_keep_alive(self):
            self._keep_alive_start_time = datetime.now()

        def loop_task(self):
            loop = asyncio.new_event_loop()
            all_addr = [(item['server_ip'], item['port']) for item in global_server_infos]
            all_client = mds_data_set.register_all_8102(all_addr, loop)
            print('start background task.')
            while not self._stop_task and \
                    (datetime.now() - self._keep_alive_start_time).total_seconds() < _MyNamespace.KEEP_ALIVE_INTERVAL:
                for ip, client in all_client.items():
                    data = client.get_data()
                    if data:
                        data = [item.to_json() for item in data]
                        print('get data size: {}'.format(len(data)))
                        server_info = process_data.find_first_target_info(global_server_infos, ip)
                        self._socketio_obj.emit('push_data', {
                            'server_id': server_info['id'], 'market_time': data
                        }, room=self._name, namespace='/test')
                        # socketio_obj.sleep(3)
            print('end background task.')

        def stop(self):
            self._stop_task = True

    class _MyNamespace(Namespace):
        UNIQUE_ID = 0
        KEEP_ALIVE_INTERVAL = 30

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._unique_id = _MyNamespace.next_id()
            self._client_tasks = {}

        def __repr__(self):
            return '_MyNamespace<{}>'.format(self._unique_id)

        def on_my_ping(self, message):
            client_unique_name = message['room']
            self._client_tasks[client_unique_name].receive_keep_alive()
            emit('my_pong', room=client_unique_name)

        def on_connect(self):
            pass

        def on_leave_room(self, message):
            print('disconnect')
            client_unique_name = message['room']
            if client_unique_name in self._client_tasks:
                leave_room(client_unique_name)
                self._client_tasks[client_unique_name].stop()
                self._client_tasks.pop(client_unique_name)
                disconnect()

        def on_join_room(self, message):
            client_unique_name = message['room']
            if client_unique_name not in self._client_tasks:
                join_room(client_unique_name)
                self._client_tasks[client_unique_name] = _ClientTask(client_unique_name)
                t = threading.Thread(target=self._client_tasks[client_unique_name].loop_task)
                t.start()

        @staticmethod
        def next_id():
            _MyNamespace.UNIQUE_ID += 1
            return _MyNamespace.UNIQUE_ID

    return _MyNamespace
