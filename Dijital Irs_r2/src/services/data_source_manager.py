"""
Data Source Manager - LotDetailManager için esnek veri kaynağı sistemi
services/data_source_manager.py
"""
import os
import json
import pandas as pd
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from abc import ABC, abstractmethod


class DataSource(ABC):
    """Abstract base class for data sources"""

    @abstractmethod
    def load_data(self, identifier: str) -> Dict[str, Any]:
        """Load data for given identifier"""
        pass

    @abstractmethod
    def save_data(self, identifier: str, data: Dict[str, Any]) -> bool:
        """Save data for given identifier"""
        pass

    @abstractmethod
    def list_available_data(self) -> List[str]:
        """List all available data identifiers"""
        pass


class JSONDataSource(DataSource):
    """JSON dosyasından veri okuma/yazma"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.data = {}
        self._load_file()

    def _load_file(self):
        """JSON dosyasını yükle"""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                print(f"✓ JSON veri yüklendi: {self.file_path}")
            except Exception as e:
                print(f"HATA: JSON yükleme hatası: {e}")
                self.data = {}

    def _save_file(self):
        """JSON dosyasını kaydet"""
        try:
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            print(f"✓ JSON veri kaydedildi: {self.file_path}")
            return True
        except Exception as e:
            print(f"HATA: JSON kaydetme hatası: {e}")
            return False

    def load_data(self, identifier: str) -> Dict[str, Any]:
        """Belirli identifier için veri yükle"""
        return self.data.get(identifier, {})

    def save_data(self, identifier: str, data: Dict[str, Any]) -> bool:
        """Belirli identifier için veri kaydet"""
        self.data[identifier] = data
        return self._save_file()

    def list_available_data(self) -> List[str]:
        """Mevcut identifier'ları listele"""
        return list(self.data.keys())


class ExcelDataSource(DataSource):
    """Excel dosyasından veri okuma/yazma"""

    def __init__(self, file_path: str, sheet_name: str = "LotDetails"):
        self.file_path = file_path
        self.sheet_name = sheet_name
        self.data = {}
        self._load_file()

    def _load_file(self):
        """Excel dosyasını yükle"""
        if os.path.exists(self.file_path):
            try:
                df = pd.read_excel(self.file_path, sheet_name=self.sheet_name)

                # DataFrame'i dictionary yapısına çevir
                for _, row in df.iterrows():
                    identifier = row.get('identifier', '')
                    if identifier:
                        self.data[identifier] = {
                            'part_quantity': row.get('part_quantity', 0),
                            'part_numbers': json.loads(row.get('part_numbers', '{}')),
                            'notes': row.get('notes', ''),
                            'actual_value': row.get('actual_value', '')
                        }

                print(f"✓ Excel veri yüklendi: {self.file_path}")
            except Exception as e:
                print(f"HATA: Excel yükleme hatası: {e}")
                self.data = {}

    def _save_file(self):
        """Excel dosyasını kaydet"""
        try:
            # Dictionary'yi DataFrame'e çevir
            rows = []
            for identifier, data in self.data.items():
                rows.append({
                    'identifier': identifier,
                    'part_quantity': data.get('part_quantity', 0),
                    'part_numbers': json.dumps(data.get('part_numbers', {})),
                    'notes': data.get('notes', ''),
                    'actual_value': data.get('actual_value', '')
                })

            df = pd.DataFrame(rows)

            # Excel'e kaydet
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            df.to_excel(self.file_path, sheet_name=self.sheet_name, index=False)

            print(f"✓ Excel veri kaydedildi: {self.file_path}")
            return True
        except Exception as e:
            print(f"HATA: Excel kaydetme hatası: {e}")
            return False

    def load_data(self, identifier: str) -> Dict[str, Any]:
        """Belirli identifier için veri yükle"""
        return self.data.get(identifier, {})

    def save_data(self, identifier: str, data: Dict[str, Any]) -> bool:
        """Belirli identifier için veri kaydet"""
        self.data[identifier] = data
        return self._save_file()

    def list_available_data(self) -> List[str]:
        """Mevcut identifier'ları listele"""
        return list(self.data.keys())


