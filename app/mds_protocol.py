import struct
import zlib
from app import basic_structs


PACK_PC_LOGIN = 8001
PACK_PC_SHAKEHAND = 8002
PACK_PC_STKDICT = 8100
PACK_PC_STKQT = 8101
PACK_PC_MARKETTIME = 8102
PACK_PC_STKRTMIN = 8103
PACK_PC_STKKLINE = 8104
PACK_PC_STKMX = 8105
PACK_PC_QTLIST = 8106
PACK_PC_BLOCKMAP = 8107
PACK_PC_MARKETINFO = 8108
PACK_PC_RAWDATA = 8109
PACK_PC_QTLIST_EX = 8110
PACK_PC_STKQT_EX = 8111
PACK_PC_STKBQ = 8112
PACK_PC_STKTRACE = 8113
PACK_PC_STKBKGGLIST = 8114
PACK_PC_STKMX2 = 8115
PACK_PC_STK_QTEX = 8117
PACK_PC_STK_CAS = 8118
PACK_PC_STK_VCM = 8119
PACK_PC_STK_VERSION = 8120
PACK_PC_LIST_FUND_FLOW = 8124
PACK_PC_LIST_BUYIN_RANK = 8125
PACK_PC_MARKET_TURNOVER = 8127


MCM_VERSION = 161

PUSH_TYPE_CANCEL = 0
PUSH_TYPE_REGISTER = 1
PUSH_TYPE_ONCE = 5


class MDSBaseProtocol(object):
    message_id = 0

    def __init__(self):
        self._package_total_size = 0

    def __repr__(self):
        return '<MDSProtocol>: {}'.format(self.message_id)

    def to_bytes(self):
        raise NotImplementedError()

    def all_from_bytes(self, received_buffer, version):
        # Implement this method and return boolean result.
        raise NotImplementedError()

    def get_stock_data(self):
        raise NotImplementedError()

    def size(self):
        return self._package_total_size


class Protocol8001(MDSBaseProtocol):
    message_id = PACK_PC_LOGIN

    def __init__(self):
        self._package_total_size = 0
        self.mcm_version = None
        self.header = basic_structs.MDSPcReactHead()
        self.body = basic_structs.SPcLoginResponceBody()

    def to_bytes(self):
        if self.mcm_version:
            request_body = basic_structs.SPcLoginRequestBody(self.mcm_version)
            head = basic_structs.MDSPCRequestHead(package_size=request_body.get_memory_size(),
                                                  message_id=self.message_id)
            return head.to_bytes() + request_body.to_bytes()
        else:
            raise RuntimeError('Config the protocol {} before requesting data.'.format(self))

    def all_from_bytes(self, received_buffer, version):
        read_length = 0
        if self.header.from_bytes(received_buffer[read_length:]):
            read_length += self.header.get_memory_size()
            if self.body.from_bytes(received_buffer[read_length:]):
                print(self.body)
                self.mcm_version = self.body.mcm_version
                read_length += self.header.package_size
                self._package_total_size = read_length
                return True
            else:
                return False
        else:
            return False

    def get_stock_data(self):
        return []


class Protocol8002(MDSBaseProtocol):
    message_id = PACK_PC_SHAKEHAND

    def __init__(self):
        super().__init__()
        self.header = basic_structs.MDSPcReactHead()
        self.body = basic_structs.KeepAliveResponseBody()

    def to_bytes(self):
        head = basic_structs.MDSPCRequestHead(package_size=0, message_id=self.message_id)
        return head.to_bytes()

    def all_from_bytes(self, received_buffer, version):
        read_length = 0
        if self.header.from_bytes(received_buffer[read_length:]):
            read_length += self.header.get_memory_size()
            if self.body.from_bytes(received_buffer[read_length:]):
                read_length += self.header.package_size
                self._package_total_size = read_length
                return True
            else:
                return False
        else:
            return False

    def get_stock_data(self):
        raise NotImplementedError()


