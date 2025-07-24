# utils/observer.py
class Observable:
    def __init__(self):
        self._observers = []

    def attach(self, observer):
        self._observers.append(observer)

    def notify(self, event_type: str, data: any = None):
        for observer in self._observers:
            observer.update(event_type, data)


# main_window.py
class NavigableMainWindow(Observable):
    def on_karakter_updated(self, karakter):
        self.notify("karakter_updated", karakter)
        self.notify("stats_changed", self.get_stats())