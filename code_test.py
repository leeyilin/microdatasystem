from app import mds_data_set
from app.global_info import global_server_infos
from app.const_protocol import TYPE_HK_BLOCK, TYPE_BLOCK_OVERVIEW


all_addr = [(item['server_ip'], item['port']) for item in global_server_infos]
all_requests = {
    8100: mds_data_set.request_8100,
    8101: mds_data_set.request_8101,
    # It is unnessary to compare the market time here.
    # 8102: mds_data_set.request_8102,
    8103: mds_data_set.request_8103,
    8104: mds_data_set.request_8104,
    8105: mds_data_set.request_8105,
    8106: mds_data_set.request_8106,
    81061: mds_data_set.request_8106,
    8110: mds_data_set.request_8110,
    8112: mds_data_set.request_8112,
    # Could not support comparison of data under this message ID right now.
    # 8113: mds_data_set.request_8113,
    8115: mds_data_set.request_8115,
    8117: mds_data_set.request_8117,
    8118: mds_data_set.request_8118,
    8119: mds_data_set.request_8119,
    8124: mds_data_set.request_8124,
    8125: mds_data_set.request_8125,
}
stock_message_ids = [8101, 8103, 8104, 8105, 8112, 8115, 8117, 8118, 8119]
message_ids = [8100, 8110, 8124, 8125]
test_market_name = 'HK'
test_stock_id = '00700'


def test_all_requests():
    assert all_requests[8102](all_addr[0]) != []
    assert mds_data_set.request_all_8102(all_addr) != []
    for message_id in stock_message_ids:
        assert all_requests[message_id](all_addr[0], test_market_name, test_stock_id) != []
    assert all_requests[8106](all_addr[0], 'HKBLOCK', TYPE_HK_BLOCK) != []
    assert all_requests[8106](all_addr[0], 'HKBLOCK', TYPE_BLOCK_OVERVIEW) != []
    for message_id in message_ids:
        assert all_requests[message_id](all_addr[0], test_market_name) != []
    assert all_requests[8113](all_addr[0], test_market_name, 3440) != []


def test_comparison():
    for message_id in all_requests.keys():
        print('message_id: {}'.format(message_id))
        stock_id = test_stock_id if message_id in stock_message_ids else None
        if message_id in [8106, 81061]:
            # Select three servers to compare in order to reduce the waiting time.
            print(len(mds_data_set.compare_stock_data(all_addr[:3], message_id, 'HKBLOCK', stock_id)))
        elif message_id not in [8102, 8113]:
            # Select three servers to compare in order to reduce the waiting time.
            print(len(mds_data_set.compare_stock_data(all_addr[:3], message_id, test_market_name, stock_id)))


if __name__ == '__main__':
    # test_all_requests()
    test_comparison()