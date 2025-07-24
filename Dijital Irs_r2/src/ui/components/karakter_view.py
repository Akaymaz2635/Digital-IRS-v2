# src/ui/components/karakter_view.py - Scrollbar için iyileştirilmiş
"""
Tek karakter görünümü component'i - Scrollable ve geliştirilmiş
"""
import customtkinter as ctk
import tkinter as tk
from typing import Optional, Callable
import sys
import os

# Servis importları için path ekleme
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from services.data_processor import TeknikResimKarakteri


class SingleKarakterView(ctk.CTkFrame):
    """Tek karakter görünümü - scrollable ve geliştirilmiş"""

    def __init__(self, parent, on_update_callback: Optional[Callable[[TeknikResimKarakteri], None]] = None):
        super().__init__(parent)

        self.current_karakter: Optional[TeknikResimKarakteri] = None
        self.on_update_callback = on_update_callback
        self.actual_entry = None
        self.current_value_label = None
        self.status_label = None

        self.setup_ui()

    def setup_ui(self):
        """UI'ı oluşturur - scrollable"""
        # Ana scrollable frame
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Başlık alanı
        self._create_title_section()

        # Ana bilgiler bölümü
        self._create_info_section()

        # Parsed dimension bilgileri
        self._create_parsed_info_section()

        # Ölçüm girişi bölümü
        self._create_measurement_section()

    def _create_title_section(self):
        """Başlık bölümünü oluşturur"""
        self.title_frame = ctk.CTkFrame(self.scroll_frame)
        self.title_frame.pack(fill="x", pady=(0, 15))

        self.item_label = ctk.CTkLabel(
            self.title_frame,
            text="Karakter seçilmedi",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="white"
        )
        self.item_label.pack(pady=15)

    def _create_info_section(self):
        """Ana bilgiler bölümünü oluşturur"""
        info_frame = ctk.CTkFrame(self.scroll_frame)
        info_frame.pack(fill="x", pady=(0, 15))

        # Grid ayarları
        info_frame.grid_columnconfigure(1, weight=1)

        # Temel bilgiler
        self._add_info_row(info_frame, 0, "Ölçü:", "dim_value", wraplength=300)
        self._add_info_row(info_frame, 1, "Ölçüm Aleti:", "tool_value")
        self._add_info_row(info_frame, 2, "Bölge:", "zone_value")
        self._add_info_row(info_frame, 3, "Kontrol Seviyesi:", "level_value")
        self._add_info_row(info_frame, 4, "Açıklamalar:", "remarks_value", wraplength=350)

    def _create_parsed_info_section(self):
        """Parse edilmiş dimension bilgileri"""
        parsed_frame = ctk.CTkFrame(self.scroll_frame)
        parsed_frame.pack(fill="x", pady=(0, 15))
        parsed_frame.grid_columnconfigure(1, weight=1)

        # Başlık
        title_label = ctk.CTkLabel(
            parsed_frame,
            text="Tolerance Analizi",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="lightblue"
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(10, 15))

        # Tolerance bilgileri
        self._add_info_row(parsed_frame, 1, "Tolerance Tipi:", "tolerance_type_value", text_color="lightblue")
        self._add_info_row(parsed_frame, 2, "Nominal Değer:", "nominal_value", text_color="lightgreen")
        self._add_info_row(parsed_frame, 3, "Tolerance Sınırları:", "limits_value", text_color="yellow")

    def _create_measurement_section(self):
        """Ölçüm girişi bölümünü oluşturur"""
        measurement_frame = ctk.CTkFrame(self.scroll_frame)
        measurement_frame.pack(fill="x", pady=(0, 20))
        measurement_frame.grid_columnconfigure(1, weight=1)

        # Başlık
        measurement_title = ctk.CTkLabel(
            measurement_frame,
            text="ÖLÇÜM SONUCU",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="yellow"
        )
        measurement_title.grid(row=0, column=0, columnspan=3, pady=(15, 10))

        # Mevcut değer göstergesi
        current_label = ctk.CTkLabel(
            measurement_frame,
            text="Mevcut Değer:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        current_label.grid(row=1, column=0, sticky="w", padx=20, pady=5)

        self.current_value_label = ctk.CTkLabel(
            measurement_frame,
            text="Henüz ölçüm yapılmadı",
            font=ctk.CTkFont(size=14),
            text_color="orange"
        )
        self.current_value_label.grid(row=1, column=1, sticky="w", padx=10, pady=5)

        # Yeni değer girişi
        new_label = ctk.CTkLabel(
            measurement_frame,
            text="Yeni Ölçüm:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        new_label.grid(row=2, column=0, sticky="w", padx=20, pady=10)

        self.actual_entry = ctk.CTkEntry(
            measurement_frame,
            placeholder_text="Ölçüm değerini girin (örn: 25.48)",
            width=200,
            height=35,
            font=ctk.CTkFont(size=14)
        )
        self.actual_entry.grid(row=2, column=1, sticky="w", padx=10, pady=10)

        # Kaydet butonu (karakter view içinde)
        self.save_button = ctk.CTkButton(
            measurement_frame,
            text="Kaydet",
            command=self.save_measurement,
            width=100,
            height=35,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.save_button.grid(row=2, column=2, sticky="w", padx=10, pady=10)

        # Temizle butonu
        clear_button = ctk.CTkButton(
            measurement_frame,
            text="Temizle",
            command=self.clear_measurement,
            width=80,
            height=35,
            font=ctk.CTkFont(size=12),
            fg_color="gray"
        )
        clear_button.grid(row=3, column=1, sticky="w", padx=10, pady=5)

        # Status mesajı
        self.status_label = ctk.CTkLabel(
            measurement_frame,
            text="",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.grid(row=4, column=0, columnspan=3, pady=10)

        # Enter tuşu ile kaydetme
        self.actual_entry.bind('<Return>', lambda e: self.save_measurement())

    def _add_info_row(self, parent, row: int, label_text: str, value_attr: str,
                      wraplength: int = 250, text_color: str = None):
        """Bilgi satırı ekler"""
        # Label
        label = ctk.CTkLabel(parent, text=label_text, font=ctk.CTkFont(size=14, weight="bold"))
        label.grid(row=row, column=0, sticky="w", padx=15, pady=8)

        # Value
        value_font_size = 14 if row < 5 else 12
        sticky = "nw" if "Açıklamalar" in label_text else "w"

        value_label = ctk.CTkLabel(
            parent,
            text="-",
            font=ctk.CTkFont(size=value_font_size),
            wraplength=wraplength,
            justify="left" if "Açıklamalar" in label_text else "center"
        )

        if text_color:
            value_label.configure(text_color=text_color)

        value_label.grid(row=row, column=1, sticky=sticky, padx=15, pady=8)

        # Attribute olarak sakla
        setattr(self, value_attr, value_label)

    def load_karakter(self, karakter: TeknikResimKarakteri):
        """Karakteri yükler ve gösterir"""
        self.current_karakter = karakter

        # Temel bilgileri güncelle
        self._update_basic_info(karakter)

        # Parsed dimension bilgilerini güncelle
        self._update_parsed_info(karakter)

        # Mevcut ölçüm değerini güncelle
        self._update_current_measurement(karakter)

        # Status'u temizle ve focus ver
        self.status_label.configure(text="")
        self.actual_entry.focus()

    def _update_basic_info(self, karakter: TeknikResimKarakteri):
        """Temel bilgileri günceller"""
        self.item_label.configure(text=f"Item: {karakter.item_no}")
        self.dim_value.configure(text=karakter.dimension)
        self.tool_value.configure(text=karakter.tooling)
        self.zone_value.configure(text=karakter.bp_zone or "Belirtilmemiş")
        self.level_value.configure(text=karakter.inspection_level or "100%")
        self.remarks_value.configure(text=karakter.remarks or "Açıklama yok")

    def _update_parsed_info(self, karakter: TeknikResimKarakteri):
        """Parse edilmiş dimension bilgilerini günceller"""
        if (hasattr(karakter, 'parsed_dimension') and karakter.parsed_dimension and
                hasattr(karakter, 'tolerance_type') and karakter.tolerance_type):

            # Tolerance Type
            self.tolerance_type_value.configure(
                text=karakter.tolerance_type.capitalize(),
                text_color="lightblue"
            )

            # Nominal Value
            if hasattr(karakter, 'nominal_value') and karakter.nominal_value is not None:
                self.nominal_value.configure(
                    text=f"{karakter.nominal_value}",
                    text_color="lightgreen"
                )
            else:
                self.nominal_value.configure(text="Tanımsız", text_color="gray")

            # Tolerance Limits
            self._update_tolerance_limits(karakter)
        else:
            # Parse edilemedi
            self.tolerance_type_value.configure(text="Parse edilemedi", text_color="gray")
            self.nominal_value.configure(text="-", text_color="gray")
            self.limits_value.configure(text="-", text_color="gray")

    def _update_tolerance_limits(self, karakter: TeknikResimKarakteri):
        """Tolerance limit bilgilerini günceller"""
        has_lower = hasattr(karakter, 'lower_limit') and karakter.lower_limit is not None
        has_upper = hasattr(karakter, 'upper_limit') and karakter.upper_limit is not None

        if has_lower and has_upper:
            limits_text = f"{karakter.lower_limit} ↔ {karakter.upper_limit}"
            self.limits_value.configure(text=limits_text, text_color="yellow")
        elif has_upper:
            self.limits_value.configure(text=f"Max: {karakter.upper_limit}", text_color="orange")
        elif has_lower:
            self.limits_value.configure(text=f"Min: {karakter.lower_limit}", text_color="orange")
        else:
            self.limits_value.configure(text="Limit yok", text_color="gray")

    def _update_current_measurement(self, karakter: TeknikResimKarakteri):
        """Mevcut ölçüm değerini günceller"""
        if karakter.actual:
            self.current_value_label.configure(
                text=f"{karakter.actual}",
                text_color="green"
            )
            # Entry'e de yerleştir
            self.actual_entry.delete(0, tk.END)
            self.actual_entry.insert(0, str(karakter.actual))
        else:
            self.current_value_label.configure(
                text="Henüz ölçüm yapılmadı",
                text_color="orange"
            )
            self.actual_entry.delete(0, tk.END)

    def save_measurement(self):
        """Ölçümü kaydeder"""
        if not self.current_karakter:
            return

        try:
            new_value = self.actual_entry.get().strip()

            if new_value == "":
                self.status_label.configure(text="⚠ Değer boş bırakılamaz", text_color="orange")
                return

            # Virgülü noktaya çevir
            new_value = new_value.replace(',', '.')

            # Ölçümü kaydet
            self.current_karakter.actual = new_value

            # Tolerance kontrolü ve status mesajı
            status_message = self._get_save_status_message(new_value)
            self.status_label.configure(text=status_message, text_color="green")

            # Mevcut değer göstergesini güncelle
            self.current_value_label.configure(
                text=f"{new_value}",
                text_color="green"
            )

            # Callback çağır
            if self.on_update_callback:
                self.on_update_callback(self.current_karakter)

        except Exception as e:
            self.status_label.configure(text=f"Hata: {str(e)}", text_color="red")

    def _get_save_status_message(self, new_value: str) -> str:
        """Kaydetme işlemi için status mesajını oluşturur"""
        try:
            actual_float = float(new_value)
            tolerance_status = self.check_tolerance(actual_float)
            if tolerance_status:
                return f"✓ Kaydedildi! {tolerance_status}"
            else:
                return "✓ Ölçüm kaydedildi!"
        except ValueError:
            return "✓ Kaydedildi (metin değer)"

    def clear_measurement(self):
        """Ölçümü temizler"""
        if self.current_karakter:
            self.current_karakter.actual = None
            self.actual_entry.delete(0, tk.END)
            self.current_value_label.configure(
                text="Henüz ölçüm yapılmadı",
                text_color="orange"
            )
            self.status_label.configure(text="Ölçüm temizlendi", text_color="gray")

            if self.on_update_callback:
                self.on_update_callback(self.current_karakter)

    def check_tolerance(self, actual_value: float) -> str:
        """Tolerance kontrolü yapar ve sonuç mesajı döner"""
        karakter = self.current_karakter

        if not karakter:
            return ""

        # Parsed dimension bilgileri var mı kontrol et
        if not (hasattr(karakter, 'lower_limit') or hasattr(karakter, 'upper_limit')):
            return ""

        has_lower = hasattr(karakter, 'lower_limit') and karakter.lower_limit is not None
        has_upper = hasattr(karakter, 'upper_limit') and karakter.upper_limit is not None

        if not has_lower and not has_upper:
            return ""

        try:
            if has_lower and has_upper:
                if karakter.lower_limit <= actual_value <= karakter.upper_limit:
                    return "✅ Tolerance İçinde"
                else:
                    return "❌ Tolerance Dışı"
            elif has_upper:
                if actual_value <= karakter.upper_limit:
                    return "✅ Max Limit İçinde"
                else:
                    return "❌ Max Limit Aşıldı"
            elif has_lower:
                if actual_value >= karakter.lower_limit:
                    return "✅ Min Limit İçinde"
                else:
                    return "❌ Min Limit Altında"
        except:
            pass

        return ""

    def set_callback(self, callback: Callable[[TeknikResimKarakteri], None]):
        """Update callback'ini değiştirir"""
        self.on_update_callback = callback

    def get_current_karakter(self) -> Optional[TeknikResimKarakteri]:
        """Mevcut karakteri döner"""
        return self.current_karakter

    def get_actual_value(self) -> str:
        """Entry'deki actual değeri döner"""
        if self.actual_entry:
            return self.actual_entry.get().strip()
        return ""

    def set_actual_value(self, value: str):
        """Entry'e actual değer yerleştirir"""
        if self.actual_entry:
            self.actual_entry.delete(0, tk.END)
            if value:
                self.actual_entry.insert(0, str(value))