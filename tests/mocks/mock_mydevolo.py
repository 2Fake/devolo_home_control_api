class MockMydevolo:
    @staticmethod
    def get_full_url(gateway_id):
        return gateway_id

    def __init__(self, request):
        self._request = request

    def _call(self, url):
        uuid = self._request.cls.user.get("uuid")
        gateway_id = self._request.cls.gateway.get("id")
        full_url = self._request.cls.gateway.get("full_url")

        response = {}
        response[f'https://www.mydevolo.com/v1/users/{uuid}/hc/gateways/{gateway_id}/fullURL'] = {"url": full_url}
        response['https://www.mydevolo.com/v1/users/uuid'] = {"uuid": uuid}
        response[f'https://www.mydevolo.com/v1/users/{uuid}/hc/gateways/status'] = {"items": []} \
            if self._request.node.name == "test_gateway_ids_empty" else {"items": [{"gatewayId": gateway_id}]}
        response[f'https://www.mydevolo.com/v1/users/{uuid}/hc/gateways/{gateway_id}'] = \
            {"gatewayId": gateway_id, "status": "devolo.hc_gateway.status.online", "state": "devolo.hc_gateway.state.idle"}
        response['https://www.mydevolo.com/v1/hc/maintenance'] = {"state": "off"} \
            if self._request.node.name == "test_maintenance_off" else {"state": "on"}
        response['https://www.mydevolo.com/v1/zwave/products/0x0060/0x0001/0x000'] = {"brand": "Everspring",
                                                                                      "deviceType": "Door Lock Keypad",
                                                                                      "genericDeviceClass": "Entry Control",
                                                                                      "identifier": "SP814-US",
                                                                                      "isZWavePlus": True,
                                                                                      "manufacturerId": "0x0060",
                                                                                      "name": "Everspring PIR Sensor SP814",
                                                                                      "productId": "0x0002",
                                                                                      "productTypeId": "0x0001",
                                                                                      "zwaveVersion": "6.51.07"}
        response['https://www.mydevolo.com/v1/zwave/products/0x0175/0x0001/0x0011'] = {"manufacturerId": "0x0175",
                                                                                       "productTypeId": "0x0001",
                                                                                       "productId": "0x0011",
                                                                                       "name": "Metering Plug",
                                                                                       "brand": "devolo",
                                                                                       "identifier": "MT02646",
                                                                                       "isZWavePlus": True,
                                                                                       "deviceType": "On/Off Power Switch",
                                                                                       "zwaveVersion": "6.51.00",
                                                                                       "specificDeviceClass": None,
                                                                                       "genericDeviceClass": None}
        return response[url]
