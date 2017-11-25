import os
import socket
import errno
from app.net import base_client
from app import mds_protocol

LOGGER = base_client.LOGGER


def client(mds_protocol_cls):
    class _Client(base_client.BaseClient(mds_protocol_cls)):
        def __init__(self, loop):
            super().__init__(loop)

        def async_connect(self, addr):
            self._sock.setblocking(False)
            ec = self._sock.connect_ex(addr)
            if ec == errno.EINPROGRESS:
                self._loop.add_writer(self._sock.fileno(), self._handle_writeable)
            else:
                raise RuntimeError('Failed to connect to {}: {}'.format(addr, os.strerror(ec)))

        def async_send_data(self, data):
            try:
                self._sock.sendall(data)
            except socket.error as e:
                if e.args[0] in (errno.EWOULDBLOCK, errno.EAGAIN):
                    # In this case, the local buffer is full.
                    # The STATE is not really changed so don't use _change_state()
                    self._state = self.CONNECTED
                    self._loop.add_writer(self._sock.fileno(), self._handle_writeable)
                elif e.args[0] != errno.EPIPE:
                    raise
                return False
            return True

        def _remove_watcher(self):
            if self._need_watch_writable():
                self._loop.remove_writer(self._sock.fileno())

            if self.is_connected():
                self._loop.remove_reader(self._sock.fileno())

        def _close(self):
            self._remove_watcher()
            super()._close()

        def _need_watch_writable(self):
            # the stable state is WRITABLE
            return self.state == self.CONNECTING or self.state == self.CONNECTED

        def _data_ready(self):
            try:
                data = self._sock.recv(65536)
            except socket.error as e:
                if e.args[0] not in (errno.EWOULDBLOCK, errno.EAGAIN, errno.ECONNRESET):
                    raise
            else:
                self._handle_data(data)

        # The socket is writable as long as the local buffer is not full.
        # So it is very easy to achieve the state 'writable'.
        # Once the connection is established, we can send data almost at any time.
        def _handle_writeable(self):
            LOGGER.info('state {}'.format(self.STATE[self.state]))
            # Remove the writer, otherwise the function will be called constantly.
            self._loop.remove_writer(self._sock.fileno())
            if not self.is_connected():
                e = self._sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
                if not e:
                    self._change_state(self.CONNECTED)
                    self._change_state(self.WRITABLE)
                    self._loop.add_reader(self._sock.fileno(), self._data_ready)
                else:
                    print('connection: {}'.format(os.strerror(e)))
                    self._close()
                    raise RuntimeError(os.strerror(e))
            else:
                self._change_state(self.WRITABLE)

    return _Client


class Client(client(mds_protocol.MDSAllProtocols)):
    def __init__(self, loop, *args, **kwargs):
        super().__init__(loop, *args, **kwargs)
        self.mcm_version = mds_protocol.MCM_VERSION
        self.is_logined = False

    def handle_packet(self, protocol_obj):
        # Interrupt all login response here and behave like nothing happened.
        if protocol_obj.message_id == mds_protocol.PACK_PC_LOGIN:
            self.mcm_version = protocol_obj.mcm_version or 1
            self.state = Client.CONNECTING
            super().handle_state_change(Client.CONNECTED)
            self.state = Client.CONNECTED
            super().handle_state_change(Client.WRITABLE)
            self.state = Client.WRITABLE
            self.is_logined = True
        else:
            super().handle_packet(protocol_obj)

    def handle_state_change(self, new_state):
        if new_state >= Client.CONNECTED:
            if self.is_logined:
                super().handle_state_change(new_state)
            elif new_state == Client.CONNECTED and not self.is_logined:
                login_protocol = mds_protocol.Protocol8001()
                login_protocol.mcm_version = self.mcm_version
                self.request(login_protocol)
        else:
            self.is_logined = False
            super().handle_state_change(new_state)
