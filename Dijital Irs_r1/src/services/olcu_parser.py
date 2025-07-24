import re
from abc import ABC, abstractmethod
from typing import Optional, Tuple, Dict, Any, List

class OlcuFormati(ABC):
    @abstractmethod
    def eslestir(self, olcu: str) -> bool:
        pass
    
    @abstractmethod
    def degerler(self) -> Dict[str, Any]:
        pass

class EsitToleransliOlcu(OlcuFormati):
    def __init__(self):
        self.desen = r"(\d+\.?\d*)\s*(±|\+/-)\s*(\d+\.?\d*)"
        self.nominal = None
        self.tolerans = None
    
    def eslestir(self, olcu: str) -> bool:
        eslesen = re.search(self.desen, olcu, re.IGNORECASE)
        if eslesen:
            self.nominal = float(eslesen.group(1))
            self.tolerans = float(eslesen.group(3))
            return True
        return False
    
    def degerler(self) -> Dict[str, Any]:
        return {
            "nominal": self.nominal,
            "alt_limit": self.nominal - self.tolerans if self.nominal is not None else None,
            "ust_limit": self.nominal + self.tolerans if self.nominal is not None else None,
            "format": "toleranslı"
        }

class ArtiEksiOlcu(OlcuFormati):
    def __init__(self):
        self.desen = r".*?(\d+\.?\d*)\s*\+\s*(\d+\.?\d*)\s*/\s*-\s*(\d+\.?\d*)"
        self.nominal = None
        self.ust_tol = None
        self.alt_tol = None
    
    def eslestir(self, olcu: str) -> bool:
        eslesen = re.search(self.desen, olcu, re.IGNORECASE)
        if eslesen:
            self.nominal = float(eslesen.group(1))
            self.ust_tol = float(eslesen.group(2))
            self.alt_tol = float(eslesen.group(3))
            return True
        return False
    
    def degerler(self) -> Dict[str, Any]:
        return {
            "nominal": self.nominal,
            "alt_limit": self.nominal - self.alt_tol if self.nominal is not None else None,
            "ust_limit": self.nominal + self.ust_tol if self.nominal is not None else None,
            "format": "artı-eksi"
        }

class MaxOlcu(OlcuFormati):
    def __init__(self):
        self.desenler = [
            r"MAX\s*(\d+\.?\d*)",
            r"R?\s*(\d+\.?\d*)\s+MAX",
            r"R(\d+\.?\d*)\s+MAX",
        ]            
        self.deger = None
    
    def eslestir(self, olcu: str) -> bool:
        for desen in self.desenler:
            eslesen = re.search(desen, olcu, re.IGNORECASE)
            if eslesen:
                self.deger = float(eslesen.group(1))
                return True
        return False
    
    def degerler(self) -> Dict[str, Any]:
        return {
            "nominal": None,
            "alt_limit": None,
            "ust_limit": self.deger,
            "format": "maksimum"
        }

class MinOlcu(OlcuFormati):
    def __init__(self):
        self.desenler = [
            r"MIN\s+R?\s*(\d+\.?\d*)",
            r"R?\s*(\d+\.?\d*)\s+MIN",
            r"R(\d+\.?\d*)\s+MIN",
        ]
        self.deger = None
    
    def eslestir(self, olcu: str) -> bool:
        for desen in self.desenler:
            eslesen = re.search(desen, olcu, re.IGNORECASE)
            if eslesen:
                self.deger = float(eslesen.group(1))
                return True
        return False
    
    def degerler(self) -> Dict[str, Any]:
        return {
            "nominal": None,
            "alt_limit": self.deger,
            "ust_limit": None,
            "format": "minimum"
        }

