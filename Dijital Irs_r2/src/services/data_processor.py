"""
Veri işleme servisi - Liste'yi DataFrame'e ve Model'e çevirir
"""
import pandas as pd
from typing import List, Optional
from dataclasses import dataclass
from services.olcu_parser import OlcuYakalayici 


@dataclass
class TeknikResimKarakteri:
    """Teknik resim karakteri veri modeli"""
    item_no: str
    dimension: str
    tooling: str
    remarks: str = ""
    bp_zone: str = ""
    inspection_level: str = "100%"
    actual: Optional[str] = None
    badge: str = ""
    
    # ===== YENİ ALANLAR =====
    parsed_dimension: Optional[dict[str, any]] = None
    tolerance_type: Optional[str] = None
    nominal_value: Optional[float] = None
    upper_limit: Optional[float] = None
    lower_limit: Optional[float] = None
    # =======================

class DataProcessorService:
    """
    Word içerisinden elde edilen listeyi mantıklı bir DataFrame yapısına çevirir
    """
    
    def __init__(self):
        self.processed_data = []
        self.dataframe = None
        self.olcu_parser = OlcuYakalayici()
    
    @staticmethod
    def from_word_tables(word_reader: 'WordReaderService', file_path: str) -> pd.DataFrame:
        """
        WordReaderService'den veri alıp DataFrame oluşturur
        """
        print("DataFrame oluşturuluyor...")
        
        try:
            # Word'den veri çıkar
            extracted_data = word_reader.extract_tables(file_path)
            
            if not extracted_data or len(extracted_data) < 2:
                print("✗ Yeterli veri bulunamadı")
                return pd.DataFrame()
            
            # Header - sabit 8 kolon
            headers = ["ITEM NO", "DIMENSION", "ACTUAL", "BADGE", "TOOLING", "REMARKS", "B/P ZONE", "INSP. LEVEL"]
            data_rows = extracted_data[1:]
            
            # Her veri satırını 8 kolona pad et
            padded_rows = []
            for row in data_rows:
                # Eksik kolonları boş string ile doldur
                padded_row = row + [''] * (len(headers) - len(row))
                # Fazla kolonları kes
                padded_row = padded_row[:len(headers)]
                padded_rows.append(padded_row)
                
            print(f"  Debug - Header uzunluğu: {len(headers)}")
            print(f"  Debug - İlk satır uzunluğu: {len(padded_rows[0]) if padded_rows else 'Boş'}")
            
            df = pd.DataFrame(padded_rows, columns=headers)
            
            print(f"✓ DataFrame oluşturuldu: {len(df)} satır, {len(df.columns)} kolon")
            print(f"  Kolon isimleri: {list(df.columns)}")
            
            return df
            
        except Exception as e:
            print(f"HATA: DataFrame oluşturma hatası: {e}")
            return pd.DataFrame()
    
    def process_dataframe(self, df: pd.DataFrame) -> List[TeknikResimKarakteri]:
        """
        DataFrame'i TeknikResimKarakteri model objelerine dönüştürür
        """
        print("Model objelerine dönüştürülüyor...")
        
        if df.empty:
            print("✗ Boş DataFrame")
            return []
        
        try:
            # ===== YENİ EKLEME: Parser'ı başlat =====

            parser = OlcuYakalayici()
            # ======================================
            
            karakterler = []
            
            for index, row in df.iterrows():
                try:
                    # Güvenli veri çıkarma
                    item_no = str(row.get('ITEM NO', '')).strip()
                    dimension = str(row.get('DIMENSION', '')).strip()
                    tooling = str(row.get('TOOLING', '')).strip()
                    remarks = str(row.get('REMARKS', '')).strip()
                    bp_zone = str(row.get('B/P ZONE', '')).strip()
                    inspection_level = str(row.get('INSP. LEVEL', '100%')).strip()
                    actual = row.get('ACTUAL')
                    badge = str(row.get('BADGE', '')).strip()
                    
                    # Actual değeri işleme
                    if pd.isna(actual) or str(actual).strip() in ['', 'nan', 'None']:
                        actual = None
                    else:
                        actual = str(actual).strip()
                    
                    # Temel validasyon
                    if not item_no or item_no in ['nan', 'None']:
                        print(f"  ⚠ Satır {index + 1}: Item no boş, atlanıyor")
                        continue
                    
                    if not dimension or dimension in ['nan', 'None']:
                        print(f"  ⚠ Satır {index + 1}: Dimension boş, atlanıyor")
                        continue
                    
                    # Model objesi oluştur
                    karakter = TeknikResimKarakteri(
                        item_no=item_no,
                        dimension=dimension,
                        tooling=tooling,
                        remarks=remarks,
                        bp_zone=bp_zone,
                        inspection_level=inspection_level,
                        actual=actual,
                        badge=badge
                    )
                    
                    # ===== YENİ EKLEME: Dimension Parsing =====
                    try:
                        parsed_result = parser.isle(dimension)
                        if parsed_result:
                            # Parse edilen verileri karakter objesine ekle
                            karakter.parsed_dimension = parsed_result
                            karakter.tolerance_type = parsed_result.get('format')
                            karakter.nominal_value = parsed_result.get('nominal')
                            karakter.upper_limit = parsed_result.get('ust_limit')
                            karakter.lower_limit = parsed_result.get('alt_limit')
                            print(f"    ✓ {karakter.item_no} - Dimension parsed: {parsed_result.get('format')}")
                        else:
                            # Parse edilemedi, ama hata verme - sadece None bırak
                            karakter.parsed_dimension = None
                            print(f"    ⚠ {karakter.item_no} - Dimension parse edilemedi: {dimension}")
                    except Exception as parse_error:
                        # Parser hatası olsa bile ana işlemi durdurma
                        print(f"    ⚠ {karakter.item_no} - Parser hatası: {parse_error}")
                        karakter.parsed_dimension = None
                    # ==========================================
                    
                    karakterler.append(karakter)
                    print(f"  ✓ {karakter.item_no} eklendi")
                    
                except Exception as e:
                    print(f"  ✗ Satır {index + 1} işlenirken hata: {e}")
                    continue
            
            self.processed_data = karakterler
            print(f"✓ {len(karakterler)} karakter başarıyla işlendi")
            return karakterler
            
        except Exception as e:
            print(f"HATA: Model dönüştürme hatası: {e}")
            return []
    
    def get_summary(self) -> dict:
        """İşlenen verinin özetini döner"""
        if not self.processed_data:
            return {"mesaj": "Henüz veri işlenmedi"}
        
        # Alet dağılımını hesapla
        alet_sayilari = {}
        for karakter in self.processed_data:
            alet = karakter.tooling
            alet_sayilari[alet] = alet_sayilari.get(alet, 0) + 1
        
        return {
            "toplam_karakter": len(self.processed_data),
            "alet_dagilimi": alet_sayilari,
            "farkli_alet_sayisi": len(alet_sayilari)
        }