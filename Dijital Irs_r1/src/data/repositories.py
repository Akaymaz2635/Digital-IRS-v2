# data/repositories.py
class KarakterRepository:
    def __init__(self):
        self._karakterler: List[TeknikResimKarakteri] = []

    def add(self, karakter: TeknikResimKarakteri) -> None:
        self._karakterler.append(karakter)

    def get_by_item_no(self, item_no: str) -> Optional[TeknikResimKarakteri]:
        return next((k for k in self._karakterler if k.item_no == item_no), None)

    def get_measured_count(self) -> int:
        return len([k for k in self._karakterler if k.actual])

    def get_tolerance_violations(self) -> List[TeknikResimKarakteri]:
        # Tolerance dışı karakterleri döndür
        pass