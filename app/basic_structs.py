from datetime import datetime
import sqlalchemy
import struct
import zlib
import array
from flask_login import UserMixin
from app import mcm
from app.mds_protocol import MCM_VERSION
from app import global_info
from app.global_info import Base, reverse_global_market_infos
'''
It is really weird that I fail to create the database tables with the tables' implementation
in the same file.
'''


class CString:
    # It is really a pity here that we set the default character set to 'gbk' instead of 'utf-8'
    # because the most platforms on the mds clients are Windows.
    def __init__(self, content='', size=0, character_set='gbk'):
        if not isinstance(content, str):
            raise ValueError('Exception: the given content is not a string')

        if size < len(content):
            raise ValueError('Exception: the given size is less than the length of the given content')

        self.length = size
        self.content = content.encode(encoding=character_set)
        while len(self.content) < size:
            self.content += b'\0'
        self.character_set = character_set

    def get_memory_size(self):
        return self.length

    def __str__(self):
        str_content = self.content.decode(encoding=self.character_set)
        trail_index = str_content.index('\0')

        return str_content[:trail_index]

    def __eq__(self, other):
        if isinstance(other, str):
            return str(self) == other
        elif isinstance(other, CString):
            return self.content == other.content
        else:
            return False

    def __hash__(self):
        return hash(str(self))

    def to_bytes(self, size=None):
        if not size:
            return self.content

        content = self.content
        while len(content) < size:
            content += b'\0'
        return content[:size]

    def from_bytes(self, buffer, size):
        self.content = buffer[:size]
        self.length = size

        return self

    def size(self):
        return self.length


class McmDataType(object):
    MEMORY_SIZE = 0

    @classmethod
    def get_memory_size(cls):
        return cls.MEMORY_SIZE

    def __init__(self):
        pass

    def __repr__(self):
        raise NotImplementedError()

    def from_raw_data(self, raw_data):
        raise NotImplementedError()

    def to_json(self):
        raise NotImplementedError()


class MDSPCRequestHead:
    MEMORY_SIZE = 14

    @classmethod
    def get_memory_size(cls):
        return cls.MEMORY_SIZE

    def __init__(self, package_size, message_id, owner_id=0, magic_id=0):
        self.package_size = package_size        # The size of the package body.
        self.message_id = message_id
        self.owner_id = owner_id
        self.magic_id = magic_id                # Double check the sent package.

    def __str__(self):
        return 'Package Size: %d, Message Id: %d, Owner Id: %d, Magic Id: %d' % \
               (self.package_size, self.message_id, self.owner_id, self.magic_id)

    def to_bytes(self):
        return struct.pack('<ihii', self.package_size, self.message_id, self.owner_id, self.magic_id)


class StockDictInfo:
    MEMORY_SIZE = 34

    @classmethod
    def get_memory_size(cls):
        return cls.MEMORY_SIZE

    def __init__(self, market_id, check_sum=''):
        self.market_id = market_id
        self.check_sum = CString(check_sum, 33)

    def __str__(self):
        return 'Market Id: %d, Check Sum: %s' % (self.market_id, self.check_sum)

    def to_bytes(self):
        return struct.pack('<B', self.market_id) + self.check_sum.to_bytes()


class PcStkDictRequestBody:
    def get_memory_size(self):
        self.MEMORY_SIZE = 5 + self.stock_dict_info.get_memory_size() * self.counter
        return self.MEMORY_SIZE

    def __init__(self, is_pushed, counter, stock_dict_infos):
        # is_pushed:
        #   0 for canceling registration
        #   1 for enabling pushing data
        #   5 for disabling pushing data.
        self.is_pushed = is_pushed
        self.counter = counter
        self.stock_dict_infos = stock_dict_infos

    def __str__(self):
        return 'is_pushed: %d, Counter: %d' % \
               (self.is_pushed, self.counter)

    def to_bytes(self):
        buffer = b''
        for info in self.stock_dict_infos:
            buffer += info.to_bytes()

        return struct.pack('<Bi', self.is_pushed, self.counter) + buffer


class MDSPcReactHead:
    MEMORY_SIZE = 17

    @classmethod
    def get_memory_size(cls):
        return cls.MEMORY_SIZE

    def __init__(self, package_size=0, message_id=0, owner_id=0,
                 is_result=b'\0', is_encrypted=b'\0', is_compressed=b'\0', magic_id=0):
        self.package_size = package_size
        self.message_id = message_id
        self.owner_id = owner_id
        self.is_result = is_result
        self.is_encrypted = is_encrypted
        self.is_compressed = is_compressed
        self.magic_id = magic_id

    def __str__(self):
        return 'Package Size: %d, Message Id: %d, Owner_id: %d, is_result: %s, is_encrypted: %s, ' \
               'is_compressed: %s, Magic Id: %d' % (self.package_size, self.message_id,
                                                    self.owner_id, self.is_result, self.is_encrypted,
                                                    self.is_compressed, self.magic_id)

    def from_bytes(self, buffer):
        if len(buffer) >= self.get_memory_size():
            self.package_size, self.message_id, self.owner_id, self.is_result, \
                self.is_encrypted, self.is_compressed, self.magic_id = \
                struct.unpack_from('<ihi3bi', buffer, offset=0)
            if len(buffer) >= self.get_memory_size() + self.package_size:
                return True
            else:
                return False
        else:
            return False


class SMarketStkDict:
    MEMORY_SIZE = 43

    @classmethod
    def get_memory_size(cls):
        return cls.MEMORY_SIZE

    def __init__(self, market_id=b'', is_result=b'', check_sum='', raw_size=0, compressed_size=0, data_buffer=''):
        self.market_id = market_id
        # is_result:
        #   0 for identification success.
        #   1 for identification failure.
        self.is_result = is_result
        self.check_sum = CString(check_sum, 33)
        self.raw_size = raw_size
        self.compressed_size = compressed_size
        self.data_buffer = data_buffer

    def __str__(self):
        return 'Market Id: %s, Is result: %s, Check sum: %s, Raw size: %d, Compressed size: %d' %\
               (self.market_id, self.is_result, self.check_sum, self.raw_size, self.compressed_size)

    def from_bytes(self, buffer):
        self.market_id, self.is_result = struct.unpack_from('<2B', buffer=buffer)
        self.check_sum.from_bytes(buffer=buffer[2:], size=33)
        self.raw_size, self.compressed_size = struct.unpack_from('<ii', buffer=buffer, offset=35)

        return self


class StockDictIndexTable(Base):
    __tablename__ = 'stock_dict_index_table'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    date = sqlalchemy.Column(sqlalchemy.String(16))
    server_ip = sqlalchemy.Column(sqlalchemy.String(16))
    market_id = sqlalchemy.Column(sqlalchemy.Integer)

    def __init__(self, date, server_ip, market_id):
        self.date = date
        self.server_ip = server_ip
        self.market_id = market_id
        self.stock_dicts = []

    def __str__(self):
        return 'date: %s server_ip: %s, market_id: %s, len(stock_dicts): %d' % \
               (self.date, self.server_ip, self.market_id, len(self.stock_dicts))

    def set_stock_dicts(self, stock_dicts):
        self.stock_dicts = stock_dicts


class CStdCacheStockDict(Base):
    __tablename__ = 'stock_dict'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    market_id = sqlalchemy.Column(sqlalchemy.Integer)
    type = sqlalchemy.Column(sqlalchemy.Integer)
    stock_name = sqlalchemy.Column(sqlalchemy.String(32))
    stock_code = sqlalchemy.Column(sqlalchemy.String(16))

    stock_dict_index_table_id = sqlalchemy.Column(sqlalchemy.Integer,
                                        sqlalchemy.ForeignKey('stock_dict_index_table.id'))
    # The str in orm.barckref must be the same as the name of the attribute of the according class.
    stock_dicts = sqlalchemy.orm.relationship('StockDictIndexTable',
                                                backref=sqlalchemy.orm.backref('stock_dicts'))

    MEMORY_SIZE = 50

    @classmethod
    def get_memory_size(cls):
        return cls.MEMORY_SIZE

    def __init__(self, market_id=b'', type=b'', stock_name='', stock_code=''):
        self.market_id = market_id
        self.type = type
        # It seems ok even though the types here are CString
        # while the corresponding field types in the database table are String.
        self.stock_name = CString(stock_name, 32)
        self.stock_code = CString(stock_code, 16)

    def __eq__(self, other):
        return (self.market_id == other.market_id and
                self.type == other.type and
                self.stock_name == other.stock_name and
                self.stock_code == other.stock_code)

    def __str__(self):
        return 'Market Id: %s, Type: %s, Stock Name: %s, Stock Code: %s' %\
            (self.market_id, self.type, self.stock_name, self.stock_code)

    def __hash__(self):
        return hash(self.market_id)

    def from_bytes(self, buffer):
        self.market_id, self.type = struct.unpack_from('<2B', buffer, offset=0)
        self.stock_name.from_bytes(buffer=buffer[2:], size=32)
        self.stock_code.from_bytes(buffer=buffer[34:], size=16)

        return self

    def to_json(self):
        return {
            'market_name': global_info.reverse_global_market_infos[self.market_id],
            'type': self.type,
            'stock_name': str(self.stock_name),
            'stock_code': str(self.stock_code)
        }


class GeneralRequestBody:
    MEMORY_SIZE = 11

    @classmethod
    def get_memory_size(cls):
        return cls.MEMORY_SIZE

    def __init__(self, is_pushed=b'',style_id=0, container_id=0, type=B'', market_id=B''):
        self.is_pushed = is_pushed
        self.style_id = style_id
        self.container_id = container_id
        # type:
        #   0: request based on individual market.
        self.type = type
        self.market_id = market_id

    def __str__(self):
        return 'is_pushed: %s, style_id: %d, container_id: %d, type: %s, market_id: %s' %\
               (self.is_pushed, self.style_id, self.container_id, self.type, self.market_id)

    def from_bytes(self, buffer):
        self.is_pushed, self.style_id, self.container_id, self.type, self.market_id = \
            struct.unpack_from('<b2i2B')

        return self

    def to_bytes(self):
        return struct.pack('<b2i2B', self.is_pushed, self.style_id, self.container_id,
                           self.type, self.market_id)


class RawMultiQtIndexTable(Base):
    __tablename__ = 'raw_multi_qt_index_table'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    date = sqlalchemy.Column(sqlalchemy.String(16))
    server_ip = sqlalchemy.Column(sqlalchemy.String(16))
    market_id = sqlalchemy.Column(sqlalchemy.Integer)

    def __init__(self, date, server_ip, market_id):
        self.date = date
        self.server_ip = server_ip
        self.market_id = market_id
        self.raw_multi_qts = []

    def __str__(self):
        return 'date: %s server_ip: %s, market_id: %d, len(raw_multi_qts): %d' % \
               (self.date, self.server_ip, self.market_id, len(self.raw_multi_qts))


