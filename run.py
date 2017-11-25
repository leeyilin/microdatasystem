#!/home/lee/Documents/multimarket/trunk/src/micromds/flask/bin/python
import os
from app import micromds, socketio


os.chdir(os.path.split(os.path.abspath(__file__))[0])
socketio.run(micromds, port=7488, debug=False, host='0.0.0.0')
