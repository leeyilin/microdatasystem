from app import mds_protocol


protocol_8101 = mds_protocol.Protocol8101()
protocol_8101.is_pushed = mds_protocol.PUSH_TYPE_ONCE
protocol_8101.market_id = 116
protocol_8101.stock_id = '00700'

protocol_8102 = mds_protocol.Protocol8102()
protocol_8102.is_pushed = mds_protocol.PUSH_TYPE_ONCE
protocol_8102.market_ids = (116, 105, 106)

protocol_8103 = mds_protocol.Protocol8103()
protocol_8103.is_pushed = mds_protocol.PUSH_TYPE_ONCE
protocol_8103.market_id = 116
protocol_8103.stock_id = '00700'

protocol_8104 = mds_protocol.Protocol8104()
protocol_8104.is_pushed = mds_protocol.PUSH_TYPE_ONCE
protocol_8104.market_id = 116
protocol_8104.stock_id = '00700'
protocol_8104.period = 1

TYPE_HK_BLOCK = 5
TYPE_BLOCK_OVERVIEW = 7
protocol_8106 = mds_protocol.Protocol8106()
protocol_8106.is_pushed = mds_protocol.PUSH_TYPE_ONCE
protocol_8106.type = TYPE_BLOCK_OVERVIEW
protocol_8106.market_id = 201
protocol_8106.sub_type = -1

protocol_8100 = mds_protocol.Protocol8100()
protocol_8100.is_pushed = mds_protocol.PUSH_TYPE_ONCE
protocol_8100.counter = 1
protocol_8100.market_id = 116

protocol_8110 = mds_protocol.Protocol8110()
protocol_8110.is_pushed = mds_protocol.PUSH_TYPE_ONCE
protocol_8110.request_type = 0
protocol_8110.market_id = 116

protocol_8112 = mds_protocol.Protocol8112()
protocol_8112.is_pushed = mds_protocol.PUSH_TYPE_ONCE
protocol_8112.market_id = 116
protocol_8112.block_id = '00700'

protocol_8113 = mds_protocol.Protocol8113()
protocol_8113.is_pushed = mds_protocol.PUSH_TYPE_ONCE
protocol_8113.market_id = 116
protocol_8113.broker_no = 3440

# the register type is not tested.
protocol_8115 = mds_protocol.Protocol8115()
protocol_8115.is_pushed = mds_protocol.PUSH_TYPE_ONCE
protocol_8115.market_id = 116
protocol_8115.stock_id = '00700'

# the register type is not tested.
protocol_8124 = mds_protocol.Protocol8124()
protocol_8124.is_pushed = mds_protocol.PUSH_TYPE_ONCE
protocol_8124.request_type = 0
protocol_8124.market_id = 116

protocol_8125 = mds_protocol.Protocol8125()
protocol_8125.is_pushed = mds_protocol.PUSH_TYPE_ONCE
protocol_8125.request_type = 0
protocol_8125.market_id = 116

protocol_8117 = mds_protocol.Protocol8117()
protocol_8117.is_pushed = mds_protocol.PUSH_TYPE_ONCE
protocol_8117.market_id = 116
protocol_8117.stock_id = '00700'

protocol_8118 = mds_protocol.Protocol8118()
protocol_8118.is_pushed = mds_protocol.PUSH_TYPE_ONCE
protocol_8118.market_id = 116
protocol_8118.stock_id = '00700'

protocol_8119 = mds_protocol.Protocol8119()
protocol_8119.is_pushed = mds_protocol.PUSH_TYPE_ONCE
protocol_8119.market_id = 116
protocol_8119.stock_id = '00700'

protocol_8127 = mds_protocol.Protocol8127()
protocol_8127.is_pushed = mds_protocol.PUSH_TYPE_ONCE
protocol_8127.market_id = 148
protocol_8127.stock_code = 'CSCSHQ'

