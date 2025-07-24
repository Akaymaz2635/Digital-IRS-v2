# src/ui/main_window.py
"""
Ana pencere - Component'leri koordine eden temiz ana sınıf
"""
import customtkinter as ctk
import os
import sys
from tkinter import filedialog, messagebox
from typing import List, Optional
import pandas as pd


# Path ayarları
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))  # src klasörünün üstü
sys.path.insert(0, project_root)

# Component importları - Absolute import
try:
    from ui.components.karakter_view import SingleKarakterView
    from ui.components.navigation_panel import NavigationPanel
    from ui.components.document_viewer import DocumentViewer
    from ui.components.stats_panel import StatsPanel
except ImportError:
    # Fallback - Eğer ui klasörü src içindeyse
    sys.path.insert(0, os.path.dirname(current_dir))
    from components.karakter_view import SingleKarakterView
    from components.navigation_panel import NavigationPanel
    from components.document_viewer import DocumentViewer
    from components.stats_panel import StatsPanel

# Servis importları
try:
    from services.word_reader import WordReaderService
    from services.data_processor import DataProcessorService, TeknikResimKarakteri
    from services.word_save_as import WordSaveAsService
except ImportError:
    # Path'i genişlet
    services_path = os.path.join(project_root, 'services')
    if os.path.exists(services_path):
        sys.path.insert(0, project_root)
    
    from services.word_reader import WordReaderService
    from services.data_processor import DataProcessorService, TeknikResimKarakteri
    from services.word_save_as import WordSaveAsService


