import sqlalchemy
import collections
import threading
import functools
import logging
from app.basic_structs import (CString, StockDictIndexTable, RawMultiQtIndexTable,
                           ListMultiFundFlowItemIndexTable, ListMultiBuyinRankItemIndexTable,
                           SinaRawMultiQtIndexTable, HKSERawMultiQtIndexTable, User)
from app.global_info import global_market_infos, engine, global_server_infos
from app import eoddata_login, process_data, crawl_web, mds_protocol, request_once, register, global_info, const_protocol


def populate_stock_dict_index_table(index_table):
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = Session()
    session.expire_on_commit = False

    # Notice that it is not allowed to use one long boolean expression in only one filter.
    filter_result = session.query(StockDictIndexTable).filter(
        StockDictIndexTable.date == index_table.date).filter(
        StockDictIndexTable.server_ip == index_table.server_ip).filter(
        StockDictIndexTable.market_id == index_table.market_id).first()

    if filter_result is None:
        print(index_table)
        for item in index_table.stock_dicts:
            item.stock_name = item.stock_name.to_bytes()
            item.stock_code = item.stock_code.to_bytes()
        session.add(index_table)

    else:
        print('IndexTable-> StockDict: is already in the database\n\t '
              'date: %s\n\t server_ip: %s\n\t market_id: %d\n' % \
              (index_table.date, index_table.server_ip, index_table.market_id))

    session.commit()


def query_sina_stock_data(date):
    raise RuntimeError('Idle function!')
#     Session = sqlalchemy.orm.sessionmaker(bind=engine)
#     session = Session()
#
#     server_ip = global_server_infos[0]
#     market_id = 116
#     sina_raw_multi_qts = []
#     index_tables = session.query(SinaRawMultiQtIndexTable). \
#         filter(SinaRawMultiQtIndexTable.date.like(sqlalchemy.text("'%" + date + "%'"))). \
#         filter(SinaRawMultiQtIndexTable.server_ip == server_ip). \
#         filter(SinaRawMultiQtIndexTable.market_id == market_id).all()
#     # Just get one target index table.
#     for index_table in index_tables:
#         sina_raw_multi_qts.extend(index_table.raw_multi_qts)
#         break
#
#     for item in sina_raw_multi_qts:
#         try:
#             item.stock_code = CString(bytes(ord(x) for x in item.stock_code).decode('gbk'), 16)
#             item.stock_name = CString(bytes(ord(x) for x in item.stock_name).decode('gbk'), 32)
#         except UnicodeDecodeError:
#             # stock code 'CBON' name is very long..
#             item.stock_name = CString(bytes(ord(x) for x in item.stock_name[: 30]).decode('gbk'), 32)
#
#     raw_multi_qts = [item.to_json() for item in sina_raw_multi_qts]
#     return raw_multi_qts


def query_hkse_stock_data(date):
    raise RuntimeError('Idle function!')
#     Session = sqlalchemy.orm.sessionmaker(bind=engine)
#     session = Session()
#
#     server_ip = global_server_infos[0]
#     market_id = 116
#     hkse_raw_multi_qts = []
#     index_tables = session.query(HKSERawMultiQtIndexTable). \
#         filter(HKSERawMultiQtIndexTable.date.like(sqlalchemy.text("'%" + date + "%'"))). \
#         filter(HKSERawMultiQtIndexTable.server_ip == server_ip). \
#         filter(HKSERawMultiQtIndexTable.market_id == market_id).all()
#     # Just get one target index table.
#     for index_table in index_tables:
#         hkse_raw_multi_qts.extend(index_table.raw_multi_qts)
#         break
#
#     for item in hkse_raw_multi_qts:
#         item.stock_code = CString(bytes(ord(x) for x in item.stock_code).decode('gbk'), 16)
#
#     raw_multi_qts = [item.to_json() for item in hkse_raw_multi_qts]
#     return raw_multi_qts


def query_stock_dict(date, server_ip, market_id):
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = Session()

    stock_dicts = []
    index_tables = session.query(StockDictIndexTable). \
        filter(StockDictIndexTable.date.like(sqlalchemy.text("'%" + date + "%'"))). \
        filter(StockDictIndexTable.server_ip == server_ip). \
        filter(StockDictIndexTable.market_id == market_id).all()

    # Just get one target index table.
    for index_table in index_tables:
        stock_dicts.extend(index_table.stock_dicts)
        break

    for stock_dict in stock_dicts:
        try:
            stock_dict.stock_code = CString(bytes(ord(x) for x in stock_dict.stock_code).decode('gbk'), 16)
            stock_dict.stock_name = CString(bytes(ord(x) for x in stock_dict.stock_name).decode('gbk'), 32)
        except UnicodeDecodeError:
            # stock code 'CBON' name is very long..
            stock_dict.stock_name = CString(bytes(ord(x) for x in stock_dict.stock_name[: 30]).decode('gbk'), 32)

    stock_dicts = [stock_dict.to_json() for stock_dict in stock_dicts]
    return stock_dicts