class Protocol8100(MDSBaseProtocol):
    message_id = PACK_PC_STKDICT

    def __init__(self):
        super().__init__()
        self.is_pushed = None
        self.counter = None
        self.market_id = None
        self.header = basic_structs.MDSPcReactHead()
        self.body = basic_structs.SPcStkStockDictResponceBody()
        self.stock_dicts = []

    def to_bytes(self):
        if self.is_pushed is not None and self.market_id and self.counter:
            stock_dict_info = basic_structs.StockDictInfo(market_id=self.market_id)
            request_body = basic_structs.PcStkDictRequestBody(is_pushed=self.is_pushed, counter=self.counter,
                                                              stock_dict_infos=[stock_dict_info])
            head = basic_structs.MDSPCRequestHead(package_size=len(request_body.to_bytes()),
                                                  message_id=self.message_id)
            return head.to_bytes() + request_body.to_bytes()
        else:
            raise RuntimeError('Config the protocol<{}> before requesting data.'.format(self))

    def all_from_bytes(self, received_buffer, version):
        read_length = 0
        if self.header.from_bytes(received_buffer[read_length:]):
            read_length += self.header.get_memory_size()
            if self.body.from_bytes(received_buffer[read_length:]):
                read_length += self.header.package_size
                self.stock_dicts = self.body.get_stock_data()
                self._package_total_size = read_length
                return True
            else:
                return False
        else:
            return False

    def get_stock_data(self):
        return self.stock_dicts


class Protocol8101(MDSBaseProtocol):
    message_id = PACK_PC_STKQT

    def __init__(self):
        super().__init__()
        self.stock_data = []
        self.is_pushed = None
        self.market_id = None
        self.stock_id = None
        self.header = basic_structs.MDSPcReactHead()
        self.body = basic_structs.BasicQtResponseBody()

    def to_bytes(self):
        if self.is_pushed is not None and self.market_id and self.stock_id:
            request_body = basic_structs.BasicQtRequestBody(self.is_pushed, self.market_id, self.stock_id)
            head = basic_structs.MDSPCRequestHead(package_size=request_body.get_memory_size(),
                                                  message_id=self.message_id)
            return head.to_bytes() + request_body.to_bytes()
        else:
            raise RuntimeError('Config the protocol before requesting data.')

    def all_from_bytes(self, received_buffer, version):
        read_length = 0
        if self.header.from_bytes(received_buffer[read_length:]):
            read_length += self.header.get_memory_size()
            if self.body.from_bytes(received_buffer[read_length:]):
                read_length += self.header.package_size
                self.stock_data = self.body.get_stock_data()
                self._package_total_size = read_length
                return True
            else:
                return False
        else:
            return False

    def get_stock_data(self):
        return self.stock_data


class Protocol8102(MDSBaseProtocol):
    message_id = PACK_PC_MARKETTIME

    def __init__(self):
        super().__init__()
        self.stock_data = []
        self.is_pushed = None
        self.market_ids = None
        self.header = basic_structs.MDSPcReactHead()
        self.body = basic_structs.SPcMarketTimeResponseBody()

    def to_bytes(self):
        if self.is_pushed is not None and self.market_ids:
            request_body = basic_structs.SPcMarketTimeRequestBody(self.is_pushed, self.market_ids)
            head = basic_structs.MDSPCRequestHead(package_size=request_body.get_memory_size(),
                                                  message_id=self.message_id)
            return head.to_bytes() + request_body.to_bytes()
        else:
            raise RuntimeError('Config the protocol<{}> before requesting data.'.format(self))

    def all_from_bytes(self, received_buffer, version):
        read_length = 0
        if self.header.from_bytes(received_buffer[read_length:]):
            read_length += self.header.get_memory_size()
            if self.body.from_bytes(received_buffer[read_length:], version):
                read_length += self.header.package_size
                self.stock_data = self.body.get_stock_data()
                self._package_total_size = read_length
                return True
            else:
                return False
        else:
            return False

    def get_stock_data(self):
        return self.stock_data