class RawMultiQt(Base):
    __tablename__ = 'raw_multi_qt'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    trade_sequence = sqlalchemy.Column(sqlalchemy.Integer)
    trade_date = sqlalchemy.Column(sqlalchemy.Integer)
    trade_time = sqlalchemy.Column(sqlalchemy.Integer)
    stock_name = sqlalchemy.Column(sqlalchemy.String(32))
    stock_code = sqlalchemy.Column(sqlalchemy.String(16))
    market_id = sqlalchemy.Column(sqlalchemy.Integer)
    type = sqlalchemy.Column(sqlalchemy.String(1))
    trade_flag = sqlalchemy.Column(sqlalchemy.String(1))
    closed_price = sqlalchemy.Column(sqlalchemy.Integer)
    open_price = sqlalchemy.Column(sqlalchemy.Integer)
    highest_price = sqlalchemy.Column(sqlalchemy.Integer)
    lowest_price = sqlalchemy.Column(sqlalchemy.Integer)
    newest_price = sqlalchemy.Column(sqlalchemy.Integer)
    volume = sqlalchemy.Column(sqlalchemy.BigInteger)
    amount = sqlalchemy.Column(sqlalchemy.BigInteger)
    trade_number = sqlalchemy.Column(sqlalchemy.BigInteger)
    waipan = sqlalchemy.Column(sqlalchemy.BigInteger)
    current_volume = sqlalchemy.Column(sqlalchemy.BigInteger)
    current_volume_direction = sqlalchemy.Column(sqlalchemy.String(1))
    current_oi = sqlalchemy.Column(sqlalchemy.BigInteger)
    average_price = sqlalchemy.Column(sqlalchemy.Integer)
    open_interest = sqlalchemy.Column(sqlalchemy.BigInteger)
    settlement_price = sqlalchemy.Column(sqlalchemy.Integer)
    last_open_interest = sqlalchemy.Column(sqlalchemy.BigInteger)
    last_settlement_price = sqlalchemy.Column(sqlalchemy.Integer)
    limit_up = sqlalchemy.Column(sqlalchemy.Integer)
    limit_down = sqlalchemy.Column(sqlalchemy.Integer)

    raw_multi_qt_id = sqlalchemy.Column(sqlalchemy.Integer,
                                              sqlalchemy.ForeignKey('raw_multi_qt_index_table.id'))
    # The str in orm.barckref must be the same as the name of the attribute of the according class.
    raw_multi_qts = sqlalchemy.orm.relationship('RawMultiQtIndexTable',
                                                backref=sqlalchemy.orm.backref('raw_multi_qts'))
    MEMORY_SIZE = 288

    @classmethod
    def get_memory_size(cls):
        return cls.MEMORY_SIZE

    def __init__(self):
        self.trade_sequence = 0
        self.trade_date = 0
        self.trade_time = 0
        self.stock_name = CString('', 32)
        self.stock_code = CString('', 16)
        self.market_id = 0
        self.type = B''
        # trade_flag:
        #   0: for trading
        #   1: for trading closed
        self.trade_flag = B''
        self.closed_price = 0
        self.open_price = 0
        self.highest_price = 0
        self.lowest_price = 0
        self.newest_price = 0
        self.volume = 0
        self.amount = 0
        self.trade_number = 0
        self.mmp_prices = [0 for i in range(10)]
        self.mmp_volumes = [0 for i in range(10)]
        self.waipan = 0
        self.current_volume = 0
        self.current_volume_direction = b''
        self.current_oi = 0
        self.average_price = 0
        self.open_interest = 0
        self.settlement_price = 0
        self.last_open_interest = 0
        self.last_settlement_price = 0
        self.limit_up = 0
        self.limit_down = 0

    def __str__(self):
        return 'Stock Name: %s, Stock Code: %s, Close: %d, Open:%d, High: %d, Low:%d, Price:%d' % \
               (self.stock_name, self.stock_code, self.closed_price,
                self.open_price, self.highest_price, self.lowest_price ,self.newest_price)

    def from_crawmultiqt(self, craw_multi_qt):
        self.trade_sequence = craw_multi_qt.m_dwTradeSequence
        self.trade_date = craw_multi_qt.m_dwDate
        self.trade_time = craw_multi_qt.m_dwTime
        self.stock_name = CString(str(craw_multi_qt.m_pcName), 32)
        self.stock_code = CString(str(craw_multi_qt.m_pchCode), 16)
        self.market_id = int(craw_multi_qt.m_bytMarket)
        self.type = struct.pack('<B', craw_multi_qt.m_bytType)
        self.trade_flag = struct.pack('<B', craw_multi_qt.m_bytTradeFlag)
        self.closed_price = craw_multi_qt.m_dwClose
        self.open_price = craw_multi_qt.m_dwOpen
        self.highest_price = craw_multi_qt.m_dwHigh
        self.lowest_price = craw_multi_qt.m_dwLow
        self.newest_price = craw_multi_qt.m_dwPrice
        self.volume = craw_multi_qt.m_xVolume
        self.amount = craw_multi_qt.m_xAmount
        self.trade_number = craw_multi_qt.m_xTradeNum
        for i in range(10):
            self.mmp_prices[i] = craw_multi_qt.m_pdwMMP[i]
            self.mmp_volumes[i] = craw_multi_qt.m_pxMMPVol[i]
        self.waipan = craw_multi_qt.m_xWaiPan
        self.current_volume = craw_multi_qt.m_xCurVol
        self.current_volume_direction = struct.pack('<B', craw_multi_qt.m_cCurVol)
        self.current_oi = craw_multi_qt.m_xCurOI
        self.average_price = craw_multi_qt.m_dwAvg
        self.open_interest = craw_multi_qt.m_xOpenInterest
        self.settlement_price = craw_multi_qt.m_dwSettlementPrice
        self.last_open_interest = craw_multi_qt.m_xPreOpenInterest
        self.last_settlement_price = craw_multi_qt.m_dwPreSettlementPrice
        self.limit_up = craw_multi_qt.m_dwPriceZT
        self.limit_down = craw_multi_qt.m_dwPriceDT

        return self

    def to_json(self):
        attached_msg = 'Warning: '
        return {
            'market_name': global_info.reverse_global_market_infos.get(self.market_id, 'Unknown'),
            'trade_sequence': self.trade_sequence,
            'trade_date': self.trade_date,
            'close_price': self.closed_price,
            'open_price': self.open_price,
            'highest_price': self.highest_price,
            'lowest_price': self.lowest_price,
            'newest_price': self.newest_price,
            'volume': self.volume,
            'amount': self.amount,
            'stock_code': str(self.stock_code),
            'waipan': str(self.waipan) if self.waipan <= self.volume else (attached_msg + str(self.waipan))
        }


class SinaRawMultiQtIndexTable(Base):
    __tablename__ = 'sina_raw_multi_qt_index_table'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    date = sqlalchemy.Column(sqlalchemy.String(16))
    server_ip = sqlalchemy.Column(sqlalchemy.String(16))
    market_id = sqlalchemy.Column(sqlalchemy.Integer)

    def __init__(self, date, server_ip, market_id):
        self.date = date
        self.server_ip = server_ip
        self.market_id = market_id
        self.raw_multi_qts = []

    def __str__(self):
        return 'date: %s server_ip: %s, market_id: %d, len(raw_multi_qts): %d' % \
               (self.date, self.server_ip, self.market_id, len(self.raw_multi_qts))


class HKSERawMultiQtIndexTable(Base):
    __tablename__ = 'hkse_raw_multi_qt_index_table'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    date = sqlalchemy.Column(sqlalchemy.String(16))
    server_ip = sqlalchemy.Column(sqlalchemy.String(16))
    market_id = sqlalchemy.Column(sqlalchemy.Integer)

    def __init__(self, date, server_ip, market_id):
        self.date = date
        self.server_ip = server_ip
        self.market_id = market_id
        self.raw_multi_qts = []

    def __str__(self):
        return 'date: %s server_ip: %s, market_id: %d, len(raw_multi_qts): %d' % \
               (self.date, self.server_ip, self.market_id, len(self.raw_multi_qts))


class SinaRawMultiQt(Base):
    __tablename__ = 'sina_raw_multi_qt'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    market_id = sqlalchemy.Column(sqlalchemy.Integer)
    trade_date = sqlalchemy.Column(sqlalchemy.Integer)
    stock_name = sqlalchemy.Column(sqlalchemy.String(32))
    stock_code = sqlalchemy.Column(sqlalchemy.String(16))
    open_price = sqlalchemy.Column(sqlalchemy.Integer)
    highest_price = sqlalchemy.Column(sqlalchemy.Integer)
    lowest_price = sqlalchemy.Column(sqlalchemy.Integer)
    close_price = sqlalchemy.Column(sqlalchemy.Integer)
    newest_price = sqlalchemy.Column(sqlalchemy.Integer)
    volume = sqlalchemy.Column(sqlalchemy.BigInteger)
    amount = sqlalchemy.Column(sqlalchemy.BigInteger)

    sina_raw_multi_qt_index_table_id = sqlalchemy.Column(sqlalchemy.Integer,
                                        sqlalchemy.ForeignKey('sina_raw_multi_qt_index_table.id'))
    # The str in orm.barckref must be the same as the name of the attribute of the according class.
    raw_multi_qts = sqlalchemy.orm.relationship('SinaRawMultiQtIndexTable',
                                                backref=sqlalchemy.orm.backref('raw_multi_qts'))

    def __init__(self, **kwargs):
        self.market_id = 116
        # It seems ok even though the types here are CString
        # while the corresponding field types in the database table are String.
        self.stock_name = CString(kwargs.pop('stock_name', ''), 32)
        self.stock_code = CString(kwargs.pop('stock_code', ''), 16)
        self.trade_date = kwargs.pop('trade_date', 20121231)
        self.open_price = kwargs.pop('open_price', 0)
        self.highest_price = kwargs.pop('highest_price', 0)
        self.lowest_price = kwargs.pop('lowest_price', 0)
        self.close_price = kwargs.pop('close_price', 0)
        self.newest_price = kwargs.pop('newest_price', 0)
        self.volume = kwargs.pop('volume', 0)
        self.amount = kwargs.pop('amount', 0)

    def __str__(self):
        return str(self.to_json())

    def to_json(self):
        return {
            'stock_code': str(self.stock_code),
            'trade_date': self.trade_date,
            'open_price': self.open_price,
            'highest_price': self.highest_price,
            'lowest_price': self.lowest_price,
            'newest_price': self.newest_price,
            'volume': self.volume,
            'amount': self.amount,
        }


class HKSERawMultiQt(Base):
    __tablename__ = 'hkse_raw_multi_qt'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    market_id = sqlalchemy.Column(sqlalchemy.Integer)
    trade_date = sqlalchemy.Column(sqlalchemy.Integer)
    stock_code = sqlalchemy.Column(sqlalchemy.String(16))
    highest_price = sqlalchemy.Column(sqlalchemy.Integer)
    lowest_price = sqlalchemy.Column(sqlalchemy.Integer)
    newest_price = sqlalchemy.Column(sqlalchemy.Integer)
    volume = sqlalchemy.Column(sqlalchemy.BigInteger)
    amount = sqlalchemy.Column(sqlalchemy.BigInteger)

    hkse_raw_multi_qt_index_table_id = sqlalchemy.Column(sqlalchemy.Integer,
                                        sqlalchemy.ForeignKey('hkse_raw_multi_qt_index_table.id'))
    # The str in orm.barckref must be the same as the name of the attribute of the according class.
    raw_multi_qts = sqlalchemy.orm.relationship('HKSERawMultiQtIndexTable',
                                                backref=sqlalchemy.orm.backref('raw_multi_qts'))

    def __init__(self, **kwargs):
        self.market_id = 116
        # It seems ok even though the types here are CString
        # while the corresponding field types in the database table are String.
        self.stock_code = CString(kwargs.pop('stock_code', ''), 16)
        self.trade_date = kwargs.pop('trade_date', 20121231)
        self.highest_price = kwargs.pop('highest_price', 0)
        self.lowest_price = kwargs.pop('lowest_price', 0)
        self.newest_price = kwargs.pop('newest_price', 0)
        self.volume = kwargs.pop('volume', 0)
        self.amount = kwargs.pop('amount', 0)

    def __str__(self):
        return 'Market Id: %d, Stock Code: %s' %\
            (self.market_id, self.stock_code)

    def to_json(self):
        return {
            'stock_code': str(self.stock_code),
            'highest_price': self.highest_price,
            'lowest_price': self.lowest_price,
            'newest_price': self.newest_price,
            'volume': self.volume,
            'amount': self.amount,
        }


