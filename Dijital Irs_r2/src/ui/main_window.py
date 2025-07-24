# src/ui/main_window.py
"""
Enhanced Ana pencere - Project Manager ve Lot Detail Manager entegreli
Tab-based UI ile modern yapı
"""
import customtkinter as ctk
import os
import sys
from tkinter import filedialog, messagebox
from typing import List, Optional
import pandas as pd

# Path ayarları
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

# Component importları
try:
    from ui.components.karakter_view import SingleKarakterView
    from ui.components.navigation_panel import NavigationPanel
    from ui.components.document_viewer import DocumentViewer
    from ui.components.stats_panel import StatsPanel
except ImportError:
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
    from services.project_manager import ProjectManager
    from services.lot_detail_manager import LotDetailManager
    from services.auto_save_recovery import AutoSaveRecoveryService
except ImportError:
    services_path = os.path.join(project_root, 'services')
    if os.path.exists(services_path):
        sys.path.insert(0, project_root)

    from services.word_reader import WordReaderService
    from services.data_processor import DataProcessorService, TeknikResimKarakteri
    from services.word_save_as import WordSaveAsService
    from services.project_manager import ProjectManager
    from services.lot_detail_manager import LotDetailManager
    from services.auto_save_recovery import AutoSaveRecoveryService


