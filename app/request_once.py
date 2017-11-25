import asyncio
from app import net, const_protocol


def request_once(*protocols):
    class RequestOnce(object):
        unique_id = 0

        def __init__(self, loop=None):
            self._unique_id = RequestOnce._next_id()
            self._protocols = protocols
            self._received_protocol_counter = 0
            self._loop = loop or asyncio.new_event_loop()
            # The event loop handles almost all exceptions internally,
            # set this handler in order to know the detail of the exception.
            self._loop.set_exception_handler(self.exception_handler)
            self._addr = None
            self.client = net.Client(self._loop)
            self.client.set_message_callback(self.handle_received_protocol)
            self.client.set_state_callback(self.state_callback)
            self._protocol_stock_data = {}
            self._exception_description = None

        def __repr__(self):
            return 'RequestOnce<{}>'.format(self._unique_id)

        def connect(self, address):
            self._addr = address
            self.client.connect(self._addr)
            # In case of long-time non-response.
            self._loop.call_later(5 * len(self._protocols), self.negative_stop)
            self._loop.run_forever()

        def negative_stop(self):
            self._loop.stop()
            raise RuntimeError('Connection Timeout: {}...'.format(self._addr))

        def handle_received_protocol(self, c, protocol_obj):
            self._protocol_stock_data[protocol_obj.message_id] = protocol_obj.get_stock_data()
            self._received_protocol_counter += 1
            if self._received_protocol_counter == len(self._protocols):
                self._loop.stop()

        def state_callback(self, c, new_state):
            if new_state == net.Client.CONNECTED:
                for p in self._protocols:
                    c.request(p)

        def get_data(self):
            if self._exception_description is None:
                return self._protocol_stock_data
            else:
                raise RuntimeError(self._exception_description)

        def exception_handler(self, loop, context):
            self._exception_description = context.get('exception', None)

        @staticmethod
        def _next_id():
            RequestOnce.unique_id += 1
            return RequestOnce.unique_id

    return RequestOnce