class SPcStkStockDictResponceBody():
    def __init__(self):
        self.MEMORY_SIZE = 4
        self.stock_dicts = []

    def from_bytes(self, buffer):
        if len(buffer) >= self.MEMORY_SIZE:
            read_length = 0
            counter, = struct.unpack_from('<i', buffer, read_length)
            read_length += 4
            decompress_obj = zlib.decompressobj()
            for i in range(counter):
                market_stk_dict = SMarketStkDict().from_bytes(buffer[read_length:])
                read_length += market_stk_dict.get_memory_size()
                raw_buffer = decompress_obj.decompress(buffer[read_length:])
                read_length += market_stk_dict.compressed_size
                self.MEMORY_SIZE = read_length
                stock_dict_counter = len(raw_buffer) // CStdCacheStockDict.get_memory_size()
                for j in range(stock_dict_counter):
                    stock_dict = CStdCacheStockDict().from_bytes(raw_buffer)
                    self.stock_dicts.append(stock_dict)
                    raw_buffer = raw_buffer[stock_dict.get_memory_size():]
            return True
        else:
            return False

    def get_stock_data(self):
        return self.stock_dicts


class SPcStkNewListResponceBody:
    # This function intends to return the actual size of the class in the
    # compressed buffer.
    def get_memory_size(self):
        return 7 + self.compressed_length

    def __init__(self):
        # status:
        #   exists when the message id == 8110
        #   removed when the message id == 8106
        self.status = B''
        # type:
        #   0: request based on individual market.
        #   1:
        #   4:
        self.request_type = B''
        self.market_id = B''
        self.compressed_length = 0
        self.raw_multi_qts = []

    def __str__(self):
        return 'status: %s, request_type: %s, market_id: %s, compressed_length: %d' %\
               (self.status, self.request_type, self.market_id, self.compressed_length)

    def from_bytes(self, buffer):
        read_length = 0
        self.status, self.request_type, self.market_id, self.compressed_length = \
            struct.unpack_from('<3Bi', buffer, offset=read_length)
        read_length += 7

        craw_multi_qts = mcm.Mcm().UcmpMultiQtList(list(buffer[read_length:]))
        for item in craw_multi_qts:
            raw_multi_qt = RawMultiQt().from_crawmultiqt(item)
            self.raw_multi_qts.append(raw_multi_qt)

        return self

    def get_raw_multi_qts(self):
        return self.raw_multi_qts


class SPcListFundFlowResponseBody:
    # This function intends to return the actual size of the class in the
    # compressed buffer.
    def get_memory_size(self):
        return self.MEMORY_SIZE

    def __init__(self):
        self.MEMORY_SIZE = 7
        # status:
        #   exists when the message id == 8110
        #   removed when the message id == 8106
        self.status = B''
        # type:
        #   0: request based on individual market.
        #   1:
        #   4:
        self.request_type = B''
        self.market_id = B''
        self.compressed_length = 0
        self.mcm_obj = mcm.Mcm()
        self.stock_datas = []

    def __str__(self):
        return '<SPcListFundFlowResponseBody>: status: %s, request_type: %s, market_id: %s, compressed_length: %d' %\
               (self.status, self.request_type, self.market_id, self.compressed_length)

    def from_bytes(self, buffer):
        if len(buffer) >= self.get_memory_size():
            self.stock_datas = []
            read_length = 0
            self.status, self.request_type, self.market_id, self.compressed_length = \
                struct.unpack_from('<3Bi', buffer, offset=read_length)
            read_length += 7
            self.MEMORY_SIZE += self.compressed_length
            list_multi_fund_flow_items = self.mcm_obj.UcmpListMultiFFItem(list(buffer[read_length:]), MCM_VERSION)
            for item in list_multi_fund_flow_items:
                stock_data = RawListMultiFundFlowItem().from_raw_list_multi_ff_item(item)
                self.stock_datas.append(stock_data)
            return True
        else:
            return False

    def get_stock_datas(self):
        return self.stock_datas


class SPcListBuyinRankResponseBody:
    # This function intends to return the actual size of the class in the
    # compressed buffer.
    def get_memory_size(self):
        return self.MEMORY_SIZE

    def __init__(self):
        self.MEMORY_SIZE = 7
        # status:
        #   exists when the message id == 8110
        #   removed when the message id == 8106
        self.status = B''
        # type:
        #   0: request based on individual market.
        #   1:
        #   4:
        self.request_type = B''
        self.market_id = B''
        self.compressed_length = 0
        self.mcm_obj = mcm.Mcm()
        self.stock_datas = []

    def __str__(self):
        return '<SPcListBuyinRankResponceBody> status: %s, request_type: %s, market_id: %s, compressed_length: %d' %\
               (self.status, self.request_type, self.market_id, self.compressed_length)

    def from_bytes(self, buffer):
        if len(buffer) >= self.get_memory_size():
            self.stock_datas = []
            read_length = 0
            self.status, self.request_type, self.market_id, self.compressed_length = \
                struct.unpack_from('<3Bi', buffer, offset=read_length)
            read_length += 7
            self.MEMORY_SIZE += self.compressed_length
            list_multi_buyin_rank_items = self.mcm_obj.UcmpListMultiBuyinRankItem(list(buffer[read_length:]), MCM_VERSION)
            for item in list_multi_buyin_rank_items:
                list_buyin_rank = RawListMultiBuyinRankItem().from_raw_list_multi_buyin_rank_item(item)
                self.stock_datas.append(list_buyin_rank)
            return True
        else:
            return False

    def get_stock_datas(self):
        return self.stock_datas


class SPcLoginRequestBody:
    MEMORY_SIZE = 85

    @classmethod
    def get_memory_size(cls):
        return cls.MEMORY_SIZE

    def __init__(self, mcm_version):
        self.version = 0
        self.minor_version = 0
        self.revision = 0
        self.proxy = 0
        self.build = 0
        self.mcm_version = mcm_version
        self.dummy = 0
        self.client_type = 0
        self.username = CString('X' * 31, 32)
        self.disk_id = 0
        self.password = CString('*' * 31, 32)
        self.login_id = 0

    def __str__(self):
        return 'mcm_version: {}, username: {}, password: {}'.format(self.mcm_version, self.username, self.password)

    def to_bytes(self):
        return struct.pack('<5b', self.version, self.minor_version,
                           self.revision, self.proxy, self.build) + \
                struct.pack('<HHi', self.mcm_version, self.dummy, self.client_type) +\
                self.username.to_bytes() + struct.pack('<I', self.disk_id) + self.password.to_bytes() +\
                            struct.pack('<I', self.login_id)


class SPcLoginResponceBody:
    MEMORY_SIZE = 38

    @classmethod
    def get_memory_size(cls):
        return cls.MEMORY_SIZE

    def __init__(self):
        self.version = 0
        self.minor_version = 0
        self.revision = 0
        self.mcm_version = 0
        self.dummy = 0
        self.begin_date = 0
        self.end_date = 0
        self.user_type = 0
        self.user_id = 0
        self.right = 0
        self.left_days = 0
        self.dhpub_key = CString('', 8)
        self.server_ip = 0          # Private IP.

    def __str__(self):
        return '<SPcLoginResponceBody>: version: {}, minor_version: {}, mcm_version: {}, ' \
               'user_id: {}, dhpub_key: {}, server_ip: {}'.format(self.version, self.minor_version, self.mcm_version,
                                      self.user_id, self.dhpub_key, self.server_ip)

    def from_bytes(self, buffer):
        if len(buffer) >= self.get_memory_size():
            read_length = 0
            self.version, self.minor_version, self.revision, self.mcm_version, self.dummy, self.begin_date, self.end_date, \
            self.user_type, self.user_id, self.right, self.left_days = struct.unpack_from('<3bHh4iBH', buffer, offset=read_length)
            read_length += 26
            self.dhpub_key.from_bytes(buffer=buffer[read_length:], size=8)
            read_length += 8
            self.server_ip, = struct.unpack_from('<i', buffer, read_length)
            read_length += 4
            return True
        else:
            return False


# For the use of double association table.
class RawMultiFundFlowItem(Base):
    __tablename__ = 'multi_fund_flow_item'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    buy_amount = sqlalchemy.Column(sqlalchemy.Integer)
    sell_amount = sqlalchemy.Column(sqlalchemy.Integer)
    buy_volume = sqlalchemy.Column(sqlalchemy.String(16))
    sell_volume = sqlalchemy.Column(sqlalchemy.String(16))

    list_multi_fund_flow_item_id = sqlalchemy.Column(sqlalchemy.Integer,
                                                                 sqlalchemy.ForeignKey(
                                                                     'list_multi_fund_flow_item.id'))
    # The str in orm.barckref must be the same as the name of the attribute of the according class.
    orders = sqlalchemy.orm.relationship('RawListMultiFundFlowItem',
                                                  backref=sqlalchemy.orm.backref('orders'))

    def __init__(self):
        self.buy_amount = 0
        self.sell_amount = 0
        self.buy_volume = ''
        self.sell_volume = ''

    def __str__(self):
        return 'buy_amount: %d, sell_amount: %d, buy_volume: %s, sell_volume: %s\n' %\
               (self.buy_amount, self.sell_amount, self.buy_volume, self.sell_volume)

    def from_sraw_multi_ff_item(self, item):
        self.buy_amount = item.m_buyAmount
        self.sell_amount = item.m_sellAmount
        # Their values are too big to be held as integers,
        # so I change their types to str.
        self.buy_volume = str(item.m_buyVolume)
        self.sell_volume = str(item.m_sellVolume)

        return self


class ListMultiFundFlowItemIndexTable(Base):
    __tablename__ = 'list_multi_fund_flow_item_index_table'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    date = sqlalchemy.Column(sqlalchemy.String(16))
    server_ip = sqlalchemy.Column(sqlalchemy.String(16))
    market_id = sqlalchemy.Column(sqlalchemy.Integer)

    def __init__(self, date, server_ip, market_id):
        self.date = date
        self.server_ip = server_ip
        self.market_id = market_id
        self.list_fund_flows = []

    def __str__(self):
        return 'date: %s server_ip: %s, market_id: %s, len(list_fund_flows): %d' % \
               (self.date, self.server_ip, self.market_id, len(self.list_fund_flows))

    def set_list_fund_flows(self, list_fund_flows):
        self.list_fund_flows = list_fund_flows


