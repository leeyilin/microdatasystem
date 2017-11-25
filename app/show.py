import flask
from app import mds_data_set, process_data, const_protocol
from app.global_info import global_server_infos


def show_stock_dict(server_ip, port, market_name):
    try:
        all_datas = mds_data_set.request_8100((server_ip, port), market_name)
    except Exception:
        flask.flash('Fail to request data of {} from {}: {}'.format(market_name, server_ip, port))
        all_datas = []
    finally:
        selected_message_id = '8100'

        return flask.render_template('stock_data_table.html', stock_dicts=all_datas,
                                     selected_market_name=market_name, selected_ip=server_ip,
                                     selected_port=port, selected_message_id=selected_message_id,
                                     selected_navbar_item='stock_data', server_infos=global_server_infos)


def show_rtmin(server_ip, port, market_name, stock_id):
    try:
        all_datas = mds_data_set.request_8103((server_ip, port), market_name, stock_id)
    except Exception:
        flask.flash('Fail to request data of {} from {}: {}'.format((market_name, stock_id), server_ip, port))
        all_datas = []
    finally:
        selected_message_id = '8103'
        selected_stock_id = stock_id
        return flask.render_template('stock_data_table.html', rtmins=all_datas,
                                     selected_market_name=market_name, selected_ip=server_ip,
                                     selected_port=port, selected_message_id=selected_message_id,
                                     selected_navbar_item='stock_data', selected_stock_id=selected_stock_id,
                                     server_infos=global_server_infos)


def show_kline(server_ip, port, market_name, stock_id):
    try:
        all_datas = mds_data_set.request_8104((server_ip, port), market_name, stock_id)
    except Exception:
        flask.flash('Fail to request data of {} from {}: {}'.format((market_name, stock_id), server_ip, port))
        all_datas = []
    finally:
        selected_message_id = '8104'
        selected_stock_id = stock_id
        return flask.render_template('stock_data_table.html', rtmins=all_datas,
                                     selected_market_name=market_name, selected_ip=server_ip,
                                     selected_port=port, selected_message_id=selected_message_id,
                                     selected_navbar_item='stock_data', selected_stock_id=selected_stock_id,
                                     server_infos=global_server_infos)


def show_blockqt(server_ip, port, market_name):
    try:
        all_datas = mds_data_set.request_8106((server_ip, port), market_name, const_protocol.TYPE_HK_BLOCK)
    except Exception:
        flask.flash('Fail to request data of {} from {}: {}'.format(market_name, server_ip, port))
        all_datas = []
    finally:
        selected_message_id = '8106'
        return flask.render_template('stock_data_table.html', blockqts=all_datas,
                                     selected_market_name=market_name, selected_ip=server_ip,
                                     selected_port=port, selected_message_id=selected_message_id,
                                     selected_navbar_item='stock_data', server_infos=global_server_infos)


def show_block_overview(server_ip, port, market_name):
    try:
        all_datas = mds_data_set.request_8106((server_ip, port), market_name, const_protocol.TYPE_BLOCK_OVERVIEW)
    except Exception:
        flask.flash('Fail to request data of {} from {}: {}'.format(market_name, server_ip, port))
        all_datas = []
    finally:
        selected_message_id = '8106_ex'
        return flask.render_template('stock_data_table.html', block_overviews=all_datas,
                                     selected_market_name=market_name, selected_ip=server_ip,
                                     selected_port=port, selected_message_id=selected_message_id,
                                     selected_navbar_item='stock_data', server_infos=global_server_infos)


def show_basic_qt(server_ip, port, market_name, stock_id):
    try:
        all_datas = mds_data_set.request_8101((server_ip, port), market_name, stock_id)
    except Exception:
        flask.flash('Fail to request data of {} from {}: {}'.format((market_name, stock_id), server_ip, port))
        all_datas = []
    finally:
        selected_message_id = '8101'
        return flask.render_template('stock_data_table.html', new_lists=all_datas,
                                     selected_market_name=market_name, selected_ip=server_ip,
                                     selected_port=port, selected_message_id=selected_message_id,
                                     selected_navbar_item='stock_data', server_infos=global_server_infos,
                                     selected_stock_id=stock_id)


def show_raw_multi_qt(server_ip, port, market_name):
    try:
        all_datas = mds_data_set.request_8110((server_ip, port), market_name)
    except Exception:
        flask.flash('Fail to request data of {} from {}: {}'.format(market_name, server_ip, port))
        all_datas = []
    finally:
        selected_message_id = '8110'
        return flask.render_template('stock_data_table.html', new_lists=all_datas,
                                     selected_market_name=market_name, selected_ip=server_ip,
                                     selected_port=port, selected_message_id=selected_message_id,
                                     selected_navbar_item='stock_data', server_infos=global_server_infos)