class Protocol8103(MDSBaseProtocol):
    message_id = PACK_PC_STKRTMIN

    def __init__(self):
        super().__init__()
        self.is_pushed = None
        self.market_id = None
        self.stock_id = None
        self.header = basic_structs.MDSPcReactHead()
        self.body = basic_structs.SPcStkRtMinResponceBody()
        self.stock_data = []

    def to_bytes(self):
        if self.is_pushed is not None and self.market_id and self.stock_id:
            request_body = basic_structs.SPcStkRtMinRequestBody(self.is_pushed, self.market_id, self.stock_id)
            head = basic_structs.MDSPCRequestHead(package_size=request_body.get_memory_size(),
                                                  message_id=self.message_id)
            return head.to_bytes() + request_body.to_bytes()
        else:
            raise RuntimeError('Config the protocol<{}> before requesting data.'.format(self))

    def all_from_bytes(self, received_buffer, version):
        read_length = 0
        if self.header.from_bytes(received_buffer[read_length:]):
            read_length += self.header.get_memory_size()
            if self.body.from_bytes(received_buffer[read_length:]):
                read_length += self.header.package_size
                self.stock_data = self.body.get_stock_data()
                self._package_total_size = read_length
                return True
            else:
                return False
        else:
            return False

    def get_stock_data(self):
        return self.stock_data


class Protocol8104(MDSBaseProtocol):
    message_id = PACK_PC_STKKLINE

    def __init__(self):
        super().__init__()
        self.is_pushed = None
        self.market_id = None
        self.stock_id = None
        self.period = None
        self.header = basic_structs.MDSPcReactHead()
        self.body = basic_structs.SPcStkKMinResponceBody()
        self.stock_data = []

    def to_bytes(self):
        if self.is_pushed is not None and self.market_id and self.stock_id and self.period:
            request_body = basic_structs.SPcStkKMinRequestBody(self.is_pushed, self.market_id, self.stock_id,
                                                               self.period)
            head = basic_structs.MDSPCRequestHead(package_size=request_body.get_memory_size(),
                                                  message_id=self.message_id)
            return head.to_bytes() + request_body.to_bytes()
        else:
            raise RuntimeError('Config the protocol<{}> before requesting data.'.format(self))

    def all_from_bytes(self, received_buffer, version):
        read_length = 0
        if self.header.from_bytes(received_buffer[read_length:]):
            read_length += self.header.get_memory_size()
            if self.body.from_bytes(received_buffer[read_length:]):
                read_length += self.header.package_size
                self.stock_data = self.body.get_stock_data()
                self._package_total_size = read_length
                return True
            else:
                return False
        else:
            return False

    def get_stock_data(self):
        return self.stock_data


class Protocol8105(MDSBaseProtocol):
    message_id = PACK_PC_STKMX

    def __init__(self):
        super().__init__()
        self.stock_data = []
        self.is_pushed = None
        self.market_id = None
        self.stock_id = None
        self.header = basic_structs.MDSPcReactHead()
        self.body = basic_structs.SPcStkMxResponceBody()

    def to_bytes(self):
        if self.is_pushed is not None and self.market_id and self.stock_id:
            request_body = basic_structs.SPcStkMxRequestBody(self.is_pushed, self.market_id, self.stock_id)
            head = basic_structs.MDSPCRequestHead(package_size=request_body.get_memory_size(),
                                                  message_id=self.message_id)
            return head.to_bytes() + request_body.to_bytes()
        else:
            raise RuntimeError('Config the protocol<{}> before requesting data.'.format(self))

    def all_from_bytes(self, received_buffer, version):
        read_length = 0
        if self.header.from_bytes(received_buffer[read_length:]):
            read_length += self.header.get_memory_size()
            if self.body.from_bytes(received_buffer[read_length:]):
                read_length += self.header.package_size
                self.stock_data = self.body.get_stock_data()
                self._package_total_size = read_length
                return True
            else:
                return False
        else:
            return False

    def get_stock_data(self):
        return self.stock_data