class RawListMultiFundFlowItem(Base):
    __tablename__ = 'list_multi_fund_flow_item'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    market_id = sqlalchemy.Column(sqlalchemy.Integer)
    stock_code = sqlalchemy.Column(sqlalchemy.String(16))
    call_auction_amount = sqlalchemy.Column(sqlalchemy.Integer)
    latest_price = sqlalchemy.Column(sqlalchemy.Integer)
    previous_close = sqlalchemy.Column(sqlalchemy.Integer)

    list_multi_fund_flow_item_index_table_id = sqlalchemy.Column(sqlalchemy.Integer,
                                                  sqlalchemy.ForeignKey('list_multi_fund_flow_item_index_table.id'))
    # The str in orm.barckref must be the same as the name of the attribute of the according class.
    list_fund_flows = sqlalchemy.orm.relationship('ListMultiFundFlowItemIndexTable',
                                              backref=sqlalchemy.orm.backref('list_fund_flows'))

    def __init__(self):
        self.market_id = B''
        self.stock_code = CString('', 16)
        self.orders = [RawMultiFundFlowItem() for i in range(4)]
        self.call_auction_amount = 0
        self.latest_price = 0
        self.previous_close = 0

    def __str__(self):
        str_orders = ''
        for order in self.orders:
            str_orders += str(order)

        return 'market_id: %d, stock_code: %s, call_auction_amount: %d, ' \
               'latest_price: %d, previous_close: %d \n orders: \n%s' %\
               (self.market_id, self.stock_code, self.call_auction_amount,\
                self.latest_price, self.previous_close, str_orders)

    def from_raw_list_multi_ff_item(self, item):
        self.orders = []
        # Notice that I change the type of market_id to int.
        self.market_id = int(item.marketID)
        self.stock_code = CString(str(item.stockCode), 16)
        self.call_auction_amount = item.m_callAuctionAmount
        self.latest_price = item.m_latestPrice
        self.previous_close = item.m_prevClose
        for i in range(4):
            order = RawMultiFundFlowItem().from_sraw_multi_ff_item(item.m_orders[i])
            self.orders.append(order)

        return self

    def to_json(self):
        return {
            'stock_code': str(self.stock_code),
            'call_auction_amount': self.call_auction_amount,
            'latest_price': self.latest_price,
            'previous_close': self.previous_close
        }


class RawMultiBuyinRankItem(Base):
    __tablename__ = 'multi_buyin_rank_item'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    previous_close = sqlalchemy.Column(sqlalchemy.Integer)
    buyin_ratio = sqlalchemy.Column(sqlalchemy.Integer)
    rank = sqlalchemy.Column(sqlalchemy.Integer)
    previous_rank = sqlalchemy.Column(sqlalchemy.Integer)

    list_multi_buyin_rank_item_id = sqlalchemy.Column(sqlalchemy.Integer,
                                                                 sqlalchemy.ForeignKey(
                                                                     'list_multi_buyin_rank_item.id'))
    # The str in orm.barckref must be the same as the name of the attribute of the according class.
    days = sqlalchemy.orm.relationship('RawListMultiBuyinRankItem',
                                                  backref=sqlalchemy.orm.backref('days'))

    def __init__(self):
        self.previous_close = 0
        self.buyin_ratio = 0
        self.rank = 0
        self.previous_rank = 0

    def __str__(self):
        return 'previous_close: %d, buyin_ratio: %d, rank: %d, previous_rank: %d\n' %\
               (self.previous_close, self.buyin_ratio, self.rank, self.previous_rank)

    def from_sraw_multi_buyin_rank_item(self, item):
        self.previous_close = item.m_prevClose
        self.buyin_ratio = int(item.m_buyinRatio * 10000)
        self.rank = item.m_rank
        self.previous_rank = item.m_prevRank

        return self

    def to_json(self):
        return {
            'previous_close': self.previous_close,
            'buyin_ratio': self.buyin_ratio,
            'rank': self.rank,
            'previous_rank': self.previous_rank
        }


class ListMultiBuyinRankItemIndexTable(Base):
    __tablename__ = 'list_multi_buyin_rank_item_index_table'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    date = sqlalchemy.Column(sqlalchemy.String(16))
    server_ip = sqlalchemy.Column(sqlalchemy.String(16))
    market_id = sqlalchemy.Column(sqlalchemy.Integer)

    def __init__(self, date, server_ip, market_id):
        self.date = date
        self.server_ip = server_ip
        self.market_id = market_id
        self.list_buyin_ranks = []

    def __str__(self):
        return 'date: %s server_ip: %s, market_id: %s, len(list_buyin_ranks): %d' % \
               (self.date, self.server_ip, self.market_id, len(self.list_buyin_ranks))

    def set_list_buyin_ranks(self, list_buyin_ranks):
        self.list_buyin_ranks = list_buyin_ranks


class RawListMultiBuyinRankItem(Base):
    __tablename__ = 'list_multi_buyin_rank_item'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    market_id = sqlalchemy.Column(sqlalchemy.Integer)
    stock_code = sqlalchemy.Column(sqlalchemy.String(16))
    latest_price = sqlalchemy.Column(sqlalchemy.Integer)

    list_multi_buyin_rank_item_index_table_id = sqlalchemy.Column(sqlalchemy.Integer,
                                                                 sqlalchemy.ForeignKey(
                                                                     'list_multi_buyin_rank_item_index_table.id'))
    # The str in orm.barckref must be the same as the name of the attribute of the according class.
    list_buyin_ranks = sqlalchemy.orm.relationship('ListMultiBuyinRankItemIndexTable',
                                                  backref=sqlalchemy.orm.backref('list_buyin_ranks'))

    def __init__(self):
        self.market_id = B''
        self.stock_code = CString('', 16)
        self.days = [RawMultiBuyinRankItem() for i in range(4)]
        self.latest_price = 0

    def __str__(self):
        str_days = ''
        for day in self.days:
            str_days += str(day)

        return 'market_id: %d, stock_code: %s, latest_price: %d, \n days: \n%s' % \
               (self.market_id, self.stock_code, self.latest_price, str_days)

    def from_raw_list_multi_buyin_rank_item(self, item):
        self.days = []
        # Notice that I change the type of market_id to int.
        self.market_id = int(item.marketID)
        self.stock_code = CString(str(item.stockCode), 16)
        self.latest_price = item.m_latestPrice
        for i in range(4):
            day = RawMultiBuyinRankItem().from_sraw_multi_buyin_rank_item(item.m_days[i])
            self.days.append(day)

        return self

    def to_json(self):
        list_buyin_rank = {
            'stock_code': str(self.stock_code),
            'latest_price': self.latest_price,
        }

        list_buyin_rank.update(self.days[0].to_json())

        return list_buyin_rank


class User(UserMixin, Base):
    __tablename__ = 'user'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    nickname = sqlalchemy.Column(sqlalchemy.String(32), index=True, unique=True)
    email = sqlalchemy.Column(sqlalchemy.String(48), index=True, unique=True)
    self_introduction = sqlalchemy.Column(sqlalchemy.String(128))
    employee_id = sqlalchemy.Column(sqlalchemy.INTEGER)
    password = sqlalchemy.Column(sqlalchemy.String(32))

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    def __init__(self, **kwargs):
        self.nickname = kwargs.pop('nickname', '')
        self.email = kwargs.pop('email', '')
        self.self_introduction = kwargs.pop('self_introduction', '')
        self.employee_id = kwargs.pop('employee_id', 0)
        self.password = kwargs.pop('password', '********')

    def __repr__(self):
        return 'User: Email: {} EmployeeID: {} Password: {}'.format(self.email, self.employee_id, self.password)

    def __eq__(self, other):
        return self.employee_id == other.employee_id

    def to_json(self):
        return {
            'nickname': self.nickname,
            'email': self.email,
            'employee_id': self.employee_id,
            'password': self.password
        }


class BasicQtRequestBody(object):
    MEMORY_SIZE = 34

    @classmethod
    def get_memory_size(cls):
        return cls.MEMORY_SIZE

    def __init__(self, is_pushed, market_id, stock_id):
        # 0: cancel registration
        # 1: registration
        # 5: request once
        self.is_pushed = is_pushed
        self.style_id = 0
        self.counter = 1
        self.container_id = 0
        self.inner_counter = 1
        self.market_id = market_id
        self.stock_id = CString(stock_id, 16)

    def __repr__(self):
        return '<BasicQtRequestBody>: is_pushed: {} market_id: {} stock_id: {}'.format(
            self.is_pushed, self.market_id, self.stock_id
        )

    def to_bytes(self):
        return struct.pack('<b4iB', self.is_pushed, self.style_id, self.counter, self.container_id,
                           self.inner_counter, self.market_id) + self.stock_id.to_bytes()


class BasicQtResponseBody(object):
    def __init__(self):
        self.MEMORY_SIZE = 25
        self.counter = 0
        self.market_id = B''
        self.stock_id = CString('', 16)
        self.compressed_length = 0
        self.stock_data = None
        self.mcm_obj = mcm.Mcm()

    def __repr__(self):
        return '<BasicQtResponceBody>: market_id: {} stock_id: {}'.format(self.market_id, self.stock_id)

    def get_memory_size(self):
        return self.MEMORY_SIZE

    def from_bytes(self, buffer):
        if len(buffer) >= self.get_memory_size():
            read_length = 0
            self.counter, self.market_id = struct.unpack_from('<iB', buffer, offset=read_length)
            read_length += 5
            self.stock_id.from_bytes(buffer[read_length:], 16)
            read_length += 16
            self.compressed_length, = struct.unpack_from('<i', buffer, offset=read_length)
            read_length += 4
            self.MEMORY_SIZE += self.compressed_length
            craw_multi_qt = self.mcm_obj.UcmpMultiQt(list(buffer[read_length:]))
            raw_multi_qt = RawMultiQt().from_crawmultiqt(craw_multi_qt)
            self.stock_data = [raw_multi_qt]
            return True
        else:
            return False

    def get_stock_data(self):
        return self.stock_data


class SPcStkRtMinRequestBody(object):
    MEMORY_SIZE = 42

    @classmethod
    def get_memory_size(cls):
        return cls.MEMORY_SIZE

    def __init__(self, is_pushed, market_id, stock_id):
        # 0: cancel registration
        # 1: registration
        # 5: request once
        self.is_pushed = is_pushed
        self.style_id = 0
        self.counter = 1
        self.container_id = 0
        self.inner_counter = 1
        self.market_id = market_id
        self.stock_id = CString(stock_id, 16)
        self.trade_sequence = 20121231
        self.num_rtmin_cached = 0

    def __repr__(self):
        return '<SPcStkRtMinRequestBody>: is_pushed: {} market_id: {} stock_id: {}'.format(
            self.is_pushed, self.market_id, self.stock_id
        )

    def to_bytes(self):
        return struct.pack('<b4iB', self.is_pushed, self.style_id, self.counter, self.container_id,
                           self.inner_counter, self.market_id) + self.stock_id.to_bytes() +\
                    struct.pack('<Ii', self.trade_sequence, self.num_rtmin_cached)


class SPcStkRtMinResponceBody(object):
    def __init__(self):
        self.MEMORY_SIZE = 33
        self.counter = 0
        self.market_id = B''
        self.stock_id = CString('', 16)
        self.trade_sequence = 0
        self.index = 0
        self.compressed_length = 0
        self.mcm_obj = mcm.Mcm()
        self.stock_data = []

    def __repr__(self):
        return '<SPcStkRtMinResponceBody>: market_id: {} stock_id: {} trade_sequence: {} index: {}'.format(
            self.market_id, self.stock_id, self.trade_sequence, self.index
        )

    def get_memory_size(self):
        return self.MEMORY_SIZE

    def from_bytes(self, buffer):
        if len(buffer) >= self.get_memory_size():
            read_length = 0
            self.counter, self.market_id = struct.unpack_from('<iB', buffer, offset=read_length)
            read_length += 5
            self.stock_id.from_bytes(buffer[read_length:], 16)
            read_length += 16
            self.trade_sequence, self.index, self.compressed_length = struct.unpack_from('<I2i', buffer, offset=read_length)
            read_length += 12
            self.MEMORY_SIZE += self.compressed_length
            craw_multi_rtmins = self.mcm_obj.UcmpMultiRtMin(list(buffer[read_length:]))
            for item in craw_multi_rtmins:
                new_item = SRawMultiRtMin().from_raw_data(item)
                self.stock_data.append(new_item)
            return True
        else:
            return False

    def get_stock_data(self):
        return self.stock_data


