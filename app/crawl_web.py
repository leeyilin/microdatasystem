from urllib import request
from urllib import error
import datetime
import bs4
import logging
import traceback
from app import basic_structs
from app import process_data


def formalize_time(my_time):
    time_fragments = my_time.split('/')
    try:
        formalized_time = '20' + time_fragments[2] + time_fragments[0] + time_fragments[1] + ' ' + \
            datetime.datetime.now().strftime('%H%M%S')
    except IndexError as e:
        raise IndexError('The format of the given time value is incorrect: ', my_time)

    return formalized_time


def crawl_eod(market, stock_code):
    try:
        html = request.urlopen('http://www.eoddata.com/stockquote/%s/%s.htm' % (market, stock_code))
        bs_object = bs4.BeautifulSoup(html.read(), 'lxml')
    except (error.HTTPError, error.URLError) as e:
        logging.error('Caught connection errors(market: %s, stock_code: %s)' %
                      (market, stock_code))
        # logging.error(traceback.format_exc())
    else:
        try:
            eod_data = {}
            eod_data['code'] = stock_code
            wk_row = bs_object.find('div', {'id': 'ctl00_cph1_divFundamentals'}). \
                table.find_all('tr')[11]
            wk_row_content = wk_row.get_text()
            start_position = wk_row_content.index(':')
            if start_position != -1:
                price_range = wk_row_content[start_position + 1:].replace(' ', '').split('-')
                eod_data['pricedt'] = price_range[0]
                eod_data['pricezt'] = price_range[1]

            field_values = bs_object.find('table', {'class': 'quotes'}).find_all('tr')[1]
            fields = ['date_time', 'open', 'high', 'low', 'close', 'volume', 'open_interest']
            # print('====== %s: %s ======' % (market, stock_code))
            for field_name, field_value in zip(fields, field_values):
                eod_data[field_name] = field_value.get_text().replace(',', '')

                if field_name == 'date_time':
                    eod_data[field_name] = formalize_time(eod_data[field_name])

            return eod_data

        except (AttributeError, IndexError, TimeoutError) as errors:
            logging.error('Caught expected error:', errors,
                          'market: %s, stock_code: %s' % (market, stock_code))
            return {}
        except Exception as unexpected_errors:
            logging.error('Caught unexpected errors(market: %s, stock_code: %s), to be fixed.....' %
                          (market, stock_code))
            logging.error(traceback.format_exc())
            return {}


def write_eoddata_to_file(eoddatas, filename):
    # Here it is not advisable to check whether the target file already exists.
    if not eoddatas:
        return

    file_line_format = '{date_time},{code},{close},{open},{high},{low},{volume},{pricezt},{pricedt},{open_interest}\n'
    with open(filename, 'w+') as f:
        f.write(file_line_format.replace('{', '').replace('}', ''))
        for eoddata in eoddatas:
            f.write(file_line_format.format(**eoddata))


def crawl_tokyo_stock_exchange():
    try:
        target_url = 'http://quote.jpx.co.jp/jpx/template/quote.cgi?F=tmp/e_real_index2&QCODE=101'
        html = request.urlopen(target_url)
        bs_object = bs4.BeautifulSoup(html.read(), 'lxml')
    except (error.HTTPError, error.URLError) as e:
        logging.error('Caught connection errors when crawling data from tokyo stock exchange: %s)' % target_url)
        # logging.error(traceback.format_exc())
    else:
        stock_data = {}
        target_table = bs_object.find('div', {'class': 'component-normal-table'}).table
        tree_datas = target_table.find_all('tr')[1].find_all('td')
        fields = ['date_time', 'open', 'high', 'low', 'recent', 'change']
        for field, td in zip(fields, tree_datas):
            tree_data_value = td.get_text().replace('\r', '').replace('\t', '')
            target_index = tree_data_value.find('(')
            field_value = tree_data_value[: target_index]
            stock_data[field] = field_value

        stock_data.pop('recent', None)
        stock_data.pop('change', None)
        stock_data['stock_code'] = 'N225'

        return stock_data


def crawl_singapore_stock_exchange():
    import requests
    target_url = 'http://www.sgx.com/JsonRead/chartdata?type=intra&ric=.STI'
    headers = {
        'Host': 'www.sgx.com',
        'Pragma': 'no-cache',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }
    responce = requests.session().get(target_url, headers=headers)
    batch_datas = str(responce.text)
    # The data in the last line is the newest stock data.
    target_index = batch_datas.rfind('\n', 0, -1)
    stock_data = {}
    if target_index != -1:
        field_values = batch_datas[target_index:].split(',')
        stock_data['high'] = field_values[2]
        stock_data['low'] = field_values[3]
        stock_data['price'] = field_values[4]
        stock_data['stock_code'] = 'STI'

        return stock_data
    else:
        return {}


def crawl_london_stock_exchange():
    try:
        target_url = 'http://www.londonstockexchange.com/exchange/prices-and-markets/stocks/' \
                     'indices/summary/summary-indices.html?index=UKX'
        html = request.urlopen(target_url)
        bs_object = bs4.BeautifulSoup(html.read(), 'lxml')
    except (error.HTTPError, error.URLError) as e:
        logging.error('Caught connection errors when crawling data from london stock exchange: %s)' % target_url)
        # logging.error(traceback.format_exc())
    else:
        stock_data = {}
        target_table = bs_object.find('table', {'summary': 'Price data'})
        tree_datas = target_table.tbody.find_all('tr')[0].find_all('td')
        fields = ['price', '+/-', '%+/-', 'high', 'low', 'close']
        for field_name, td in zip(fields, tree_datas):
            stock_data[field_name] = 0 if td.get_text() == '-' else td.get_text()

        stock_data.pop('+/-', None)
        stock_data.pop('%+/-', None)
        stock_data['stock_code'] = 'FTSE'

        return stock_data