class Protocol8106(MDSBaseProtocol):
    message_id = PACK_PC_QTLIST

    def __init__(self):
        super().__init__()
        self.stock_data = []
        self.is_pushed = None
        self.type = None
        self.market_id = None
        self.sub_type = None
        self.header = basic_structs.MDSPcReactHead()
        self.body = basic_structs.SPcStkListResponse57Body()

    def to_bytes(self):
        if self.is_pushed is not None and self.market_id and self.type and self.sub_type:
            request_body = basic_structs.SPcStkListRequestBody57(self.is_pushed, self.type, self.market_id, self.sub_type)
            head = basic_structs.MDSPCRequestHead(package_size=request_body.get_memory_size(),
                                                  message_id=self.message_id)
            return head.to_bytes() + request_body.to_bytes()
        else:
            raise RuntimeError('Config the protocol before requesting data.')

    def all_from_bytes(self, received_buffer, version):
        read_length = 0
        if self.header.from_bytes(received_buffer[read_length:]):
            read_length += self.header.get_memory_size()
            if self.body.from_bytes(received_buffer[read_length:], version):
                read_length += self.header.package_size
                self.stock_data = self.body.get_stock_data()
                self._package_total_size = read_length
                return True
            else:
                return False
        else:
            return False

    def get_stock_data(self):
        return self.stock_data


class Protocol8110(MDSBaseProtocol):
    message_id = PACK_PC_QTLIST_EX

    def __init__(self):
        super().__init__()
        self.stock_data = []
        self.is_pushed = None
        self.request_type = None
        self.market_id = None
        self.header = basic_structs.MDSPcReactHead()
        self.body = basic_structs.SPcStkListResponseBody()

    def to_bytes(self):
        if self.is_pushed is not None and self.market_id and self.request_type is not None:
            request_body = basic_structs.SPcStkListRequestBody(self.is_pushed, self.request_type, self.market_id)
            head = basic_structs.MDSPCRequestHead(package_size=request_body.get_memory_size(),
                                                  message_id=self.message_id)
            return head.to_bytes() + request_body.to_bytes()
        else:
            raise RuntimeError('Config the protocol<{}> before requesting data.'.format(self))

    def all_from_bytes(self, received_buffer, version):
        read_length = 0
        if self.header.from_bytes(received_buffer[read_length:]):
            read_length += self.header.get_memory_size()
            if self.body.from_bytes(received_buffer[read_length:], version):
                read_length += self.header.package_size
                self.stock_data = self.body.get_stock_data()
                self._package_total_size = read_length
                return True
            else:
                return False
        else:
            return False

    def get_stock_data(self):
        return self.stock_data


class Protocol8112(MDSBaseProtocol):
    message_id = PACK_PC_STKBQ

    def __init__(self):
        super().__init__()
        self.stock_data = []
        self.is_pushed = None
        self.market_id = None
        self.block_id = None
        self.header = basic_structs.MDSPcReactHead()
        self.body = basic_structs.SPcStkBQResponseBody()

    def to_bytes(self):
        if self.is_pushed is not None and self.market_id and self.block_id:
            request_body = basic_structs.SPcStkBQRequestBody(self.is_pushed, self.market_id, self.block_id)
            head = basic_structs.MDSPCRequestHead(package_size=request_body.get_memory_size(),
                                                  message_id=self.message_id)
            return head.to_bytes() + request_body.to_bytes()
        else:
            raise RuntimeError('Config the protocol<{}> before requesting data.'.format(self))

    def all_from_bytes(self, received_buffer, version):
        read_length = 0
        if self.header.from_bytes(received_buffer[read_length:]):
            read_length += self.header.get_memory_size()
            if self.body.from_bytes(received_buffer[read_length:], version):
                read_length += self.header.package_size
                self.stock_data = self.body.get_stock_data()
                self._package_total_size = read_length
                return True
            else:
                return False
        else:
            return False

    def get_stock_data(self):
        return self.stock_data