class SRawMultiRtMin(McmDataType):
    MEMORY_SIZE = 80

    def __init__(self):
        self.trade_time = 0     # format: (YYMMDDHHMI)
        self.open_price = 0
        self.highest_price = 0
        self.lowest_price = 0
        self.closed_price = 0
        self.average_price = 0
        self.volume = 0
        self.amount = 0
        self.trade_number = 0
        self.waipan = 0
        self.ext1_volume = 0
        self.ext2_volume = 0
        self.ext1_price = 0
        self.ext2_price = 0

    def __repr__(self):
        return 'trade_time: {}, open_price: {}, highest_price: {}, lowest_price: {}, closed_price: {},' \
               'average_price: {}, volume: {}, amount: {}, trade_number: {}, waipan: {}, ext1_volume: {},' \
               'ext2_volume: {}, ext1_price: {}, ext2_price: {}'.format(
                    self.trade_time, self.open_price, self.highest_price, self.lowest_price, self.closed_price,
                    self.average_price, self.volume, self.amount, self.trade_number, self.waipan, self.ext1_volume,
                    self.ext2_volume, self.ext1_price, self.ext2_price
                )

    def from_raw_data(self, raw_data):
        self.trade_time = raw_data.m_wTime
        self.open_price = raw_data.m_dwOpen
        self.highest_price = raw_data.m_dwHigh
        self.lowest_price = raw_data.m_dwLow
        self.closed_price = raw_data.m_dwClose
        self.average_price = raw_data.m_dwAve
        self.volume = raw_data.m_xVolume
        self.amount = raw_data.m_xAmount
        self.trade_number = raw_data.m_xTradeNum
        self.waipan = raw_data.m_xWaiPan
        self.ext1_volume = raw_data.m_xExt1
        self.ext2_volume = raw_data.m_xExt2
        self.ext1_price = raw_data.m_dwExt1
        self.ext2_price = raw_data.m_dwExt2

        return self

    def to_json(self):
        return {
            'trade_time': self.trade_time,
            'open_price': self.open_price,
            'highest_price': self.highest_price,
            'lowest_price': self.lowest_price,
            'closed_price': self.closed_price,
            'average_price': self.average_price,
            'volume': self.volume,
            'amount': self.amount,
            'trade_number': self.trade_number,
            'waipan': self.waipan,
            'ext1_volume': self.ext1_volume,
            'ext2_volume': self.ext2_volume,
            'ext1_price': self.ext1_price,
            'ext2_price': self.ext2_price
        }


class SPcStkMxRequestBody(object):
    MEMORY_SIZE = 51

    @classmethod
    def get_memory_size(cls):
        return cls.MEMORY_SIZE

    def __init__(self, is_pushed, market_id, stock_id, **kwargs):
        # 0: cancel registration
        # 1: registration
        # 5: request once
        self.is_pushed = is_pushed
        self.style_id = 0
        self.counter = 1
        self.container_id = 0
        self.inner_counter = 1
        self.market_id = market_id
        self.stock_id = CString(stock_id, 16)
        self.trade_sequence = 20121231
        # 0: request the latest data
        # 1: the data after option_date: option_time
        self.request_type = kwargs.pop('request_type', 0)
        self.option_date = kwargs.pop('option_date', 0)
        self.option_time = kwargs.pop('option_time', 0)
        self.num_mx_cached = 0

    def __repr__(self):
        return '<SPcStkMxRequestBody>: is_pushed: {} market_id: {} stock_id: {}'.format(
            self.is_pushed, self.market_id, self.stock_id
        )

    def to_bytes(self):
        return struct.pack('<b4iB', self.is_pushed, self.style_id, self.counter, self.container_id,
                           self.inner_counter, self.market_id) + self.stock_id.to_bytes() +\
                    struct.pack('<Ib3i', self.trade_sequence, self.request_type, self.option_date,
                                self.option_time, self.num_mx_cached)


class SPcStkMxResponceBody(object):
    def __init__(self):
        self.MEMORY_SIZE = 33
        self.counter = 0
        self.market_id = B''
        self.stock_id = CString('', 16)
        self.trade_sequence = 0
        self.index = 0
        self.compressed_length = 0
        self.stock_data = []
        self.mcm_obj = mcm.Mcm()

    def __repr__(self):
        return '<SPcStkMxResponceBody>: market_id: {} stock_id: {} trade_sequence: {} index: {}'.format(
            self.market_id, self.stock_id, self.trade_sequence, self.index
        )

    def get_memory_size(self):
        return self.MEMORY_SIZE

    def from_bytes(self, buffer):
        if len(buffer) >= self.get_memory_size():
            read_length = 0
            self.counter, self.market_id = struct.unpack_from('<iB', buffer, offset=read_length)
            read_length += 5
            self.stock_id.from_bytes(buffer[read_length:], 16)
            read_length += 16
            self.trade_sequence, self.index, self.compressed_length = struct.unpack_from('<I2i', buffer, offset=read_length)
            read_length += 12
            self.MEMORY_SIZE += self.compressed_length
            craw_multi_mxs = self.mcm_obj.UcmpMultiMx(list(buffer[read_length:]))
            for item in craw_multi_mxs:
                new_item = SRawMultiMx().from_raw_data(item)
                self.stock_data.append(new_item)
            return True
        else:
            return False

    def get_stock_data(self):
        return self.stock_data


class SRawMultiMx(McmDataType):
    MEMORY_SIZE = 32

    def __init__(self):
        self.trade_date = 0     # format: YYYYMMDD
        self.trade_time = 0     # format: hhmmss
        self.price = 0
        self.volume = 0
        self.trade_number = 0
        self.buyin_volume = 0
        self.trade_type = 0

    def __repr__(self):
        return 'trade_date: {}, trade_time: {}, price: {}, volume: {}, ' \
               'trade_number: {}, buyin_volume: {}, trade_type: {}'.format(
                    self.trade_date, self.trade_time, self.price,
                    self.volume, self.trade_number, self.buyin_volume, self.trade_type
                )

    def from_raw_data(self, raw_data):
        self.trade_date = raw_data.m_dwDate
        self.trade_time = raw_data.m_dwTime
        self.price = raw_data.m_dwPrice
        self.volume = raw_data.m_xVolume
        self.trade_number = raw_data.m_dwTradeNum
        self.buyin_volume = raw_data.m_xOI
        self.trade_type = raw_data.m_cBS

        return self

    def to_json(self):
        return {
            'trade_date': self.trade_date,
            'trade_time': self.trade_time,
            'price': self.price,
            'volume': self.volume,
            'trade_number': self.trade_number,
            'buyin_volume': self.buyin_volume,
            'trade_type': self.trade_type
        }


class SPcStkKMinRequestBody(object):
    MEMORY_SIZE = 44

    @classmethod
    def get_memory_size(cls):
        return cls.MEMORY_SIZE

    def __init__(self, is_pushed, market_id, stock_id, period=1):
        # 0: cancel registration
        # 1: registration
        # 5: request once
        self.is_pushed = is_pushed
        self.style_id = 0
        self.counter = 1
        self.container_id = 0
        self.inner_counter = 1
        self.market_id = market_id
        self.stock_id = CString(stock_id, 16)
        self.trade_sequence = 20121231
        self.period = period         # minute k line period: 1,5,15,30,60,120
        self.num_kline_cached = 0

    def __repr__(self):
        return '<SPcStkKMinRequestBody>: is_pushed: {} market_id: {} stock_id: {} period: {}'.format(
            self.is_pushed, self.market_id, self.stock_id, self.period
        )

    def to_bytes(self):
        return struct.pack('<b4iB', self.is_pushed, self.style_id, self.counter, self.container_id,
                           self.inner_counter, self.market_id) + self.stock_id.to_bytes() +\
                    struct.pack('<IHi', self.trade_sequence, self.period, self.num_kline_cached)


class SPcStkKMinResponceBody(object):
    def __init__(self):
        self.MEMORY_SIZE = 35
        self.counter = 0
        self.market_id = B''
        self.stock_id = CString('', 16)
        self.trade_sequence = 0
        self.period = 0
        self.index = 0
        self.compressed_length = 0
        self.mcm_obj = mcm.Mcm()
        self.stock_data = []

    def __repr__(self):
        return '<SPcStkKMinResponceBody>: market_id: {} stock_id: {} trade_sequence: {} period: {}'.format(
            self.market_id, self.stock_id, self.trade_sequence, self.period
        )

    def get_memory_size(self):
        return self.MEMORY_SIZE

    def from_bytes(self, buffer):
        if len(buffer) >= self.get_memory_size():
            read_length = 0
            self.counter, self.market_id = struct.unpack_from('<iB', buffer, offset=read_length)
            read_length += 5
            self.stock_id.from_bytes(buffer[read_length:], 16)
            read_length += 16
            self.trade_sequence, self.period, self.index, self.compressed_length = \
                struct.unpack_from('<IH2i', buffer, offset=read_length)
            read_length += 14
            self.MEMORY_SIZE += self.compressed_length
            craw_multi_rtmins = self.mcm_obj.UcmpMultiRtMin(list(buffer[read_length:]))
            for item in craw_multi_rtmins:
                new_item = SRawMultiRtMin().from_raw_data(item)
                self.stock_data.append(new_item)
            return True
        else:
            return False

    def get_stock_data(self):
        return self.stock_data


class CRawMultiBlockQt(McmDataType):
    MEMORY_SIZE = 193

    def __init__(self):
        self.trade_sequence = 0
        self.trade_date = 0         # Format: YYYYMMDD
        self.trade_time = 0         # Format: hhmmss
        self.stock_name = CString('', 32)
        self.stock_code = CString('', 16)
        self.market_id = 0
        self.type = 0
        self.closed_price = 0
        self.open_price = 0
        self.highest_price = 0
        self.lowest_price = 0
        self.newest_price = 0
        self.volume = 0
        self.amount = 0
        self.top_stock_code = CString('', 32)
        self.top_stock_market_id = 0
        self.stock_counter = 0
        self.up_counter = 0
        self.down_counter = 0
        self.total_capital_stock = 0
        self.total_market_value = 0
        self.average_profit = 0
        self.pe_ratio = 0
        self.turnover_2days = 0
        self.percent_3days = 0
        self.previous_5minutes_price = array.array('i', [0 for _ in range(5)])

    def __repr__(self):
        return '<CRawMultiBlockQt>: stock_name: {} stock_code: {} market_id: {} ' \
               'top_stock_code: {} top_stock_market_id: {}'.format(
            self.stock_name, self.stock_code, self.market_id, self.top_stock_code, self.top_stock_market_id
        )

    def from_raw_data(self, raw_data):
        self.trade_sequence = raw_data.m_dwTradeSequence
        self.trade_date = raw_data.m_dwDate
        self.trade_time = raw_data.m_dwTime
        self.stock_name = CString(str(raw_data.m_pcName), 32)
        self.stock_code = CString(str(raw_data.m_pchCode), 16)
        self.market_id = raw_data.m_wMarket
        self.type = raw_data.m_wType
        self.closed_price = raw_data.m_dwClose
        self.open_price = raw_data.m_dwOpen
        self.highest_price = raw_data.m_dwHigh
        self.lowest_price = raw_data.m_dwLow
        self.newest_price = raw_data.m_dwPrice
        self.volume = raw_data.m_xVolume
        self.amount = raw_data.m_xAmount
        self.top_stock_code = CString(str(raw_data.m_pchTopStockCode), 32)
        self.top_stock_market_id = raw_data.m_pchTopStockMarketID
        self.stock_counter = raw_data.m_dwStockNum
        self.up_counter = raw_data.m_dwUpNum
        self.down_counter = raw_data.m_dwDownNum
        self.total_capital_stock = raw_data.m_xZGB
        self.total_market_value = raw_data.m_xZSZ
        self.average_profit = raw_data.m_xAvgProfit
        self.pe_ratio = raw_data.m_xPeRatio
        self.turnover_2days = raw_data.m_xTurnover2Day
        self.percent_3days = raw_data.m_xPercent3Day
        for i in range(5):
            self.previous_5minutes_price[i] = raw_data.m_dwPre5MinPrice[i]

        return self

    def to_json(self):
        return {
            'stock_code': str(self.stock_code),
            'market_id': self.market_id,
            'trade_sequence': self.trade_sequence,
            'closed_price': self.closed_price,
            'open_price': self.open_price,
            'highest_price': self.highest_price,
            'lowest_price': self.lowest_price,
            'newest_price': self.newest_price,
            'top_stock_code': str(self.top_stock_code),
            'total_capital_stock': self.total_capital_stock,
            'total_market_value': self.total_market_value,
            'pe_ratio': self.pe_ratio,
            'turnover_2days': self.turnover_2days,
            'percent_3days': self.percent_3days
        }