class GeometrikTolerans(OlcuFormati):
    def __init__(self):
        self.tolerans_degeri = None
        self.referanslar = []
        self.sembol = None
        self.tip = None
        self.ozellikler = []
        self.alt_tip = None
        
    def _ozellik_ayikla(self, metin: str) -> List[str]:
        """(M), (L), (P), (U), (F) gibi özellikleri ayıklar"""
        ozellikler = re.findall(r'\(([MLPUF])\)', metin, re.IGNORECASE)
        return [oz.upper() for oz in ozellikler]
    
    def _referans_ayikla(self, metin: str) -> List[str]:
        """A, B, C gibi referansları ayıklar"""
        # Önce A-B gibi birleşik referansları kontrol et
        birlestik = re.findall(r'([A-Z])-([A-Z])', metin, re.IGNORECASE)
        if birlestik:
            return [birlestik[0][0].upper(), birlestik[0][1].upper()]
        
        # Normal referansları yakala (özellik parantezlerini hariç tut)
        referanslar = []
        # | A | B | C formatını yakala
        ref_matches = re.findall(r'\|\s*([A-Z])(?:\s*\([MLPUF]\))?\s*(?=\||$)', metin, re.IGNORECASE)
        if ref_matches:
            referanslar.extend([ref.upper() for ref in ref_matches])
        else:
            # Diğer formatları yakala
            ref_matches = re.findall(r'\b([A-Z])(?:\s*\([MLPUF]\))?\b', metin, re.IGNORECASE)
            referanslar.extend([ref.upper() for ref in ref_matches if ref.upper() not in ['M', 'L', 'P', 'U', 'F']])
        
        return list(set(referanslar))  # Tekrarları kaldır
    
    def _tolerans_ayikla(self, metin: str) -> Optional[float]:
        """Tolerans değerini ayıklar (∅ ile veya olmadan)"""
        match = re.search(r'(?:∅\s*)?(\d+\.?\d*)', metin, re.IGNORECASE)
        return float(match.group(1)) if match else None
    
    def _sembol_kontrol(self, metin: str) -> Optional[str]:
        """∅ sembolünü kontrol eder"""
        return "∅" if "∅" in metin else None

class FormToleransi(GeometrikTolerans):
    def __init__(self):
        super().__init__()
        self.tip = "Form"
        
    def eslestir(self, olcu: str) -> bool:
        # Form toleransları anahtar kelimeleri - büyük harfle normalize et
        form_keywords = {
            'STRAIGHTNESS': 'Straightness',
            'FLATNESS': 'Flatness', 
            'CIRCULARITY': 'Circularity',
            'CYLINDRICITY': 'Cylindricity'
        }
        
        olcu_upper = olcu.upper()
        
        # Köşeli parantez formatını kontrol et
        koseli_match = re.search(r'\[\s*([^|]+)\s*\|\s*([^|]+)\s*\]', olcu, re.IGNORECASE)
        if koseli_match:
            tolerans_kismi = koseli_match.group(1).strip().upper()
            deger_kismi = koseli_match.group(2).strip()
            
            for keyword, tip in form_keywords.items():
                if keyword in tolerans_kismi:
                    self.tolerans_degeri = self._tolerans_ayikla(deger_kismi)
                    if self.tolerans_degeri:
                        self.sembol = self._sembol_kontrol(deger_kismi)
                        self.ozellikler = self._ozellik_ayikla(olcu)
                        self.alt_tip = tip
                        return True
        
        # Normal format kontrol
        for keyword, tip in form_keywords.items():
            if keyword in olcu_upper:
                self.tolerans_degeri = self._tolerans_ayikla(olcu)
                if self.tolerans_degeri:
                    self.sembol = self._sembol_kontrol(olcu)
                    self.ozellikler = self._ozellik_ayikla(olcu)
                    self.alt_tip = tip
                    return True
        
        return False
    
    def degerler(self) -> Dict[str, Any]:
        return {
            "tolerans": self.tolerans_degeri,
            "tip": self.tip,
            "alt_tip": self.alt_tip,
            "sembol": self.sembol,
            "ozellikler": self.ozellikler,
            "format": "geometrik"
        }

