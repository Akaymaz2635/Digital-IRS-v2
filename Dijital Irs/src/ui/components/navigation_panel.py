# src/ui/components/navigation_panel.py
"""
Navigasyon paneli component'i - önceki/sonraki butonları ve progress bar
"""
import customtkinter as ctk
from typing import Optional, Callable


class NavigationPanel(ctk.CTkFrame):
    """Navigasyon paneli - önceki/sonraki butonları"""
    
    def __init__(self, parent, on_navigate_callback: Optional[Callable[[int], None]] = None):
        super().__init__(parent)
        
        self.on_navigate_callback = on_navigate_callback
        self.current_index = 0
        self.total_count = 0
        
        self.setup_ui()
    
    def setup_ui(self):
        """Navigasyon UI'ı oluşturur"""
        # Önceki butonu
        self.prev_button = ctk.CTkButton(
            self,
            text="◀ Önceki",
            command=self.go_previous,
            width=120,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            state="disabled"
        )
        self.prev_button.pack(side="left", padx=20, pady=15)
        
        # Pozisyon göstergesi
        self.position_label = ctk.CTkLabel(
            self,
            text="0 / 0",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.position_label.pack(side="left", padx=30, pady=15)
        
        # Sonraki butonu
        self.next_button = ctk.CTkButton(
            self,
            text="Sonraki ▶",
            command=self.go_next,
            width=120,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            state="disabled"
        )
        self.next_button.pack(side="left", padx=20, pady=15)
        
        # Progress bar
        self.progress = ctk.CTkProgressBar(self, width=200)
        self.progress.pack(side="right", padx=20, pady=15)
        self.progress.set(0)
    
    def update_navigation(self, current_index: int, total_count: int):
        """Navigasyon durumunu günceller"""
        self.current_index = current_index
        self.total_count = total_count
        
        # Pozisyon etiketi
        self.position_label.configure(text=f"{current_index + 1} / {total_count}")
        
        # Buton durumları
        self.prev_button.configure(state="normal" if current_index > 0 else "disabled")
        self.next_button.configure(state="normal" if current_index < total_count - 1 else "disabled")
        
        # Progress bar
        if total_count > 0:
            progress = (current_index + 1) / total_count
            self.progress.set(progress)
    
    def go_previous(self):
        """Önceki karaktere git"""
        if self.current_index > 0 and self.on_navigate_callback:
            self.on_navigate_callback(self.current_index - 1)
    
    def go_next(self):
        """Sonraki karaktere git"""
        if self.current_index < self.total_count - 1 and self.on_navigate_callback:
            self.on_navigate_callback(self.current_index + 1)
    
    def set_callback(self, callback: Callable[[int], None]):
        """Navigate callback'ini değiştirir"""
        self.on_navigate_callback = callback
    
    def get_current_position(self) -> tuple[int, int]:
        """Mevcut pozisyon bilgisini döner"""
        return self.current_index, self.total_count
    
    def reset(self):
        """Navigasyon durumunu sıfırlar"""
        self.update_navigation(0, 0)