class ProjectInfoTab(ctk.CTkFrame):
    """Proje bilgileri sekmesi"""

    def __init__(self, parent, project_manager: ProjectManager, on_project_ready_callback=None):
        super().__init__(parent)

        self.project_manager = project_manager
        self.on_project_ready_callback = on_project_ready_callback
        self.selected_file_path = None

        self.setup_ui()

    def setup_ui(self):
        """Proje bilgileri UI'ı"""
        # Başlık
        title_label = ctk.CTkLabel(
            self,
            text="Proje Bilgileri ve Dosya Seçimi",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(20, 30))

        # Proje bilgi frame
        self.create_project_info_section()

        # Dosya seçimi frame
        self.create_file_selection_section()

        # Durum bilgisi
        self.status_label = ctk.CTkLabel(
            self,
            text="Proje oluşturulmadı",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(pady=10)

    def create_project_info_section(self):
        """Proje bilgileri bölümü"""
        info_frame = ctk.CTkFrame(self)
        info_frame.pack(fill="x", padx=40, pady=10)

        # Alt başlık
        ctk.CTkLabel(info_frame, text="Proje Bilgileri",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))

        # Grid frame
        grid_frame = ctk.CTkFrame(info_frame)
        grid_frame.pack(fill="x", padx=20, pady=10)

        # Proje tipi
        ctk.CTkLabel(grid_frame, text="Proje Tipi:", font=ctk.CTkFont(size=14)).grid(
            row=0, column=0, padx=10, pady=15, sticky="e"
        )
        self.project_type = ctk.CTkComboBox(
            grid_frame,
            values=["Kalite Kontrol", "Prototip Test", "Seri Üretim", "R&D", "Bakım"],
            font=ctk.CTkFont(size=14),
            width=250
        )
        self.project_type.grid(row=0, column=1, padx=10, pady=15, sticky="w")

        # Parça numarası
        ctk.CTkLabel(grid_frame, text="Parça Numarası:", font=ctk.CTkFont(size=14)).grid(
            row=1, column=0, padx=10, pady=15, sticky="e"
        )
        self.part_number = ctk.CTkEntry(grid_frame, font=ctk.CTkFont(size=14), width=250)
        self.part_number.grid(row=1, column=1, padx=10, pady=15, sticky="w")

        # Operasyon numarası
        ctk.CTkLabel(grid_frame, text="Operasyon No:", font=ctk.CTkFont(size=14)).grid(
            row=2, column=0, padx=10, pady=15, sticky="e"
        )
        self.operation_number = ctk.CTkEntry(grid_frame, font=ctk.CTkFont(size=14), width=250)
        self.operation_number.grid(row=2, column=1, padx=10, pady=15, sticky="w")

        # Seri numarası
        ctk.CTkLabel(grid_frame, text="Seri No:", font=ctk.CTkFont(size=14)).grid(
            row=3, column=0, padx=10, pady=15, sticky="e"
        )
        self.serial_number = ctk.CTkEntry(grid_frame, font=ctk.CTkFont(size=14), width=250)
        self.serial_number.grid(row=3, column=1, padx=10, pady=15, sticky="w")

        # Devam etme checkbox
        self.continue_measurement = ctk.CTkCheckBox(
            grid_frame,
            text="Mevcut projeden devam et",
            font=ctk.CTkFont(size=14)
        )
        self.continue_measurement.grid(row=4, column=0, columnspan=2, pady=20)

        # Grid ayarları
        grid_frame.grid_columnconfigure(0, weight=1)
        grid_frame.grid_columnconfigure(1, weight=1)

        # Proje oluştur butonu
        create_btn = ctk.CTkButton(
            info_frame,
            text="Proje Oluştur / Yükle",
            command=self.create_or_load_project,
            font=ctk.CTkFont(size=16),
            width=200,
            height=40
        )
        create_btn.pack(pady=15)

    def create_file_selection_section(self):
        """Dosya seçimi bölümü"""
        file_frame = ctk.CTkFrame(self)
        file_frame.pack(fill="x", padx=40, pady=10)

        # Alt başlık
        ctk.CTkLabel(file_frame, text="Word Dosyası Seçimi",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))

        # Dosya seç butonu
        self.select_file_btn = ctk.CTkButton(
            file_frame,
            text="Word Dosyası Seç",
            command=self.select_word_file,
            font=ctk.CTkFont(size=14),
            width=200,
            height=40,
            state="disabled"  # Proje oluşturulana kadar disabled
        )
        self.select_file_btn.pack(pady=15)

        # Dosya yolu gösterge
        self.file_path_label = ctk.CTkLabel(
            file_frame,
            text="Önce proje oluşturun",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.file_path_label.pack(pady=5)

        # İlerle butonu
        self.proceed_btn = ctk.CTkButton(
            file_frame,
            text="Sonraki Sekmeye Geç →",
            command=self.proceed_to_next_tab,
            font=ctk.CTkFont(size=14),
            width=200,
            height=35,
            state="disabled"
        )
        self.proceed_btn.pack(pady=15)

    def create_or_load_project(self):
        """Proje oluştur veya yükle"""
        project_type = self.project_type.get()
        part_number = self.part_number.get().strip()
        operation_number = self.operation_number.get().strip()
        serial_number = self.serial_number.get().strip()
        continue_existing = self.continue_measurement.get()

        if not all([project_type, part_number, operation_number, serial_number]):
            messagebox.showwarning("Uyarı", "Tüm alanları doldurun!")
            return

        try:
            if continue_existing:
                # Mevcut proje yükle
                success, folder = self.project_manager.load_existing_project(
                    project_type, part_number, operation_number, serial_number
                )

                if success:
                    self.status_label.configure(text=f"✓ Mevcut proje yüklendi: {os.path.basename(folder)}")
                    self.select_file_btn.configure(state="normal")

                    # Callback çağır
                    if self.on_project_ready_callback:
                        self.on_project_ready_callback(folder)

                    messagebox.showinfo("Başarılı", f"Mevcut proje yüklendi!\nKlasör: {folder}")
                else:
                    # Bulunamadı, yeni oluştur
                    messagebox.showinfo("Bilgi", "Mevcut proje bulunamadı. Yeni proje oluşturulacak.")
                    self._create_new_project(project_type, part_number, operation_number, serial_number)
            else:
                # Yeni proje oluştur
                self._create_new_project(project_type, part_number, operation_number, serial_number)

        except Exception as e:
            messagebox.showerror("Hata", f"Proje işlemi hatası: {str(e)}")

    def _create_new_project(self, project_type, part_number, operation_number, serial_number):
        """Yeni proje oluştur"""
        success, folder, error = self.project_manager.create_project_structure(
            project_type, part_number, operation_number, serial_number
        )

        if success:
            self.status_label.configure(text=f"✓ Proje oluşturuldu: {os.path.basename(folder)}")
            self.select_file_btn.configure(state="normal")

            # Callback çağır
            if self.on_project_ready_callback:
                self.on_project_ready_callback(folder)

            # Klasör aç
            self.project_manager.open_project_folder()

            messagebox.showinfo("Başarılı", f"Proje oluşturuldu!\nKlasör: {folder}")
        else:
            self.status_label.configure(text=f"✗ Hata: {error}")
            messagebox.showerror("Hata", error or "Proje oluşturma hatası!")

    def select_word_file(self):
        """Word dosyası seç ve proje klasörüne kopyala"""
        if not self.project_manager.get_project_folder():
            messagebox.showwarning("Uyarı", "Önce proje oluşturun!")
            return

        # Dosya seç
        file_path = filedialog.askopenfilename(
            title="Word Dosyası Seçin",
            filetypes=[
                ("Word Dosyaları", "*.docx *.doc"),
                ("Tüm Dosyalar", "*.*")
            ]
        )

        if not file_path:
            return

        try:
            # Dosyayı proje klasörüne kopyala
            success, target_path, error = self.project_manager.copy_word_file_to_project(file_path)

            if success:
                self.selected_file_path = target_path
                file_name = os.path.basename(file_path)
                self.file_path_label.configure(text=f"✓ Seçilen: {file_name}")
                self.proceed_btn.configure(state="normal")

                print(f"Word dosyası kopyalandı: {target_path}")
            else:
                messagebox.showerror("Hata", f"Dosya kopyalama hatası: {error}")

        except Exception as e:
            messagebox.showerror("Hata", f"Dosya işleme hatası: {str(e)}")

    def proceed_to_next_tab(self):
        """Sonraki sekmeye geç"""
        if self.on_project_ready_callback:
            self.on_project_ready_callback(self.project_manager.get_project_folder(), self.selected_file_path)

    def get_selected_file_path(self):
        """Seçilen dosya yolunu döner"""
        return self.selected_file_path


class MeasurementTab(ctk.CTkFrame):
    """Ölçüm sekmesi - navigate edilebilir karakter görünümü + lot detayları"""

    def __init__(self, parent, project_manager: ProjectManager, lot_manager: LotDetailManager):
        super().__init__(parent)

        self.project_manager = project_manager
        self.lot_manager = lot_manager
        self.karakterler: List[TeknikResimKarakteri] = []
        self.current_index = 0

        self.setup_ui()

    def setup_ui(self):
        """Ölçüm sekmesi UI'ı"""
        # Grid ayarları
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Başlık
        title_label = ctk.CTkLabel(
            self,
            text="Ölçüm ve Lot Detayları",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(20, 10))

        # Sol panel - Karakter görünümü
        self.create_left_panel()

        # Sağ panel - Doküman görüntüleyici
        self.create_right_panel()

        # Alt panel - İstatistikler
        self.create_bottom_panel()

    def create_left_panel(self):
        """Sol panel - karakter görünümü"""
        left_frame = ctk.CTkFrame(self)
        left_frame.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=10)
        left_frame.grid_rowconfigure(0, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)

        # Karakter görünümü - doğrudan left_frame içinde
        self.karakter_view = SingleKarakterView(
            left_frame,
            on_update_callback=self.on_karakter_updated
        )
        self.karakter_view.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 5))

        # Alt panel - navigasyon ve butonlar (SABIT)
        bottom_panel = ctk.CTkFrame(left_frame)
        bottom_panel.grid(row=1, column=0, sticky="ew", padx=10, pady=(5, 10))
        bottom_panel.grid_columnconfigure(0, weight=1)

        # Navigasyon paneli
        self.navigation_panel = NavigationPanel(
            bottom_panel,
            on_navigate_callback=self.navigate_to
        )
        self.navigation_panel.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        # Buton frame - Kaydet, Temizle, Lot Detayı aynı satırda
        button_frame = ctk.CTkFrame(bottom_panel)
        button_frame.grid(row=1, column=0, sticky="ew", pady=5)

        # Kaydet butonu
        self.save_btn = ctk.CTkButton(
            button_frame,
            text="💾 Kaydet",
            command=self.save_current_measurement,
            font=ctk.CTkFont(size=12),
            width=100,
            height=32
        )
        self.save_btn.pack(side="left", padx=5, pady=5)

        # Temizle butonu
        self.clear_btn = ctk.CTkButton(
            button_frame,
            text="🗑️ Temizle",
            command=self.clear_current_measurement,
            font=ctk.CTkFont(size=12),
            width=100,
            height=32,
            fg_color="gray"
        )
        self.clear_btn.pack(side="left", padx=5, pady=5)

        # Lot detay butonu
        self.lot_detail_btn = ctk.CTkButton(
            button_frame,
            text="🔍 Lot Detayı",
            command=self.show_lot_detail,
            font=ctk.CTkFont(size=12),
            width=120,
            height=32,
            state="disabled"
        )
        self.lot_detail_btn.pack(side="right", padx=5, pady=5)

    def create_right_panel(self):
        """Sağ panel - doküman görüntüleyici"""
        right_frame = ctk.CTkFrame(self)
        right_frame.grid(row=1, column=1, sticky="nsew", padx=(5, 10), pady=10)
        right_frame.grid_rowconfigure(0, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)

        # Doküman görüntüleyici
        self.document_viewer = DocumentViewer(right_frame)
        self.document_viewer.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    def create_bottom_panel(self):
        """Alt panel - istatistikler"""
        self.stats_panel = StatsPanel(
            self,
            on_export_excel=self.export_to_excel,
            on_save_word=self.save_to_word
        )
        self.stats_panel.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=10)

    def load_data(self, file_path: str):
        """Dosyadan veri yükle"""
        try:
            # Word servisi
            word_service = WordReaderService()

            # DataFrame oluştur
            df = DataProcessorService.from_word_tables(word_service, file_path)

            if df.empty:
                messagebox.showwarning("Uyarı", "Geçerli veri bulunamadı!")
                return

            # Model objelerine dönüştür
            data_service = DataProcessorService()
            self.karakterler = data_service.process_dataframe(df)

            if not self.karakterler:
                messagebox.showwarning("Uyarı", "Geçerli karakter bulunamadı!")
                return

            # Lot manager'a callback ayarla
            self.lot_manager.set_update_callback(self.update_actual_value)

            # İlk karakteri göster
            self.current_index = 0
            self.show_current_karakter()
            self.update_navigation()
            self.update_stats()

            # Dokümanı yükle
            self.document_viewer.load_document(file_path)

            # Lot detay butonunu aktif et
            self.lot_detail_btn.configure(state="normal")

            print(f"✓ {len(self.karakterler)} karakter yüklendi")

        except Exception as e:
            messagebox.showerror("Hata", f"Veri yükleme hatası: {str(e)}")

    def show_current_karakter(self):
        """Mevcut karakteri göster"""
        if 0 <= self.current_index < len(self.karakterler):
            karakter = self.karakterler[self.current_index]
            self.karakter_view.load_karakter(karakter)

    def navigate_to(self, new_index: int):
        """Belirtilen indekse navigate et"""
        if 0 <= new_index < len(self.karakterler):
            self.current_index = new_index
            self.show_current_karakter()
            self.update_navigation()
            self.update_stats()

    def update_navigation(self):
        """Navigasyon durumunu güncelle"""
        if self.karakterler:
            self.navigation_panel.update_navigation(self.current_index, len(self.karakterler))

    def update_stats(self):
        """İstatistikleri güncelle"""
        if self.karakterler:
            self.stats_panel.update_stats(self.karakterler, self.current_index)

    def on_karakter_updated(self, karakter: TeknikResimKarakteri):
        """Karakter güncellendiğinde çağrılır"""
        self.update_stats()
        print(f"Karakter güncellendi: {karakter.item_no} = {karakter.actual}")

    def update_actual_value(self, identifier: str, actual_value: str):
        """Lot detayından gelen ACTUAL değer güncellemesi"""
        # identifier formatı: "dimension_item_no"
        parts = identifier.split('_', 1)
        if len(parts) == 2:
            dimension, item_no = parts

            # İlgili karakteri bul ve güncelle
            for karakter in self.karakterler:
                if karakter.dimension == dimension and karakter.item_no == item_no:
                    karakter.actual = actual_value

                    # Eğer bu karakter şu an gösteriliyorsa, görünümü güncelle
                    current_karakter = self.karakterler[self.current_index]
                    if (current_karakter.dimension == dimension and
                            current_karakter.item_no == item_no):
                        self.show_current_karakter()

                    self.update_stats()
                    print(f"Lot detayından ACTUAL güncellendi: {identifier} = {actual_value}")
                    break

    def save_current_measurement(self):
        """Mevcut ölçümü kaydet"""
        if not self.karakterler or self.current_index >= len(self.karakterler):
            return

        # Karakter view'daki save_measurement metodunu çağır
        if hasattr(self.karakter_view, 'save_measurement'):
            self.karakter_view.save_measurement()

            # Ek status mesajı
            karakter = self.karakterler[self.current_index]
            if karakter.actual:
                self.show_temp_message(f"✓ {karakter.item_no} kaydedildi")

    def clear_current_measurement(self):
        """Mevcut ölçümü temizle"""
        if not self.karakterler or self.current_index >= len(self.karakterler):
            return

        # Karakter view'daki clear_measurement metodunu çağır
        if hasattr(self.karakter_view, 'clear_measurement'):
            self.karakter_view.clear_measurement()

            # Ek status mesajı
            karakter = self.karakterler[self.current_index]
            self.show_temp_message(f"🗑️ {karakter.item_no} temizlendi")

    def show_temp_message(self, message: str, duration: int = 2000):
        """Geçici mesaj göster"""
        try:
            # Navigation panel'de geçici mesaj
            if hasattr(self.navigation_panel, 'position_label'):
                original_text = self.navigation_panel.position_label.cget("text")
                self.navigation_panel.position_label.configure(text=message)

                # Belirtilen süre sonra eski metne dön
                self.after(duration, lambda: self.navigation_panel.position_label.configure(text=original_text))
        except:
            pass

    def show_lot_detail(self):
        """Mevcut karakter için lot detay dialog'unu göster"""
        if not self.karakterler or self.current_index >= len(self.karakterler):
            return

        karakter = self.karakterler[self.current_index]
        identifier = f"{karakter.dimension}_{karakter.item_no}"

        # Lot detay dialog'unu göster
        self.lot_manager.show_lot_detail_dialog(
            self,
            identifier,
            karakter.item_no,
            karakter.dimension,
            karakter.actual or ""
        )

    def export_to_excel(self):
        """Excel'e aktar"""
        if not self.karakterler:
            messagebox.showwarning("Uyarı", "Veri yok!")
            return

        try:
            project_folder = self.project_manager.get_project_folder()
            if not project_folder:
                messagebox.showerror("Hata", "Proje klasörü bulunamadı!")
                return

            # Excel dosyası yolu
            excel_path = os.path.join(project_folder, "measurement_data.xlsx")

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

                # Parsed dimension bilgileri
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
            df.to_excel(excel_path, index=False)

            messagebox.showinfo("Başarılı", f"Excel'e aktarıldı:\n{excel_path}")

        except Exception as e:
            messagebox.showerror("Hata", f"Excel aktarım hatası: {str(e)}")

    def save_to_word(self):
        """Word'e kaydet"""
        if not self.karakterler:
            messagebox.showwarning("Uyarı", "Veri yok!")
            return

        # Word save işlemi (mevcut implementasyon ile)
        messagebox.showinfo("Bilgi", "Word kaydetme özelliği yakında eklenecek!")


