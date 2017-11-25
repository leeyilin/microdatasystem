import socket
import logging


_formater = logging.Formatter(
    fmt='%(asctime)s %(name)-12s %(levelname)s %(message)s',
    datefmt='%F %T')

_shandler = logging.StreamHandler()
_shandler.setLevel(logging.INFO)
_shandler.setFormatter(_formater)

LOGGER = logging.getLogger("client")
LOGGER.addHandler(_shandler)


def default_message_callback(c, protocol_obj):
    print('client[{}] received protocol: {}'.format(c.cid, protocol_obj))
    # LOGGER.debug('client[{}] received protocol: {}'.format(c.cid, protocol_obj))


def default_state_callback(c, state):
    print('client[{}] state changed to: {}'.format(c.cid, state))
    # LOGGER.debug('client[{}] state changed to: {}'.format(c.cid, state))


def default_exception_callback(c, e):
    raise e


# The state machine in this class is really incomprehensible.
def BaseClient(protocol_cls):
    class _BaseClient(object):
        # State change: CLOSED -> CONNECTING -> CONNECTED -> WRITABLE
        # Afterwards, if the user calls close(),    -> CLOSING -> CLOSED
        # else -> CLOSED
        CLOSING = 0
        CLOSED = 1
        CONNECTING = 2
        CONNECTED = 3
        WRITABLE = 4

        STATE = {
            CLOSED: 'CLOSED', CONNECTING: 'CONNECTING',
            CONNECTED: 'CONNECTED', CLOSING: 'CLOSING',
            WRITABLE: 'WRITABLE',
        }

        current_client_id = 0

        def __init__(self, loop):
            self.cid = _BaseClient.next_cid()
            self.state = _BaseClient.CLOSED
            self.local_addr = None
            self.peer_addr = None
            self._loop = loop
            self._sock = None
            self._message_callback = default_message_callback
            self._state_callback = default_state_callback
            self._exception_callback = default_exception_callback
            self._buf = b''
            self._mds_all_protocols = protocol_cls()

        def __repr__(self):
            return 'Client<{}>'.format(self.cid)

        def connect(self, address):
            '''
            address should be a (host, port) tuple
            '''
            self._setup_connection()
            self.async_connect(address)

        def async_connect(self, host, port):
            raise NotImplementedError('')

        def is_connected(self):
            return self.state == self.CONNECTED or self.state == self.WRITABLE

        def send_data(self, data):
            return self.async_send_data(data)

        def async_send_data(self, data):
            raise NotImplementedError('do not use this class directly')

        def request(self, *protocols):
            assert len(protocols)
            tmp_buffer = b''
            for p in protocols:
                tmp_buffer += p.to_bytes()
            self.send_data(tmp_buffer)

        def parse_data(self, buf):
            return self._mds_all_protocols.all_from_bytes(self._buf)

        def handle_state_change(self, new_state):
            self._state_callback(self, new_state)

        def handle_packet(self, protocol_obj):
            self._message_callback(self, protocol_obj)

        def _handle_data(self, data):
            if not len(data):
                self._close()
            else:
                self._buf += data
                while True:
                    protocol_obj = self.parse_data(self._buf)
                    if not protocol_obj:
                        break
                    self._buf = self._buf[protocol_obj.size():]
                    self.handle_packet(protocol_obj)

        def _setup_connection(self):
            if self.state == _BaseClient.CONNECTED:
                raise RuntimeError('{} connected to {}'.format(
                    self, self._sock.getpeername())
                )

            if self.state == _BaseClient.CONNECTING:
                print('{} connection in progress'.format(self))
                # LOGGER.debug('{} connection in progress'.format(self))
                return

            self.state = _BaseClient.CONNECTING
            self._sock = socket.socket()

        def set_exception_callback(self, callback):
            self._exception_callback = callback or default_exception_callback

        def set_message_callback(self, callback):
            self._message_callback = callback or default_message_callback

        def set_state_callback(self, callback):
            self._state_callback = callback or default_state_callback

        def close(self):
            if self.state in (_BaseClient.CLOSING, _BaseClient.CLOSED):
                print('{}:close in {} state'.format(self, self.STATE[self.state]))
                # LOGGER.debug('{}:close in {} state'.format(self, self.STATE[self.state]))
                return

            self.state = _BaseClient.CLOSING
            self._close()

        def _change_state(self, new_state):
            if new_state == self.state:
                return

            LOGGER.debug('client<{}> state changed from [{}] to [{}]'.format(
                self.cid, _BaseClient.STATE[self.state], _BaseClient.STATE[new_state]
            ))

            if new_state == _BaseClient.CONNECTED:
                self.local_addr = '{}:{}'.format(*self._sock.getsockname())
                self.peer_addr = '{}:{}'.format(*self._sock.getpeername())

            self.handle_state_change(new_state)
            self.state = new_state

        def _close(self):
            if self.state == _BaseClient.CLOSED:
                return

            self._change_state(_BaseClient.CLOSED)
            self._buf = b''
            self._sock.close()

        @staticmethod
        def next_cid():
            _BaseClient.current_client_id += 1
            return _BaseClient.current_client_id

    return _BaseClient