def crawl_nasdaq_stock_exchange():
    try:
        target_url = 'http://www.nasdaq.com/zh'
        html = request.urlopen(target_url)
        bs_object = bs4.BeautifulSoup(html.read(), 'lxml')
    except (error.HTTPError, error.URLError) as e:
        logging.error('Caught connection errors when crawling data from nasdaq stock exchange: %s)' % target_url)
        # logging.error(traceback.format_exc())
    else:
        target_table = bs_object.find('table', {'id': 'indexTable'})
        js_text = str(target_table.script.get_text())
        begin_tag = '//<![CDATA['
        begin_index = js_text.find(begin_tag)
        if begin_index != -1:
            end_tag = '//]]>'
            end_index = js_text.find(end_tag)
            target_content = js_text[begin_index + len(begin_tag): end_index].strip('\r\n').split(';')
            stock_datas = {}
            for line_content in target_content:
                try:
                    field_names = ['stock_code', 'newest_price', '_', '__', 'volume', 'highest_price', 'lowest_price']
                    field_values = eval(line_content[line_content.index('(') + 1: line_content.index(')')])
                    stock_data = {}
                    for field_name, field_value in zip(field_names, field_values):
                        if 'price' in field_name:
                            field_value = int(float(field_value) * 100)
                        stock_data[field_name] = field_value

                    stock_data.pop('_', None)
                    stock_data.pop('__', None)
                    stock_data.pop('volume', None)
                    target_stock_codes = {
                        'DJIA': 'DJIA',
                        'S&P 500': 'SPX',
                        'NASDAQ': 'NDX'
                    }
                    if stock_data['stock_code'] in target_stock_codes:
                        stock_code = target_stock_codes[stock_data['stock_code']]
                        stock_data.pop('stock_code', None)
                        stock_datas[stock_code] = stock_data
                except ValueError as e:
                    pass

            return stock_datas


def crawl_sina_stock_data(stock_codes):
    hk_stock_codes = ['hk' + stock_code for stock_code in sorted(stock_codes)]
    step = 150
    stock_datas = []
    for i in range(0, len(hk_stock_codes), step):
        try:
            target_url = 'http://hq.sinajs.cn/list=' + ','.join(hk_stock_codes[i: i + step])
            html = request.urlopen(target_url)
            bs_object = bs4.BeautifulSoup(html.read().decode('gbk'), 'lxml')
        except (error.HTTPError, error.URLError) as e:
            logging.error('Caught connection errors when crawling data from Hong Kong stock exchange: %s)' % target_url)
            # logging.error(traceback.format_exc())
        else:
            js_text = bs_object.body.p.get_text().split('\n')[: -1]
            for line in js_text:
                try:
                    split_js = line.rstrip('\r\n').split(',')
                    stock_code = split_js[0].split('=')[0].split('_')[-1].replace('hk', '')
                    stock_data = {
                        'stock_code': stock_code,
                        'stock_name': split_js[1],
                        'open_price': int(float(split_js[2]) * 1000),
                        'highest_price': int(float(split_js[4]) * 1000),
                        'lowest_price': int(float(split_js[5]) * 1000),
                        'close_price': int(float(split_js[3]) * 1000),
                        'newest_price': int(float(split_js[6]) * 1000),
                        'volume': split_js[12],
                        'amount': split_js[11],
                        'trade_date': split_js[17].replace('/', '')
                    }
                    # Filter out weird datas.
                    if float(stock_data['highest_price']) > 1:
                        sina_raw_multi_qt = basic_structs.SinaRawMultiQt(**stock_data)
                        stock_datas.append(sina_raw_multi_qt)

                except IndexError:
                    logging.getLogger().debug('Caught unexpected format of js. '
                                              'Possible the data of stock code: HK%s is empty: %s' %
                                              (stock_code, split_js))

    return stock_datas


def crawl_hongkong_stock_exchange(stock_codes):
    stock_datas = []
    for stock_code in stock_codes:
        try:
            target_url = 'http://www.hkex.com.hk/eng/invest/company/quote_page_e.asp?' \
                         'WidCoID=%s&WidCoAbbName=&Month=1&langcode=e' % stock_code
            html = request.urlopen(target_url)
            bs_object = bs4.BeautifulSoup(html.read(), 'lxml')
        except (error.HTTPError, error.URLError) as e:
            logging.error('Caught connection errors when crawling data from nasdaq stock exchange: %s)' % target_url)
            # logging.error(traceback.format_exc())
        else:
            tree_rows = bs_object.table.table.find_all('tr')[9].table.find_all('tr')
            date_time = tree_rows[0].td.font.get_text().split()[2]
            newest_price = tree_rows[8].td.font.get_text()
            target_datas = tree_rows[11].find_all('td')
            high_price = target_datas[0].get_text()
            low_price = target_datas[1].get_text()
            volume = int(target_datas[3].get_text().replace(',', '')) * 1000
            amount = int(target_datas[4].get_text().replace(',', '')) * 1000
            stock_data = {
                'stock_code': stock_code,
                'trade_date': process_data.convert_date_to_numeric(date_time),
                'newest_price': 0 if newest_price == 'N/A' else int(float(newest_price) * 1000),
                'highest_price': 0 if high_price == '' else int(float(high_price) * 1000),
                'lowest_price': 0 if low_price == '' else int(float(low_price) * 1000),
                'volume': volume,
                'amount': amount
            }
            hkse_raw_multi_qt = basic_structs.HKSERawMultiQt(**stock_data)
            stock_datas.append(hkse_raw_multi_qt)

    return stock_datas


if __name__ == '__main__':
    crawl_hongkong_stock_exchange(['00700'])