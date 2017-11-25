import queue
import threading
import time
from twisted.internet import protocol, reactor
from app import mds_protocol


class MyClient(protocol.Protocol):
    def __init__(self):
        # Why do this?
        super().__init__()
        self._buf = b''
        self._is_login = False
        self.mcm_version = mds_protocol.MCM_VERSION
        self._login_protocol = mds_protocol.Protocol8001()
        self._mds_protocol_8101 = mds_protocol.Protocol8101()
        self._mds_protocol_8103 = mds_protocol.Protocol8103()
        self._mds_protocol_8104 = mds_protocol.Protocol8104()
        self._mds_protocol_8115 = mds_protocol.Protocol8115()

    def dataReceived(self, data):
        self._buf += data
        self.parse_data()
        # self.transport.loseConnection()

    def connectionMade(self):
        print('Connection made! Now login....')
        self.login()

    def parse_data(self):
        if not self._is_login:
            self.parse_login()
            self.request_8101(1, 116, '00700')
            # self.request_8103(5, 116, '00700')
            # self.request_8115(5, 116, '00700')
            # self.request_8104(5, 116, '00700')
        else:
            self.parse_message_8101()
            # self.parse_message_8115()
            # self.parse_message_8104()

    def send_data(self, data):
        self.transport.write(data)

    def login(self):
        login_packet = self._login_protocol.package_request(self.mcm_version)
        self.send_data(login_packet)

    def parse_login(self):
        read_length = self._login_protocol.all_from_bytes(self._buf)
        if read_length:
            self._buf = self._buf[read_length:]
            self._is_login = True

    def request_8101(self, is_pushed, market_id, stock_id):
        if self._is_login:
            packet = self._mds_protocol_8101.package_request(is_pushed, market_id, stock_id)
            self.send_data(packet)

    def request_8103(self, is_pushed, market_id, stock_id):
        if self._is_login:
            packet = self._mds_protocol_8103.package_request(is_pushed, market_id, stock_id)
            self.send_data(packet)

    def request_8104(self, is_pushed, market_id, stock_id, period=1):
        if self._is_login:
            packet = self._mds_protocol_8104.package_request(is_pushed, market_id, stock_id, period)
            self.send_data(packet)

    def request_8115(self, is_pushed, market_id, stock_id):
        if self._is_login:
            packet = self._mds_protocol_8115.package_request(is_pushed, market_id, stock_id)
            self.send_data(packet)

    def parse_message_8101(self):
        read_length = self._mds_protocol_8101.all_from_bytes(self._buf)
        if read_length:
            self._buf = self._buf[read_length:]
            stock_data = self._mds_protocol_8101.get_stock_data()
            global qt_queue
            try:
                qt_queue.put(stock_data, block=False)
            # print('receive a packet: {}'.format(stock_data))
            except queue.Full:
                pass

    def parse_message_8103(self):
        read_length = self._mds_protocol_8103.all_from_bytes(self._buf)
        if read_length:
            self._buf = self._buf[read_length:]
            stock_data = self._mds_protocol_8103.get_stock_data()
            print('receive a packet: {}'.format(stock_data))

    def parse_message_8104(self):
        read_length = self._mds_protocol_8104.all_from_bytes(self._buf)
        if read_length:
            self._buf = self._buf[read_length:]
            stock_data = self._mds_protocol_8104.get_stock_data()
            # print('receive a packet: {}'.format(stock_data))

    def parse_message_8115(self):
        read_length = self._mds_protocol_8115.all_from_bytes(self._buf)
        if read_length:
            self._buf = self._buf[read_length:]
            stock_data = self._mds_protocol_8115.get_stock_data()
            print('receive a packet: {}'.format(stock_data))

    # This is useless currently.
    def keep_alive(self):
        packet = mds_protocol.Protocol8002.package_request()
        self.send_data(packet)


class MyClientFactory(protocol.ClientFactory):
    protocol = MyClient

    def __init__(self, ip, port):
        self._ip = ip
        self._port = port

    def startedConnecting(self, connector):
        print('Start connecting...')

    def clientConnectionLost(self, connector, reason):
        print('Connection Lost(IP: {} Port: {}). Reason: {}'.format(self._ip, self._port, reason))
        print('Stopping the reactor..')
        # reactor.stop()

    def clientConnectionFailed(self, connector, reason):
        print('Connection Failed(IP: {} Port: {}). Reason: {}'.format(self._ip, self._port, reason))
        print('Stopping the reactor..')
        # reactor.stop()


def worker():
    global qt_queue
    while True:
        try:
            qt = qt_queue.get(timeout=5)
            print('Get a qt from the queue! \n {}. Now sleep for three seconds.'.format(qt))
            time.sleep(3)
        except queue.Empty:
            break


def restart():
    time.sleep(10)
    print('Now stop the reactor temporarily...')
    reactor.stop()
    ip = '112.124.113.78'
    port = 1861
    cf = MyClientFactory(ip, port)
    reactor.connectTCP(ip, port, cf)
    print('Now run the reactor again...')
    reactor.run(installSignalHandlers=True)

def stop():
    time.sleep(5)
    # reactor.crash()
    reactor.stop()