class NavigableMainWindow(ctk.CTk):
    """Temizlenmiş ana pencere - Component koordinasyonu"""
    
    def __init__(self):
        super().__init__()
        
        # Pencere ayarları
        self.title("Teknik Resim Karakter Okuyucu - Modüler Yapı")
        self.geometry("1400x900")
        
        # Veri
        self.karakterler: List[TeknikResimKarakteri] = []
        self.current_index = 0
        self.current_file_path: Optional[str] = None
        
        # Servisler
        self.word_save_service = WordSaveAsService()
        
        # UI
        self.setup_ui()
        self.setup_keyboard_shortcuts()
    
    def setup_ui(self):
        """Ana UI yapısını oluşturur"""
        # Grid ayarları
        self._configure_grid()
        
        # UI bölümlerini oluştur
        self._create_top_panel()
        self._create_main_content()
        self._create_bottom_panel()
    
    def _configure_grid(self):
        """Grid konfigürasyonu"""
        self.grid_columnconfigure(0, weight=1)  # Sol panel
        self.grid_columnconfigure(1, weight=1)  # Sağ panel
        self.grid_rowconfigure(1, weight=1)     # Ana içerik
    
    def _create_top_panel(self):
        """Üst panel - dosya işlemleri"""
        top_frame = ctk.CTkFrame(self)
        top_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        
        # Dosya seçme alanı
        self._create_file_selection(top_frame)
    
    def _create_file_selection(self, parent):
        """Dosya seçme UI'ı"""
        # Dosya seç butonu
        self.file_button = ctk.CTkButton(
            parent,
            text="Word Dosyası Seç",
            command=self.select_file,
            height=40,
            font=ctk.CTkFont(size=14)
        )
        self.file_button.pack(side="left", padx=10, pady=10)
        
        # Dosya yolu gösterici
        self.file_path_label = ctk.CTkLabel(
            parent,
            text="Dosya seçilmedi",
            font=ctk.CTkFont(size=12)
        )
        self.file_path_label.pack(side="left", padx=10, pady=10)
        
        # İşle butonu
        self.process_button = ctk.CTkButton(
            parent,
            text="Dosyayı Yükle",
            command=self.process_file,
            height=40,
            font=ctk.CTkFont(size=14),
            state="disabled"
        )
        self.process_button.pack(side="right", padx=10, pady=10)
    
    def _create_main_content(self):
        """Ana içerik alanı"""
        # Sol panel - Karakter görünümü
        self._create_left_panel()
        
        # Sağ panel - Doküman görüntüleyici
        self._create_right_panel()
    
    def _create_left_panel(self):
        """Sol panel - karakter görünümü ve navigasyon"""
        left_frame = ctk.CTkFrame(self)
        left_frame.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=10)
        left_frame.grid_rowconfigure(0, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)
        
        # Karakter görünümü
        self.karakter_view = SingleKarakterView(
            left_frame,
            on_update_callback=self.on_karakter_updated
        )
        self.karakter_view.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 5))
        
        # Navigasyon paneli
        self.navigation_panel = NavigationPanel(
            left_frame,
            on_navigate_callback=self.navigate_to
        )
        self.navigation_panel.grid(row=1, column=0, sticky="ew", padx=10, pady=(5, 10))
    
    def _create_right_panel(self):
        """Sağ panel - doküman görüntüleyici"""
        right_frame = ctk.CTkFrame(self)
        right_frame.grid(row=1, column=1, sticky="nsew", padx=(5, 10), pady=10)
        right_frame.grid_rowconfigure(0, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)
        
        # Doküman görüntüleyici
        self.document_viewer = DocumentViewer(right_frame)
        self.document_viewer.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
    
    def _create_bottom_panel(self):
        """Alt panel - istatistikler ve butonlar"""
        # İstatistik paneli
        self.stats_panel = StatsPanel(
            self,
            on_export_excel=self.export_to_excel,
            on_save_word=self.save_to_word
        )
        self.stats_panel.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
    
    def setup_keyboard_shortcuts(self):
        """Klavye kısayollarını ayarlar"""
        self.bind('<Left>', lambda e: self.navigate_to(self.current_index - 1))
        self.bind('<Right>', lambda e: self.navigate_to(self.current_index + 1))
        self.focus_set()
    
    # Dosya İşlemleri
    def select_file(self):
        """Word dosyası seçme"""
        file_path = filedialog.askopenfilename(
            title="Word Dosyası Seçin",
            filetypes=[
                ("Word Dosyaları", "*.docx *.doc"),
                ("Tüm Dosyalar", "*.*")
            ]
        )
        
        if file_path:
            self.current_file_path = file_path
            file_name = os.path.basename(file_path)
            self.file_path_label.configure(text=f"Seçilen: {file_name}")
            self.process_button.configure(state="normal")
    
    def process_file(self):
        """Dosyayı işler"""
        if not self.current_file_path:
            messagebox.showerror("Hata", "Önce bir dosya seçin!")
            return
        
        try:
            self._show_processing_status("İşleniyor...")
            
            # Veri işleme
            karakterler = self._extract_data_from_file()
            
            if not karakterler:
                messagebox.showwarning("Uyarı", "Geçerli karakter bulunamadı!")
                return
            
            self.karakterler = karakterler
            
            # Servisleri hazırla
            self.word_save_service.load_original_document(self.current_file_path)
            
            # UI'ı güncelle
            self._initialize_ui_with_data()
            
            # Başarı mesajı
            self._show_success_message()
            
        except Exception as e:
            messagebox.showerror("Hata", f"İşleme hatası:\n{str(e)}")
            print(f"İşleme hatası: {e}")
    
    def _extract_data_from_file(self) -> List[TeknikResimKarakteri]:
        """Dosyadan veri çıkarır"""
        # Word servisi
        word_service = WordReaderService()
        
        # DataFrame oluştur
        df = DataProcessorService.from_word_tables(word_service, self.current_file_path)
        
        if df.empty:
            return []
        
        # Model objelerine dönüştür
        data_service = DataProcessorService()
        return data_service.process_dataframe(df)
    
    def _initialize_ui_with_data(self):
        """UI'ı veri ile başlatır"""
        # Dokümanı yükle
        self.document_viewer.load_document(self.current_file_path)
        
        # İlk karakteri göster
        self.current_index = 0
        self.show_current_karakter()
        
        # UI bileşenlerini güncelle
        self.update_navigation()
        self.update_stats()
    
    def _show_processing_status(self, message: str):
        """İşlem durumunu gösterir"""
        self.file_path_label.configure(text=message)
        self.update()
    
    def _show_success_message(self):
        """Başarı mesajını gösterir"""
        file_name = os.path.basename(self.current_file_path)
        self.file_path_label.configure(text=f"✓ Yüklendi: {file_name}")
        
        messagebox.showinfo(
            "Başarılı", 
            f"{len(self.karakterler)} karakter yüklendi!\n\nOk tuşları ile navigate edebilirsiniz."
        )
    
    # Navigasyon İşlemleri
    def show_current_karakter(self):
        """Mevcut karakteri gösterir"""
        if 0 <= self.current_index < len(self.karakterler):
            karakter = self.karakterler[self.current_index]
            self.karakter_view.load_karakter(karakter)
            print(f"Karakter gösteriliyor: {self.current_index + 1}/{len(self.karakterler)} - {karakter.item_no}")
    
    def navigate_to(self, new_index: int):
        """Belirtilen indekse navigate eder"""
        if not self.karakterler:
            return
        
        if 0 <= new_index < len(self.karakterler):
            self.current_index = new_index
            self.show_current_karakter()
            self.update_navigation()
            self.update_stats()
            print(f"Navigate: {self.current_index + 1}/{len(self.karakterler)}")
    
    def update_navigation(self):
        """Navigasyon durumunu günceller"""
        if self.karakterler:
            self.navigation_panel.update_navigation(self.current_index, len(self.karakterler))
    
    def update_stats(self):
        """İstatistikleri günceller"""
        if self.karakterler:
            self.stats_panel.update_stats(self.karakterler, self.current_index)
    
    # Event Handler'lar
    def on_karakter_updated(self, karakter: TeknikResimKarakteri):
        """Karakter güncellendiğinde çağrılır"""
        print(f"Karakter güncellendi: {karakter.item_no} = {karakter.actual}")
        self.update_stats()
    
    # Export İşlemleri
    def save_to_word(self):
        """Ölçüm değerleriyle Word dosyasını kaydetme"""
        if not self.karakterler:
            messagebox.showwarning("Uyarı", "Önce veri yükleyin!")
            return
        
        if not hasattr(self, 'word_save_service') or not self.word_save_service.current_document:
            messagebox.showerror("Hata", "Word servisi hazır değil! Önce dosyayı yükleyin.")
            return
        
        try:
            # İstatistikleri al ve kullanıcıya göster
            stats = self.word_save_service.get_statistics(self.karakterler)
            
            if not self._confirm_word_save(stats):
                return
            
            # Progress göstergesi
            original_text = self.stats_panel.show_progress_message("Word dosyası kaydediliyor...")
            
            # Word kaydetme işlemi
            saved_path = self.word_save_service.save_with_actual_values(self.karakterler)
            
            # Başarı mesajı ve dosya açma seçeneği
            self._handle_word_save_success(saved_path, stats)
            
            # UI'ı eski haline getir
            self.stats_panel.restore_stats_text(original_text)
            
        except Exception as e:
            self._handle_word_save_error(e)
    
    def _confirm_word_save(self, stats: dict) -> bool:
        """Word kaydetme onayı alır"""
        info_msg = f"""Word dosyasına ölçüm değerleri aktarılacak:

📊 İstatistikler:
• Toplam karakter: {stats['total']}
• Ölçülen karakter: {stats['measured']}
• Bekleyen karakter: {stats['unmeasured']}
• Tamamlanma oranı: %{stats['completion_percentage']:.1f}

Devam etmek istiyor musunuz?"""
        
        return messagebox.askyesno("Word'e Kaydet", info_msg)
    
    def _handle_word_save_success(self, saved_path: str, stats: dict):
        """Word kaydetme başarısını işler"""
        success_msg = f"""✅ Word dosyası başarıyla kaydedildi!

📁 Konum: {saved_path}

📊 Aktarılan veriler:
• {stats['measured']} ölçüm değeri Word tablosuna yazıldı
• Tolerans dışı değerler sarı highlight ile işaretlendi
• Orijinal formatlar korundu

Kaydedilen dosyayı açmak istiyor musunuz?"""
        
        if messagebox.askyesno("Başarılı", success_msg):
            self._open_file(saved_path)
    
    def _handle_word_save_error(self, error: Exception):
        """Word kaydetme hatasını işler"""
        error_msg = f"Word kaydetme hatası:\n{str(error)}"
        messagebox.showerror("Hata", error_msg)
        print(f"Word kaydetme hatası: {error}")
        
        # UI'ı eski haline getir
        if self.current_file_path:
            file_name = os.path.basename(self.current_file_path)
            self.file_path_label.configure(text=f"✓ Yüklendi: {file_name}")
    
    def _open_file(self, file_path: str):
        """Dosyayı sistem varsayılan programında açar"""
        try:
            os.startfile(file_path)  # Windows
        except:
            try:
                os.system(f'open "{file_path}"')  # macOS
            except:
                os.system(f'xdg-open "{file_path}"')  # Linux
    
    def export_to_excel(self):
        """Sonuçları Excel'e aktarır"""
        if not self.karakterler:
            messagebox.showwarning("Uyarı", "Önce veri yükleyin!")
            return
        
        try:
            # Excel dosyası yolu seç
            file_path = filedialog.asksaveasfilename(
                title="Excel Dosyası Kaydet",
                defaultextension=".xlsx",
                filetypes=[("Excel Dosyaları", "*.xlsx"), ("Tüm Dosyalar", "*.*")]
            )
            
            if not file_path:
                return
            
            # Progress göstergesi
            original_text = self.stats_panel.show_progress_message("Excel dosyası oluşturuluyor...")
            
            # Excel'e aktar
            self._create_excel_file(file_path)
            
            # Başarı mesajı
            messagebox.showinfo("Başarılı", f"Veriler Excel'e aktarıldı:\n{file_path}")
            
            # UI'ı eski haline getir
            self.stats_panel.restore_stats_text(original_text)
            
        except Exception as e:
            messagebox.showerror("Hata", f"Excel aktarım hatası:\n{str(e)}")
    
    def _create_excel_file(self, file_path: str):
        """Excel dosyası oluşturur"""
        # DataFrame oluştur
        data = []
        for karakter in self.karakterler:
            row_data = {
                'Item No': karakter.item_no,
                'Dimension': karakter.dimension,
                'Tooling': karakter.tooling,
                'BP Zone': karakter.bp_zone,
                'Remarks': karakter.remarks,
                'Inspection Level': karakter.inspection_level,
                'Actual': karakter.actual,
                'Badge': karakter.badge
            }
            
            # Parsed dimension bilgileri varsa ekle
            if hasattr(karakter, 'tolerance_type') and karakter.tolerance_type:
                row_data['Tolerance Type'] = karakter.tolerance_type
            if hasattr(karakter, 'nominal_value') and karakter.nominal_value is not None:
                row_data['Nominal Value'] = karakter.nominal_value
            if hasattr(karakter, 'upper_limit') and karakter.upper_limit is not None:
                row_data['Upper Limit'] = karakter.upper_limit
            if hasattr(karakter, 'lower_limit') and karakter.lower_limit is not None:
                row_data['Lower Limit'] = karakter.lower_limit
            
            data.append(row_data)
        
        # Excel'e kaydet
        df = pd.DataFrame(data)
        df.to_excel(file_path, index=False)
    
    # Yardımcı Metodlar
    def get_current_karakter(self) -> Optional[TeknikResimKarakteri]:
        """Mevcut karakteri döner"""
        if 0 <= self.current_index < len(self.karakterler):
            return self.karakterler[self.current_index]
        return None
    
    def get_karakterler(self) -> List[TeknikResimKarakteri]:
        """Tüm karakterleri döner"""
        return self.karakterler.copy()
    
    def is_data_loaded(self) -> bool:
        """Veri yüklenip yüklenmediğini kontrol eder"""
        return len(self.charakterler) > 0


# Ana çalıştırma
def main():
    """Ana uygulama fonksiyonu"""
    # CustomTkinter tema ayarları
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    # Uygulamayı başlat
    app = NavigableMainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()