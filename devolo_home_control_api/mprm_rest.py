import json
import logging
import socket
import time

import requests
from zeroconf import DNSAddress, ServiceBrowser, ServiceStateChange, Zeroconf

from .devices.gateway import Gateway
from .devices.zwave import Zwave
from .properties.binary_switch_property import BinarySwitchProperty
from .properties.consumption_property import ConsumptionProperty


class MprmRest:
    """
    The MprmRest object handles calls to the so called mPRM. It does not cover all API calls, just those requested
    up to now. All calls are done in a gateway context, so you need to provide the ID of that gateway.

    :param gateway_id: Gateway ID (aka serial number), typically found on the label of the device
    :param url: URL of the mPRM (typically leave it at default)
    """

    def __init__(self, gateway_id: str, url: str ="https://homecontrol.mydevolo.com"):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._gateway = Gateway(gateway_id)
        self._session = requests.Session()
        self._data_id = 0
        self._mprm_url = url

        local_ip = self._detect_gateway_in_lan()

        if local_ip:
            # Get a local session
            self._logger.info("Connecting to gateway locally")
            self._mprm_url = "http://" + local_ip
            self._token_url = self._session.get(self._mprm_url + "/dhlp/port/full", auth=(self._gateway.local_user, self._gateway.local_passkey)).json()
            self._session.get(self._token_url.get('link'))
        elif self._gateway.external_access:
            # Get a remote session, if we are allowed to
            self._logger.info("Connecting to gateway via cloud")
            self._session.get(self._gateway.full_url)
        else:
            self._logger.error("Cannot connect to gateway. No gateway found in LAN and external access is prohibited.")
            raise ConnectionError("Cannot connect to gateway.")

        # create the initial device dict
        self.devices = {}
        self.update_devices()

        # update device properties
        for device in self.devices.values():
            if hasattr(device, "consumption_property"):
                for consumption_uid in device.consumption_property.keys():
                    self.update_consumption(uid=consumption_uid, consumption="current")
            if hasattr(device, "binary_switch_property"):
                for binary_switch in device.binary_switch_property:
                    self.update_binary_switch_state(uid=binary_switch)


    @property
    def binary_switch_devices(self):
        """Returns all binary switch devices."""
        return [self.devices.get(uid) for uid in self.devices if hasattr(self.devices.get(uid), "binary_switch_property")]

 
    def get_consumption(self, uid: str, consumption_type: str ="current"):
        """
        Return the consumption, specified in consumption_type for the given uid.

        :param uid: UID
        :param consumption_type: current or total consumption
        :return: Consumption as float
        """
        if consumption_type not in ['current', 'total']:
            raise ValueError('Unknown consumption type. "current" and "total" are valid consumption types.')
        # TODO: Prepare for more meter items as one
        return self._element_uid_dict.get(uid).get(f"devolo.Meter:{uid}").get(f"{consumption_type}_consumption")

    def update_binary_switch_state(self, uid, value=None):
        """
        Function to update the internal binary switch state of a device.
        If value is None, it uses a RPC-Call to retrieve the value. If a value is given, e.g. from a web socket,
        the value is written into the internal dict.

        :param uid: UID as string
        :param value: bool
        """
        if not uid.startswith('devolo.BinarySwitch:'):
            raise ValueError("Not a valid uid to get binary switch data")
        if value is not None:
            raise ValueError("Use function in mPRM web socket to update a binary state with a value")
        self._logger.debug(f"Updating state of {uid}")
        r = self._extract_data_from_element_uid(uid)
        self.devices[self._get_fim_uid_from_element_uid(uid)].binary_switch_property[uid].state = True if r['properties']['state'] == 1 else False

    def update_consumption(self, uid, consumption, value=None):
        """
        Function to update the internal consumption of a device.
        If value is None, it uses a RPC-Call to retrieve the value. If a value is given, e.g. from a web socket,
        the value is written into the internal dict.
        :param uid: UID as string
        :param consumption: String, which consumption is meant (current or total)
        :param value: consumption value as float
        """
        if consumption not in ['current', 'total']:
            raise ValueError("Consumption value is not valid. Only \"current\" and \"total\" are allowed!")
        if value is not None:
            raise ValueError("Value is not allowed here.")
        self._logger.debug(f"Updating {consumption} consumption of {uid}")
        r = self._extract_data_from_element_uid(uid)
        if consumption == 'current':
            self.devices[self._get_fim_uid_from_element_uid(uid)].consumption_property[uid].current_consumption = r['properties']['currentValue']
        elif consumption == 'total':
            self.devices[self._get_fim_uid_from_element_uid(uid)].consumption_property[uid].total_consumption = r['properties']['totalValue']

    def get_binary_switch_state(self, element_uid):
        """Return the internal saved binary switch state of a device."""
        return self.devices.get(self._get_fim_uid_from_element_uid(element_uid)).binary_switch_property[element_uid].state

    def set_binary_switch(self, element_uid, state: bool):
        """
        Set the binary switch of the given element_uid to the given state
        :param element_uid: element_uid as string
        :param state: Bool
        """
        # TODO: We should think about how to prevent an jumping binary switch in the UI of hass
        # Maybe set the state of the binary internally without waiting for the websocket to tell us the state.
        data = {'jsonrpc': '2.0',
                'method': 'FIM/invokeOperation',
                'params': [f"{element_uid}", 'turnOn' if state else 'turnOff', []]}
        self._post(data)
        # TODO: Catch errors!

    def get_current_consumption(self, element_uid):
        """Return the internal saved current consumption state of a device"""
        try:
            return self.devices.get(self._get_fim_uid_from_element_uid(element_uid)).consumption_property.get(element_uid).current_consumption
        except AttributeError:
            return None

    def update_devices(self):
        """Create the initial internal device dict"""
        # TODO: Add http, powermeter
        data = {'jsonrpc': '2.0',
                'method': 'FIM/getFunctionalItems',
                'params': [['devolo.DevicesPage'], 0]}
        response = self._post(data)
        for item in response['result']['items']:
            all_devices_list = item['properties']['deviceUIDs']
            for device in all_devices_list:
                name, element_uids, deviceModelUID = self._get_name_and_element_uids(uid=device)
                self.devices[device] = Zwave(name=name, fim_uid=device)
                for element_uid in element_uids:
                    if self._get_device_type_from_element_uid(element_uid) == 'devolo.BinarySwitch':
                        if not hasattr(self.devices[device], 'binary_switch_property'):
                            self.devices[device].binary_switch_property = {}
                        self._logger.debug(f"Adding {name} ({device}) to device list as binary switch property.")
                        self.devices[device].binary_switch_property[element_uid] = BinarySwitchProperty(element_uid=element_uid)
                    elif self._get_device_type_from_element_uid(element_uid) == 'devolo.Meter':
                        if not hasattr(self.devices[device], 'consumption_property'):
                            self.devices[device].consumption_property = {}
                            self._logger.debug(f"Adding {name} ({device}) to device list as consumption property.")
                            self.devices[device].consumption_property[element_uid] = ConsumptionProperty(element_uid=element_uid)
                    # TODO:
                    else:
                        self._logger.debug(f"Found an unexpected element uid: {element_uid}")


    def _detect_gateway_in_lan(self):
        """Detects a gateway in local network and check if it is the desired one."""
        def on_service_state_change(zeroconf, service_type, name, state_change):
            if state_change is ServiceStateChange.Added:
                zeroconf.get_service_info(service_type, name)

        local_ip = None
        zeroconf = Zeroconf()
        ServiceBrowser(zeroconf, "_http._tcp.local.", handlers=[on_service_state_change])
        # TODO: Optimize the sleep
        time.sleep(2)
        for mdns_name in zeroconf.cache.entries():
            if hasattr(mdns_name, 'address'):
                try:
                    ip = socket.inet_ntoa(mdns_name.address)
                    if requests.get('http://' + ip + '/dhlp/port/full', auth=(self._gateway.local_user, self._gateway.local_passkey)).status_code == requests.codes.ok:
                        self._logger.debug(f"Got successful answer from ip {ip}. Setting this as local gateway")
                        local_ip = ip
                        break
                except OSError:
                    # Got IPv6 address which isn't supported by socket.inet_ntoa
                    self._logger.debug(f'Found an IPv6 address. This cannot be a gateway.')
        zeroconf.close()
        return local_ip

    def _get_name_and_element_uids(self, uid):
        """Returns the name and all element uids of the given UID"""
        data = {'jsonrpc': '2.0',
                'method': 'FIM/getFunctionalItems',
                'params': [[f"{uid}"], 0]}
        response = self._post(data)
        for x in response["result"]["items"]:
            return x['properties']['itemName'], x['properties']["elementUIDs"], x['properties']['deviceModelUID']

    def _extract_data_from_element_uid(self, element_uid):
        """Returns data from an element_uid using a RPC call"""
        data = {'jsonrpc': '2.0',
                'method': 'FIM/getFunctionalItems',
                'params': [[f"{element_uid}"], 0]}
        response = self._post(data)
        # TODO: Catch error!
        return response['result']['items'][0]

    def _get_fim_uid_from_element_uid(self, element_uid):
        """Return FIM UID from the given element UID"""
        return element_uid.split(':', 1)[1].split('#')[0]

    def _get_device_type_from_element_uid(self, element_uid):
        """Return the device type of the given element uid"""
        return element_uid.split(':')[0]

    def _post(self, data: dict) -> dict:
        """
        Communicate with the RPC interface.
        :param data: Data you want so send
        """
        self._data_id += 1
        data['id'] = self._data_id
        headers = {'content-type': 'application/json'}
        rpc_url = self._mprm_url + '/remote/json-rpc'
        response = self._session.post(rpc_url, data=json.dumps(data), headers=headers).json()
        if response['id'] != self._data_id:
            self._logger.error("Got an unexpected response after posting data.")
            raise ValueError("Got an unexpected response after posting data.")
        return response
