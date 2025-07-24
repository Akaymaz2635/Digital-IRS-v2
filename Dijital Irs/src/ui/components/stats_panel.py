# src/ui/components/stats_panel.py
"""
İstatistik paneli ve aksiyon butonları component'i
"""
import customtkinter as ctk
from typing import List, Optional, Callable
import sys
import os

# Servis importları için path ekleme
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from services.data_processor import TeknikResimKarakteri


class StatsPanel(ctk.CTkFrame):
    """İstatistikler ve kaydetme butonları paneli"""
    
    def __init__(self, parent, 
                 on_export_excel: Optional[Callable[[], None]] = None,
                 on_save_word: Optional[Callable[[], None]] = None):
        super().__init__(parent)
        
        self.on_export_excel = on_export_excel
        self.on_save_word = on_save_word
        self.current_stats = {}
        
        self.setup_ui()
    
    def setup_ui(self):
        """UI'ı oluşturur"""
        # İstatistik labelı
        self.stats_label = ctk.CTkLabel(
            self,
            text="İstatistikler burada görünecek",
            font=ctk.CTkFont(size=12)
        )
        self.stats_label.pack(side="left", padx=10, pady=10)
        
        # Kaydetme butonları
        self._create_action_buttons()
    
    def _create_action_buttons(self):
        """Aksiyon butonlarını oluşturur"""
        save_frame = ctk.CTkFrame(self, fg_color="transparent")
        save_frame.pack(side="right", padx=10, pady=5)
        
        # Word Save As butonu
        self.word_save_button = ctk.CTkButton(
            save_frame,
            text="📄 Word'e Kaydet",
            command=self._on_word_save_clicked,
            height=30,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#2E8B57",
            hover_color="#228B22",
            state="disabled"
        )
        self.word_save_button.pack(side="right", padx=5)
        
        # Excel export butonu
        self.excel_export_button = ctk.CTkButton(
            save_frame,
            text="📊 Excel'e Aktar",
            command=self._on_excel_export_clicked,
            height=30,
            state="disabled"
        )
        self.excel_export_button.pack(side="right", padx=5)
    
    def update_stats(self, karakterler: List[TeknikResimKarakteri], current_index: int = 0):
        """İstatistikleri günceller"""
        if not karakterler:
            self.stats_label.configure(text="Veri yüklenmedi")
            self._disable_buttons()
            return
        
        # Temel istatistikler
        stats = self._calculate_stats(karakterler, current_index)
        self.current_stats = stats
        
        # İstatistik metnini oluştur
        stats_text = self._format_stats_text(stats)
        self.stats_label.configure(text=stats_text)
        
        # Butonları aktif et
        self._enable_buttons()
    
    def _calculate_stats(self, karakterler: List[TeknikResimKarakteri], current_index: int) -> dict:
        """İstatistikleri hesaplar"""
        total = len(karakterler)
        measured = len([k for k in karakterler if k.actual])
        unmeasured = total - measured
        
        # Tolerance istatistikleri
        tolerance_violations = 0
        tolerance_compliant = 0
        
        for karakter in karakterler:
            if karakter.actual and hasattr(karakter, 'lower_limit') or hasattr(karakter, 'upper_limit'):
                # Basit tolerance kontrolü
                try:
                    actual_float = float(str(karakter.actual).replace(',', '.'))
                    if self._is_within_tolerance(karakter, actual_float):
                        tolerance_compliant += 1
                    else:
                        tolerance_violations += 1
                except:
                    pass  # Sayısal olmayan değerler için pas geç
        
        return {
            'total': total,
            'measured': measured,
            'unmeasured': unmeasured,
            'current_index': current_index,
            'completion_percentage': (measured / total * 100) if total > 0 else 0,
            'tolerance_violations': tolerance_violations,
            'tolerance_compliant': tolerance_compliant
        }
    
    def _is_within_tolerance(self, karakter: TeknikResimKarakteri, actual_value: float) -> bool:
        """Tolerance kontrolü yapar"""
        has_lower = hasattr(karakter, 'lower_limit') and karakter.lower_limit is not None
        has_upper = hasattr(karakter, 'upper_limit') and karakter.upper_limit is not None
        
        if not has_lower and not has_upper:
            return True  # Tolerance tanımlanmamış
        
        if has_lower and has_upper:
            return karakter.lower_limit <= actual_value <= karakter.upper_limit
        elif has_upper:
            return actual_value <= karakter.upper_limit
        elif has_lower:
            return actual_value >= karakter.lower_limit
        
        return True
    
    def _format_stats_text(self, stats: dict) -> str:
        """İstatistik metnini formatlar"""
        current_info = f"Şu an: {stats['current_index'] + 1}/{stats['total']}"
        basic_stats = f"Toplam: {stats['total']} | Ölçülen: {stats['measured']} | Bekleyen: {stats['unmeasured']}"
        completion = f"Tamamlanan: %{stats['completion_percentage']:.1f}"
        
        stats_text = f"{current_info} | {basic_stats} | {completion}"
        
        # Tolerance bilgileri varsa ekle
        if stats['tolerance_violations'] > 0 or stats['tolerance_compliant'] > 0:
            tolerance_info = f" | Tolerance: ✅{stats['tolerance_compliant']} ❌{stats['tolerance_violations']}"
            stats_text += tolerance_info
        
        return stats_text
    
    def _enable_buttons(self):
        """Butonları aktif eder"""
        self.excel_export_button.configure(state="normal")
        self.word_save_button.configure(state="normal")
    
    def _disable_buttons(self):
        """Butonları deaktif eder"""
        self.excel_export_button.configure(state="disabled")
        self.word_save_button.configure(state="disabled")
    
    def _on_excel_export_clicked(self):
        """Excel export butonuna tıklandığında"""
        if self.on_export_excel:
            self.on_export_excel()
    
    def _on_word_save_clicked(self):
        """Word save butonuna tıklandığında"""
        if self.on_save_word:
            self.on_save_word()
    
    def set_excel_callback(self, callback: Callable[[], None]):
        """Excel export callback'ini ayarlar"""
        self.on_export_excel = callback
    
    def set_word_callback(self, callback: Callable[[], None]):
        """Word save callback'ini ayarlar"""
        self.on_save_word = callback
    
    def get_current_stats(self) -> dict:
        """Mevcut istatistikleri döner"""
        return self.current_stats.copy()
    
    def show_progress_message(self, message: str):
        """İşlem sırasında mesaj gösterir"""
        original_text = self.stats_label.cget("text")
        self.stats_label.configure(text=message)
        self.update()
        return original_text
    
    def restore_stats_text(self, text: str):
        """İstatistik metnini geri yükler"""
        self.stats_label.configure(text=text)
    
    def add_custom_button(self, text: str, command: Callable[[], None], **button_kwargs):
        """Özel buton ekler"""
        # Buton frame'ini al
        save_frame = None
        for child in self.winfo_children():
            if isinstance(child, ctk.CTkFrame):
                save_frame = child
                break
        
        if save_frame:
            custom_button = ctk.CTkButton(
                save_frame,
                text=text,
                command=command,
                height=30,
                **button_kwargs
            )
            custom_button.pack(side="right", padx=5)
            return custom_button
        
        return None