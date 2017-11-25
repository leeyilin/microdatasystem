import queue
from datetime import datetime
import asyncio
from app import net, mds_protocol, global_info


def register(*protocols):
    class _Register(object):
        unique_id = 0
        KEEP_ALIVE_INTERVAL = 30

        def __init__(self, loop=None):
            self._unique_id = _Register._next_id()
            self._protocols = protocols
            self._addr = None
            self._loop = loop or asyncio.new_event_loop()
            self._data_queue = queue.Queue(maxsize=200)
            self._keep_alive_protocol_cls = mds_protocol.Protocol8002
            self._keep_alive_start_time = datetime.now()
            self.client = net.Client(self._loop)
            self.client.set_message_callback(self.handle_received_protocol)
            self.client.set_state_callback(self.state_callback)

        def __repr__(self):
            return '_Register<{}>'.format(self._unique_id)

        def connect(self, addr):
            self._addr = addr
            self.client.connect(self._addr)

        def run(self):
            self._loop.run_forever()

        def handle_received_protocol(self, c, protocol_obj):
            # Handle keep alive negatively.
            self._handle_keep_alive()
            if protocol_obj.message_id != self._keep_alive_protocol_cls.message_id:
                try:
                    self._data_queue.put(protocol_obj.get_stock_data(), block=False)
                except queue.Full as e:
                    print('The internal data queue is full: {}'.format(e))
                    # Empty the old queue.
                    self._data_queue = queue.Queue(maxsize=200)
            else:
                print(protocol_obj.message_id)

        def state_callback(self, c, new_state):
            if new_state == net.Client.CONNECTED:
                for p in self._protocols:
                    c.request(p)
            else:
                print('new state: {}'.format(new_state))

        def _handle_keep_alive(self):
            now = datetime.now()
            if (now - self._keep_alive_start_time).total_seconds() > _Register.KEEP_ALIVE_INTERVAL:
                print('keep alive')
                self.client.request(self._keep_alive_protocol_cls())
                self._keep_alive_start_time = now

        def get_data(self):
            try:
                return self._data_queue.get(timeout=3)
            except queue.Empty as e:
                print('The internal data queue is empty: {}'.format(e))
                return None

        def get_addr(self):
            return self._addr

        def stop(self):
            self._loop.stop()

        @staticmethod
        def _next_id():
            _Register.unique_id += 1
            return _Register.unique_id

    return _Register