class SQLiteDataSource(DataSource):
    """SQLite veritabanından veri okuma/yazma"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._create_table()

    def _create_table(self):
        """Veritabanı tablosunu oluştur"""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS lot_details (
                        identifier TEXT PRIMARY KEY,
                        part_quantity INTEGER,
                        part_numbers TEXT,
                        notes TEXT,
                        actual_value TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
            print(f"✓ SQLite tablo oluşturuldu: {self.db_path}")
        except Exception as e:
            print(f"HATA: SQLite tablo oluşturma hatası: {e}")

    def load_data(self, identifier: str) -> Dict[str, Any]:
        """Belirli identifier için veri yükle"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    'SELECT * FROM lot_details WHERE identifier = ?',
                    (identifier,)
                )
                row = cursor.fetchone()

                if row:
                    return {
                        'part_quantity': row[1],
                        'part_numbers': json.loads(row[2] or '{}'),
                        'notes': row[3] or '',
                        'actual_value': row[4] or ''
                    }
            return {}
        except Exception as e:
            print(f"HATA: SQLite veri yükleme hatası: {e}")
            return {}

    def save_data(self, identifier: str, data: Dict[str, Any]) -> bool:
        """Belirli identifier için veri kaydet"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO lot_details 
                    (identifier, part_quantity, part_numbers, notes, actual_value, updated_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    identifier,
                    data.get('part_quantity', 0),
                    json.dumps(data.get('part_numbers', {})),
                    data.get('notes', ''),
                    data.get('actual_value', '')
                ))
            print(f"✓ SQLite veri kaydedildi: {identifier}")
            return True
        except Exception as e:
            print(f"HATA: SQLite veri kaydetme hatası: {e}")
            return False

    def list_available_data(self) -> List[str]:
        """Mevcut identifier'ları listele"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('SELECT identifier FROM lot_details')
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"HATA: SQLite veri listeleme hatası: {e}")
            return []


