import os
from functools import wraps
from datetime import datetime
import flask
from flask_login import login_user, logout_user, current_user
from app import micromds, login_manager, mds_data_set, show
from app.process_data import convert_date_to_numeric, get_client_unique_name
from . import global_info


os.chdir(os.path.split(os.path.abspath(__file__))[0])
# today = datetime.datetime.now().strftime('%m%d%Y')
# log_file_name = './log/%s_micromds.log' % today
# logging_config.config_log_system(logging.DEBUG, log_file_name)

# I am a little confused here because I need to re-implement login_required instead of
# using the built-in one in order to to use it as a decorator.
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if flask.g.user is None or flask.session.get('registered_user', None) is None:
            return flask.redirect(flask.url_for('login', next=flask.request.url))
        return f(*args, **kwargs)
    return decorated_function


@micromds.before_request
def before_request():
    flask.g.user = current_user


@login_manager.user_loader
def load_user(id):
    return mds_data_set.query_user_info(id=id)


@micromds.route('/login/',methods=['GET','POST'])
def login():
    if flask.request.method == 'GET':
        return flask.render_template('login.html')
    else:
        email = flask.request.form['login_email']
        password = flask.request.form['login_password']
        registered_user = mds_data_set.query_user_info(email=email, password=password)
        if registered_user is None:
            flask.flash('Oops! It seems you are not registered...')
            return flask.redirect(flask.url_for('login'))
        else:
            flask.session['registered_user'] = registered_user.to_json()
            login_user(registered_user)
            return flask.redirect(flask.request.args.get('next') or flask.url_for('index'))


@micromds.route('/logout/', methods=['GET', 'POST'])
def logout():
    flask.session.pop('registered_user', None)
    logout_user()
    return flask.redirect(flask.url_for('index'))


@micromds.route('/', methods=['GET', 'POST'])
@micromds.route('/index/', methods=['GET', 'POST'])
@login_required
def index():
    return show.show_stock_dict('114.80.234.100', 1861, 'NASDAQ')


@micromds.route('/basic_stock_data/', methods=['GET', 'POST'])
@login_required
def basic_stock_data():
    if flask.request.method == 'GET':
        return show.show_stock_dict('114.80.234.100', 1861, 'NASDAQ')
    else:
        server_ip = flask.request.form.get('ip_list', '114.80.234.100')
        port = int(flask.request.form.get('port', 1861))
        message_id = flask.request.form.get('message_id', '8100')
        market_name = flask.request.form.get('market_name', 'HK').upper()
        stock_id = flask.request.form.get('stock_id', '00700').upper()
        if message_id == '8100':
            return show.show_stock_dict(server_ip, port, market_name)
        elif message_id == '8101':
            return show.show_basic_qt(server_ip, port, market_name, stock_id)
        elif message_id == '8103':
            return show.show_rtmin(server_ip, port, market_name, stock_id)
        elif message_id == '8104':
            return show.show_kline(server_ip, port, market_name, stock_id)
        elif message_id == '8105':
            return show.show_mx(server_ip, port, market_name, stock_id)
        elif message_id == '8106':
            return show.show_blockqt(server_ip, port, market_name)
        elif message_id == '81061':
            return show.show_block_overview(server_ip, port, market_name)
        elif message_id == '8110':
            return show.show_raw_multi_qt(server_ip, port, market_name)
        elif message_id == '8112':
            return show.show_base_bq(server_ip, port, market_name, stock_id)
        elif message_id == '8113':
            # We should use broker no here.
            return show.show_bq_trace(server_ip, port, market_name, int(stock_id))
        elif message_id == '8115':
            return show.show_mx2(server_ip, port, market_name, stock_id)
        elif message_id == '8117':
            return show.show_qtex(server_ip, port, market_name, stock_id)
        elif message_id == '8118':
            return show.show_cas(server_ip, port, market_name, stock_id)
        elif message_id == '8119':
            return show.show_vcm(server_ip, port, market_name, stock_id)
        elif message_id == '8124':
            return show.show_list_fund_flow(server_ip, port, market_name)
        elif message_id == '8125':
            return show.show_list_buyin_rank(server_ip, port, market_name)


