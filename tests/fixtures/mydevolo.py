import pytest

from devolo_home_control_api.mydevolo import Mydevolo, WrongUrlError

from ..mocks.mock_mydevolo import MockMydevolo


@pytest.fixture()
def mydevolo(request):
    mydevolo = Mydevolo()
    mydevolo._uuid = request.cls.user.get("uuid")
    yield mydevolo
    Mydevolo.del_instance()


@pytest.fixture()
def mock_mydevolo_full_url(mocker):
    mocker.patch("devolo_home_control_api.mydevolo.Mydevolo.get_full_url", side_effect=MockMydevolo.get_full_url)


@pytest.fixture()
def mock_mydevolo__call(mocker, request):
    def _call_mock(url):
        uuid = request.cls.user.get("uuid")
        gateway_id = request.cls.gateway.get("id")
        full_url = request.cls.gateway.get("full_url")

        response = {}
        response[f'https://www.mydevolo.com/v1/users/{uuid}/hc/gateways/{gateway_id}/fullURL'] = {"url": full_url}
        response['https://www.mydevolo.com/v1/users/uuid'] = {"uuid": uuid}
        response[f'https://www.mydevolo.com/v1/users/{uuid}/hc/gateways/status'] = {"items": []} \
            if request.node.name == "test_gateway_ids_empty" else {"items": [{"gatewayId": gateway_id}]}
        response[f'https://www.mydevolo.com/v1/users/{uuid}/hc/gateways/{gateway_id}'] = \
            {"gatewayId": gateway_id, "status": "devolo.hc_gateway.status.online", "state": "devolo.hc_gateway.state.idle"}
        response['https://www.mydevolo.com/v1/hc/maintenance'] = {"state": "off"} \
            if request.node.name == "test_maintenance_off" else {"state": "on"}
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

    mocker.patch("devolo_home_control_api.mydevolo.Mydevolo._call", side_effect=_call_mock)


@pytest.fixture()
def mock_mydevolo__call_raise_WrongUrlError(mocker):
    mocker.patch("devolo_home_control_api.mydevolo.Mydevolo._call", side_effect=WrongUrlError)