class Protocol8113(MDSBaseProtocol):
    message_id = PACK_PC_STKTRACE

    def __init__(self):
        super().__init__()
        self.stock_data = []
        self.is_pushed = None
        self.market_id = None
        self.broker_no = None
        self.header = basic_structs.MDSPcReactHead()
        self.body = basic_structs.SPcStkTraceResponseBody()

    def to_bytes(self):
        if self.is_pushed is not None and self.market_id and self.broker_no:
            request_body = basic_structs.SPcStkTraceRequestBody(self.is_pushed, self.market_id, self.broker_no)
            head = basic_structs.MDSPCRequestHead(package_size=request_body.get_memory_size(),
                                                  message_id=self.message_id)
            return head.to_bytes() + request_body.to_bytes()
        else:
            raise RuntimeError('Config the protocol<{}> before requesting data.'.format(self))

    def all_from_bytes(self, received_buffer, version):
        read_length = 0
        if self.header.from_bytes(received_buffer[read_length:]):
            read_length += self.header.get_memory_size()
            if self.body.from_bytes(received_buffer[read_length:], version):
                read_length += self.header.package_size
                self.stock_data = self.body.get_stock_data()
                self._package_total_size = read_length
                return True
            else:
                return False
        else:
            return False

    def get_stock_data(self):
        return self.stock_data


class Protocol8115(MDSBaseProtocol):
    message_id = PACK_PC_STKMX2

    def __init__(self):
        super().__init__()
        self.stock_data = []
        self.is_pushed = None
        self.market_id = None
        self.stock_id = None
        self.header = basic_structs.MDSPcReactHead()
        self.body = basic_structs.SPcStkMxResponceBody()

    def to_bytes(self):
        if self.is_pushed is not None and self.market_id and self.stock_id:
            request_body = basic_structs.SPcStkMxRequestBody(self.is_pushed, self.market_id, self.stock_id)
            head = basic_structs.MDSPCRequestHead(package_size=request_body.get_memory_size(),
                                                  message_id=self.message_id)
            return head.to_bytes() + request_body.to_bytes()
        else:
            raise RuntimeError('Config the protocol<{}> before requesting data.'.format(self))

    def all_from_bytes(self, received_buffer, version):
        read_length = 0
        if self.header.from_bytes(received_buffer[read_length:]):
            read_length += self.header.get_memory_size()
            if self.body.from_bytes(received_buffer[read_length:]):
                read_length += self.header.package_size
                self.stock_data = self.body.get_stock_data()
                self._package_total_size = read_length
                return True
            else:
                return False
        else:
            return False

    def get_stock_data(self):
        return self.stock_data


class Protocol8117(MDSBaseProtocol):
    message_id = PACK_PC_STK_QTEX

    def __init__(self):
        super().__init__()
        self.stock_data = []
        self.is_pushed = None
        self.market_id = None
        self.stock_id = None
        self.header = basic_structs.MDSPcReactHead()
        self.body = basic_structs.SPcStkQtExResponseBody()

    def to_bytes(self):
        if self.is_pushed is not None and self.market_id and self.stock_id:
            request_body = basic_structs.SPcStkQtExRequestBody(self.is_pushed, self.market_id, self.stock_id)
            head = basic_structs.MDSPCRequestHead(package_size=request_body.get_memory_size(),
                                                  message_id=self.message_id)
            return head.to_bytes() + request_body.to_bytes()
        else:
            raise RuntimeError('Config the protocol<{}> before requesting data.'.format(self))

    def all_from_bytes(self, received_buffer, version):
        read_length = 0
        if self.header.from_bytes(received_buffer[read_length:]):
            read_length += self.header.get_memory_size()
            if self.body.from_bytes(received_buffer[read_length:], version):
                read_length += self.header.package_size
                self.stock_data = self.body.get_stock_data()
                self._package_total_size = read_length
                return True
            else:
                return False
        else:
            return False

    def get_stock_data(self):
        return self.stock_data


