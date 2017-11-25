import os
import flask
from flask_login import LoginManager
import flask_socketio
from config import ADMINS, MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD
from . import my_namespace


micromds = flask.Flask(__name__)
micromds.config.from_object('config')
# One unique id for one remote client address.
micromds.all_client_ids = {'127.0.0.1': 1}
login_manager= LoginManager()
login_manager.init_app(micromds)
# This view function should be called when login is required.
login_manager.login_view = 'login'
'''
Set this variable to "threading", "eventlet" or "gevent" to test the different 
async modes, or leave it set to None for the application to choose the best option
based on installed packages.
'''
async_mode = None
socketio = flask_socketio.SocketIO(micromds, async_mode=async_mode)
my_namespace_cls = my_namespace.my_namespace(socketio)
socketio.on_namespace(my_namespace_cls('/test'))

if not micromds.debug:
    import logging
    from logging.handlers import SMTPHandler, RotatingFileHandler
    credentials = None
    if MAIL_USERNAME or MAIL_PASSWORD:
        credentials = (MAIL_USERNAME, MAIL_PASSWORD)
    mail_handler = SMTPHandler((MAIL_SERVER, MAIL_PORT), 'no-reply@' + MAIL_SERVER, ADMINS,
                               'micromds failure', credentials)
    mail_handler.setLevel(logging.ERROR)
    micromds.logger.addHandler(mail_handler)

    os.chdir(os.path.split(os.path.abspath(__file__))[0])
    file_handler = RotatingFileHandler('log/micromds.log', 'a', 1 * 1024 * 1024, 10)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    micromds.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    micromds.logger.addHandler(file_handler)
    micromds.logger.info('micromds startup')
from app import views