def show_base_bq(server_ip, port, market_name, stock_id):
    try:
        all_datas = mds_data_set.request_8112((server_ip, port), market_name, stock_id)
    except Exception:
        flask.flash('Fail to request data of {} from {}: {}'.format((market_name, stock_id), server_ip, port))
        all_datas = []
    finally:
        selected_message_id = '8112'
        selected_stock_id = stock_id
        return flask.render_template('stock_data_table.html', base_bqs=all_datas,
                                     selected_market_name=market_name, selected_ip=server_ip,
                                     selected_port=port, selected_message_id=selected_message_id,
                                     selected_navbar_item='stock_data', selected_stock_id=selected_stock_id,
                                     server_infos=global_server_infos)


def show_bq_trace(server_ip, port, market_name, broker_no):
    try:
        all_datas = mds_data_set.request_8113((server_ip, port), market_name, broker_no)
    except Exception:
        flask.flash('Fail to request data of {} from {}: {}'.format((market_name, broker_no), server_ip, port))
        all_datas = []
    finally:
        selected_message_id = '8113'
        selected_stock_id = broker_no
        return flask.render_template('stock_data_table.html', bq_traces=all_datas,
                                     selected_market_name=market_name, selected_ip=server_ip,
                                     selected_port=port, selected_message_id=selected_message_id,
                                     selected_navbar_item='stock_data', selected_stock_id=selected_stock_id,
                                     server_infos=global_server_infos)


def show_mx(server_ip, port, market_name, stock_id):
    try:
        all_datas = mds_data_set.request_8105((server_ip, port), market_name, stock_id)
    except Exception:
        flask.flash('Fail to request data of {} from {}: {}'.format((market_name, stock_id), server_ip, port))
        all_datas = []
    finally:
        selected_message_id = '8105'
        selected_stock_id = stock_id
        return flask.render_template('stock_data_table.html', mxs=all_datas,
                                     selected_market_name=market_name, selected_ip=server_ip,
                                     selected_port=port, selected_message_id=selected_message_id,
                                     selected_navbar_item='stock_data', selected_stock_id=selected_stock_id,
                                     server_infos=global_server_infos)


def show_mx2(server_ip, port, market_name, stock_id):
    try:
        all_datas = mds_data_set.request_8115((server_ip, port), market_name, stock_id)
    except Exception:
        flask.flash('Fail to request data of {} from {}: {}'.format((market_name, stock_id), server_ip, port))
        all_datas = []
    finally:
        selected_message_id = '8115'
        selected_stock_id = stock_id
        return flask.render_template('stock_data_table.html', mxs=all_datas,
                                     selected_market_name=market_name, selected_ip=server_ip,
                                     selected_port=port, selected_message_id=selected_message_id,
                                     selected_navbar_item='stock_data', selected_stock_id=selected_stock_id,
                                     server_infos=global_server_infos)


def show_qtex(server_ip, port, market_name, stock_id):
    try:
        all_datas = mds_data_set.request_8117((server_ip, port), market_name, stock_id)
    except Exception:
        flask.flash('Fail to request data of {} from {}: {}'.format((market_name, stock_id), server_ip, port))
        all_datas = []
    finally:
        selected_message_id = '8117'
        selected_stock_id = stock_id
        return flask.render_template('stock_data_table.html', qtexs=all_datas,
                                     selected_market_name=market_name, selected_ip=server_ip,
                                     selected_port=port, selected_message_id=selected_message_id,
                                     selected_navbar_item='stock_data', selected_stock_id=selected_stock_id,
                                     server_infos=global_server_infos)


def show_cas(server_ip, port, market_name, stock_id):
    try:
        all_datas = mds_data_set.request_8118((server_ip, port), market_name, stock_id)
    except Exception:
        flask.flash('Fail to request data of {} from {}: {}'.format((market_name, stock_id), server_ip, port))
        all_datas = []
    finally:
        selected_message_id = '8118'
        selected_stock_id = stock_id
        return flask.render_template('stock_data_table.html', cass=all_datas,
                                     selected_market_name=market_name, selected_ip=server_ip,
                                     selected_port=port, selected_message_id=selected_message_id,
                                     selected_navbar_item='stock_data', selected_stock_id=selected_stock_id,
                                     server_infos=global_server_infos)


def show_vcm(server_ip, port, market_name, stock_id):
    try:
        all_datas = mds_data_set.request_8119((server_ip, port), market_name, stock_id)
    except Exception:
        flask.flash('Fail to request data of {} from {}: {}'.format((market_name, stock_id), server_ip, port))
        all_datas = []
    finally:
        selected_message_id = '8119'
        selected_stock_id = stock_id
        return flask.render_template('stock_data_table.html', vcms=all_datas,
                                     selected_market_name=market_name, selected_ip=server_ip,
                                     selected_port=port, selected_message_id=selected_message_id,
                                     selected_navbar_item='stock_data', selected_stock_id=selected_stock_id,
                                     server_infos=global_server_infos)


def show_list_fund_flow(server_ip, port, market_name):
    try:
        all_datas = mds_data_set.request_8124((server_ip, port), market_name)
    except Exception:
        flask.flash('Fail to request data of {} from {}: {}'.format(market_name, server_ip, port))
        all_datas = []
    finally:
        selected_message_id = '8124'
        return flask.render_template('stock_data_table.html', list_fund_flows=all_datas,
                                     selected_market_name=market_name, selected_ip=server_ip,
                                     selected_port=port, selected_message_id=selected_message_id,
                                     selected_navbar_item='stock_data', server_infos=global_server_infos)