def populate_raw_multi_qt_index_table(index_table):
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = Session()
    session.expire_on_commit = False

    # Notice that it is not allowed to use one long boolean expression in only one filter.
    filter_result = session.query(RawMultiQtIndexTable).filter(
        RawMultiQtIndexTable.date == index_table.date).filter(
        RawMultiQtIndexTable.server_ip == index_table.server_ip).filter(
        RawMultiQtIndexTable.market_id == index_table.market_id).first()

    if filter_result is None:
        session.add(index_table)

        # session.expunge(index_table)
    else:
        print('IndexTable-> RawMultiQt: is already in the database\n\t '
              'date: %s\n\t server_ip: %s\n\t market_id: %d\n' % \
              (index_table.date, index_table.server_ip, ord(index_table.market_id)))

    session.commit()


def populate_sina_raw_multi_qt_index_table(index_table):
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = Session()
    session.expire_on_commit = False

    # Notice that it is not allowed to use one long boolean expression in only one filter.
    filter_result = session.query(SinaRawMultiQtIndexTable).filter(
        SinaRawMultiQtIndexTable.date == index_table.date).filter(
        SinaRawMultiQtIndexTable.server_ip == index_table.server_ip).filter(
        SinaRawMultiQtIndexTable.market_id == index_table.market_id).first()

    if filter_result is None:
        print(index_table)
        for item in index_table.raw_multi_qts:
            item.stock_name = item.stock_name.to_bytes()
            item.stock_code = item.stock_code.to_bytes()
        session.add(index_table)

        # session.expunge(index_table)
    else:
        print('IndexTable-> SinaRawMultiQt: is already in the database\n\t '
              'date: %s\n\t server_ip: %s\n\t market_id: %d\n' % \
              (index_table.date, index_table.server_ip, ord(index_table.market_id)))

    session.commit()


def populate_hkse_raw_multi_qt_index_table(index_table):
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = Session()
    session.expire_on_commit = False

    # Notice that it is not allowed to use one long boolean expression in only one filter.
    filter_result = session.query(HKSERawMultiQtIndexTable).filter(
        HKSERawMultiQtIndexTable.date == index_table.date).filter(
        HKSERawMultiQtIndexTable.server_ip == index_table.server_ip).filter(
        HKSERawMultiQtIndexTable.market_id == index_table.market_id).first()

    if filter_result is None:
        print(index_table)
        for item in index_table.raw_multi_qts:
            item.stock_code = item.stock_code.to_bytes()
        session.add(index_table)

        # session.expunge(index_table)
    else:
        print('IndexTable-> HKSERawMultiQt: is already in the database\n\t '
              'date: %s\n\t server_ip: %s\n\t market_id: %d\n' % \
              (index_table.date, index_table.server_ip, ord(index_table.market_id)))

    session.commit()


def populate_list_multi_fund_flow_item_index_table(index_table):
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = Session()
    session.expire_on_commit = False

    # Notice that it is not allowed to use one long boolean expression in only one filter.
    filter_result = session.query(ListMultiFundFlowItemIndexTable).filter(
        ListMultiFundFlowItemIndexTable.date == index_table.date).filter(
        ListMultiFundFlowItemIndexTable.server_ip == index_table.server_ip).filter(
        ListMultiFundFlowItemIndexTable.market_id == index_table.market_id).first()

    if filter_result is None:
        session.add(index_table)

        # session.expunge(index_table)
    else:
        print('IndexTable-> ListMultiFundFlowItem: is already in the database\n\t '
              'date: %s\n\t server_ip: %s\n\t market_id: %d\n' % \
              (index_table.date, index_table.server_ip, index_table.market_id))

    session.commit()


def populate_list_multi_buyin_rank_item_index_table(index_table):
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = Session()
    session.expire_on_commit = False

    # Notice that it is not allowed to use one long boolean expression in only one filter.
    filter_result = session.query(ListMultiBuyinRankItemIndexTable).filter(
        ListMultiBuyinRankItemIndexTable.date == index_table.date).filter(
        ListMultiBuyinRankItemIndexTable.server_ip == index_table.server_ip).filter(
        ListMultiBuyinRankItemIndexTable.market_id == index_table.market_id).first()

    if filter_result is None:
        session.add(index_table)

        # session.expunge(index_table)
    else:
        print('IndexTable-> ListMultiBuyinRankItem: is already in the database\n\t '
              'date: %s\n\t server_ip: %s\n\t market_id: %d\n' % \
              (index_table.date, index_table.server_ip, index_table.market_id))

    session.commit()