class OryantasyonToleransi(GeometrikTolerans):
    def __init__(self):
        super().__init__()
        self.tip = "Oryantasyon"
        
    def eslestir(self, olcu: str) -> bool:
        # Oryantasyon toleransları - büyük harfle normalize et
        oryantasyon_keywords = {
            'PERPENDICULARITY': 'Perpendicularity',
            'ANGULARITY': 'Angularity',
            'PARALLELISM': 'Parallelism',
            'ANG': 'Angularity'  # Kısaltma
        }
        
        olcu_upper = olcu.upper()
        
        # Köşeli parantez formatını kontrol et
        koseli_match = re.search(r'\[\s*([^|]+)\s*\|\s*([^|]+)\s*(?:\|\s*(.+))?\s*\]', olcu, re.IGNORECASE)
        if koseli_match:
            tolerans_kismi = koseli_match.group(1).strip().upper()
            deger_kismi = koseli_match.group(2).strip()
            referans_kismi = koseli_match.group(3) if koseli_match.group(3) else ""
            
            for keyword, tip in oryantasyon_keywords.items():
                if keyword in tolerans_kismi:
                    self.tolerans_degeri = self._tolerans_ayikla(deger_kismi)
                    if self.tolerans_degeri:
                        self.sembol = self._sembol_kontrol(deger_kismi)
                        self.ozellikler = self._ozellik_ayikla(olcu)
                        self.referanslar = self._referans_ayikla(olcu)
                        self.alt_tip = tip
                        return True
        
        # Normal format kontrol
        for keyword, tip in oryantasyon_keywords.items():
            if keyword in olcu_upper:
                self.tolerans_degeri = self._tolerans_ayikla(olcu)
                if self.tolerans_degeri:
                    self.sembol = self._sembol_kontrol(olcu)
                    self.ozellikler = self._ozellik_ayikla(olcu)
                    self.referanslar = self._referans_ayikla(olcu)
                    self.alt_tip = tip
                    return True
        
        return False
    
    def degerler(self) -> Dict[str, Any]:
        return {
            "tolerans": self.tolerans_degeri,
            "tip": self.tip,
            "alt_tip": self.alt_tip,
            "sembol": self.sembol,
            "referanslar": self.referanslar,
            "ozellikler": self.ozellikler,
            "format": "geometrik"
        }

class LokasyonToleransi(GeometrikTolerans):
    def __init__(self):
        super().__init__()
        self.tip = "Lokasyon"
        
    def eslestir(self, olcu: str) -> bool:
        lokasyon_keywords = {
            'POSITION': 'Position',
            'TRUE POSITION': 'True Position',
            'TP': 'True Position',
            'CONCENTRICITY': 'Concentricity',
            'SYMMETRY': 'Symmetry'
        }
        
        olcu_upper = olcu.upper()
        
        # Köşeli parantez formatını kontrol et
        koseli_match = re.search(r'\[\s*([^|]+)\s*\|\s*([^|]+)\s*(?:\|\s*(.+))?\s*\]', olcu, re.IGNORECASE)
        if koseli_match:
            tolerans_kismi = koseli_match.group(1).strip().upper()
            deger_kismi = koseli_match.group(2).strip()
            
            for keyword, tip in lokasyon_keywords.items():
                if keyword in tolerans_kismi:
                    self.tolerans_degeri = self._tolerans_ayikla(deger_kismi)
                    if self.tolerans_degeri:
                        self.sembol = self._sembol_kontrol(deger_kismi)
                        self.ozellikler = self._ozellik_ayikla(olcu)
                        self.referanslar = self._referans_ayikla(olcu)
                        self.alt_tip = tip
                        return True
        
        # Normal format kontrol
        for keyword, tip in lokasyon_keywords.items():
            if keyword in olcu_upper:
                self.tolerans_degeri = self._tolerans_ayikla(olcu)
                if self.tolerans_degeri:
                    self.sembol = self._sembol_kontrol(olcu)
                    self.ozellikler = self._ozellik_ayikla(olcu)
                    self.referanslar = self._referans_ayikla(olcu)
                    self.alt_tip = tip
                    return True
        
        return False
    
    def degerler(self) -> Dict[str, Any]:
        return {
            "tolerans": self.tolerans_degeri,
            "tip": self.tip,
            "alt_tip": self.alt_tip,
            "sembol": self.sembol,
            "referanslar": self.referanslar,
            "ozellikler": self.ozellikler,
            "format": "geometrik"
        }

