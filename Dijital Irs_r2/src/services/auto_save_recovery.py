"""
Otomatik Kaydetme ve Veri Kurtarma Sistemi
services/auto_save_recovery.py
"""
import os
import json
import pickle
import time
import threading
import atexit
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from .data_processor import TeknikResimKarakteri

class AutoSaveRecoveryService:
    """
    Otomatik kaydetme ve veri kurtarma servisi
    - Her 30 saniyede bir otomatik kaydet
    - Program kapanınca acil kaydet
    - Çökme durumunda veri kurtarma
    """
    
    def __init__(self, save_directory: str = None):
        # Kaydetme klasörü
        if save_directory is None:
            save_directory = os.path.join(os.path.expanduser("~"), "TeknikResim_AutoSave")
        
        self.save_directory = Path(save_directory)
        self.save_directory.mkdir(exist_ok=True)
        
        # Otomatik kaydetme ayarları
        self.auto_save_interval = 30  # 30 saniye
        self.auto_save_enabled = False
        self.auto_save_thread = None
        
        # Veri depolama
        self.current_data = {
            'karakterler': [],
            'last_save_time': None,
            'session_start': datetime.now().isoformat(),
            'measurement_count': 0
        }
        
        # Program kapatılırken acil kaydet
        atexit.register(self.emergency_save)
        
        print(f"📁 Otomatik kaydetme klasörü: {self.save_directory}")
    
    def start_auto_save(self):
        """Otomatik kaydetmeyi başlatır"""
        if not self.auto_save_enabled:
            self.auto_save_enabled = True
            self.auto_save_thread = threading.Thread(target=self._auto_save_loop, daemon=True)
            self.auto_save_thread.start()
            print("🔄 Otomatik kaydetme başlatıldı (30 saniyede bir)")
    
    def stop_auto_save(self):
        """Otomatik kaydetmeyi durdurur"""
        self.auto_save_enabled = False
        if self.auto_save_thread:
            self.auto_save_thread.join(timeout=1)
        print("⏹ Otomatik kaydetme durduruldu")
    
    def _auto_save_loop(self):
        """Arka planda otomatik kaydetme döngüsü"""
        while self.auto_save_enabled:
            try:
                time.sleep(self.auto_save_interval)
                if self.auto_save_enabled and self.current_data['karakterler']:
                    self._save_data('auto')
            except Exception as e:
                print(f"⚠ Otomatik kaydetme hatası: {e}")
    
    def update_data(self, karakterler: List[TeknikResimKarakteri]):
        """Mevcut veriyi günceller"""
        try:
            # Karakterleri serializable formata çevir
            serializable_data = []
            measurement_count = 0
            
            for k in karakterler:
                karakter_data = {
                    'item_no': k.item_no,
                    'nominal': k.nominal,
                    'actual': k.actual,
                    'upper_limit': getattr(k, 'upper_limit', None),
                    'lower_limit': getattr(k, 'lower_limit', None),
                    'tolerans': getattr(k, 'tolerans', None),
                    'unit': getattr(k, 'unit', None),
                    'feature_type': getattr(k, 'feature_type', None)
                }
                serializable_data.append(karakter_data)
                
                if k.actual:
                    measurement_count += 1
            
            self.current_data.update({
                'karakterler': serializable_data,
                'last_update_time': datetime.now().isoformat(),
                'measurement_count': measurement_count
            })
            
            print(f"📊 Veri güncellendi: {len(karakterler)} karakter, {measurement_count} ölçüm")
            
        except Exception as e:
            print(f"⚠ Veri güncelleme hatası: {e}")
    
    def _save_data(self, save_type: str = 'manual'):
        """Veriyi dosyaya kaydeder"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # JSON formatında kaydet (insan tarafından okunabilir)
            json_file = self.save_directory / f"backup_{save_type}_{timestamp}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_data, f, indent=2, ensure_ascii=False)
            
            # Pickle formatında da kaydet (hızlı yükleme için)
            pickle_file = self.save_directory / f"backup_{save_type}_{timestamp}.pkl"
            with open(pickle_file, 'wb') as f:
                pickle.dump(self.current_data, f)
            
            # En son dosyaları da güncelle
            latest_json = self.save_directory / "latest_backup.json"
            latest_pickle = self.save_directory / "latest_backup.pkl"
            
            with open(latest_json, 'w', encoding='utf-8') as f:
                json.dump(self.current_data, f, indent=2, ensure_ascii=False)
            with open(latest_pickle, 'wb') as f:
                pickle.dump(self.current_data, f)
            
            self.current_data['last_save_time'] = datetime.now().isoformat()
            
            if save_type == 'auto':
                print(f"💾 Otomatik kaydetme: {self.current_data['measurement_count']} ölçüm")
            else:
                print(f"💾 {save_type.title()} kaydetme tamamlandı: {json_file.name}")
            
            # Eski yedekleri temizle (10'dan fazla varsa)
            self._cleanup_old_backups()
            
        except Exception as e:
            print(f"⚠ Kaydetme hatası: {e}")
    
    def manual_save(self):
        """Manuel kaydetme"""
        if self.current_data['karakterler']:
            self._save_data('manual')
            return True
        else:
            print("⚠ Kaydedilecek veri yok")
            return False
    
    def emergency_save(self):
        """Acil durum kaydetmesi (program kapanırken)"""
        if self.current_data['karakterler']:
            try:
                self.stop_auto_save()  # Otomatik kaydetmeyi durdur
                self._save_data('emergency')
                print("🚨 Acil durum kaydetmesi tamamlandı")
            except Exception as e:
                print(f"🚨 Acil durum kaydetme hatası: {e}")
    
    def _cleanup_old_backups(self):
        """Eski yedekleri temizler (disk alanı için)"""
        try:
            backup_files = list(self.save_directory.glob("backup_*.json"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Son 10 dosyayı tut, geri kalanını sil
            for old_file in backup_files[10:]:
                try:
                    old_file.unlink()
                    # Aynı zamanda pickle dosyasını da sil
                    pickle_file = old_file.with_suffix('.pkl')
                    if pickle_file.exists():
                        pickle_file.unlink()
                except Exception as e:
                    print(f"⚠ Eski dosya silinemedi {old_file.name}: {e}")
                    
        except Exception as e:
            print(f"⚠ Eski dosya temizleme hatası: {e}")
    
    def list_available_backups(self) -> List[Dict[str, Any]]:
        """Mevcut yedekleri listeler"""
        backups = []
        try:
            backup_files = list(self.save_directory.glob("backup_*.json"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            for backup_file in backup_files:
                try:
                    stat = backup_file.stat()
                    
                    # Dosya bilgilerini oku
                    with open(backup_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    backup_info = {
                        'filename': backup_file.name,
                        'full_path': str(backup_file),
                        'size_mb': stat.st_size / (1024 * 1024),
                        'modified_time': datetime.fromtimestamp(stat.st_mtime),
                        'measurement_count': data.get('measurement_count', 0),
                        'character_count': len(data.get('karakterler', [])),
                        'session_start': data.get('session_start', 'Bilinmiyor'),
                        'save_type': backup_file.stem.split('_')[1] if '_' in backup_file.stem else 'unknown'
                    }
                    backups.append(backup_info)
                    
                except Exception as e:
                    print(f"⚠ Backup dosyası okunamadı {backup_file.name}: {e}")
            
        except Exception as e:
            print(f"⚠ Backup listesi oluşturulamadı: {e}")
        
        return backups
    
    def recover_data(self, backup_filename: str = None) -> List[TeknikResimKarakteri]:
        """Verilen dosyadan veri kurtarır"""
        try:
            if backup_filename is None:
                # En son yedekten kurtar
                latest_file = self.save_directory / "latest_backup.json"
                if not latest_file.exists():
                    raise Exception("En son yedek dosyası bulunamadı")
                backup_file = latest_file
            else:
                backup_file = self.save_directory / backup_filename
                if not backup_file.exists():
                    raise Exception(f"Yedek dosyası bulunamadı: {backup_filename}")
            
            # JSON dosyasını oku
            with open(backup_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # TeknikResimKarakteri objelerini yeniden oluştur
            karakterler = []
            for k_data in data.get('karakterler', []):
                karakter = TeknikResimKarakteri(
                    item_no=k_data.get('item_no', ''),
                    nominal=k_data.get('nominal'),
                    tolerans=k_data.get('tolerans'),
                    unit=k_data.get('unit')
                )
                
                # Diğer özellikleri ekle
                karakter.actual = k_data.get('actual')
                karakter.upper_limit = k_data.get('upper_limit')
                karakter.lower_limit = k_data.get('lower_limit')
                karakter.feature_type = k_data.get('feature_type')
                
                karakterler.append(karakter)
            
            print(f"✓ Veri kurtarıldı: {len(karakterler)} karakter, {data.get('measurement_count', 0)} ölçüm")
            print(f"📅 Oturum zamanı: {data.get('session_start', 'Bilinmiyor')}")
            
            return karakterler
            
        except Exception as e:
            print(f"⚠ Veri kurtarma hatası: {e}")
            return []
    
    def export_to_excel(self, karakterler: List[TeknikResimKarakteri], filename: str = None):
        """Veriyi Excel'e aktarır"""
        try:
            import pandas as pd
            
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = self.save_directory / f"measurement_data_{timestamp}.xlsx"
            
            # DataFrame oluştur
            data_rows = []
            for k in karakterler:
                row = {
                    'ITEM NO': k.item_no,
                    'NOMINAL': k.nominal,
                    'ACTUAL': k.actual,
                    'UPPER LIMIT': getattr(k, 'upper_limit', None),
                    'LOWER LIMIT': getattr(k, 'lower_limit', None),
                    'TOLERANS': getattr(k, 'tolerans', None),
                    'UNIT': getattr(k, 'unit', None),
                    'FEATURE TYPE': getattr(k, 'feature_type', None),
                    'DURUM': 'Ölçüldü' if k.actual else 'Bekliyor'
                }
                data_rows.append(row)
            
            df = pd.DataFrame(data_rows)
            
            # Excel'e kaydet
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Measurements', index=False)
                
                # İstatistik sayfası ekle
                stats_data = {
                    'Metrik': ['Toplam Karakter', 'Ölçülen', 'Bekleyen', 'Tamamlanma %'],
                    'Değer': [
                        len(karakterler),
                        len([k for k in karakterler if k.actual]),
                        len([k for k in karakterler if not k.actual]),
                        f"{len([k for k in karakterler if k.actual]) / len(karakterler) * 100:.1f}%" if karakterler else "0%"
                    ]
                }
                stats_df = pd.DataFrame(stats_data)
                stats_df.to_excel(writer, sheet_name='İstatistikler', index=False)
            
            print(f"📊 Excel dosyası oluşturuldu: {filename}")
            return str(filename)
            
        except ImportError:
            print("⚠ pandas kütüphanesi bulunamadı. Excel export için: pip install pandas openpyxl")
            return None
        except Exception as e:
            print(f"⚠ Excel export hatası: {e}")
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """Mevcut durumu döner"""
        return {
            'auto_save_enabled': self.auto_save_enabled,
            'save_directory': str(self.save_directory),
            'character_count': len(self.current_data['karakterler']),
            'measurement_count': self.current_data['measurement_count'],
            'last_save_time': self.current_data.get('last_save_time'),
            'session_start': self.current_data.get('session_start')
        }