class SRawBlockOverView(McmDataType):
    MEMORY_SIZE = 73

    def __init__(self):
        self.stock_code = CString('', 16)
        self.market_id = 0
        self.type = 0
        self.net_flow = 0
        self.increase_in_percent = 0
        # The accumulated increasing days until yesterday.
        # The current accumulated increasing days N can be calculated by:
        # N = 0 if increase_in_percent <= 0 else increase_in_days + 1.
        self.increase_in_days = 0
        self.top_stock_code = CString('', 32)
        self.top_stock_market_id = 0
        self.top_stock_increase_in_percent = 0

    def __repr__(self):
        return '<SRawBlockOverView>: net_flow: {} stock_code: {} market_id: {} ' \
               'top_stock_code: {} top_stock_market_id: {}'.format(
            self.net_flow, self.stock_code, self.market_id, self.top_stock_code, self.top_stock_market_id
        )

    def from_raw_data(self, raw_data):
        self.stock_code = CString(str(raw_data.m_pchCode), 16)
        self.market_id = raw_data.market
        self.type = raw_data.type
        self.net_flow = raw_data.m_xNetFlow
        self.increase_in_percent = raw_data.m_dwPercent
        self.increase_in_days = raw_data.m_dwUpDay
        self.top_stock_code = CString(str(raw_data.m_pchTopStockCode), 32)
        self.top_stock_market_id = raw_data.m_pchTopStockMarketID
        self.top_stock_increase_in_percent = raw_data.m_dwTopPercent

        return self

    def to_json(self):
        return {
            'stock_code': str(self.stock_code),
            'market_id': self.market_id,
            'type': self.type,
            'net_flow': self.net_flow,
            'increase_in_percent': self.increase_in_percent,
            'increase_in_days': self.increase_in_days,
            'top_stock_code': str(self.top_stock_code),
            'top_stock_market_id': self.top_stock_market_id,
            'top_stock_increase_in_percent': self.top_stock_increase_in_percent,
        }


class SPcStkListRequestBody57(object):
    MEMORY_SIZE = 12

    @classmethod
    def get_memory_size(cls):
        return cls.MEMORY_SIZE

    def __init__(self, is_pushed, type, market_id, sub_type=-1):
        # 0: cancel registration
        # 1: registration
        # 5: request once
        self.is_pushed = is_pushed
        self.style_id = 0
        self.container_id = 0
        # 5: HK block
        self.type = type
        # 201: for Hk block and Block overview
        self.market_id = market_id
        # -1: the whole market list
        self.sub_type = sub_type

    def __repr__(self):
        return '<SPcStkListResponseBody57>: is_pushed: {} market_id: {} type: {} sub_type: {}'.format(
            self.is_pushed, self.market_id, self.type, self.sub_type
        )

    def to_bytes(self):
        return struct.pack('<b2ibBb', self.is_pushed, self.style_id, self.container_id,
                           self.type, self.market_id, self.sub_type)


class SPcStkListResponse57Body(object):
    TYPE_HK_BLOCK = 5
    TYPE_BLOCK_OVERVIEW = 7

    def __init__(self):
        self.MEMORY_SIZE = 8
        # 0: in pulling
        # 1: the first packet
        # 2: the last packet
        self.status = 0
        # 5: HK block
        self.request_type = 0
        # 201: for Hk block and Block overview
        self.market_id = 0
        # -1: the whole market list
        self.sub_type = 0
        self.compressed_length = 0
        self.stock_data = []
        self.mcm_obj = mcm.Mcm()

    def __repr__(self):
        return '<SPcStkListResponse57Body>: market_id: {} status: {} request_type: {} sub_type: {}'.format(
            self.market_id, self.status, self.request_type, self.sub_type
        )

    def get_memory_size(self):
        return self.MEMORY_SIZE

    def from_bytes(self, buffer, version):
        if len(buffer) >= self.get_memory_size():
            read_length = 0
            self.status, self.request_type, self.market_id, self.sub_type, self.compressed_length = \
                struct.unpack_from('<3Bbi', buffer, offset=read_length)
            read_length += 8
            self.MEMORY_SIZE += self.compressed_length
            if self.request_type == self.TYPE_HK_BLOCK:
                raw_datas = self.mcm_obj.UcmpMultiBlockQtList(list(buffer[read_length:]))
                self.stock_data = [CRawMultiBlockQt().from_raw_data(item) for item in raw_datas]
            elif self.request_type == self.TYPE_BLOCK_OVERVIEW:
                raw_datas = self.mcm_obj.UcmpBlockOverView(list(buffer[read_length:]), version)
                self.stock_data = [SRawBlockOverView().from_raw_data(item) for item in raw_datas]
            else:
                raise RuntimeError('Unsupported Request Type: {}'.format(self.request_type))

            return True
        else:
            return False

    def get_stock_data(self):
        return self.stock_data


class SRawMultiBaseBQ(McmDataType):
    def __init__(self):
        self.buy_broker_details = []
        self.sell_broker_details = []

    def __repr__(self):
        return 'SRawMultiBaseBQ: \n{}\n{}'.format(str(self.buy_broker_details), str(self.sell_broker_details))

    def from_raw_data(self, raw_data):
        for buy_broker_no in raw_data.m_vecBuyBrokerNo:
            tab_index = buy_broker_no.cTabIndex
            number_items = [item for item in buy_broker_no.vecBrokerNoItem]
            self.buy_broker_details.append((tab_index, number_items))

        for sell_broker_no in raw_data.m_vecSellBrokerNo:
            tab_index = sell_broker_no.cTabIndex
            number_items = [item for item in sell_broker_no.vecBrokerNoItem]
            self.sell_broker_details.append((tab_index, number_items))

        return self

    def to_json(self):
        return {
            'buy_broker1_tab': self.buy_broker_details[0][0],
            'buy_broker1_nos': str(self.buy_broker_details[0][1]),
            'sell_broker1_tab': self.sell_broker_details[0][0],
            'sell_broker1_nos': str(self.sell_broker_details[0][1])
        }


class SPcStkBQRequestBody(object):
    MEMORY_SIZE = 26

    @classmethod
    def get_memory_size(cls):
        return cls.MEMORY_SIZE

    def __init__(self, is_pushed, market_id, block_id):
        # 0: cancel registration
        # 1: registration
        # 5: request once
        self.is_pushed = is_pushed
        self.style_id = 0
        self.container_id = 0
        self.market_id = market_id
        self.block_id = CString(block_id, 16)

    def __repr__(self):
        return '<SPcStkBQRequestBody>: is_pushed: {} market_id: {} block_id: {}'.format(
            self.is_pushed, self.market_id, self.block_id
        )

    def to_bytes(self):
        return struct.pack('<b2iB', self.is_pushed, self.style_id, self.container_id, self.market_id) + \
               self.block_id.to_bytes()


class SPcStkBQResponseBody(object):
    def __init__(self):
        self.MEMORY_SIZE = 21
        self.market_id = 0
        self.block_id = CString('', 16)
        self.compressed_length = 0
        self.stock_data = []
        self.mcm_obj = mcm.Mcm()

    def __repr__(self):
        return '<SPcStkBQResponseBody>: market_id: {} block_id'.format(self.market_id, self.block_id)

    def get_memory_size(self):
        return self.MEMORY_SIZE

    def from_bytes(self, buffer, version):
        if len(buffer) >= self.get_memory_size():
            read_length = 0
            self.market_id, = struct.unpack_from('<B', buffer, offset=read_length)
            read_length += 1
            self.block_id.from_bytes(buffer[read_length:], 16)
            read_length += 16
            self.compressed_length, = struct.unpack_from('<i', buffer, offset=read_length)
            read_length += 4
            self.MEMORY_SIZE += self.compressed_length
            raw_data = self.mcm_obj.UcmpMultiBaseBQ(list(buffer[read_length:]))
            base_bq = SRawMultiBaseBQ().from_raw_data(raw_data)
            self.stock_data = [base_bq]
            return True
        else:
            return False

    def get_stock_data(self):
        return self.stock_data


class SRawMultiBQTrace(McmDataType):
    def __init__(self):
        self.buy_broker_trace_details = []
        self.sell_broker_trace_details = []

    def __repr__(self):
        return 'SRawMultiBQTrace: \n{}\n{}'.format(str(self.buy_broker_trace_details), str(self.sell_broker_trace_details))

    def from_raw_data(self, raw_data):
        for buy_broker_no in raw_data.m_vecBuyBQTrace:
            tab_index = buy_broker_no.bTabIndex
            number_items = [
                (str(item.strStockID), item.ucFlag, item.dwPrice) for item in buy_broker_no.vecBQTraceItem
            ]
            self.buy_broker_trace_details.append((tab_index, number_items))

        for sell_broker_no in raw_data.m_vecSellBQTrace:
            tab_index = sell_broker_no.bTabIndex
            number_items = [
                (str(item.strStockID), item.ucFlag, item.dwPrice) for item in buy_broker_no.vecBQTraceItem
            ]
            self.sell_broker_trace_details.append((tab_index, number_items))

        return self

    def to_json(self):
        return {
            'buy_broker1_tab': self.buy_broker_trace_details[0][0],
            'buy_stockID_flag_price': str(self.buy_broker_trace_details[0][1]),
            'sell_broker1_tab': self.sell_broker_trace_details[0][0],
            'sell_stockID_flag_price': str(self.sell_broker_trace_details[0][1])
        }


class SPcStkTraceRequestBody(object):
    MEMORY_SIZE = 12

    @classmethod
    def get_memory_size(cls):
        return cls.MEMORY_SIZE

    def __init__(self, is_pushed, market_id, broker_no):
        # 0: cancel registration
        # 1: registration
        # 5: request once
        self.is_pushed = is_pushed
        self.style_id = 0
        self.container_id = 0
        self.market_id = market_id
        self.broker_no = broker_no

    def __repr__(self):
        return '<SPcStkTraceRequestBody>: is_pushed: {} market_id: {} broker_no: {}'.format(
            self.is_pushed, self.market_id, self.broker_no
        )

    def to_bytes(self):
        return struct.pack('<b2iBH', self.is_pushed, self.style_id, self.container_id, self.market_id, self.broker_no)


