import logging
import socket
import threading

from devolo_home_control_api.mprm_api import MprmWebSocket
from devolo_home_control_api.mydevolo_api import Mydevolo

logging.basicConfig(level=logging.INFO)

user = "username"
password = "password"


class Subscriber:
    def __init__(self, name):
        self.name = name

    def update(self, message):
        print('{} got message "{}"'.format(self.name, message))


mydevolo = Mydevolo(user=user, password=password)

gateways_serial = mydevolo.get_gateway_serials()[0]
mprm_websocket = MprmWebSocket(user=user, password=password, gateway_serial=gateways_serial)

for device in mprm_websocket.devices:
        mprm_websocket.devices[device].subscriber = Subscriber(device)
        mprm_websocket.publisher.register(device, mprm_websocket.devices[device].subscriber)
