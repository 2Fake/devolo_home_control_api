import logging


class Gateway:

    def __init__(self, gateway_id: str):
        self._logger = logging.getLogger(self.__class__.__name__)
 
        self.id = gateway_id
        self.name = "Home"
        self.role = "owner"
        self.local_user = "535512AB-165D-11E7-A4E2-000C29D76CCA"
        self.local_passkey = "6b96ad097aa389209f1ceeaed6fe7029"
        self._full_url = "https://homecontrol.mydevolo.com/dhp/portal/fullLogin/?token=1410000000001_1:24b1516b93adebf7&X-MPRM-LB=1410000000001_1"
        self.external_access = True
        self.status = "devolo.hc_gateway.status.online"
        self.state = "devolo.hc_gateway.state.idle"
        self.firmware_version = "8.0.45_2016-11-17"