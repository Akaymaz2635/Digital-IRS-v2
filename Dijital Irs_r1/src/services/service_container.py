# services/service_container.py
class ServiceContainer:
    def __init__(self):
        self._services = {}

    def register(self, service_type, instance):
        self._services[service_type] = instance

    def get(self, service_type):
        return self._services.get(service_type)


# main_window.py içinde
class NavigableMainWindow(ctk.CTk):
    def __init__(self, service_container: ServiceContainer):
        self.services = service_container
        self.word_save_service = self.services.get(WordSaveAsService)