class ServiceBrowser:

    def __init__(self, *args, handlers=None, **kwargs):
        if handlers:
            handlers[0]()

    def cancel(self):
        pass
