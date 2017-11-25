# encoding: utf-8

import os
import requests
import bs4
import datetime
import logging
import codecs
try:
    import cookielib
except:
    import http.cookiejar as cookielib
import tqdm
from app import logging_config


class EoddataLogin(object):
    today = datetime.datetime.now().strftime("%Y%m%d")
    eoddata_file = './datas/eoddata/{market}-%s.csv' % today

    def __init__(self, target_markets):
        # Notice that it is extremely important to change the current working directory
        # in case of flying files because we download some files in relative path here.
        os.chdir(os.path.split(os.path.abspath(__file__))[0])
        self.headers = {
            'Referer': 'http://www.eoddata.com/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/58.0.3029.110 Safari/537.36',
            'Host': 'www.eoddata.com',
            'Origin': 'http://www.eoddata.com',
            'Upgrade-Insecure-Requests': '1'
        }
        self.target_markets = target_markets
        self.login_url = 'http://www.eoddata.com/'
        self.download_url = 'http://www.eoddata.com/download.aspx'

        self.session = requests.session()
        self.session.cookies = cookielib.LWPCookieJar(filename='eoddata_cookie')

    def load_cookie(self):
        try:
            self.session.cookies.load(ignore_discard=True)
        except Exception as e:
            print('Fail to cookie because of an error:\t', e)

    def get_param(self):
        response = self.session.get(self.login_url, headers=self.headers)
        bs_obj = bs4.BeautifulSoup(response.text, 'lxml')
        self.session.cookies.save()

        param = {}
        param['ctl00$cph1$lg1$txtEmail'] = 'leeyl@nuaa.edu.cn'
        param['ctl00$cph1$lg1$txtPassword'] = 'EastMoney161142'
        param['ctl00$cph1$lg1$btnLogin'] = 'Login'
        try:
            param['__VIEWSTATE'] = bs_obj.find('input',
                                               {'name': '__VIEWSTATE',
                                                'id': '__VIEWSTATE'}).attrs['value']

            param['__VIEWSTATEGENERATOR'] = bs_obj.find('input',
                                                        {'name': '__VIEWSTATEGENERATOR',
                                                         'id': '__VIEWSTATEGENERATOR'}).attrs['value']

            param['__PREVIOUSPAGE'] = bs_obj.find('input',
                                                  {'name': '__PREVIOUSPAGE',
                                                   'id': '__PREVIOUSPAGE'}).attrs['value']

            param['__EVENTVALIDATION'] = bs_obj.find('input',
                                                     {'name': '__EVENTVALIDATION',
                                                      'id': '__EVENTVALIDATION'}).attrs['value']

        except AttributeError as e:
            logging.getLogger().debug('Caught an error:\t', e)

        return param

    def get_magic_id(self, bs_obj):
        all_js = bs_obj.find_all('script', {'type': 'text/javascript',
                                            'language': 'javascript'})

        for ele in all_js:
            target_js = ele.get_text()
            pre_magic_id = 'url += \"&o=d&k='
            target_index = target_js.find(pre_magic_id)
            if target_index != -1:
                magic_id = target_js[target_index + len(pre_magic_id): target_index + len(pre_magic_id) + 10]
                logging.getLogger().info('Get a magic_id: %s' % magic_id)
                # Just find the first magic id.
                return magic_id

        logging.getLogger().debug('Fail to get magic_id...')

    @staticmethod
    def load_raw_multi_qt_quote(date, market_name):
        filename = './datas/eoddata/{}-{}.csv'.format(market_name, date)
        if not os.path.exists(filename):
            logging.getLogger().debug('File: %s does not exists.' % filename)
            return

        qt_quote = {}
        with codecs.open(filename, encoding='UTF-8') as infile:
            column_headers = infile.readline()
            for line in infile:
                field_values = line.strip('\r\n').split(',')
                value_dict = {}
                # The field names must be the same with that of the new list.
                field_names = ['stock_code', 'trade_sequence', 'open_price',
                               'highest_price', 'lowest_price', 'newest_price', 'volume']
                for field_name, field_value in zip(field_names, field_values):
                    # convert the value of price to integer
                    value_dict[field_name] = int(float(field_value) * 100) if 'price' in field_name else field_value
                stock_code = value_dict['stock_code']
                value_dict.pop('stock_code')
                qt_quote[stock_code] = value_dict
        yesterday_qt_quote = EoddataLogin.load_yesterday_qt_quote(date, market_name)
        for stock_code in qt_quote.keys():
            # Note that some stock codes today may lose some fields like the 'close_price' in this way.
            if stock_code in yesterday_qt_quote:
                qt_quote[stock_code].update(yesterday_qt_quote[stock_code])
        return qt_quote

    # date format: 'YYYYmmdd'
    @staticmethod
    def load_yesterday_qt_quote(date, market_name):
        # In case of some unexpected holidays.
        for i in range(10):
            yesterday = (datetime.datetime.strptime(date, '%Y%m%d') - datetime.timedelta(days=i+1)).strftime('%Y%m%d')
            filename = './datas/eoddata/{}-{}.csv'.format(market_name, yesterday)
            if os.path.exists(filename):
                break
        if os.path.exists(filename):
            qt_quote = {}
            with codecs.open(filename, encoding='UTF-8') as infile:
                column_headers = infile.readline()
                for line in infile:
                    field_values = line.strip('\r\n').split(',')
                    value_dict = {}
                    # The field names must be the same with that of the new list.
                    field_names = ['stock_code', '_', '_', '_', '_', 'close_price', '_']
                    for field_name, field_value in zip(field_names, field_values):
                        # convert the value of price to integer
                        if field_name in ['stock_code', 'close_price']:
                            value_dict[field_name] = int(float(field_value) * 100) \
                                if 'price' in field_name else field_value
                    stock_code = value_dict.pop('stock_code')
                    qt_quote[stock_code] = value_dict
                return qt_quote
        else:
            raise ValueError('Could not find yesterday file.')

    def parse_batch_data_url(self, bs_obj):
        batch_data_url = 'http://www.eoddata.com/data/filedownload.aspx?e=%s&sd=%s&ea=1&ed=%s&d=9&p=0&o=d&k=%s'
        # Notice that the schedule time of this program is 10:30 AM, UTC+8
        # while New York is in UTC-4, namely 12 hours in advance.
        yesterday = (datetime.datetime.today() - datetime.timedelta(days=1)).strftime('%Y%m%d')
        magic_id = self.get_magic_id(bs_obj=bs_obj)
        for market in self.target_markets:
            download_file = self.eoddata_file.format(market=market)
            if os.path.exists(download_file):
                continue

            target_url = batch_data_url % (market, yesterday, yesterday, magic_id)
            logging.getLogger().info('Download from...\n%s' % target_url)
            responce = self.session.get(target_url, headers=self.headers)

            if len(responce.content):
                with open(download_file, "wb") as handle:
                    fields = 'code,date_time,open,high,low,price,volume\n'
                    handle.write(fields.encode())
                    for data in tqdm.tqdm(responce.iter_content()):
                        handle.write(data)
            else:
                logging.getLogger().debug('The url of %s returns nothing..' % market)

    def login(self):
        param = self.get_param()
        response = self.session.post(self.login_url, data=param, headers=self.headers)
        self.session.cookies.save()

        bs_obj = bs4.BeautifulSoup(response.text, 'lxml')
        res = bs_obj.find('span', {'id': 'ctl00_cph1_lg1_lblName'})
        if res:
            logging.getLogger().info('Login with Account %s successfully!' % res.get_text())
        else:
            logging.getLogger().debug('OMG! Fail to login...')

    def download_batch_data(self):
        self.login()
        responce = self.session.get(self.download_url, headers=self.headers)
        bs_obj = bs4.BeautifulSoup(responce.text, 'lxml')
        self.parse_batch_data_url(bs_obj=bs_obj)


if __name__ == "__main__":
    os.chdir(os.path.split(os.path.abspath(__file__))[0])
    today = datetime.datetime.now().strftime('%m%d%Y')
    log_file_name = './log/%s_craw_eod.log' % today
    logging_config.config_log_system(logging.DEBUG, log_file_name)

    target_markets = ['NASDAQ', 'AMEX', 'NYSE']
    # target_markets = ['NASDAQ']
    eoddata_login = EoddataLogin(target_markets=target_markets)
    eoddata_login.download_batch_data()
    # t = eoddata_login.load_raw_multi_qt_quote('20170815', 'NASDAQ')
    # for item in t.items():
    #     print(item)

