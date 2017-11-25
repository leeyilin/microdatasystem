from xml.etree import ElementTree
import collections


def are_floats_equal(eastmoney_val, source_val, precision=0.01):
    try:
        return (abs(float(eastmoney_val) - float(source_val))) < precision
    except ValueError:
        # If one of the given value is empty, exception ValueError will be raised.
        return False


def convert_date_to_numeric(date):
    result = ''
    if '/' in date:
        date_split = date.split('/')
        result = ''.join(date_split[::-1])
    elif '-' in date:
        result = date.replace('-', '')

    return result


def load_market_infos(market_infos, filename):
    tree = ElementTree.parse(filename)
    market_list = tree.getroot()[0]
    try:
        for market_info in market_list:
            market_name = market_info.attrib['code']
            market_id = int(market_info.attrib['id'])
            market_infos[market_name] = market_id
    except KeyError as e:
        print('Exception in load_market_infos(): {}'.format(e))


def load_server_infos(server_infos, filename):
    tree = ElementTree.parse(filename)
    server_list = tree.getroot()[1]
    try:
        for tag_info in server_list:
            server_infos.append({
                'server_ip': tag_info.attrib['ip'],
                'port': int(tag_info.attrib['port']),
                'server_name': tag_info.attrib['name'],
                'id': tag_info.attrib['id']
            })
    except KeyError as e:
        print('Exception in load_server_infos(): {}'.format(e))


def load_user_infos(user_infos, filename):
    tree = ElementTree.parse(filename)
    user_list = tree.getroot()[2]
    try:
        for tag_info in user_list:
            nickname = tag_info.attrib['nickname']
            email = tag_info.attrib['email']
            employee_id = tag_info.attrib['employee_id']
            password = tag_info.attrib['password']
            user = {
                'nickname': nickname,
                'email': email,
                'employee_id': int(employee_id),
                'password': password,
            }
            user_infos.append(user)
    except KeyError as e:
        print('Exception in load_user_infos(): {}'.format(e))


# For eod comparison.
# Notice that the returned value may be empty and there may be some fields absent in the sub-dict.
def summarize_differ_result(all_data):
    differ_result = collections.defaultdict(lambda: collections.defaultdict(int))
    for tree_row in all_data:
        for name, value in tree_row.items():
            if name != 'stock_code' and value != '-':
                if 'null /' in value:
                    differ_result['eod_exclusively'][name] += 1
                elif '/ null' in value:
                    differ_result['eastmoney_exclusively'][name] += 1
                else:
                    differ_result['common_stock'][name] += 1
                differ_result['sum'][name] += 1

    return differ_result


# For eod comparison.
def split_differ_result(all_data):
    split_result = collections.defaultdict(list)
    for tree_row in all_data:
        if 'null /' in str(tree_row.values()):
            split_result['eod_exclusively'].append(tree_row)
        elif '/ null' in str(tree_row.values()):
            split_result['eastmoney_exclusively'].append(tree_row)
        else:
            split_result['common_stock'].append(tree_row)

    return split_result


def find_first_target_info(all_info, target_info):
    for info in all_info:
        if target_info in info.values():
            return info
    return None


def get_client_unique_name(all_client_ids, remote_addr):
    if remote_addr not in all_client_ids:
        all_client_ids[remote_addr] = max(all_client_ids.values()) + 1
    return 'client' + str(all_client_ids[remote_addr])

