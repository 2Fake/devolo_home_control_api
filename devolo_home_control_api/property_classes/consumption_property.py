from property_classes.property import Property


class ConsumptionProperty(Property):
    def __init__(self, element_uid):
        super().__init__(element_uid=element_uid)
        self._current_consumption = None
        self._total_consumption = None

    def get_current_consumption(self):
        return self._current_consumption

    def get_total_consumption(self):
        return self._total_consumption

    def set_current_consumption(self, current_consumption: float):
        self._current_consumption = current_consumption

    def set_total_consumption(self, total_consumption: float):
        self._total_consumption = total_consumption