def query_raw_multi_qt(date, server_ip, market_id):
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = Session()

    raw_multi_qts = []
    raw_multi_qt_index_tables = session.query(RawMultiQtIndexTable). \
        filter(RawMultiQtIndexTable.date.like(sqlalchemy.text("'%" + date + "%'"))). \
        filter(RawMultiQtIndexTable.server_ip == server_ip). \
        filter(RawMultiQtIndexTable.market_id == market_id).all()
    # Just get one target index table.
    for index_table in raw_multi_qt_index_tables:
        raw_multi_qts.extend(index_table.raw_multi_qts)
        break

    for item in raw_multi_qts:
        item.stock_name = CString(bytes(ord(x) for x in item.stock_name).decode('gbk'), 32)
        item.stock_code = CString(bytes(ord(x) for x in item.stock_code).decode('gbk'), 16)

    qts = [item.to_json() for item in raw_multi_qts]

    return qts


def format_qt_quote(qt_quote):
    qt_quotes = {}
    for qt in qt_quote:
        # Pop the non-numeric field data.
        stock_code = qt.pop('stock_code')
        qt.pop('market_name')
        qt_quotes[stock_code] = qt

    return qt_quotes


def all_to_dict(stock_data, stock_code):
    stock_quote = {}
    for data in stock_data:
        stock_code = data.pop('stock_code', stock_code)
        stock_quote[stock_code] = data
    return stock_quote


def query_raw_list_multi_fund_flow_item(date, server_ip, market_id):
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = Session()

    raw_list_multi_fund_flows = []
    raw_list_multi_fund_flow_item_index_tables = session.query(ListMultiFundFlowItemIndexTable). \
        filter(ListMultiFundFlowItemIndexTable.date.like(sqlalchemy.text("'%" + date + "%'"))). \
        filter(ListMultiFundFlowItemIndexTable.server_ip == server_ip). \
        filter(ListMultiFundFlowItemIndexTable.market_id == market_id).all()

    # Just get one target index table.
    for index_table in raw_list_multi_fund_flow_item_index_tables:
        raw_list_multi_fund_flows.extend(index_table.list_fund_flows)
        break

    for item in raw_list_multi_fund_flows:
        item.stock_code = CString(bytes(ord(x) for x in item.stock_code).decode('gbk'), 16)

    datas = [item.to_json() for item in raw_list_multi_fund_flows]

    return datas


def query_raw_list_multi_buyin_rank_item(date, server_ip, market_id):
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = Session()

    raw_list_multi_buyin_ranks = []
    raw_list_multi_buyin_rank_item_index_tables = session.query(ListMultiBuyinRankItemIndexTable). \
        filter(ListMultiBuyinRankItemIndexTable.date.like(sqlalchemy.text("'%" + date + "%'"))). \
        filter(ListMultiBuyinRankItemIndexTable.server_ip == server_ip). \
        filter(ListMultiBuyinRankItemIndexTable.market_id == market_id).all()

    # Just get one target index table.
    for index_table in raw_list_multi_buyin_rank_item_index_tables:
        raw_list_multi_buyin_ranks.extend(index_table.list_buyin_ranks)
        break

    for item in raw_list_multi_buyin_ranks:
        item.stock_code = CString(bytes(ord(x) for x in item.stock_code).decode('gbk'), 16)

    datas = [item.to_json() for item in raw_list_multi_buyin_ranks]

    return datas


def load_raw_multi_qt_quote(date, server_ip, market_id):
    qts = query_raw_multi_qt(date, server_ip, market_id)
    qt_quotes = {}
    for qt in qts:
        stock_code = qt['stock_code']
        # Pop the non-numeric field data.
        qt.pop('stock_code')
        qt.pop('market_name')
        qt_quotes[stock_code] = qt

    return qt_quotes


def pile_up_stock_data_in_servers(stock_data_in_servers):
    all_datas = []
    for stock_code, left_dict in stock_data_in_servers.items():
        for field_name, value_dict in left_dict.items():
            for value, ip_list in value_dict.items():
                column_headers = ['stock_code', 'field_name', 'value', 'counter', 'ip_list']
                column_content = (stock_code, field_name, value, len(ip_list), '/'.join(ip_list))
                column_dict = {}
                for k, v in zip(column_headers, column_content):
                    column_dict[k] = v
                all_datas.append(column_dict)

    return all_datas


