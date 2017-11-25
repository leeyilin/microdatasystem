import os
import sqlalchemy
from sqlalchemy.ext import declarative
from app.process_data import load_server_infos, load_market_infos, load_user_infos


os.chdir(os.path.split(os.path.abspath(__file__))[0])

global_market_infos = {}
reverse_global_market_infos = {}
global_server_infos = []
global_user_infos = []
if not global_market_infos:
    load_market_infos(global_market_infos, './config/config.xml')
    reverse_global_market_infos = {v: k for k, v in global_market_infos.items()}
    load_server_infos(global_server_infos, './config/config.xml')
    load_user_infos(global_user_infos, './config/config.xml')

engine = sqlalchemy.create_engine("mysql://root:lee@localhost/stock_data_test2", echo=False)
Base = declarative.declarative_base()


def create_dababase():
    Base.metadata.create_all(engine)