class SPcStkTraceResponseBody(object):
    def __init__(self):
        self.MEMORY_SIZE = 7
        self.market_id = 0
        self.broker_no = 0
        self.compressed_length = 0
        self.stock_data = []
        self.mcm_obj = mcm.Mcm()

    def __repr__(self):
        return '<SPcStkTraceResponseBody>: market_id: {} broker_no'.format(self.market_id, self.broker_no)

    def get_memory_size(self):
        return self.MEMORY_SIZE

    def from_bytes(self, buffer, version):
        if len(buffer) >= self.get_memory_size():
            read_length = 0
            self.market_id, self.broker_no, self.compressed_length = struct.unpack_from('<BHi', buffer, offset=read_length)
            read_length += 7
            self.MEMORY_SIZE += self.compressed_length
            raw_data = self.mcm_obj.UcmpMultiBQTrace(list(buffer[read_length:]))
            bq_trace = SRawMultiBQTrace().from_raw_data(raw_data)
            self.stock_data = [bq_trace]
            return True
        else:
            return False

    def get_stock_data(self):
        return self.stock_data


class SPcStkListRequestBody(object):
    MEMORY_SIZE = 11

    @classmethod
    def get_memory_size(cls):
        return cls.MEMORY_SIZE

    def __init__(self, is_pushed, request_type, market_id):
        # 0: cancel registration
        # 1: registration
        # 5: request once
        self.is_pushed = is_pushed
        self.style_id = 0
        self.container_id = 0
        # 0: request based on individual market
        # 1: request based on individual stock
        # 2: request based on block id
        # 4: request based on security type
        self.request_type = request_type
        self.market_id = market_id

    def __repr__(self):
        return '<SPcStkListRequestBody0>: is_pushed: {} market_id: {} request_type: {}'.format(
            self.is_pushed, self.market_id, self.request_type
        )

    def to_bytes(self):
        return struct.pack('<b2i2B', self.is_pushed, self.style_id, self.container_id, self.request_type, self.market_id)


class SPcStkListResponseBody(object):
    def __init__(self):
        self.MEMORY_SIZE = 7
        self.status = 0
        self.request_type = 0
        self.market_id = 0
        self.compressed_length = 0
        self.stock_data = []
        self.mcm_obj = mcm.Mcm()

    def __repr__(self):
        return '<SPcStkListRetBody>: market_id: {} request_type: {}'.format(self.market_id, self.request_type)

    def get_memory_size(self):
        return self.MEMORY_SIZE

    def from_bytes(self, buffer, version):
        if len(buffer) >= self.get_memory_size():
            read_length = 0
            self.status, self.request_type, self.market_id, self.compressed_length = \
                struct.unpack_from('<3Bi', buffer, offset=read_length)
            read_length += 7
            self.MEMORY_SIZE += self.compressed_length
            raw_datas = self.mcm_obj.UcmpMultiQtList(list(buffer[read_length:]))
            self.stock_data = [RawMultiQt().from_crawmultiqt(raw_data) for raw_data in raw_datas]
            return True
        else:
            return False

    def get_stock_data(self):
        return self.stock_data


class KeepAliveResponseBody(object):
    def __init__(self):
        self.MEMORY_SIZE = 9
        self.server_date = 0
        self.server_time = 0
        self.server_status = 0

    def __repr__(self):
        return '<KeepAliveResponseBody>: server_date: {} server_time: {} server_status'.format(
            self.server_date, self.server_time, self.server_status)

    def get_memory_size(self):
        return self.MEMORY_SIZE

    def from_bytes(self, buffer):
        if len(buffer) >= self.get_memory_size():
            read_length = 0
            self.server_date, self.server_time, self.server_status = struct.unpack_from('<2iB', buffer, offset=read_length)
            read_length += 9
            return True
        else:
            return False

    def get_stock_data(self):
        return self.stock_data


class CRawMultiQtEx(McmDataType):
    def __init__(self):
        # 0: is trading.
        # 2: suspend trading.
        # 3: continue trading.
        self.trade_status = 0
        # 'HKD','USD','EUR','JPY','GBP','CAD','SGD','CNY'
        self.currency_code = CString('', 4)
        self.lot_size = 0
        # '01':Part A   '03':Part B
        self.spread_table = CString('', 3)
        self.is_cas = CString('', 2)
        self.is_vcm = CString('', 2)
        self.is_short_sold = CString('', 2)
        self.is_ccass_security = CString('', 2)
        self.is_dummy_security = CString('', 2)
        self.is_stamp_duty = CString('', 2)
        self.listing_date = 0
        self.delisting_date = 0
        self.reserved_fields = CString('', 4)
        self.is_efn = CString('', 2)
        self.coupon_rate = 0
        self.accumulated_interest = 0
        self.yield_value = 0
        self.call_or_put = CString('', 2)
        self.conversion_ratio = 0
        self.strike_price = 0
        self.maturity_date = 0
        self.underlying_market = 0
        self.underlying_stock_code = CString('', 16)
        self.style = CString('', 2)
        self.price_to_refer = 0
        self.volume_to_refer = 0

    def __repr__(self):
        return 'CRawMultiQtEx: currency_code: {} spread_table: {} listing_date: {} ' \
               'delisting_date: {} underlying_stock_code: {}'.format(self.currency_code, self.spread_table,
                                                                     self.listing_date, self.delisting_date,
                                                                     self.underlying_stock_code)

    def from_raw_data(self, raw_data):
        self.trade_status = raw_data.m_bTradingStatus
        self.currency_code = CString(str(raw_data.m_cCurrencyCode), 4)
        self.lot_size = raw_data.m_dwLotSize
        self.spread_table = CString(str(raw_data.m_cSpreadTable), 3)
        self.is_cas = CString(str(raw_data.m_cCASFlag), 2)
        self.is_vcm = CString(str(raw_data.m_cVCMFlag), 2)
        self.is_short_sold = CString(str(raw_data.m_cShortSellFlag), 2)
        self.is_ccass_security = CString(str(raw_data.m_cCCASSFlag), 2)
        self.is_dummy_security = CString(str(raw_data.m_cDummySecurityFlag), 2)
        self.is_stamp_duty = CString(str(raw_data.m_cStampDutyFlag), 2)
        self.listing_date = raw_data.m_dwListingDate
        self.delisting_date = raw_data.m_dwDelistingDate
        self.reserved_fields = CString(str(raw_data.m_cFiller), 4)
        self.is_efn = CString(str(raw_data.m_cEFNFalg), 2)
        self.coupon_rate = raw_data.m_dwCouponRate
        self.accumulated_interest = raw_data.m_dwAccruedInt
        self.yield_value = raw_data.m_dwYield
        self.call_or_put = CString(str(raw_data.m_cCallPutFlag), 2)
        self.conversion_ratio = raw_data.m_dwConversionRatio
        self.strike_price = raw_data.m_dwStrikePrice
        self.maturity_date = raw_data.m_dwMaturityDate
        self.underlying_market = raw_data.m_bytUnderlyingMarket
        self.underlying_stock_code = CString(str(raw_data.m_pchUnderlyingCode), 16)
        self.style = CString(str(raw_data.m_cStyle), 2)
        self.price_to_refer = raw_data.m_dwIEPrice
        self.volume_to_refer = raw_data.m_xIEVolume

        return self

    def to_json(self):
        return {
            'currency_code': str(self.currency_code),
            'spread_table': str(self.spread_table),
            'listing_date': self.listing_date,
            'coupon_rate': self.coupon_rate,
            'yield_value': self.yield_value,
            'conversion_ratio': self.conversion_ratio,
            'strike_price': self.strike_price,
            'maturity_date': self.maturity_date,
            'price_to_refer': self.price_to_refer,
            'volume_to_refer': self.volume_to_refer,
        }


class SPcStkQtExRequestBody(object):
    MEMORY_SIZE = 34

    @classmethod
    def get_memory_size(cls):
        return cls.MEMORY_SIZE

    def __init__(self, is_pushed, market_id, stock_id):
        # 0: cancel registration
        # 1: registration
        # 5: request once
        self.is_pushed = is_pushed
        self.style_id = 0
        self.counter = 1
        self.container_id = 0
        self.internal_counter = 1
        self.market_id = market_id
        self.stock_id = CString(stock_id, 16)

    def __repr__(self):
        return '<SPcStkQtExRequestBody>: is_pushed: {} market_id: {} stock_id: {}'.format(
            self.is_pushed, self.market_id, self.stock_id
        )

    def to_bytes(self):
        return struct.pack('<b4iB', self.is_pushed, self.style_id, self.counter, self.container_id,
                           self.internal_counter, self.market_id) + self.stock_id.to_bytes()


class SPcStkQtExResponseBody(object):
    def __init__(self):
        self.MEMORY_SIZE = 25
        self.counter = 0
        self.market_id = 0
        self.stock_id = CString('', 16)
        self.compressed_length = 0
        self.stock_data = []
        self.mcm_obj = mcm.Mcm()

    def __repr__(self):
        return '<SPcStkQtExResponseBody>: market_id: {} stock_id: {}'.format(self.market_id, self.stock_id)

    def get_memory_size(self):
        return self.MEMORY_SIZE

    def from_bytes(self, buffer, version):
        if len(buffer) >= self.get_memory_size():
            read_length = 0
            self.counter, self.market_id = struct.unpack_from('<iB', buffer, offset=read_length)
            read_length += 5
            self.stock_id.from_bytes(buffer[read_length:], 16)
            read_length += 16
            self.compressed_length, = struct.unpack_from('<i', buffer, offset=read_length)
            read_length += 4
            self.MEMORY_SIZE += self.compressed_length
            raw_data = self.mcm_obj.UcmpMultiQtEx(list(buffer[read_length:]))
            self.stock_data = [CRawMultiQtEx().from_raw_data(raw_data)]
            return True
        else:
            return False

    def get_stock_data(self):
        return self.stock_data


class SPcStkCASVCMRequestBody(object):
    MEMORY_SIZE = 26

    @classmethod
    def get_memory_size(cls):
        return cls.MEMORY_SIZE

    def __init__(self, is_pushed, market_id, stock_id):
        # 0: cancel registration
        # 1: registration
        # 5: request once
        self.is_pushed = is_pushed
        self.style_id = 0
        self.container_id = 0
        self.market_id = market_id
        self.stock_id = CString(stock_id, 16)

    def __repr__(self):
        return '<SPcStkCASVCMRequestBody>: is_pushed: {} market_id: {} stock_id: {}'.format(
            self.is_pushed, self.market_id, self.stock_id
        )

    def to_bytes(self):
        return struct.pack('<b2iB', self.is_pushed, self.style_id, self.container_id, self.market_id) + \
               self.stock_id.to_bytes()