def compare_quote(source_quote, dest_quote, field_cmp_map, need_datetime_check=True,
                  are_different_quotes_picked_up=False):
    if (not source_quote) or (not dest_quote):
        return {}

    common_codes = set(source_quote) & set(dest_quote)
    summary_differ_dict = {}
    for code in common_codes:
        source_data_dict = source_quote[code]
        dest_data_dict = dest_quote[code]
        differ_dict = collections.defaultdict(dict)
        if need_datetime_check:
            source_date = source_data_dict.get('trade_date', 0)
            dest_date = source_data_dict.get('trade_date', 0)
            if source_date != dest_date:
                differ_dict['trade_date']['source'] = source_date
                differ_dict['trade_date']['dest'] = dest_date
                continue
        common_fields = set(source_data_dict) & set(dest_data_dict) & set(field_cmp_map)
        for field in common_fields:
            cmp_op = field_cmp_map[field]
            if not cmp_op(source_data_dict[field], dest_data_dict[field]):
                differ_dict[field]['source'] = source_data_dict[field]
                differ_dict[field]['dest'] = dest_data_dict[field]
        if differ_dict:
            summary_differ_dict[code] = differ_dict
    if are_different_quotes_picked_up:
        source_unique_codes = set(source_quote) - set(dest_quote)
        for stock_code in source_unique_codes:
            source_data_dict = source_quote[stock_code]
            fields = set(field_cmp_map) & set(source_data_dict)
            differ_dict = collections.defaultdict(dict)
            for field in fields:
                differ_dict[field]['source'] = source_data_dict[field]
                differ_dict[field]['dest'] = 'null'
            if differ_dict:
                summary_differ_dict[stock_code] = differ_dict
        dest_unique_codes = set(dest_quote) - set(source_quote)
        for stock_code in dest_unique_codes:
            dest_data_dict = dest_quote[stock_code]
            fields = set(field_cmp_map) & set(dest_data_dict)
            differ_dict = collections.defaultdict(dict)
            for field in fields:
                differ_dict[field]['source'] = 'null'
                differ_dict[field]['dest'] = dest_data_dict[field]
            if differ_dict:
                summary_differ_dict[stock_code] = differ_dict

    return summary_differ_dict


# for convenient display of the table in the front end.
def pile_up_differ_dict(differ_dict, column_headers):
    all_datas = []
    for stock_code, left_dict in differ_dict.items():
        piled_up_dict = {}
        for field_name, differ_values in left_dict.items():
            piled_up_dict[field_name] = \
                str(differ_values['source']) + ' / ' + str(differ_values['dest'])
        piled_up_dict['stock_code'] = stock_code

        for header in column_headers:
            if header not in piled_up_dict.keys():
                piled_up_dict[header] = '-'

        all_datas.append(piled_up_dict)

    return all_datas


def pile_up_dict(data_to_pile_up, column_headers):
    for item in data_to_pile_up:
        for header in column_headers:
            if header not in item.keys():
                item[header] = '-'

    return data_to_pile_up


def compare_with_eoddata(server_ip, port, market, eod_file_date):
    try:
        qt_quote = request_8110((server_ip, port), market)
    except Exception as e:
        raise e
    else:
        source_qt_quote = format_qt_quote(qt_quote)
        if not source_qt_quote:
            logging.getLogger().debug('empty source qt quote of %s' % market)
            return []
        eod_login = eoddata_login.EoddataLogin(target_markets=[market])
        dest_qt_quote = eod_login.load_raw_multi_qt_quote(date=eod_file_date, market_name=market)
        if not dest_qt_quote:
            logging.getLogger().debug('empty dest qt quote of %s' % market)
            return []

        are_volume_equal = functools.partial(process_data.are_floats_equal, precision=100 ** 1)
        are_ints_equal = functools.partial(process_data.are_floats_equal, precision=10)
        are_date_equal = functools.partial(process_data.are_floats_equal, precision=1)
        summary_differ_dict = compare_quote(source_qt_quote, dest_qt_quote,
                                            field_cmp_map={
                                                'open_price': are_ints_equal,
                                                'newest_price': are_ints_equal,
                                                'highest_price': are_ints_equal,
                                                'lowest_price': are_ints_equal,
                                                'close_price': are_ints_equal,
                                                'volume': are_volume_equal,
                                                'trade_sequence': are_date_equal,
                                            },
                                            are_different_quotes_picked_up=True
                                            )
        column_headers = ['stock_code', 'trade_sequence', 'open_price', 'close_price',
                          'newest_price', 'highest_price', 'lowest_price', 'volume']
        return pile_up_differ_dict(summary_differ_dict, column_headers)