class Protocol8118(MDSBaseProtocol):
    message_id = PACK_PC_STK_CAS

    def __init__(self):
        super().__init__()
        self.stock_data = []
        self.is_pushed = None
        self.market_id = None
        self.stock_id = None
        self.header = basic_structs.MDSPcReactHead()
        self.body = basic_structs.SPcStkCASVCMResponseBody('CAS')

    def to_bytes(self):
        if self.is_pushed is not None and self.market_id and self.stock_id:
            request_body = basic_structs.SPcStkCASVCMRequestBody(self.is_pushed, self.market_id, self.stock_id)
            head = basic_structs.MDSPCRequestHead(package_size=request_body.get_memory_size(),
                                                  message_id=self.message_id)
            return head.to_bytes() + request_body.to_bytes()
        else:
            raise RuntimeError('Config the protocol<{}> before requesting data.'.format(self))

    def all_from_bytes(self, received_buffer, version):
        read_length = 0
        if self.header.from_bytes(received_buffer[read_length:]):
            read_length += self.header.get_memory_size()
            if self.body.from_bytes(received_buffer[read_length:], version):
                read_length += self.header.package_size
                self.stock_data = self.body.get_stock_data()
                self._package_total_size = read_length
                return True
            else:
                return False
        else:
            return False

    def get_stock_data(self):
        return self.stock_data


class Protocol8119(MDSBaseProtocol):
    message_id = PACK_PC_STK_VCM

    def __init__(self):
        super().__init__()
        self.stock_data = []
        self.is_pushed = None
        self.market_id = None
        self.stock_id = None
        self.header = basic_structs.MDSPcReactHead()
        self.body = basic_structs.SPcStkCASVCMResponseBody('VCM')

    def to_bytes(self):
        if self.is_pushed is not None and self.market_id and self.stock_id:
            request_body = basic_structs.SPcStkCASVCMRequestBody(self.is_pushed, self.market_id, self.stock_id)
            head = basic_structs.MDSPCRequestHead(package_size=request_body.get_memory_size(),
                                                  message_id=self.message_id)
            return head.to_bytes() + request_body.to_bytes()
        else:
            raise RuntimeError('Config the protocol<{}> before requesting data.'.format(self))

    def all_from_bytes(self, received_buffer, version):
        read_length = 0
        if self.header.from_bytes(received_buffer[read_length:]):
            read_length += self.header.get_memory_size()
            if self.body.from_bytes(received_buffer[read_length:], version):
                read_length += self.header.package_size
                self.stock_data = self.body.get_stock_data()
                self._package_total_size = read_length
                return True
            else:
                return False
        else:
            return False

    def get_stock_data(self):
        return self.stock_data


class Protocol8124(MDSBaseProtocol):
    message_id = PACK_PC_LIST_FUND_FLOW

    def __init__(self):
        self.stock_datas = []
        self.is_pushed = None
        self.request_type = None
        self.market_id = None
        self.header = basic_structs.MDSPcReactHead()
        self.body = basic_structs.SPcListFundFlowResponseBody()

    def to_bytes(self):
        if self.is_pushed is not None and self.request_type is not None and self.market_id:
            request_body = basic_structs.GeneralRequestBody(
                is_pushed=self.is_pushed, type=self.request_type, market_id=self.market_id)
            head = basic_structs.MDSPCRequestHead(package_size=request_body.get_memory_size(),
                                                  message_id=self.message_id)
            return head.to_bytes() + request_body.to_bytes()
        else:
            raise RuntimeError('Config the protocol<{}> before requesting data.'.format(self))

    def all_from_bytes(self, received_buffer, version):
        read_length = 0
        if self.header.from_bytes(received_buffer[read_length:]):
            read_length += self.header.get_memory_size()
            if self.body.from_bytes(received_buffer[read_length:]):
                read_length += self.header.package_size
                self.stock_datas = self.body.get_stock_datas()
                self._package_total_size = read_length
                return True
            else:
                return False
        else:
            return False

    def get_stock_data(self):
        return self.stock_datas


