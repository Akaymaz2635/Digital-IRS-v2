# services/lot_detail_manager.py - Quick version
"""
Lot Detail Manager - Basit versiyon
"""
import customtkinter as ctk
import tkinter as tk
from typing import Dict, Optional, Callable, Any
import json
import os

class LotDetailDialog:
    def __init__(self, parent, lot_manager, identifier: str, 
                 item_no: str, dimension: str, actual_value: str = ""):
        self.parent = parent
        self.lot_manager = lot_manager
        self.identifier = identifier
        self.item_no = item_no
        self.dimension = dimension
        self.actual_value = actual_value
        
        self.dialog = None
        self.part_entries = {}
        self.quantity_var = None
        self.notes_entry = None
        
        self.create_dialog()
    
    def create_dialog(self):
        """Dialog oluştur"""
        self.dialog = ctk.CTkToplevel(self.parent)
        self.dialog.title(f"Lot Detayı - {self.item_no}")
        self.dialog.geometry("600x700")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Ana scrollable frame - TÜM İÇERİK İÇİN
        main_scroll = ctk.CTkScrollableFrame(self.dialog)
        main_scroll.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Başlık
        title_label = ctk.CTkLabel(
            main_scroll,
            text=f"Lot Detayı - {self.item_no}",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Bilgi frame
        info_frame = ctk.CTkFrame(main_scroll)
        info_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(info_frame, text=f"DIMENSION: {self.dimension}", 
                    font=ctk.CTkFont(size=12)).pack(anchor="w", padx=15, pady=3)
        ctk.CTkLabel(info_frame, text=f"ITEM NO: {self.item_no}", 
                    font=ctk.CTkFont(size=12)).pack(anchor="w", padx=15, pady=3)
        ctk.CTkLabel(info_frame, text=f"ACTUAL: {self.actual_value}", 
                    font=ctk.CTkFont(size=12)).pack(anchor="w", padx=15, pady=3)
        
        # Miktar kontrolü
        quantity_frame = ctk.CTkFrame(main_scroll)
        quantity_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(quantity_frame, text="Parça Miktarı:", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(10, 5))
        
        control_frame = ctk.CTkFrame(quantity_frame)
        control_frame.pack(pady=(0, 10))
        
        decrease_btn = ctk.CTkButton(control_frame, text="-", width=40, height=30, command=self.decrease_quantity)
        decrease_btn.pack(side="left", padx=5)
        
        self.quantity_var = tk.StringVar(value="1")
        quantity_label = ctk.CTkLabel(control_frame, textvariable=self.quantity_var,
                                     font=ctk.CTkFont(size=14, weight="bold"), width=50)
        quantity_label.pack(side="left", padx=10)
        
        increase_btn = ctk.CTkButton(control_frame, text="+", width=40, height=30, command=self.increase_quantity)
        increase_btn.pack(side="left", padx=5)
        
        # Parça numaraları
        ctk.CTkLabel(main_scroll, text="Parça Numaraları:", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(15, 5))
        
        # Parça numaraları için ayrı scrollable frame
        self.parts_scroll = ctk.CTkScrollableFrame(main_scroll, height=200)
        self.parts_scroll.pack(fill="x", pady=(0, 15))
        
        # Notlar
        ctk.CTkLabel(main_scroll, text="Notlar:", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(15, 5))
        
        self.notes_entry = ctk.CTkTextbox(main_scroll, height=100)
        self.notes_entry.pack(fill="x", pady=(0, 15))
        
        # Butonlar - SABIT POZISYON (scroll dışında)
        button_frame = ctk.CTkFrame(self.dialog)
        button_frame.pack(fill="x", side="bottom", padx=20, pady=(0, 20))
        
        save_btn = ctk.CTkButton(
            button_frame, text="Kaydet", 
            command=self.save_data,
            font=ctk.CTkFont(size=14, weight="bold"),
            width=120, height=35
        )
        save_btn.pack(side="left", padx=10, pady=10)
        
        cancel_btn = ctk.CTkButton(
            button_frame, text="İptal", 
            command=self.dialog.destroy, 
            fg_color="gray",
            width=100, height=35
        )
        cancel_btn.pack(side="right", padx=10, pady=10)
        
        # İlk güncelleme
        self.update_part_entries()
        self.load_existing_data()
    
    def increase_quantity(self):
        current = int(self.quantity_var.get())
        self.quantity_var.set(str(current + 1))
        self.update_part_entries()
    
    def decrease_quantity(self):
        current = int(self.quantity_var.get())
        if current > 0:
            self.quantity_var.set(str(current - 1))
            self.update_part_entries()
    
    def update_part_entries(self):
        for widget in self.parts_scroll.winfo_children():
            widget.destroy()
        
        self.part_entries = {}
        quantity = int(self.quantity_var.get())
        
        for i in range(1, quantity + 1):
            entry_frame = ctk.CTkFrame(self.parts_scroll)
            entry_frame.pack(fill="x", pady=2)
            
            ctk.CTkLabel(entry_frame, text=f"{i}:", width=30).pack(side="left", padx=5)
            
            entry = ctk.CTkEntry(entry_frame, height=30)
            entry.pack(side="left", fill="x", expand=True, padx=5)
            
            self.part_entries[str(i)] = entry
    
    def load_existing_data(self):
        data = self.lot_manager.load_lot_data(self.identifier)
        if data:
            self.quantity_var.set(str(data.get('part_quantity', 1)))
            self.update_part_entries()
            
            part_numbers = data.get('part_numbers', {})
            for i, entry in self.part_entries.items():
                if i in part_numbers:
                    entry.insert(0, part_numbers[i])
            
            notes = data.get('notes', '')
            if notes:
                self.notes_entry.insert("1.0", notes)
    
    def save_data(self):
        part_numbers = {}
        for i, entry in self.part_entries.items():
            value = entry.get().strip()
            if value:
                part_numbers[i] = value
        
        actual_value = self.calculate_min_max(part_numbers)
        
        lot_data = {
            'part_quantity': int(self.quantity_var.get()),
            'part_numbers': part_numbers,
            'notes': self.notes_entry.get("1.0", "end").strip(),
            'actual_value': actual_value
        }
        
        success = self.lot_manager.save_lot_data(self.identifier, lot_data)
        
        if success:
            if hasattr(self.lot_manager, 'update_actual_callback') and self.lot_manager.update_actual_callback:
                self.lot_manager.update_actual_callback(self.identifier, actual_value)
            self.dialog.destroy()
        else:
            tk.messagebox.showerror("Hata", "Kaydetme hatası!")
    
    def calculate_min_max(self, part_numbers: Dict[str, str]) -> str:
        if not part_numbers:
            return self.actual_value
        
        values = []
        for part_value in part_numbers.values():
            try:
                if '/' in part_value:
                    for v in part_value.split('/'):
                        if v.strip():
                            values.append(float(v.strip()))
                else:
                    if part_value.strip():
                        values.append(float(part_value.strip()))
            except ValueError:
                continue
        
        if values:
            min_val = min(values)
            max_val = max(values)
            return f"{min_val} / {max_val}" if min_val != max_val else str(min_val)
        
        return self.actual_value


class LotDetailManager:
    def __init__(self, project_manager=None):
        self.project_manager = project_manager
        self.update_actual_callback: Optional[Callable] = None
        self.data_file = None
        self.lot_data = {}
        
        if project_manager and project_manager.get_project_folder():
            self.setup_project_sources()
    
    def setup_project_sources(self):
        project_folder = self.project_manager.get_project_folder()
        if project_folder:
            self.data_file = os.path.join(project_folder, "lot_details.json")
            self.load_data_file()
    
    def load_data_file(self):
        if self.data_file and os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.lot_data = json.load(f)
                print(f"✓ Lot data yüklendi: {len(self.lot_data)} kayıt")
            except Exception as e:
                print(f"Lot data yükleme hatası: {e}")
                self.lot_data = {}
    
    def save_data_file(self):
        if self.data_file:
            try:
                os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
                with open(self.data_file, 'w', encoding='utf-8') as f:
                    json.dump(self.lot_data, f, indent=2, ensure_ascii=False)
                return True
            except Exception as e:
                print(f"Lot data kaydetme hatası: {e}")
                return False
        return False
    
    def set_update_callback(self, callback: Callable[[str, str], None]):
        self.update_actual_callback = callback
    
    def show_lot_detail_dialog(self, parent, identifier: str, 
                             item_no: str, dimension: str, actual_value: str = ""):
        dialog = LotDetailDialog(parent, self, identifier, item_no, dimension, actual_value)
        return dialog
    
    def load_lot_data(self, identifier: str) -> Dict[str, Any]:
        return self.lot_data.get(identifier, {})
    
    def save_lot_data(self, identifier: str, data: Dict[str, Any]) -> bool:
        self.lot_data[identifier] = data
        return self.save_data_file()
    
    def get_lot_statistics(self) -> Dict[str, Any]:
        total_lots = len(self.lot_data)
        lots_with_data = len([d for d in self.lot_data.values() if d.get('part_quantity', 0) > 0])
        total_parts = sum(d.get('part_quantity', 0) for d in self.lot_data.values())
        
        return {
            'total_lots': total_lots,
            'lots_with_data': lots_with_data,
            'total_parts': total_parts,
            'completion_rate': (lots_with_data / total_lots * 100) if total_lots > 0 else 0,
            'data_sources': ['json']
        }
    
    def export_to_format(self, file_path: str, file_type: str = "json") -> bool:
        try:
            if file_type == "json":
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.lot_data, f, indent=2, ensure_ascii=False)
                return True
            # Diğer formatlar için pandas gerekli
            return False
        except Exception as e:
            print(f"Export hatası: {e}")
            return False