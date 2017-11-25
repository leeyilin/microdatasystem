#!/home/lee/Documents/multimarket/trunk/src/micromds/flask/bin/python
import os
import logging
from datetime import datetime
from app import logging_config, eoddata_login, mds_data_set, eastmoney_email, process_data


os.chdir(os.path.split(os.path.abspath(__file__))[0])
today = datetime.now().strftime('%m-%d-%Y')
log_file_name = './app/log/cronjob_{}.log'.format(today)
logging_config.config_log_system(logging.DEBUG, log_file_name)


def download_eoddata():
    target_markets = [{blablabla}]
    eod_login = eoddata_login.EoddataLogin(target_markets=target_markets)
    eod_login.download_batch_data()


def findout_weird_qt_quote(target_markets):
    server_ip = {theIP}
    port = 1861
    weird_qt_quote = []
    for market_name in target_markets:
        new_list = mds_data_set.request_8110((server_ip, port), market_name)
        for item in new_list:
            if 'Warning' in item['waipan']:
                weird_qt_quote.append(item)

    content = 'server ip: {} \nport: {}\n target markets: {}\n'.format(server_ip, port, target_markets)
    msg = ''
    for weird_quote in weird_qt_quote:
        msg += '{}\n'.format(weird_quote)

    if msg:
        subject = 'Find out some weird qt quotes on: {}'.format(today)
        content += '\nWeird qt quotes:\n'
        content += msg
    else:
        subject = 'No weird qt quote found on: {}'.format(today)

    receivers = [{myEmail}]
    print('{}\n{}\n{}\n'.format(subject, content, receivers))
    eastmoney_email.send_email(subject, content, receivers)


def check_global_quote():
    server_ip = {theIP}
    port = 1861
    result = mds_data_set.compare_global_quote(server_ip, port)

    subject = 'Compare global quote on: {}'.format(today)
    content = 'server ip: {} \nport: {}\n\n'.format(server_ip, port)
    msg = ''
    LINE_SEPORATOR = '\n'
    for item in result:
        msg += (str(item) + LINE_SEPORATOR)

    table_cell_format = 'EastMoney/Global Quote\n\n'
    content += table_cell_format
    content += msg
    receivers = [{myEmail}]

    print('{}\n{}\n{}\n'.format(subject, content, receivers))

    eastmoney_email.send_email(subject, content, receivers)


def check_with_eoddata():
    server_ip = {theIP}
    port = 1861
    eod_file_date = datetime.today().strftime('%Y%m%d')
    market_names = [{blablabla}]
    content = ''
    content += '{: <20}{: <20}\n{: <20}{: <20}\n{: <20}{: <20}\n\n'.format(
        'Server IP:', server_ip, 'Port:', port, 'Eoddata file date:', eod_file_date
    )
    for market_name in market_names:
        try:
            msg = ''
            all_datas = mds_data_set.compare_with_eoddata(server_ip, port, market_name, eod_file_date)
        except Exception as e:
            msg += 'Confronted with an unexpected error: {}'.format(str(e))
            all_datas = []
        finally:
            diff_result_summary = process_data.summarize_differ_result(all_datas)
            compared_fields = ['trade_sequence', 'open_price', 'highest_price',
                               'lowest_price', 'newest_price', 'close_price', 'volume']
            subsummary_titles = ['eastmoney_exclusively', 'eod_exclusively', 'common_stock', 'sum']
            msg += '-----Market: {}-----\n'.format(market_name)
            LINE_SEPERATOR = '-' * 120
            str_subtitles = '{: <20}'.format('Field Names')
            for item in subsummary_titles:
                str_subtitles += '{: >25}'.format(item)
            msg += '{}\n'.format(str_subtitles)
            msg += '{}\n'.format(LINE_SEPERATOR)
            for field in compared_fields:
                msg += '{: <20}'.format(field)
                for title in subsummary_titles:
                    msg += '{: >25}'.format(diff_result_summary[title][field])
                msg += '\n'

            content += '{}\n\n'.format(msg)

    subject = '<Diff Eoddata> Summary on: {}'.format(today)
    receivers = [{myEmail}]
    print('{}\n{}\n{}\n'.format(subject, content, receivers))
    eastmoney_email.send_email(subject, content, receivers)


if __name__ == '__main__':
    current_hour = datetime.now().strftime('%H')
    if datetime.today().isoweekday() != 1 and current_hour == '09':
        download_eoddata()
        check_with_eoddata()
        target_markets = [{blablabla}]
        findout_weird_qt_quote(target_markets)

    if current_hour == '08':
        check_global_quote()