class CSVDataSource(DataSource):
    """CSV dosyasından veri okuma/yazma"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.data = {}
        self._load_file()

    def _load_file(self):
        """CSV dosyasını yükle"""
        if os.path.exists(self.file_path):
            try:
                df = pd.read_csv(self.file_path)

                for _, row in df.iterrows():
                    identifier = row.get('identifier', '')
                    if identifier:
                        self.data[identifier] = {
                            'part_quantity': row.get('part_quantity', 0),
                            'part_numbers': json.loads(row.get('part_numbers', '{}')),
                            'notes': row.get('notes', ''),
                            'actual_value': row.get('actual_value', '')
                        }

                print(f"✓ CSV veri yüklendi: {self.file_path}")
            except Exception as e:
                print(f"HATA: CSV yükleme hatası: {e}")
                self.data = {}

    def _save_file(self):
        """CSV dosyasını kaydet"""
        try:
            rows = []
            for identifier, data in self.data.items():
                rows.append({
                    'identifier': identifier,
                    'part_quantity': data.get('part_quantity', 0),
                    'part_numbers': json.dumps(data.get('part_numbers', {})),
                    'notes': data.get('notes', ''),
                    'actual_value': data.get('actual_value', '')
                })

            df = pd.DataFrame(rows)
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            df.to_csv(self.file_path, index=False)

            print(f"✓ CSV veri kaydedildi: {self.file_path}")
            return True
        except Exception as e:
            print(f"HATA: CSV kaydetme hatası: {e}")
            return False

    def load_data(self, identifier: str) -> Dict[str, Any]:
        return self.data.get(identifier, {})

    def save_data(self, identifier: str, data: Dict[str, Any]) -> bool:
        self.data[identifier] = data
        return self._save_file()

    def list_available_data(self) -> List[str]:
        return list(self.data.keys())


class DataSourceManager:
    """Veri kaynaklarını yöneten ana sınıf"""

    def __init__(self):
        self.sources: Dict[str, DataSource] = {}
        self.primary_source: Optional[str] = None

    def add_source(self, name: str, source: DataSource, is_primary: bool = False):
        """Veri kaynağı ekle"""
        self.sources[name] = source
        if is_primary or not self.primary_source:
            self.primary_source = name
        print(f"✓ Veri kaynağı eklendi: {name}")

    def remove_source(self, name: str):
        """Veri kaynağını kaldır"""
        if name in self.sources:
            del self.sources[name]
            if self.primary_source == name:
                self.primary_source = next(iter(self.sources.keys())) if self.sources else None
            print(f"✓ Veri kaynağı kaldırıldı: {name}")

    def set_primary_source(self, name: str):
        """Ana veri kaynağını ayarla"""
        if name in self.sources:
            self.primary_source = name
            print(f"✓ Ana veri kaynağı: {name}")
        else:
            print(f"HATA: Veri kaynağı bulunamadı: {name}")

    def load_data(self, identifier: str, source_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Veri yükle - önce belirtilen kaynaktan, sonra diğerlerinden

        Args:
            identifier: Veri tanımlayıcısı
            source_name: Belirli kaynak adı (None ise tüm kaynaklardan)

        Returns:
            Dict[str, Any]: Yüklenen veri
        """
        # Belirli kaynaktan yükle
        if source_name and source_name in self.sources:
            data = self.sources[source_name].load_data(identifier)
            if data:
                print(f"✓ Veri yüklendi ({source_name}): {identifier}")
                return data

        # Ana kaynaktan yükle
        if self.primary_source and self.primary_source in self.sources:
            data = self.sources[self.primary_source].load_data(identifier)
            if data:
                print(f"✓ Veri yüklendi (ana kaynak): {identifier}")
                return data

        # Tüm kaynaklardan yükle
        for name, source in self.sources.items():
            if name == self.primary_source:  # Ana kaynağı zaten denedik
                continue

            data = source.load_data(identifier)
            if data:
                print(f"✓ Veri yüklendi ({name}): {identifier}")
                return data

        print(f"⚠ Veri bulunamadı: {identifier}")
        return {}

    def save_data(self, identifier: str, data: Dict[str, Any],
                  sync_all: bool = False, source_name: Optional[str] = None) -> bool:
        """
        Veri kaydet

        Args:
            identifier: Veri tanımlayıcısı
            data: Kaydedilecek veri
            sync_all: Tüm kaynaklara kaydet mi
            source_name: Belirli kaynak adı

        Returns:
            bool: Başarılı mı
        """
        success = False

        # Belirli kaynağa kaydet
        if source_name and source_name in self.sources:
            success = self.sources[source_name].save_data(identifier, data)
            return success

        # Ana kaynağa kaydet
        if self.primary_source and self.primary_source in self.sources:
            success = self.sources[self.primary_source].save_data(identifier, data)

        # Tüm kaynaklara kaydet
        if sync_all:
            for name, source in self.sources.items():
                try:
                    source.save_data(identifier, data)
                except Exception as e:
                    print(f"HATA: {name} kaynağına kaydetme hatası: {e}")

        return success

    def list_all_available_data(self) -> Dict[str, List[str]]:
        """Tüm kaynaklardaki mevcut verileri listele"""
        all_data = {}
        for name, source in self.sources.items():
            try:
                all_data[name] = source.list_available_data()
            except Exception as e:
                print(f"HATA: {name} kaynağı listeleme hatası: {e}")
                all_data[name] = []
        return all_data

    def get_source_names(self) -> List[str]:
        """Mevcut kaynak isimlerini döner"""
        return list(self.sources.keys())

    def create_project_sources(self, project_folder: str) -> bool:
        """
        Proje klasörü için varsayılan veri kaynaklarını oluştur

        Args:
            project_folder: Proje klasör yolu

        Returns:
            bool: Başarılı mı
        """
        try:
            # JSON kaynağı (ana kaynak)
            json_path = os.path.join(project_folder, "lot_details.json")
            json_source = JSONDataSource(json_path)
            self.add_source("json", json_source, is_primary=True)

            # Excel kaynağı (yedek)
            excel_path = os.path.join(project_folder, "lot_details.xlsx")
            excel_source = ExcelDataSource(excel_path)
            self.add_source("excel", excel_source)

            # SQLite kaynağı (performans için)
            sqlite_path = os.path.join(project_folder, "lot_details.db")
            sqlite_source = SQLiteDataSource(sqlite_path)
            self.add_source("sqlite", sqlite_source)

            print(f"✓ Proje veri kaynakları oluşturuldu: {project_folder}")
            return True

        except Exception as e:
            print(f"HOTA: Proje veri kaynakları oluşturma hatası: {e}")
            return False