class Protocol8125(MDSBaseProtocol):
    message_id = PACK_PC_LIST_BUYIN_RANK

    def __init__(self):
        super().__init__()
        self.is_pushed = None
        self.request_type = None
        self.market_id = None
        self.header = basic_structs.MDSPcReactHead()
        self.body = basic_structs.SPcListBuyinRankResponseBody()
        self.stock_datas = []

    def to_bytes(self):
        if self.is_pushed is not None and self.request_type is not None and self.market_id:
            request_body = basic_structs.GeneralRequestBody(
                is_pushed=self.is_pushed, type=self.request_type, market_id=self.market_id)
            head = basic_structs.MDSPCRequestHead(package_size=request_body.get_memory_size(),
                                                  message_id=self.message_id)
            return head.to_bytes() + request_body.to_bytes()
        else:
            raise RuntimeError('Config the protocol<{}> before requesting data.'.format(self))

    def all_from_bytes(self, received_buffer, version):
        read_length = 0
        if self.header.from_bytes(received_buffer[read_length:]):
            read_length += self.header.get_memory_size()
            if self.body.from_bytes(received_buffer[read_length:]):
                read_length += self.header.package_size
                self.stock_datas = self.body.get_stock_datas()
                self._package_total_size = read_length
                return True
            else:
                return False
        else:
            return False

    def get_stock_data(self):
        return self.stock_datas


class Protocol8127(MDSBaseProtocol):
    message_id = PACK_PC_MARKET_TURNOVER

    def __init__(self):
        super().__init__()
        self.stock_data = []
        self.is_pushed = None
        self.market_id = None
        self.stock_code = None
        self.header = basic_structs.MDSPcReactHead()
        self.body = basic_structs.SPcMarketTurnoverResponseBody()

    def to_bytes(self):
        if self.is_pushed is not None and self.market_id and self.stock_code:
            request_body = basic_structs.SPcMarketTurnoverRequestBody(self.is_pushed, self.market_id, self.stock_code)
            head = basic_structs.MDSPCRequestHead(package_size=request_body.get_memory_size(),
                                                  message_id=self.message_id)
            return head.to_bytes() + request_body.to_bytes()
        else:
            raise RuntimeError('Config the protocol<{}> before requesting data.'.format(self))

    def all_from_bytes(self, received_buffer, version):
        read_length = 0
        if self.header.from_bytes(received_buffer[read_length:]):
            read_length += self.header.get_memory_size()
            if self.body.from_bytes(received_buffer[read_length:], version):
                read_length += self.header.package_size
                self.stock_data = self.body.get_stock_data()
                self._package_total_size = read_length
                return True
            else:
                return False
        else:
            return False

    def get_stock_data(self):
        return self.stock_data


class MDSAllProtocols(object):
    def __init__(self):
        self.header = basic_structs.MDSPcReactHead()
        self.mcm_version = 1
        self.all_protocols = {
            8001: Protocol8001(),
            8002: Protocol8002(),
            8100: Protocol8100(),
            8101: Protocol8101(),
            8102: Protocol8102(),
            8103: Protocol8103(),
            8104: Protocol8104(),
            8105: Protocol8105(),
            8106: Protocol8106(),
            8110: Protocol8110(),
            8112: Protocol8112(),
            8113: Protocol8113(),
            8115: Protocol8115(),
            8117: Protocol8117(),
            8118: Protocol8118(),
            8119: Protocol8119(),
            8124: Protocol8124(),
            8125: Protocol8125(),
            8127: Protocol8127(),
        }

    def __repr__(self):
        return '<MDSAllProtocols>'

    def all_from_bytes(self, received_buffer):
        if self.header.from_bytes(received_buffer) and \
                self.all_protocols[self.header.message_id].all_from_bytes(received_buffer, self.mcm_version):
            if self.header.message_id == Protocol8001.message_id:
                # In case the server does not support version control.
                self.mcm_version = self.all_protocols[self.header.message_id].mcm_version or 1
            return self.all_protocols[self.header.message_id]
        else:
            return None

