# ui/viewmodels/karakter_viewmodel.py
class KarakterViewModel:
    def __init__(self, karakter: TeknikResimKarakteri):
        self._karakter = karakter

    @property
    def display_title(self) -> str:
        return f"Item: {self._karakter.item_no}"

    @property
    def tolerance_status_color(self) -> str:
        if self.is_within_tolerance():
            return "green"
        return "red"

    def format_tolerance_info(self) -> str:
        # Tolerance bilgilerini formatla
        pass