class ProfilToleransi(GeometrikTolerans):
    def __init__(self):
        super().__init__()
        self.tip = "Profil"
        self.unilateral_deger = None
        
    def eslestir(self, olcu: str) -> bool:
        profil_keywords = {
            'PROFILE OF A LINE': 'Profile of a Line',
            'PROFILE OF A SURFACE': 'Profile of a Surface',
            'LP': 'Profile of a Line',
            'SP': 'Profile of a Surface'
        }
        
        olcu_upper = olcu.upper()
        
        # Unilateral toleransları kontrol et
        unilateral_match = re.search(r'(\d+\.?\d*)\(U\)(\d+\.?\d*)', olcu, re.IGNORECASE)
        if unilateral_match:
            self.tolerans_degeri = float(unilateral_match.group(1))
            self.unilateral_deger = float(unilateral_match.group(2))
            self.ozellikler = ['U']
            self.referanslar = self._referans_ayikla(olcu)
            self.alt_tip = 'Profile of a Line'
            return True
        
        # Köşeli parantez formatını kontrol et
        koseli_match = re.search(r'\[\s*([^|]+)\s*\|\s*([^|]+)\s*(?:\|\s*(.+))?\s*\]', olcu, re.IGNORECASE)
        if koseli_match:
            tolerans_kismi = koseli_match.group(1).strip().upper()
            deger_kismi = koseli_match.group(2).strip()
            
            for keyword, tip in profil_keywords.items():
                if keyword in tolerans_kismi:
                    self.tolerans_degeri = self._tolerans_ayikla(deger_kismi)
                    if self.tolerans_degeri:
                        self.ozellikler = self._ozellik_ayikla(olcu)
                        self.referanslar = self._referans_ayikla(olcu)
                        self.alt_tip = tip
                        return True
        
        # Normal format kontrol
        for keyword, tip in profil_keywords.items():
            if keyword in olcu_upper:
                self.tolerans_degeri = self._tolerans_ayikla(olcu)
                if self.tolerans_degeri:
                    self.ozellikler = self._ozellik_ayikla(olcu)
                    self.referanslar = self._referans_ayikla(olcu)
                    self.alt_tip = tip
                    return True
        
        return False
    
    def degerler(self) -> Dict[str, Any]:
        result = {
            "tolerans": self.tolerans_degeri,
            "tip": self.tip,
            "alt_tip": self.alt_tip,
            "referanslar": self.referanslar,
            "ozellikler": self.ozellikler,
            "format": "geometrik"
        }
        if self.unilateral_deger:
            result["unilateral_deger"] = self.unilateral_deger
        return result

class RunoutToleransi(GeometrikTolerans):
    def __init__(self):
        super().__init__()
        self.tip = "Runout"
        
    def eslestir(self, olcu: str) -> bool:
        runout_keywords = {
            'CIRCULAR RUNOUT': 'Circular Runout',
            'TOTAL RUNOUT': 'Total Runout',
            'RUNOUT': 'Runout'
        }
        
        olcu_upper = olcu.upper()
        
        # Köşeli parantez formatını kontrol et
        koseli_match = re.search(r'\[\s*([^|]+)\s*\|\s*([^|]+)\s*(?:\|\s*(.+))?\s*\]', olcu, re.IGNORECASE)
        if koseli_match:
            tolerans_kismi = koseli_match.group(1).strip().upper()
            deger_kismi = koseli_match.group(2).strip()
            
            for keyword, tip in runout_keywords.items():
                if keyword in tolerans_kismi:
                    self.tolerans_degeri = self._tolerans_ayikla(deger_kismi)
                    if self.tolerans_degeri:
                        self.referanslar = self._referans_ayikla(olcu)
                        self.alt_tip = tip
                        return True
        
        # Normal format kontrol
        for keyword, tip in runout_keywords.items():
            if keyword in olcu_upper:
                self.tolerans_degeri = self._tolerans_ayikla(olcu)
                if self.tolerans_degeri:
                    self.referanslar = self._referans_ayikla(olcu)
                    self.alt_tip = tip
                    return True
        
        return False
    
    def degerler(self) -> Dict[str, Any]:
        return {
            "tolerans": self.tolerans_degeri,
            "tip": self.tip,
            "alt_tip": self.alt_tip,
            "referanslar": self.referanslar,
            "format": "geometrik"
        }