def compare_global_quote(server_ip, port):
    try:
        market = 'QQZS'
        qt_quote = request_8110((server_ip, port), market)
    except Exception as e:
        raise e
    else:
        source_qt_quote = format_qt_quote(qt_quote)
        if not source_qt_quote:
            logging.getLogger().debug('empty source qt quote of market: %d' % market_id)
            return []

        dest_qt_quote = crawl_web.crawl_nasdaq_stock_exchange()
        summary_differ_dict = compare_quote(source_qt_quote, dest_qt_quote,
                                           field_cmp_map={
                                               'newest_price': process_data.are_floats_equal,
                                               'highest_price': process_data.are_floats_equal,
                                               'lowest_price': process_data.are_floats_equal,
                                           }
                                           )
        column_headers = ['stock_code', 'newest_price', 'highest_price', 'lowest_price']

        return pile_up_differ_dict(summary_differ_dict, column_headers)


def compare_with_sina_data(server_ip, port):
    try:
        market = 'HK'
        hk_stock_dicts = request_8100((server_ip, port), market)
        qt_quote = request_8110((server_ip, port), market)
    except Exception as e:
        raise e
    else:
        source_qt_quote = format_qt_quote(qt_quote)
        if not source_qt_quote:
            logging.getLogger().debug('empty source qt quote of market: %s' % market)
            return []

        stock_codes = [stock_dict['stock_code'] for stock_dict in hk_stock_dicts]
        sina_raw_multi_qts = crawl_web.crawl_sina_stock_data(stock_codes)
        sina_raw_multi_qts = [item.to_json() for item in sina_raw_multi_qts]

        if not sina_raw_multi_qts:
            logging.getLogger().debug('Fail to request sina stock data.')
            return []

        dest_qt_quote = {}
        for qt in sina_raw_multi_qts:
            stock_code = qt.pop('stock_code', None)
            dest_qt_quote[stock_code] = qt
        are_integer_equal = functools.partial(process_data.are_floats_equal, precision=10 ** 2)
        are_volume_equal = functools.partial(process_data.are_floats_equal, precision=10 ** 3)
        are_amount_equal = functools.partial(process_data.are_floats_equal, precision=10 ** 3)
        summary_differ_dict = compare_quote(source_qt_quote, dest_qt_quote,
                                           field_cmp_map={
                                               'open_price': are_integer_equal,
                                               'highest_price': are_integer_equal,
                                               'lowest_price': are_integer_equal,
                                               'newest_price': are_integer_equal,
                                               'volume': are_volume_equal,
                                               'amount': are_amount_equal,
                                           }
                                           )
        column_headers = ['stock_code', 'open_price', 'highest_price', 'lowest_price',
                          'newest_price', 'volume', 'amount']
        return pile_up_differ_dict(summary_differ_dict, column_headers)


def compare_with_hkse_data(server_ip, port):
    try:
        market = 'HK'
        hk_stock_dicts = request_8100((server_ip, port), market)
        qt_quote = request_8110((server_ip, port), market)
    except Exception as e:
        raise e
    else:
        source_qt_quote = format_qt_quote(qt_quote)
        if not source_qt_quote:
            logging.getLogger().debug('empty source qt quote of market: %s' % market)
            return []

        stock_codes = [stock_dict['stock_code'] for stock_dict in hk_stock_dicts]
        # Limit the size of requested stock codes to guarantee the speed.
        hkse_raw_multi_qts = crawl_web.crawl_hongkong_stock_exchange(stock_codes[:5])
        hkse_raw_multi_qts = [item.to_json() for item in hkse_raw_multi_qts]
        dest_qt_quote = {}
        for qt in hkse_raw_multi_qts:
            stock_code = qt.pop('stock_code', None)
            dest_qt_quote[stock_code] = qt

        are_integer_equal = functools.partial(process_data.are_floats_equal, precision=10 ** 2)
        are_volume_equal = functools.partial(process_data.are_floats_equal, precision=10 ** 3)
        are_amount_equal = functools.partial(process_data.are_floats_equal, precision=10 ** 3)
        summary_differ_dict = compare_quote(source_qt_quote, dest_qt_quote,
                                           field_cmp_map={
                                               'highest_price': are_integer_equal,
                                               'lowest_price': are_integer_equal,
                                               'newest_price': are_integer_equal,
                                               'volume': are_volume_equal,
                                               'amount': are_amount_equal,
                                           }
                                           )
        column_headers = ['stock_code', 'highest_price', 'lowest_price',
                          'newest_price', 'volume', 'amount']

        return pile_up_differ_dict(summary_differ_dict, column_headers)