class SPcStkCASVCMResponseBody(object):
    def __init__(self, cas_or_vcm):
        self.MEMORY_SIZE = 21
        self.cas_or_vcm = cas_or_vcm
        self.market_id = 0
        self.stock_id = CString('', 16)
        self.compressed_length = 0
        self.stock_data = []
        self.mcm_obj = mcm.Mcm()

    def __repr__(self):
        return '<SPcStkCASVCMResponseBody>: market_id: {} stock_id: {}'.format(self.market_id, self.stock_id)

    def get_memory_size(self):
        return self.MEMORY_SIZE

    def from_bytes(self, buffer, version):
        if len(buffer) >= self.get_memory_size():
            read_length = 0
            self.market_id, = struct.unpack_from('<B', buffer, offset=read_length)
            read_length += 1
            self.stock_id.from_bytes(buffer[read_length:], 16)
            read_length += 16
            self.compressed_length, = struct.unpack_from('<i', buffer, offset=read_length)
            read_length += 4
            self.MEMORY_SIZE += self.compressed_length
            if self.cas_or_vcm == 'CAS':
                raw_data = self.mcm_obj.UcmpMultiCAS(list(buffer[read_length:]))
                self.stock_data = [CRawMultiCAS().from_raw_data(raw_data)]
            elif self.cas_or_vcm == 'VCM':
                raw_data = self.mcm_obj.UcmpMultiVCM(list(buffer[read_length:]))
                self.stock_data = [CRawMultiVCM().from_raw_data(raw_data)]
            else:
                raise RuntimeError('Unknown data type!')
            return True
        else:
            return False

    def get_stock_data(self):
        return self.stock_data


class CRawMultiCAS(McmDataType):
    def __init__(self):
        # 'N': buy == sell
        # 'B': buy > sell
        # 'S': buy < sell
        # ' ': when IEP is not available.
        self.order_imbalance_direction = CString('', 2)
        # This value should be ignored if order_imbalance_direction is null.
        self.order_imbalance_quantity = 0
        self.price_to_refer = 0
        self.lower_limit_of_price_to_refer = 0
        self.upper_limit_of_price_to_refer = 0

    def __repr__(self):
        return 'CRawMultiCAS: order_imbalance_direction: {} order_imbalance_quantity: {} price_to_refer: {} ' \
               'lower_limit_of_price_to_refer: {} upper_limit_of_price_to_refer: {}'.\
            format(self.order_imbalance_direction, self.order_imbalance_quantity, self.price_to_refer,
                   self.lower_limit_of_price_to_refer, self.upper_limit_of_price_to_refer)

    def from_raw_data(self, raw_data):
        self.order_imbalance_direction = CString(str(raw_data.m_cOrderImbalanceDirection), 2)
        self.order_imbalance_quantity = raw_data.m_xOrderImbalanceQuantity
        self.price_to_refer = raw_data.m_dwReferencePrice
        self.lower_limit_of_price_to_refer = raw_data.m_dwLowerPrice
        self.upper_limit_of_price_to_refer = raw_data.m_xUpperPrice

        return self

    def to_json(self):
        return {
            'order_imbalance_direction': str(self.order_imbalance_direction),
            'order_imbalance_quantity': self.order_imbalance_quantity,
            'price_to_refer': self.price_to_refer,
            'lower_limit_of_price_to_refer': self.lower_limit_of_price_to_refer,
            'upper_limit_of_price_to_refer': self.upper_limit_of_price_to_refer,
        }


class CRawMultiVCM(McmDataType):
    def __init__(self):
        self.vcm_date = 0
        self.vcm_start_time = 0
        self.vcm_end_time = 0
        self.vcm_price_to_refer = 0
        self.vcm_lower_limit_of_price = 0
        self.vcm_upper_limit_of_price = 0

    def __repr__(self):
        return 'CRawMultiVCM: vcm_date: {} vcm_start_time: {} vcm_end_time: {} ' \
               'vcm_price_to_refer: {} vcm_lower_limit_of_price: {} vcm_upper_limit_of_price: {}'.\
            format(self.vcm_date, self.vcm_start_time, self.vcm_end_time, self.vcm_price_to_refer,
                   self.vcm_lower_limit_of_price, self.vcm_upper_limit_of_price)

    def from_raw_data(self, raw_data):
        self.vcm_date = raw_data.m_dwVCMDate
        self.vcm_start_time = raw_data.m_dwVCMStartTime
        self.vcm_end_time = raw_data.m_dwVCMEndTime
        self.vcm_price_to_refer = raw_data.m_dwVCMReferencePrice
        self.vcm_lower_limit_of_price = raw_data.m_xVCMLowerPrice
        self.vcm_upper_limit_of_price = raw_data.m_xVCMUpperPrice

        return self

    def to_json(self):
        return {
            'vcm_date': self.vcm_date,
            'vcm_start_time': self.vcm_start_time,
            'vcm_end_time': self.vcm_end_time,
            'vcm_price_to_refer': self.vcm_price_to_refer,
            'vcm_lower_limit_of_price': self.vcm_lower_limit_of_price,
            'vcm_upper_limit_of_price': self.vcm_upper_limit_of_price,
        }


class SPcMarketTimeRequestBody(object):
    def __init__(self, is_pushed, market_ids):
        # 0: cancel registration
        # 1: registration
        # 5: request once
        self.is_pushed = is_pushed
        self.counter = len(market_ids)
        self.market_ids = list(market_ids)
        self.MEMORY_SIZE = 5 + len(market_ids) * 1

    def __repr__(self):
        return '<SPcMarketTimeRequestBody>: is_pushed: {} counter: {} markets: {}'.format(
            self.is_pushed, self.counter, self.market_ids
        )

    def get_memory_size(self):
        return self.MEMORY_SIZE

    def to_bytes(self):
        tmp_buffer = struct.pack('<bi', self.is_pushed, self.counter)
        for market_id in self.market_ids:
            tmp_buffer += struct.pack('<B', market_id)
        return tmp_buffer


class SMarketTime(McmDataType):
    MEMORY_SIZE = 13

    def __init__(self):
        self.market_id = 0
        self.trade_sequence = 0
        self.trade_date = 0
        self.trade_time = 0

    def __repr__(self):
        return 'SMarketTime: market_id: {} trade_sequence: {} trade_date: {} trade_time: {}'.format(
            self.market_id, self.trade_sequence, self.trade_date, self.trade_time
        )

    def from_raw_data(self, raw_data):
        return self

    def from_bytes(self, buffer):
        if len(buffer) >= self.get_memory_size():
            self.market_id, self.trade_sequence, self.trade_date, self.trade_time = struct.unpack_from('<B3I', buffer)
            return self
        else:
            return None

    def to_json(self):
        this_year = datetime.now().strftime('%Y')
        trade_sequence = str(self.trade_sequence)[4:] if this_year in str(self.trade_sequence) \
            else str(self.trade_sequence)
        trade_date = str(self.trade_date)[4:] if this_year in str(self.trade_date) \
            else str(self.trade_date)
        cell_content = '{}[{}: {}]'.format(trade_sequence, trade_date, self.trade_time)
        return {
            'market_id': self.market_id,
            'time': cell_content,
            'market_name': reverse_global_market_infos[self.market_id],
        }


class SPcMarketTimeResponseBody(object):
    def __init__(self):
        self.MEMORY_SIZE = 4
        self.counter = 0
        self.stock_data = []

    def __repr__(self):
        return '<SPcMarketTimeResponseBody>: counter: {}'.format(self.counter)

    def get_memory_size(self):
        return self.MEMORY_SIZE

    def from_bytes(self, buffer, version):
        if len(buffer) >= self.get_memory_size():
            read_length = 0
            self.counter, = struct.unpack_from('<i', buffer, offset=read_length)
            read_length += 4
            tmp_list = []
            for i in range(self.counter):
                market_time = SMarketTime().from_bytes(buffer[read_length:])
                if market_time:
                    read_length += market_time.get_memory_size()
                    tmp_list.append(market_time)
            self.MEMORY_SIZE += read_length
            self.stock_data = tmp_list
            return True
        else:
            return False

    def get_stock_data(self):
        return self.stock_data


class SPcMarketTurnoverRequestBody(object):
    MEMORY_SIZE = 34

    @classmethod
    def get_memory_size(cls):
        return cls.MEMORY_SIZE

    def __init__(self, is_pushed, market_id, stock_code):
        # 0: cancel registration
        # 1: registration
        # 5: request once
        self.is_pushed = is_pushed
        self.style_id = 0
        self.counter = 1
        self.container_id = 0
        self.internal_counter = 1
        # martket_id: 148
        self.market_id = market_id
        # stock_code:
        # CSCSHQ -- Shanghai Stock Exchange
        # CSCSZQ -- Shenzhen Stock Exchange
        self.stock_code = CString(stock_code, 16)

    def __repr__(self):
        return '<SPcMarketTurnoverRequestBody>: is_pushed: {} market_id: {} stock_code: {}'.format(
            self.is_pushed, self.market_id, str(self.stock_code)
        )

    def get_memory_size(self):
        return self.MEMORY_SIZE

    def to_bytes(self):
        return struct.pack('<b4iB', self.is_pushed, self.style_id, self.counter, self.container_id,
                           self.internal_counter, self.market_id) + self.stock_code.to_bytes()


class SPcMarketTurnoverResponseBody(object):
    def __init__(self):
        self.MEMORY_SIZE = 25
        self.counter = 0
        self.market_id = 0
        self.stock_code = CString('', 16)
        self.compressed_length = 0
        self.mcm_obj = mcm.Mcm()
        self.stock_data = []

    def __repr__(self):
        return '<SPcMarketTurnoverResponseBody>: counter: {} market_id: {} stock_code: {}'.format(
            self.counter, self.market_id, str(self.stock_code)
        )

    def get_memory_size(self):
        return self.MEMORY_SIZE

    def from_bytes(self, buffer, version):
        if len(buffer) >= self.get_memory_size():
            read_length = 0
            self.counter, self.market_id = struct.unpack_from('<iB', buffer, offset=read_length)
            read_length += 5
            self.stock_code = CString().from_bytes(buffer[read_length:], 16)
            read_length += 16
            self.compressed_length, = struct.unpack_from('<i', buffer, offset=read_length)
            read_length += 4
            raw_data = self.mcm_obj.UcmpMarketTurnover(list(buffer[read_length:]), version)
            self.stock_data = [SRawMarketTurnover().from_raw_data(raw_data)]
            read_length += self.compressed_length
            self.MEMORY_SIZE += self.compressed_length
            return True
        else:
            return False

    def get_stock_data(self):
        return self.stock_data


class SRawMarketTurnover(McmDataType):
    TRADE_DIRECTION = {
        0: 'UNKNOWN',
        1: 'NORTH',
        2: 'SOUTH'
    }

    def __init__(self):
        self.trade_date = 0
        self.trade_time = 0
        self.buyin_amount = 0
        self.sold_amount = 0
        self.total_amount = 0
        self.direction = self.TRADE_DIRECTION[0]

    def __repr__(self):
        return '<SRawMarketTurnover>:  trade_date: {}, trade_time: {}, buyin_amount: {} ' \
               'sold_amount: {}, total_amount: {}, direction: {}'.format(
            self.trade_date, self.trade_time, self.buyin_amount, self.sold_amount, self.total_amount, self.direction
        )

    def from_raw_data(self, raw_data):
        self.trade_date = raw_data.date_in_yymmdd
        self.trade_time = raw_data.time_in_hhmmss
        self.buyin_amount = raw_data.buyin_amount
        self.sold_amount = raw_data.sold_amount
        self.total_amount = raw_data.total_amount
        self.direction = self.TRADE_DIRECTION[raw_data.direction]

        return self

    def to_json(self):
        return {
            'trade_date': self.trade_date,
            'trade_time': self.trade_time,
            'buyin_amount': self.buyin_amount,
            'sold_amount': self.sold_amount,
            'total_amount': self.total_amount,
            'direction': self.direction
        }

