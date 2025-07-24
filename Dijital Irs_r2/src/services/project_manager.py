"""
Project Manager Service - Proje klasör yapısı ve bilgi yönetimi
services/project_manager.py
"""
import os
import json
import shutil
import datetime
import subprocess
import sys
from pathlib import Path
from typing import Dict, Tuple, Optional, Any
from tkinter import messagebox


class ProjectManager:
    """
    Proje klasör yapısı oluşturma ve yönetimi
    Desktop/Report/{project_type}/{part_number}/{operation_number}/{serial_number}/ yapısı
    """

    def __init__(self):
        self.project_info = {}
        self.project_folder = None
        self.project_file = None

    def create_project_structure(self,
                                 project_type: str,
                                 part_number: str,
                                 operation_number: str,
                                 serial_number: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Proje klasör yapısını oluşturur

        Args:
            project_type: Proje tipi
            part_number: Parça numarası
            operation_number: Operasyon numarası
            serial_number: Seri numarası

        Returns:
            Tuple[bool, str, str]: (başarılı_mı, klasör_yolu, hata_mesajı)
        """
        try:
            # Girdi validasyonu
            if not all([project_type, part_number, operation_number, serial_number]):
                return False, None, "Tüm alanlar doldurulmalıdır"

            # Proje bilgilerini sakla
            self.project_info = {
                "PROJE_TIPI": project_type,
                "PARCA_NUMARASI": part_number,
                "OPERASYON_NO": operation_number,
                "SERI_NO": serial_number,
                "OLUSTURMA_TARIHI": datetime.datetime.now().isoformat(),
                "SON_GUNCELLEME": datetime.datetime.now().isoformat()
            }

            # Desktop path
            desktop_path = Path.home() / "Desktop"

            # Klasör yapısını oluştur
            folder_path = (desktop_path / "Report" / project_type /
                           part_number / operation_number / serial_number)

            # Klasör oluştur
            folder_path.mkdir(parents=True, exist_ok=True)

            self.project_folder = str(folder_path)

            # Proje bilgilerini JSON dosyasına kaydet
            self._save_project_info()

            print(f"✓ Proje klasörü oluşturuldu: {folder_path}")
            return True, str(folder_path), None

        except Exception as e:
            error_msg = f"Proje klasörü oluşturma hatası: {str(e)}"
            print(f"HATA: {error_msg}")
            return False, None, error_msg

    def load_existing_project(self,
                              project_type: str,
                              part_number: str,
                              operation_number: str,
                              serial_number: str) -> Tuple[bool, Optional[str]]:
        """
        Mevcut proje klasörünü yükler

        Returns:
            Tuple[bool, str]: (bulundu_mu, klasör_yolu)
        """
        try:
            # Desktop path
            desktop_path = Path.home() / "Desktop"

            # Klasör yolunu oluştur
            folder_path = (desktop_path / "Report" / project_type /
                           part_number / operation_number / serial_number)

            if folder_path.exists():
                self.project_folder = str(folder_path)

                # Mevcut proje bilgilerini yükle
                self._load_project_info()

                print(f"✓ Mevcut proje yüklendi: {folder_path}")
                return True, str(folder_path)
            else:
                print(f"⚠ Proje klasörü bulunamadı: {folder_path}")
                return False, None

        except Exception as e:
            print(f"HATA: Proje yükleme hatası: {str(e)}")
            return False, None

    def copy_word_file_to_project(self, source_file_path: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Word dosyasını proje klasörüne kopyalar

        Args:
            source_file_path: Kaynak Word dosyası yolu

        Returns:
            Tuple[bool, str, str]: (başarılı_mı, hedef_dosya_yolu, hata_mesajı)
        """
        try:
            if not self.project_folder:
                return False, None, "Proje klasörü oluşturulmamış"

            if not os.path.exists(source_file_path):
                return False, None, "Kaynak dosya bulunamadı"

            # Hedef dosya adını oluştur
            source_filename = os.path.basename(source_file_path)
            name_without_ext = os.path.splitext(source_filename)[0]
            extension = os.path.splitext(source_filename)[1]

            # Seri numarası ile dosya adını oluştur
            serial_no = self.project_info.get("SERI_NO", "")
            target_filename = f"{serial_no}_{name_without_ext}_original{extension}"
            target_path = os.path.join(self.project_folder, target_filename)

            # Dosyayı kopyala
            shutil.copy2(source_file_path, target_path)

            # Proje bilgilerini güncelle
            self.project_info["WORD_DOSYASI"] = target_filename
            self.project_info["KAYNAK_DOSYA"] = source_file_path
            self.project_info["SON_GUNCELLEME"] = datetime.datetime.now().isoformat()

            self._save_project_info()

            print(f"✓ Word dosyası kopyalandı: {target_path}")
            return True, target_path, None

        except Exception as e:
            error_msg = f"Dosya kopyalama hatası: {str(e)}"
            print(f"HATA: {error_msg}")
            return False, None, error_msg

    def get_project_files(self) -> Dict[str, str]:
        """
        Proje klasöründeki dosyaları listeler

        Returns:
            Dict[str, str]: Dosya tipleri ve yolları
        """
        if not self.project_folder:
            return {}

        files = {}
        try:
            folder_path = Path(self.project_folder)

            for file_path in folder_path.iterdir():
                if file_path.is_file():
                    extension = file_path.suffix.lower()

                    if extension == '.docx':
                        if 'original' in file_path.name:
                            files['original_word'] = str(file_path)
                        elif 'report' in file_path.name or 'rapor' in file_path.name:
                            files['report_word'] = str(file_path)
                        else:
                            files['word_file'] = str(file_path)
                    elif extension == '.xlsx':
                        files['excel_file'] = str(file_path)
                    elif extension == '.txt':
                        if 'lot_details' in file_path.name:
                            files['lot_details'] = str(file_path)
                        else:
                            files['text_file'] = str(file_path)
                    elif extension == '.pdf':
                        files['pdf_file'] = str(file_path)
                    elif extension == '.json':
                        if file_path.name == 'project_info.json':
                            files['project_info'] = str(file_path)
                        else:
                            files['json_file'] = str(file_path)

            return files

        except Exception as e:
            print(f"HATA: Dosya listeleme hatası: {str(e)}")
            return {}

    def open_project_folder(self) -> bool:
        """
        Proje klasörünü dosya gezgininde açar

        Returns:
            bool: Başarılı mı
        """
        if not self.project_folder or not os.path.exists(self.project_folder):
            return False

        try:
            if os.name == 'nt':  # Windows
                os.startfile(self.project_folder)
            elif sys.platform == 'darwin':  # macOS
                subprocess.call(['open', self.project_folder])
            else:  # Linux
                subprocess.call(['xdg-open', self.project_folder])

            print(f"✓ Klasör açıldı: {self.project_folder}")
            return True

        except Exception as e:
            print(f"HATA: Klasör açma hatası: {str(e)}")
            return False

    def _save_project_info(self):
        """Proje bilgilerini JSON dosyasına kaydeder"""
        if not self.project_folder:
            return

        try:
            project_file = os.path.join(self.project_folder, "project_info.json")

            with open(project_file, 'w', encoding='utf-8') as f:
                json.dump(self.project_info, f, indent=2, ensure_ascii=False)

            self.project_file = project_file
            print(f"✓ Proje bilgileri kaydedildi: {project_file}")

        except Exception as e:
            print(f"HATA: Proje bilgileri kaydetme hatası: {str(e)}")

    def _load_project_info(self):
        """Proje bilgilerini JSON dosyasından yükler"""
        if not self.project_folder:
            return

        try:
            project_file = os.path.join(self.project_folder, "project_info.json")

            if os.path.exists(project_file):
                with open(project_file, 'r', encoding='utf-8') as f:
                    self.project_info = json.load(f)

                self.project_file = project_file
                print(f"✓ Proje bilgileri yüklendi: {project_file}")

        except Exception as e:
            print(f"HATA: Proje bilgileri yükleme hatası: {str(e)}")

    def get_project_info(self) -> Dict[str, Any]:
        """Proje bilgilerini döner"""
        return self.project_info.copy()

    def update_project_info(self, **kwargs):
        """Proje bilgilerini günceller"""
        self.project_info.update(kwargs)
        self.project_info["SON_GUNCELLEME"] = datetime.datetime.now().isoformat()
        self._save_project_info()

    def get_project_folder(self) -> Optional[str]:
        """Proje klasör yolunu döner"""
        return self.project_folder

    def create_backup(self, file_path: str) -> Optional[str]:
        """
        Dosyanın yedeğini oluşturur

        Args:
            file_path: Yedeklenecek dosya yolu

        Returns:
            str: Yedek dosya yolu
        """
        if not self.project_folder:
            return None

        try:
            filename = os.path.basename(file_path)
            name_without_ext = os.path.splitext(filename)[0]
            extension = os.path.splitext(filename)[1]

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{name_without_ext}_backup_{timestamp}{extension}"
            backup_path = os.path.join(self.project_folder, backup_filename)

            shutil.copy2(file_path, backup_path)

            print(f"✓ Yedek oluşturuldu: {backup_path}")
            return backup_path

        except Exception as e:
            print(f"HATA: Yedek oluşturma hatası: {str(e)}")
            return None


# Test fonksiyonu
def test_project_manager():
    """Project Manager'ı test eder"""
    print("=== PROJECT MANAGER TEST ===")

    pm = ProjectManager()

    # Test 1: Proje oluşturma
    success, folder, error = pm.create_project_structure(
        "TestProject",
        "TP001",
        "OP10",
        "SN001"
    )

    if success:
        print(f"✓ Proje oluşturuldu: {folder}")

        # Test 2: Klasör açma
        if pm.open_project_folder():
            print("✓ Klasör açıldı")

        # Test 3: Proje bilgileri
        info = pm.get_project_info()
        print(f"✓ Proje bilgileri: {info}")

        # Test 4: Dosya listesi
        files = pm.get_project_files()
        print(f"✓ Proje dosyaları: {files}")

    else:
        print(f"✗ Proje oluşturma hatası: {error}")

    print("Test tamamlandı")


if __name__ == "__main__":
    test_project_manager()