def request_hkse_stock_data(server_ip, port):
    # It takes a long time to request all the stock codes from the website.
    # However, here we just care about the stock codes whose data is different from the sina website.
    stock_codes = [item['stock_code'] for item in compare_with_sina_data(server_ip, port)]
    if not stock_codes:
        logging.getLogger().debug('There is no stock code left when comparing with sina data with ip: {}: port: {}'.\
                                  format(server_ip, port))
        return []

    # Limit the size of requested stock codes to guarantee the speed.
    raw_multi_qts = crawl_web.crawl_hongkong_stock_exchange(stock_codes[:20])
    if not raw_multi_qts:
        logging.getLogger().debug('Fail to request hkse stock data.')

    return raw_multi_qts


def populate_user_info(user_infos):
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = Session()
    session.expire_on_commit = False

    for item in user_infos:
        user = User(**item)
        # Notice that it is not allowed to use one long boolean expression in only one filter.
        filter_result = session.query(User).filter(
            User.nickname == user.nickname).first()

        if filter_result is None:
            session.add(user)
        else:
            print('User: %r is already in the database.' % user)
    session.commit()


def query_user_info(**kwargs):
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = Session()

    id = kwargs.pop('id', None)
    email = kwargs.pop('email', None)
    password = kwargs.pop('password', None)
    all_users = session.query(User).all()
    for user in all_users:
        if user.id == id or (user.email == email and str(user.password) == password):
            return user
    return None


def request_8101(addr, market_name, stock_id):
    p8101 = mds_protocol.Protocol8101()
    p8101.is_pushed = mds_protocol.PUSH_TYPE_ONCE
    p8101.market_id = global_market_infos[market_name]
    p8101.stock_id = stock_id
    client = request_once.request_once(p8101)()
    try:
        client.connect(addr)
    except Exception as e:
        raise e
    else:
        stock_data_list = client.get_data().get(p8101.message_id, [])
        # Because this information is not returned under the message ID 8101, I make it myself.
        stock_data_list = [item.to_json() for item in stock_data_list]
        stock_info = {'market_name': market_name, 'stock_code': stock_id}
        for item in stock_data_list:
            item.update(stock_info)
        return stock_data_list


def request_8102(addr):
    p8102 = mds_protocol.Protocol8102()
    p8102.is_pushed = mds_protocol.PUSH_TYPE_ONCE
    p8102.market_ids = global_market_infos.values()
    client = request_once.request_once(p8102)()
    try:
        client.connect(addr)
    except Exception as e:
        raise e
    else:
        stock_data_list = client.get_data().get(p8102.message_id, [])
        stock_data_list = [item.to_json() for item in stock_data_list]
        return stock_data_list


def request_all_8102(all_address):
    market_time_dict = collections.defaultdict(dict)
    for addr in all_address:
        stock_data_list = request_8102(addr)
        for item in stock_data_list:
            server_info = process_data.find_first_target_info(global_server_infos, addr[0])
            if server_info:
                item[server_info['id']] = item.pop('time')
                market_time_dict[item['market_id']].update(item)
    all_data = list(market_time_dict.values())
    column_headers = [item['id'] for item in global_server_infos]

    return pile_up_dict(all_data, column_headers)


def request_8103(addr, market_name, stock_id):
    p8103 = mds_protocol.Protocol8103()
    p8103.is_pushed = mds_protocol.PUSH_TYPE_ONCE
    p8103.market_id = global_market_infos[market_name]
    p8103.stock_id = stock_id
    client = request_once.request_once(p8103)()
    try:
        client.connect(addr)
    except Exception as e:
        raise e
    else:
        stock_data_list = client.get_data().get(p8103.message_id, [])
        stock_data_list = [item.to_json() for item in stock_data_list]
        return stock_data_list


def request_8104(addr, market_name, stock_id, period=1):
    p8104 = mds_protocol.Protocol8104()
    p8104.is_pushed = mds_protocol.PUSH_TYPE_ONCE
    p8104.market_id = global_market_infos[market_name]
    p8104.stock_id = stock_id
    p8104.period = period
    client = request_once.request_once(p8104)()
    try:
        client.connect(addr)
    except Exception as e:
        raise e
    else:
        stock_data_list = client.get_data().get(p8104.message_id, [])
        stock_data_list = [item.to_json() for item in stock_data_list]
        return stock_data_list


def request_8105(addr, market_name, stock_id):
    p8105 = mds_protocol.Protocol8105()
    p8105.is_pushed = mds_protocol.PUSH_TYPE_ONCE
    p8105.market_id = global_market_infos[market_name]
    p8105.stock_id = stock_id
    client = request_once.request_once(p8105)()
    try:
        client.connect(addr)
    except Exception as e:
        raise e
    else:
        stock_data_list = client.get_data().get(p8105.message_id, [])
        stock_data_list = [item.to_json() for item in stock_data_list]
        return stock_data_list