class SembolTolerans(OlcuFormati):
    """Sembol tabanlı toleranslar için"""
    def __init__(self):
        self.sembol_map = {
            '⏜': 'Straightness',
            '⟂': 'Perpendicularity', 
            '⌖': 'Position',
            '∠': 'Angularity',
            '⏩': 'Runout'
        }
        self.tolerans_degeri = None
        self.tip = None
        
    def eslestir(self, olcu: str) -> bool:
        for sembol, tip in self.sembol_map.items():
            if sembol in olcu:
                match = re.search(r'(\d+\.?\d*)', olcu, re.IGNORECASE)
                if match:
                    self.tolerans_degeri = float(match.group(1))
                    self.tip = tip
                    return True
        return False
    
    def degerler(self) -> Dict[str, Any]:
        return {
            "tolerans": self.tolerans_degeri,
            "tip": self.tip,
            "format": "sembol"
        }

class OlcuYakalayici:
    def __init__(self):
        self.format_tipleri = [
            FormToleransi(),
            OryantasyonToleransi(),
            LokasyonToleransi(),
            ProfilToleransi(),
            RunoutToleransi(),
            SembolTolerans(),
            EsitToleransliOlcu(),
            ArtiEksiOlcu(),
            MaxOlcu(),
            MinOlcu(),
        ]
    
    def isle(self, olcu: str) -> Optional[Dict[str, Any]]:
        for format_tipi in self.format_tipleri:
            if format_tipi.eslestir(olcu):
                return format_tipi.degerler()
        return None

# Test fonksiyonu
if __name__ == "__main__":
    # Test verileri - büyük harfli versiyonlar da eklendi
    test_verileri = [
        "[ Straightness | 0.02 ]",
        "[ STRAIGHTNESS | 0.02 ]",  # Büyük harf
        "[ SP | 0.02 ]",
        "[ Straightness | ∅0.05 ]", 
        "[ Straightness (M) | ∅0.01 (M) ]",
        "[ FLATNESS | 0.05 ]",
        "[ flatness | 0.05 ]",  # Küçük harf
        "[ Perpendicularity | 0.02 | A ]",
        "[ PERPENDICULARITY | 0.02 | A ]",  # Büyük harf
        "[ Perpendicularity (M) | ∅0.03 (M) | A (M) ]",
        "[ Position | ∅0.02 | A | B | C ]",
        "[ POSITION | ∅0.02 | A | B | C ]",  # Büyük harf
        "[ PROFILE OF A LINE | 1(U)0.6 | A ]",
        "[ profile of a line | 1(U)0.6 | A ]",  # Küçük harf
        "[ Total Runout | 0.02 | A-B ]",
        "[ TOTAL RUNOUT | 0.02 | A-B ]",  # Büyük harf
        "25.55±0.1",
        "Ø250 +0.1/-0.1",
        "Ø250 +/-0.1",
        "MAX 6.3",
        "max 6.3",  # Küçük harf
        "⏜ 0.02",
        "⟂ 0.01"
    ]
    
    yakalayici = OlcuYakalayici()
    
    print("=== TEST SONUÇLARI ===\n")
    for i, veri in enumerate(test_verileri, 1):
        sonuc = yakalayici.isle(veri)
        if sonuc:
            print(f"✓ {i:2d}. {veri}")
            print(f"     => {sonuc}")
        else:
            print(f"✗ {i:2d}. {veri} => YAKALANAMIYOR")
        print() 