class EnhancedMainWindow(ctk.CTk):
    """Gelişmiş ana pencere - Project Manager ve Lot Detail Manager entegreli"""

    def __init__(self):
        super().__init__()

        # Pencere ayarları
        self.title("Dijital IRS - Gelişmiş Ölçüm Sistemi")
        self.geometry("1400x900")

        # Servisler
        self.project_manager = ProjectManager()
        self.lot_manager = LotDetailManager(self.project_manager)
        self.word_save_service = WordSaveAsService()
        self.auto_save_service = AutoSaveRecoveryService()

        self.setup_ui()
        self.setup_keyboard_shortcuts()

    def setup_ui(self):
        """Ana UI yapısını oluştur"""
        # Ana frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # TabView oluştur
        self.tabview = ctk.CTkTabview(main_frame)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        # Sekmeleri oluştur
        self.create_tabs()

    def create_tabs(self):
        """Sekmeleri oluştur"""
        # 1. Proje Bilgileri sekmesi
        self.project_tab = self.tabview.add("📁 Proje Bilgileri")
        self.project_info_tab = ProjectInfoTab(
            self.project_tab,
            self.project_manager,
            on_project_ready_callback=self.on_project_ready
        )
        self.project_info_tab.pack(fill="both", expand=True)

        # 2. Ölçüm sekmesi
        self.measurement_tab = self.tabview.add("📏 Ölçüm")
        self.measurement_tab_content = MeasurementTab(
            self.measurement_tab,
            self.project_manager,
            self.lot_manager
        )
        self.measurement_tab_content.pack(fill="both", expand=True)

        # 3. Rapor sekmesi
        self.report_tab = self.tabview.add("📊 Rapor")
        self.create_report_tab()

        # İlk sekmeyi aktif et
        self.tabview.set("📁 Proje Bilgileri")

    def create_report_tab(self):
        """Rapor sekmesini oluştur"""
        # Başlık
        title_label = ctk.CTkLabel(
            self.report_tab,
            text="Rapor ve Export İşlemleri",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(20, 30))

        # Rapor bilgileri frame
        info_frame = ctk.CTkFrame(self.report_tab)
        info_frame.pack(fill="x", padx=40, pady=10)

        # Proje özeti
        ctk.CTkLabel(info_frame, text="Proje Özeti",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 5))

        self.project_summary = ctk.CTkTextbox(info_frame, height=100)
        self.project_summary.pack(fill="x", padx=15, pady=5)

        # Ölçüm özeti
        ctk.CTkLabel(info_frame, text="Ölçüm Özeti",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 5))

        self.measurement_summary = ctk.CTkTextbox(info_frame, height=100)
        self.measurement_summary.pack(fill="x", padx=15, pady=5)

        # Lot detay özeti
        ctk.CTkLabel(info_frame, text="Lot Detay Özeti",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 5))

        self.lot_summary = ctk.CTkTextbox(info_frame, height=80)
        self.lot_summary.pack(fill="x", padx=15, pady=(5, 15))

        # Butonlar frame
        button_frame = ctk.CTkFrame(self.report_tab)
        button_frame.pack(fill="x", padx=40, pady=20)

        # Export butonları
        export_frame = ctk.CTkFrame(button_frame)
        export_frame.pack(pady=15)

        # Word raporu oluştur
        word_report_btn = ctk.CTkButton(
            export_frame,
            text="📄 Word Raporu Oluştur",
            command=self.generate_word_report,
            font=ctk.CTkFont(size=14, weight="bold"),
            width=200,
            height=40
        )
        word_report_btn.pack(side="left", padx=10)

        # Excel export
        excel_export_btn = ctk.CTkButton(
            export_frame,
            text="📊 Excel Export",
            command=self.export_excel_report,
            font=ctk.CTkFont(size=14),
            width=150,
            height=40
        )
        excel_export_btn.pack(side="left", padx=10)

        # Lot detayları export
        lot_export_btn = ctk.CTkButton(
            export_frame,
            text="🔍 Lot Detayları Export",
            command=self.export_lot_details,
            font=ctk.CTkFont(size=14),
            width=180,
            height=40
        )
        lot_export_btn.pack(side="left", padx=10)

        # Proje klasörü aç
        open_folder_btn = ctk.CTkButton(
            export_frame,
            text="📁 Proje Klasörü Aç",
            command=self.open_project_folder,
            font=ctk.CTkFont(size=14),
            width=150,
            height=40,
            fg_color="gray"
        )
        open_folder_btn.pack(side="left", padx=10)

        # Özet güncelleme butonu
        refresh_btn = ctk.CTkButton(
            button_frame,
            text="🔄 Özet Bilgileri Güncelle",
            command=self.update_report_summaries,
            font=ctk.CTkFont(size=12),
            width=200,
            height=30
        )
        refresh_btn.pack(pady=10)

    def setup_keyboard_shortcuts(self):
        """Klavye kısayolları"""
        self.bind('<Control-s>', lambda e: self.quick_save())
        self.bind('<F5>', lambda e: self.update_report_summaries())
        self.bind('<Control-o>', lambda e: self.open_project_folder())
        self.focus_set()

    def on_project_ready(self, project_folder: str, file_path: str = None):
        """Proje hazır olduğunda çağrılır"""
        print(f"Proje hazır: {project_folder}")

        # Lot manager'ın veri kaynaklarını ayarla
        self.lot_manager.setup_project_sources()

        # Auto-save servisini başlat
        self.auto_save_service.start_auto_save()

        if file_path:
            # Dosya seçildiyse, ölçüm sekmesine geç ve veri yükle
            self.tabview.set("📏 Ölçüm")
            self.measurement_tab_content.load_data(file_path)

            # Word save servisini ayarla
            self.word_save_service.load_original_document(file_path)

        # Rapor özetlerini güncelle
        self.update_report_summaries()

    def update_report_summaries(self):
        """Rapor özetlerini güncelle"""
        try:
            # Proje özeti
            project_info = self.project_manager.get_project_info()
            if project_info:
                project_text = ""
                for key, value in project_info.items():
                    project_text += f"{key}: {value}\n"

                self.project_summary.delete("1.0", "end")
                self.project_summary.insert("1.0", project_text)

            # Ölçüm özeti
            karakterler = self.measurement_tab_content.karakterler
            if karakterler:
                total = len(karakterler)
                measured = len([k for k in karakterler if k.actual])
                unmeasured = total - measured
                completion_rate = (measured / total * 100) if total > 0 else 0

                measurement_text = f"""Toplam Karakter: {total}
Ölçülen: {measured}
Bekleyen: {unmeasured}
Tamamlanma Oranı: %{completion_rate:.1f}

Tolerance Analizi:
• Toleranslı Ölçümler: {len([k for k in karakterler if hasattr(k, 'tolerance_type') and k.tolerance_type])}
• Parse Edilen Dimensionlar: {len([k for k in karakterler if hasattr(k, 'parsed_dimension') and k.parsed_dimension])}
"""

                self.measurement_summary.delete("1.0", "end")
                self.measurement_summary.insert("1.0", measurement_text)

            # Lot detay özeti
            lot_stats = self.lot_manager.get_lot_statistics()
            if lot_stats:
                lot_text = f"""Toplam Lot: {lot_stats.get('total_lots', 0)}
Detaylı Lot: {lot_stats.get('lots_with_data', 0)}
Toplam Parça: {lot_stats.get('total_parts', 0)}
Tamamlanma: %{lot_stats.get('completion_rate', 0):.1f}
Veri Kaynakları: {', '.join(lot_stats.get('data_sources', []))}
"""

                self.lot_summary.delete("1.0", "end")
                self.lot_summary.insert("1.0", lot_text)

            print("✓ Rapor özetleri güncellendi")

        except Exception as e:
            print(f"HATA: Özet güncelleme hatası: {e}")

    def generate_word_report(self):
        """Word raporu oluştur"""
        try:
            karakterler = self.measurement_tab_content.karakterler
            if not karakterler:
                messagebox.showwarning("Uyarı", "Ölçüm verisi bulunamadı!")
                return

            if not self.word_save_service.current_document:
                messagebox.showwarning("Uyarı", "Word dokümanı yüklenmemiş!")
                return

            # İstatistikleri al
            stats = self.word_save_service.get_statistics(karakterler)

            # Kullanıcı onayı
            confirm_msg = f"""Word raporu oluşturulacak:

📊 İstatistikler:
• Toplam karakter: {stats['total']}
• Ölçülen karakter: {stats['measured']}
• Bekleyen karakter: {stats['unmeasured']}
• Tamamlanma oranı: %{stats['completion_percentage']:.1f}

Devam etmek istiyor musunuz?"""

            if not messagebox.askyesno("Word Raporu", confirm_msg):
                return

            # Progress göster
            original_text = "Word raporu oluşturuluyor..."

            # Proje klasöründe kaydet
            project_folder = self.project_manager.get_project_folder()
            if project_folder:
                project_info = self.project_manager.get_project_info()
                serial_no = project_info.get("SERI_NO", "report")
                save_path = os.path.join(project_folder, f"{serial_no}_rapor.docx")
            else:
                save_path = None

            # Word kaydetme
            saved_path = self.word_save_service.save_with_actual_values(karakterler, save_path)

            # Başarı mesajı
            success_msg = f"""✅ Word raporu oluşturuldu!

📁 Konum: {saved_path}

📊 Detaylar:
• {stats['measured']} ölçüm değeri aktarıldı
• Tolerans dışı değerler işaretlendi
• Orijinal format korundu

Raporu açmak istiyor musunuz?"""

            if messagebox.askyesno("Başarılı", success_msg):
                os.startfile(saved_path)

        except Exception as e:
            messagebox.showerror("Hata", f"Word raporu hatası: {str(e)}")

    def export_excel_report(self):
        """Excel raporu export et"""
        try:
            karakterler = self.measurement_tab_content.karakterler
            if not karakterler:
                messagebox.showwarning("Uyarı", "Ölçüm verisi bulunamadı!")
                return

            # Excel export
            self.measurement_tab_content.export_to_excel()

        except Exception as e:
            messagebox.showerror("Hata", f"Excel export hatası: {str(e)}")

    def export_lot_details(self):
        """Lot detaylarını export et"""
        try:
            project_folder = self.project_manager.get_project_folder()
            if not project_folder:
                messagebox.showwarning("Uyarı", "Proje klasörü bulunamadı!")
                return

            # Export formatını sor
            format_choice = messagebox.askyesno(
                "Export Format",
                "JSON formatında export edilsin mi?\n\n"
                "Evet: JSON\n"
                "Hayır: Excel"
            )

            if format_choice:
                # JSON export
                json_path = os.path.join(project_folder, "lot_details_export.json")
                success = self.lot_manager.export_to_format(json_path, "json")
            else:
                # Excel export
                excel_path = os.path.join(project_folder, "lot_details_export.xlsx")
                success = self.lot_manager.export_to_format(excel_path, "excel")

            if success:
                messagebox.showinfo("Başarılı", "Lot detayları export edildi!")
            else:
                messagebox.showerror("Hata", "Export işlemi başarısız!")

        except Exception as e:
            messagebox.showerror("Hata", f"Lot export hatası: {str(e)}")

    def open_project_folder(self):
        """Proje klasörünü aç"""
        if self.project_manager.open_project_folder():
            print("✓ Proje klasörü açıldı")
        else:
            messagebox.showwarning("Uyarı", "Proje klasörü bulunamadı!")

    def quick_save(self):
        """Hızlı kaydetme (Ctrl+S)"""
        try:
            karakterler = self.measurement_tab_content.karakterler
            if karakterler:
                # Auto-save servisini güncelle
                self.auto_save_service.update_data(karakterler)
                self.auto_save_service.manual_save()

                # Özet bilgileri güncelle
                self.update_report_summaries()

                print("✓ Hızlı kaydetme tamamlandı")

                # Status göster (kısa süreliğine)
                self.show_temporary_status("💾 Kaydedildi")

        except Exception as e:
            print(f"HATA: Hızlı kaydetme hatası: {e}")

    def show_temporary_status(self, message: str, duration: int = 2000):
        """Geçici status mesajı göster"""
        try:
            # Pencere başlığını geçici olarak değiştir
            original_title = self.title()
            self.title(f"{original_title} - {message}")

            # Belirtilen süre sonra eski başlığa dön
            self.after(duration, lambda: self.title(original_title))

        except:
            pass

    def on_closing(self):
        """Pencere kapatılırken"""
        try:
            # Auto-save durdur
            self.auto_save_service.stop_auto_save()

            # Son kaydetme
            karakterler = getattr(self.measurement_tab_content, 'karakterler', [])
            if karakterler:
                self.auto_save_service.update_data(karakterler)
                self.auto_save_service.emergency_save()

            print("✓ Uygulama güvenli şekilde kapatıldı")

        except Exception as e:
            print(f"HATA: Kapatma hatası: {e}")
        finally:
            self.destroy()


# Ana çalıştırma fonksiyonu
def main():
    """Ana uygulama fonksiyonu"""
    # CustomTkinter tema ayarları
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    # Uygulamayı başlat
    app = EnhancedMainWindow()

    # Kapatma event'ini ayarla
    app.protocol("WM_DELETE_WINDOW", app.on_closing)

    print("🚀 Dijital IRS - Gelişmiş sistem başlatıldı")
    print("📁 Project Manager aktif")
    print("🔍 Lot Detail Manager aktif")
    print("💾 Auto-save aktif")
    print("⌨️  Klavye kısayolları:")
    print("   Ctrl+S: Hızlı kaydetme")
    print("   F5: Özet güncelleme")
    print("   Ctrl+O: Proje klasörü aç")

    app.mainloop()


if __name__ == "__main__":
    main()