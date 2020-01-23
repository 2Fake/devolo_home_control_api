import logging

from devolo_home_control_api.mprm_websocket import MprmWebSocket
from devolo_home_control_api.mydevolo import Mydevolo

logging.basicConfig(level=logging.DEBUG)

user = "username"
password = "password"


class Subscriber:
    def __init__(self, name):
        self.name = name

    def update(self, message):
        print('{} got message "{}"'.format(self.name, message))


mydevolo = Mydevolo.get_instance()
mydevolo.user = user
mydevolo.password = password

gateway_id = mydevolo.gateway_ids[0]
gateway = mydevolo.get_gateway(gateway_id)
mprm_websocket = MprmWebSocket(user=user, password=password, gateway_id=gateway_id)

for device in mprm_websocket.devices:
        mprm_websocket.devices[device].subscriber = Subscriber(device)
        mprm_websocket.publisher.register(device, mprm_websocket.devices[device].subscriber)