def request_8106(addr, market_name, block_type):
    p8106 = mds_protocol.Protocol8106()
    p8106.is_pushed = mds_protocol.PUSH_TYPE_ONCE
    p8106.type = block_type
    p8106.market_id = global_market_infos[market_name]
    p8106.sub_type = -1
    client = request_once.request_once(p8106)()
    try:
        client.connect(addr)
    except Exception as e:
        raise e
    else:
        stock_data_list = client.get_data().get(p8106.message_id, [])
        stock_data_list = [item.to_json() for item in stock_data_list]
        return stock_data_list


def request_8100(addr, market_name):
    p8100 = mds_protocol.Protocol8100()
    p8100.is_pushed = mds_protocol.PUSH_TYPE_ONCE
    p8100.market_id = global_market_infos[market_name]
    p8100.counter = 1
    client = request_once.request_once(p8100)()
    try:
        client.connect(addr)
    except Exception as e:
        raise e
    else:
        stock_dict = client.get_data().get(p8100.message_id, [])
        stock_dict = [item.to_json() for item in stock_dict]
        return stock_dict


def request_8110(addr, market_name):
    p8110 = mds_protocol.Protocol8110()
    p8110.is_pushed = mds_protocol.PUSH_TYPE_ONCE
    p8110.request_type = 0
    p8110.market_id = global_market_infos[market_name]
    client = request_once.request_once(p8110)()
    try:
        client.connect(addr)
    except Exception as e:
        raise e
    else:
        stock_data_list = client.get_data().get(p8110.message_id, [])
        stock_data_list = [item.to_json() for item in stock_data_list]
        return stock_data_list


def request_8112(addr, market_name, block_id):
    protocol_8112 = mds_protocol.Protocol8112()
    protocol_8112.is_pushed = mds_protocol.PUSH_TYPE_ONCE
    protocol_8112.market_id = global_market_infos[market_name]
    protocol_8112.block_id = block_id
    client = request_once.request_once(protocol_8112)()
    try:
        client.connect(addr)
    except Exception as e:
        raise e
    else:
        stock_data_list = client.get_data().get(protocol_8112.message_id, [])
        stock_data_list = [item.to_json() for item in stock_data_list]
        return stock_data_list


def request_8113(addr, market_name, broker_no):
    protocol_8113 = mds_protocol.Protocol8113()
    protocol_8113.is_pushed = mds_protocol.PUSH_TYPE_ONCE
    protocol_8113.market_id = global_market_infos[market_name]
    protocol_8113.broker_no = broker_no
    client = request_once.request_once(protocol_8113)()
    try:
        client.connect(addr)
    except Exception as e:
        raise e
    else:
        stock_data_list = client.get_data().get(protocol_8113.message_id, [])
        stock_data_list = [item.to_json() for item in stock_data_list]
        return stock_data_list


def request_8115(addr, market_name, stock_id):
    p8115 = mds_protocol.Protocol8115()
    p8115.is_pushed = mds_protocol.PUSH_TYPE_ONCE
    p8115.market_id = global_market_infos[market_name]
    p8115.stock_id = stock_id
    client = request_once.request_once(p8115)()
    try:
        client.connect(addr)
    except Exception as e:
        raise e
    else:
        stock_data_list = client.get_data().get(p8115.message_id, [])
        stock_data_list = [item.to_json() for item in stock_data_list]
        return stock_data_list


def request_8117(addr, market_name, stock_id):
    p8117 = mds_protocol.Protocol8117()
    p8117.is_pushed = mds_protocol.PUSH_TYPE_ONCE
    p8117.market_id = global_market_infos[market_name]
    p8117.stock_id = stock_id
    client = request_once.request_once(p8117)()
    try:
        client.connect(addr)
    except Exception as e:
        raise e
    else:
        stock_data_list = client.get_data().get(p8117.message_id, [])
        stock_data_list = [item.to_json() for item in stock_data_list]
        return stock_data_list


def request_8118(addr, market_name, stock_id):
    p8118 = mds_protocol.Protocol8118()
    p8118.is_pushed = mds_protocol.PUSH_TYPE_ONCE
    p8118.market_id = global_market_infos[market_name]
    p8118.stock_id = stock_id
    client = request_once.request_once(p8118)()
    try:
        client.connect(addr)
    except Exception as e:
        raise e
    else:
        stock_data_list = client.get_data().get(p8118.message_id, [])
        stock_data_list = [item.to_json() for item in stock_data_list]
        return stock_data_list


def request_8119(addr, market_name, stock_id):
    p8119 = mds_protocol.Protocol8119()
    p8119.is_pushed = mds_protocol.PUSH_TYPE_ONCE
    p8119.market_id = global_market_infos[market_name]
    p8119.stock_id = stock_id
    client = request_once.request_once(p8119)()
    try:
        client.connect(addr)
    except Exception as e:
        raise e
    else:
        stock_data_list = client.get_data().get(p8119.message_id, [])
        stock_data_list = [item.to_json() for item in stock_data_list]
        return stock_data_list