# Ana uygulamaya entegrasyon için helper sınıf
class CrashSafeDataManager:
    """
    Ana uygulama için çökme güvenli veri yöneticisi
    """
    
    def __init__(self, karakterler: List[TeknikResimKarakteri] = None):
        self.auto_save = AutoSaveRecoveryService()
        self.karakterler = karakterler or []
        
        # Otomatik kaydetmeyi başlat
        if self.karakterler:
            self.auto_save.update_data(self.karakterler)
        self.auto_save.start_auto_save()
        
        print("🛡 Çökme güvenli veri yöneticisi aktif")
    
    def update_measurement(self, item_no: str, actual_value: str):
        """Bir ölçüm değerini günceller ve otomatik kaydeder"""
        try:
            for karakter in self.karakterler:
                if karakter.item_no == item_no:
                    karakter.actual = actual_value
                    self.auto_save.update_data(self.karakterler)
                    print(f"📝 {item_no}: {actual_value} (otomatik kaydedildi)")
                    return True
            print(f"⚠ Karakter bulunamadı: {item_no}")
            return False
        except Exception as e:
            print(f"⚠ Ölçüm güncelleme hatası: {e}")
            return False
    
    def manual_save_all(self):
        """Tüm veriyi manuel olarak kaydeder"""
        return self.auto_save.manual_save()
    
    def safe_export_to_word(self, word_service, save_path: str = None):
        """Güvenli Word export (hata durumunda yedek kaydetme)"""
        try:
            # Önce manuel kaydet
            self.auto_save.manual_save()
            
            # Word export dene
            result = word_service.save_with_actual_values(self.karakterler, save_path)
            print("✓ Word export başarılı")
            return result
            
        except Exception as e:
            print(f"⚠ Word export hatası: {e}")
            # Hata durumunda Excel'e kaydet
            excel_file = self.auto_save.export_to_excel(self.karakterler)
            if excel_file:
                print(f"💾 Yedek olarak Excel'e kaydedildi: {excel_file}")
            raise e
    
    def recover_last_session(self):
        """Son oturumu kurtar"""
        recovered_data = self.auto_save.recover_data()
        if recovered_data:
            self.karakterler = recovered_data
            self.auto_save.update_data(self.karakterler)
            return True
        return False
    
    def show_recovery_options(self):
        """Kurtarma seçeneklerini gösterir"""
        backups = self.auto_save.list_available_backups()
        if not backups:
            print("📝 Hiç yedek dosyası bulunamadı")
            return
        
        print("\n📋 Mevcut Yedekler:")
        print("-" * 80)
        for i, backup in enumerate(backups, 1):
            print(f"{i:2}. {backup['filename']}")
            print(f"    📊 {backup['measurement_count']} ölçüm, {backup['character_count']} karakter")
            print(f"    📅 {backup['modified_time'].strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"    📁 {backup['size_mb']:.2f} MB")
            print()
    
    def cleanup(self):
        """Temizlik işlemleri"""
        self.auto_save.stop_auto_save()
        self.auto_save.emergency_save()

# Test fonksiyonu
def test_auto_save_recovery():
    """Otomatik kaydetme ve kurtarma sistemini test eder"""
    print("=== AUTO SAVE RECOVERY TEST ===")
    
    # Test karakterleri oluştur
    from .data_processor import TeknikResimKarakteri
    
    karakterler = [
        TeknikResimKarakteri("KN001", 25.5, "±0.1", "mm"),
        TeknikResimKarakteri("KN002", 30.0, "+0.2/-0.1", "mm"),
        TeknikResimKarakteri("KN003", 45.0, "±0.05", "mm")
    ]
    
    # Test ölçümleri ekle
    karakterler[0].actual = "25.52"
    karakterler[1].actual = "30.1"
    
    # Crash-safe manager test
    manager = CrashSafeDataManager(karakterler)
    
    print("⏱ 5 saniye beklenecek (otomatik kaydetme testi)...")
    time.sleep(5)
    
    # Yeni ölçüm ekle
    manager.update_measurement("KN003", "45.02")
    
    # Manuel kaydet
    manager.manual_save_all()
    
    # Kurtarma seçeneklerini göster
    manager.show_recovery_options()
    
    # Temizlik
    manager.cleanup()
    
    print("✓ Test tamamlandı")

if __name__ == "__main__":
    test_auto_save_recovery()