def show_list_buyin_rank(server_ip, port, market_name):
    try:
        all_datas = mds_data_set.request_8125((server_ip, port), market_name)
    except Exception:
        flask.flash('Fail to request data of {} from {}: {}'.format(market_name, server_ip, port))
        all_datas = []
    finally:
        selected_message_id = '8125'

        return flask.render_template('stock_data_table.html', list_buyin_ranks=all_datas,
                                     selected_market_name=market_name, selected_ip=server_ip,
                                     selected_port=port, selected_message_id=selected_message_id,
                                     selected_navbar_item='stock_data', server_infos=global_server_infos)


def show_diff_eoddata(server_ip, port, market_name, eod_file_date):
    table_cell_format = 'Table Cell Format: EastMoney / Eoddata'
    try:
        all_datas = mds_data_set.compare_with_eoddata(server_ip, port, market_name, eod_file_date)
    except Exception as e:
        flask.flash(e)
        all_datas = []
    finally:
        diff_result_summary = process_data.summarize_differ_result(all_datas)
        split_result = process_data.split_differ_result(all_datas)
        selected_date = eod_file_date[0: 4] + '-' + eod_file_date[4: 6] + '-' + eod_file_date[6: 8]
        return flask.render_template('diff_eoddata_table.html', split_result=split_result,
                                     selected_market_name=market_name, selected_ip=server_ip,
                                     selected_port=port, table_cell_format=table_cell_format,
                                     selected_navbar_item='dropdown1', selected_date=selected_date,
                                     diff_result_summary=diff_result_summary, server_infos=global_server_infos)


def show_diff_global_quote(server_ip, port):
    try:
        all_datas = mds_data_set.compare_global_quote(server_ip, port)
    except Exception:
        flask.flash('Fail to request data from {}: {}'.format(server_ip, port))
        all_datas = []
    finally:
        market_name = 'QQZS'
        table_cell_format = 'EastMoney/Global Quote'
        return flask.render_template('diff_global_quote_table.html', all_global_quotes=all_datas,
                                     selected_market_name=market_name, selected_ip=server_ip, selected_port=port,
                                     table_cell_format=table_cell_format, selected_navbar_item='dropdown1',
                                     server_infos=global_server_infos)


def show_diff_sina_data(server_ip, port, market_name):
    try:
        all_datas = mds_data_set.compare_with_sina_data(server_ip, port)
    except Exception:
        flask.flash('Fail to request data from {}: {}'.format(server_ip, port))
        all_datas = []
    finally:
        table_cell_format = 'EastMoney/Sina Data'
        return flask.render_template('diff_sina_data_table.html', all_sina_datas=all_datas,
                                     selected_market_name=market_name, selected_ip=server_ip, selected_port=port,
                                     table_cell_format=table_cell_format, selected_navbar_item='dropdown1',
                                     server_infos=global_server_infos)


def show_diff_hkse_data(server_ip, port, market_name):
    try:
        all_datas = mds_data_set.compare_with_hkse_data(server_ip, port)
    except Exception:
        flask.flash('Fail to request data from {}: {}'.format(server_ip, port))
        all_datas = []
    finally:
        table_cell_format = 'EastMoney/HKSE Data'
        return flask.render_template('diff_hkse_data_table.html', all_hkse_datas=all_datas,
                                     selected_market_name=market_name, selected_ip=server_ip, selected_port=port,
                                     table_cell_format=table_cell_format, selected_navbar_item='dropdown1',
                                     server_infos=global_server_infos)


def show_all_market_time(all_address, client_unique_name):
    try:
        all_datas = mds_data_set.request_all_8102(all_address)
    except Exception as e:
        flask.flash('Caught an exception: {}. \nData has been cleared.'.format(e))
        all_datas = []
    finally:
        return flask.render_template('real_time_data.html', all_market_time=all_datas,
                                     selected_navbar_item='realtime_data', client_unique_name=client_unique_name)


def show_different_stock_data(address_pairs, message_id, market_name, stock_id=None):
    try:
        different_data_among_servers = mds_data_set.compare_stock_data(address_pairs, message_id, market_name, stock_id)
        all_different_data = mds_data_set.pile_up_stock_data_in_servers(different_data_among_servers)
        # Currently there is no need to flash since the address_pairs is always [].
        # if not all_different_data:
        #     flask.flash('Oops! No different data is found.')
    except ValueError as e:
        flask.flash(e)
        all_different_data = []
    finally:
        stock_id = stock_id or ''
        return flask.render_template('diff_stock_data.html', all_different_data=all_different_data,
                                     selected_message_id=str(message_id), selected_market_name=market_name,
                                     selected_stock_id=stock_id, selected_navbar_item='diff_stock_data',
                                     all_server_info=global_server_infos)