class LotDataAdapter:
    """
    Lot detail verilerini farklı formatlar arasında dönüştürür
    IRS_YAZICI formatı ile Dijital IRS formatı arasında bridge
    """

    @staticmethod
    def from_irs_yazici_format(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        IRS_YAZICI lot detail formatından standart formata çevir

        Expected IRS_YAZICI format:
        {
            'part_quantities': {'key': '5'},
            'part_numbers': {'key': {'1': 'part1', '2': 'part2'}},
            'lot_notes': {'key': 'notes'},
            'actual_values': {'key': '25.4/25.6'}
        }
        """
        standardized = {}

        # Part quantities
        part_quantities = data.get('part_quantities', {})
        part_numbers = data.get('part_numbers', {})
        lot_notes = data.get('lot_notes', {})
        actual_values = data.get('actual_values', {})

        # Her key için standardize et
        all_keys = set()
        all_keys.update(part_quantities.keys())
        all_keys.update(part_numbers.keys())
        all_keys.update(lot_notes.keys())
        all_keys.update(actual_values.keys())

        for key in all_keys:
            standardized[key] = {
                'part_quantity': int(part_quantities.get(key, 0)),
                'part_numbers': part_numbers.get(key, {}),
                'notes': lot_notes.get(key, ''),
                'actual_value': actual_values.get(key, '')
            }

        return standardized

    @staticmethod
    def to_irs_yazici_format(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Standart formattan IRS_YAZICI formatına çevir
        """
        part_quantities = {}
        part_numbers = {}
        lot_notes = {}
        actual_values = {}

        for key, lot_data in data.items():
            part_quantities[key] = str(lot_data.get('part_quantity', 0))
            part_numbers[key] = lot_data.get('part_numbers', {})
            lot_notes[key] = lot_data.get('notes', '')
            actual_values[key] = lot_data.get('actual_value', '')

        return {
            'part_quantities': part_quantities,
            'part_numbers': part_numbers,
            'lot_notes': lot_notes,
            'actual_values': actual_values
        }

    @staticmethod
    def from_dijital_irs_format(karakterler: List) -> Dict[str, Any]:
        """
        Dijital IRS karakter listesinden lot data formatına çevir
        """
        lot_data = {}

        for karakter in karakterler:
            if hasattr(karakter, 'item_no') and hasattr(karakter, 'dimension'):
                key = f"{karakter.dimension}_{karakter.item_no}"

                lot_data[key] = {
                    'part_quantity': 1,  # Varsayılan
                    'part_numbers': {'1': karakter.actual or ''},
                    'notes': karakter.remarks or '',
                    'actual_value': karakter.actual or '',
                    # Dijital IRS'e özgü veriler
                    'tolerance_type': getattr(karakter, 'tolerance_type', ''),
                    'nominal_value': getattr(karakter, 'nominal_value', None),
                    'upper_limit': getattr(karakter, 'upper_limit', None),
                    'lower_limit': getattr(karakter, 'lower_limit', None),
                    'tooling': karakter.tooling or '',
                    'bp_zone': karakter.bp_zone or ''
                }

        return lot_data


# Test ve örnek kullanım
def test_data_source_manager():
    """Data Source Manager'ı test et"""
    print("=== DATA SOURCE MANAGER TEST ===")

    # Test klasörü oluştur
    test_folder = Path.home() / "Desktop" / "test_data_sources"
    test_folder.mkdir(exist_ok=True)

    # Manager oluştur
    manager = DataSourceManager()

    # Test için veri kaynakları ekle
    json_source = JSONDataSource(str(test_folder / "test.json"))
    excel_source = ExcelDataSource(str(test_folder / "test.xlsx"))

    manager.add_source("json", json_source, is_primary=True)
    manager.add_source("excel", excel_source)

    # Test verisi
    test_data = {
        'part_quantity': 3,
        'part_numbers': {'1': 'ABC123', '2': 'DEF456', '3': 'GHI789'},
        'notes': 'Test lot detayı',
        'actual_value': '25.4/25.6/25.5'
    }

    # Veri kaydet
    identifier = "test_dimension_KN001"
    success = manager.save_data(identifier, test_data, sync_all=True)
    print(f"Veri kaydetme: {'✓' if success else '✗'}")

    # Veri yükle
    loaded_data = manager.load_data(identifier)
    print(f"Veri yükleme: {'✓' if loaded_data else '✗'}")
    print(f"Yüklenen veri: {loaded_data}")

    # Tüm verileri listele
    all_data = manager.list_all_available_data()
    print(f"Mevcut veriler: {all_data}")

    # Format dönüştürme testi
    print("\n=== FORMAT DÖNÜŞTÜRME TEST ===")

    adapter = LotDataAdapter()

    # IRS_YAZICI formatından standart formata
    irs_data = {
        'part_quantities': {identifier: '3'},
        'part_numbers': {identifier: {'1': 'ABC123', '2': 'DEF456'}},
        'lot_notes': {identifier: 'IRS_YAZICI test notu'},
        'actual_values': {identifier: '25.4/25.6'}
    }

    standardized = adapter.from_irs_yazici_format(irs_data)
    print(f"IRS_YAZICI -> Standart: {standardized}")

    # Geri dönüştürme
    back_to_irs = adapter.to_irs_yazici_format(standardized)
    print(f"Standart -> IRS_YAZICI: {back_to_irs}")

    print("Test tamamlandı")


if __name__ == "__main__":
    test_data_source_manager()