class EventBus:
    def __init__(self):
        self.listeners = {}

    def subscribe(self, event_type, callback):
        self.listeners.setdefault(event_type, []).append(callback)

    def emit(self, event_type, data=None):
        for callback in self.listeners.get(event_type, []):
            callback(data)