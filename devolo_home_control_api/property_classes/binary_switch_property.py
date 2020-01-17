from property_classes.property import Property


class BinarySwitchProperty(Property):
    def __init__(self, element_uid):
        super().__init__(element_uid=element_uid)
        self.state = None