@micromds.route('/diff_eoddata/', methods=['GET', 'POST'])
@login_required
def diff_eoddata():
    if flask.request.method == 'GET':
        today = datetime.today().strftime('%Y%m%d')
        return show.show_diff_eoddata('114.80.234.100', 1861, 'NASDAQ', today)
    else:
        market_name = flask.request.form['market_name']
        server_ip = flask.request.form['ip_list']
        port = int(flask.request.form['port'])
        eod_file_date = convert_date_to_numeric(flask.request.form['query_date'])
        return show.show_diff_eoddata(server_ip, port, market_name, eod_file_date)


@micromds.route('/diff_sina_data/', methods=['GET', 'POST'])
@login_required
def diff_sina_data():
    if flask.request.method == 'GET':
        return show.show_diff_sina_data('114.80.234.100', 1861, 'HK')
    else:
        server_ip = flask.request.form['ip_list']
        port = int(flask.request.form['port'])
        market_name = flask.request.form['market_name']
        return show.show_diff_sina_data(server_ip, port, market_name)


@micromds.route('/diff_hkse_data/', methods=['GET', 'POST'])
@login_required
def diff_hkse_data():
    if flask.request.method == 'GET':
        return show.show_diff_hkse_data('114.80.234.100', 1861, 'HK')
    else:
        server_ip = flask.request.form['ip_list']
        market_name = flask.request.form['market_name']
        date = convert_date_to_numeric(flask.request.form['query_date'])
        return show.show_diff_hkse_data(date, market_name, server_ip)


@micromds.route('/diff_global_quote/', methods=['GET', 'POST'])
@login_required
def diff_global_quote():
    if flask.request.method == 'GET':
        return show.show_diff_global_quote('114.80.234.100', 1861)
    else:
        server_ip = flask.request.form['ip_list']
        port = int(flask.request.form['port'])
        return show.show_diff_global_quote(server_ip, port)


@micromds.errorhandler(404)
def not_found_error(error):
    return flask.render_template('404.html'), 404


@micromds.errorhandler(500)
def internal_error(error):
    return flask.render_template('500.html'), 500


@micromds.route('/mds_monitor/', methods=['GET', 'POST'])
@login_required
def mds_monitor():
    client_unique_name = get_client_unique_name(micromds.all_client_ids, flask.request.remote_addr)
    all_addr = [(item['server_ip'], item['port']) for item in global_info.global_server_infos]
    return show.show_all_market_time(all_addr, client_unique_name)


def extract_all_addresses():
    address_pairs = []
    for name, value in flask.request.form.items():
        if 'server_ip' in name and value != '':
            braket_index = name.find('[')
            if braket_index != -1:
                no = name[braket_index + 1: -1]
                port_field_name = 'port[' + no + ']'
                server_ip = value
                port = int(flask.request.form[port_field_name])
                address_pairs.append((server_ip, port))
    return address_pairs


@micromds.route('/diff_stock_data/', methods=['GET', 'POST'])
@login_required
def diff_stock_data():
    if flask.request.method == 'GET':
        return show.show_different_stock_data([], 8100, 'HK')
    else:
        message_id = int(flask.request.form.get('message_id', 8100))
        market_name = flask.request.form.get('market_name', 'HK').upper()
        stock_id = flask.request.form.get('stock_id', None).upper() or None
        address_pairs = extract_all_addresses()
        exception_description = None
        try:
            different_data_among_servers = mds_data_set.compare_stock_data(address_pairs, message_id, market_name,
                                                                           stock_id)
            all_different_data = mds_data_set.pile_up_stock_data_in_servers(different_data_among_servers)
        except Exception as e:
            exception_description = str(e)
            all_different_data = []
        finally:
            message = {
                'diff_result': len(all_different_data),
                'different_data': all_different_data,
                'myexception': exception_description if exception_description else 'No exception',
            }
            return flask.jsonify(message)


