from property_classes.property import Property


class ConsumptionProperty(Property):
    def __init__(self, element_uid):
        super().__init__(element_uid=element_uid)
        self.current_consumption = None
        self.current_consumption_unit = 'W'
        self.total_consumption = None
        self.total_consumption_unit = "kWh"