def request_8124(addr, market_name):
    p8124 = mds_protocol.Protocol8124()
    p8124.is_pushed = mds_protocol.PUSH_TYPE_ONCE
    p8124.market_id = global_market_infos[market_name]
    p8124.request_type = 0
    client = request_once.request_once(p8124)()
    try:
        client.connect(addr)
    except Exception as e:
        raise e
    else:
        stock_data_list = client.get_data().get(p8124.message_id, [])
        stock_data_list = [item.to_json() for item in stock_data_list]
        return stock_data_list


def request_8125(addr, market_name):
    p8125 = mds_protocol.Protocol8125()
    p8125.is_pushed = mds_protocol.PUSH_TYPE_ONCE
    p8125.market_id = global_market_infos[market_name]
    p8125.request_type = 0
    client = request_once.request_once(p8125)()
    try:
        client.connect(addr)
    except Exception as e:
        raise e
    else:
        stock_data_list = client.get_data().get(p8125.message_id, [])
        stock_data_list = [item.to_json() for item in stock_data_list]
        return stock_data_list


def register_8102(addr, event_loop):
    p8102 = mds_protocol.Protocol8102()
    p8102.is_pushed = mds_protocol.PUSH_TYPE_REGISTER
    p8102.market_ids = global_info.global_market_infos.values()
    client = register.register(p8102)(event_loop)
    client.connect(addr)
    return client


def register_all_8102(all_address, event_loop):
    all_client = {}
    for addr in all_address:
        client = register_8102(addr, event_loop)
        all_client[addr[0]] = client
    t = threading.Thread(target=event_loop.run_forever)
    t.start()
    return all_client


def compare_stock_data(address_pairs, message_id, market_name, stock_id=None):
    all_requests = {
        8100: request_8100,
        8101: request_8101,
        # It is unnessary to compare the market time here.
        # 8102: request_8102,
        8103: request_8103,
        8104: request_8104,
        8105: request_8105,
        8106: request_8106,
        81061: request_8106,
        8110: request_8110,
        8112: request_8112,
        # Could not support comparison of data under this message ID right now.
        # 8113: request_8113,
        8115: request_8115,
        8117: request_8117,
        8118: request_8118,
        8119: request_8119,
        8124: request_8124,
        8125: request_8125,
    }
    stock_data_in_servers = []
    for server_ip, port in address_pairs:
        try:
            if message_id == 8106:
                stock_data = all_requests[message_id]((server_ip, port), market_name, const_protocol.TYPE_HK_BLOCK)
            elif message_id == 81061:
                stock_data = all_requests[message_id]((server_ip, port), market_name, const_protocol.TYPE_BLOCK_OVERVIEW)
            else:
                stock_message_ids = [8101, 8103, 8104, 8105, 8112, 8115, 8117, 8118, 8119]
                if message_id in stock_message_ids:
                    stock_data = all_requests[message_id]((server_ip, port), market_name, stock_id)
                else:
                    stock_data = all_requests[message_id]((server_ip, port), market_name)
        except Exception as e:
            print('Caught an exception: {}'.format(e))
            raise RuntimeError('Exception confronted when accessing {}: {}'.format((server_ip, port), e))
        else:
            stock_quote = all_to_dict(stock_data, stock_id)
            stock_data_in_servers.append((stock_quote, server_ip))
    all_data_dict = collections.defaultdict(lambda: collections.defaultdict(list))
    for stock_quote, ip in stock_data_in_servers:
        for stock_code, field_dict in stock_quote.items():
            for fname, fvalue in field_dict.items():
                all_data_dict[stock_code][fname].append((fvalue, ip))

    differ_data_dict = collections.defaultdict(lambda: collections.defaultdict(list))
    for stock_code, field_dict in all_data_dict.items():
        for _fname, _fvaluelist in field_dict.items():
            _value_dict = collections.defaultdict(list)
            for _fvalue, ip in _fvaluelist:
                _value_dict[_fvalue].append(ip)

            if len(_value_dict) > 1:
                differ_data_dict[stock_code][_fname] = _value_dict
            elif len(_value_dict) == 1 and len(list(_value_dict.values())[0]) < len(address_pairs):
                all_servers = [item[0] for item in address_pairs]
                absent_servers = set(all_servers) - set(list(_value_dict.values())[0])
                _value_dict['null'] = list(absent_servers)
                differ_data_dict[stock_code][_fname] = _value_dict
            else:
                pass
    return differ_data_dict
