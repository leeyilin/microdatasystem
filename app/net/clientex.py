import socket
import select
import errno
import logging
from app import basic_structs, mds_protocol


_formater = logging.Formatter(fmt='%(asctime)s %(name)-12s %(levelname)s %(message)s', datefmt='%F %T')
_stream_handler = logging.StreamHandler()
_stream_handler.setLevel(logging.INFO)
_stream_handler.setFormatter(_formater)

LOGGER = logging.getLogger('clientex')
LOGGER.addHandler(_stream_handler)


class SocketTask(object):
    def __init__(self, sock, mds_login_protocol_cls, mds_protocol_cls, target_market_id, target_stock_id):
        self._sock = sock
        self.buf = b''
        self._mds_login_protocol_cls = mds_login_protocol_cls
        self._mds_protocol_cls = mds_protocol_cls
        self._need_login = True
        self._is_task_finished = False
        self._target_market_id = target_market_id
        self._target_stock_id = target_stock_id
        self._stock_data = None

    def __repr__(self):
        return 'SocketTask<{}>'.format(self._sock)

    def need_login(self):
        return self._need_login

    def login(self):
        buffer = self._mds_login_protocol_cls.package_request(mds_protocol.MCM_VERSION)
        self._sock.sendall(buffer)

    def parse_login_info(self):
        read_length = self._mds_login_protocol_cls.all_from_bytes(self, self.buf)
        if read_length != 0:
            self._need_login = False
            self.buf = self.buf[read_length:]
        return read_length

    def request(self):
        if self._target_stock_id is None:
            buffer = self._mds_protocol_cls.package_request(is_pushed=5, market_id=self._target_market_id)
        else:
            buffer = self._mds_protocol_cls.package_request(is_pushed=5, market_id=self._target_market_id,
                                                            stock_id=self._target_stock_id)
        self._sock.sendall(buffer)

    def parse_responce(self):
        protocol_obj = self._mds_protocol_cls()
        read_length = protocol_obj.all_from_bytes(self.buf)
        if read_length != 0:
            self._stock_data = protocol_obj.get_stock_data()
            self.buf = self.buf[read_length:]
            self._is_task_finished = True
        return read_length

    def is_task_finished(self):
        return self._is_task_finished

    def get_stock_data(self):
        return self._stock_data

    def get_socket(self):
        return self._sock


def clientex_factory(*mds_protocols):
    class _ClientEx(object):
        def __init__(self, target_markets, **kwargs):
            self._mds_login_protocol_cls = mds_protocol.Protocol8001
            self._mds_protocols = list(mds_protocols)
            self._socks_to_task = {}
            self._target_markets = target_markets
            self._target_stock_id = kwargs.pop('stock_id', None)

        @staticmethod
        def _setup_connection(addr):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                sock.connect(addr)
                sock.setblocking(False)
            except Exception as e:
                raise RuntimeError('Fail to connect to: {}\n Exception: {}'.format(addr, e))
            else:
                return sock

        def connect(self, addr):
            for market_id in self._target_markets:
                for protocol in self._mds_protocols:
                    sock = self._setup_connection(addr)
                    # One socket task consists of one protocol and one market id.
                    self._socks_to_task[sock] = SocketTask(
                        sock, self._mds_login_protocol_cls, protocol, market_id, self._target_stock_id)

        def loop(self):
            # Reference the sockets instead of copying them.
            socks_to_write = [sock_task.get_socket() for sock_task in self._socks_to_task.values()]
            socks_to_read = [sock_task.get_socket() for sock_task in self._socks_to_task.values()]
            while socks_to_read or socks_to_write:
                rlist, wlist, _ = select.select(socks_to_read, socks_to_write, [])
                for sock in rlist:
                    while True:
                        try:
                            new_data = sock.recv(4096)
                        except socket.error as e:
                            if e.args[0] == errno.EWOULDBLOCK:
                                # This error code means we could have blocked if the socket was blocking.
                                # So we could just skip to the next socket.
                                break
                            sock.close()
                            socks_to_read.remove(sock)
                            socks_to_write.remove(sock)
                            self._socks_to_task.pop(sock, None)
                        else:
                            if not new_data:
                                break
                            else:
                                self._socks_to_task[sock].buf += new_data
                    socket_task = self._socks_to_task[sock]
                    if socket_task.need_login():
                        socket_task.parse_login_info()
                    if not socket_task.need_login() and not socket_task.is_task_finished():
                        if socket_task.parse_responce() != 0:
                            sock.close()
                            socks_to_read.remove(sock)

                # Assume that the data is sent successfully at one time.
                for sock in wlist:
                    socket_task = self._socks_to_task[sock]
                    socket_task.login()
                    socket_task.request()
                    socks_to_write.remove(sock)

        # This method failed on the baoleiji.
        def iter_stock_data_list(self):
            for task in self._socks_to_task.values():
                yield task.get_stock_data()

        def close(self):
            self._socks_to_task = {}

    return _ClientEx


