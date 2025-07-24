# ui/theme/theme_manager.py
class ThemeManager:
    def __init__(self):
        self.current_theme = "dark"
        self.themes = {
            "dark": {
                "bg_color": "#2b2b2b",
                "text_color": "#ffffff",
                "accent_color": "#4fc3f7"
            },
            "light": {
                "bg_color": "#ffffff",
                "text_color": "#000000",
                "accent_color": "#1976d2"
            }
        }

    def apply_theme(self, theme_name: str):
        ctk.set_appearance_mode(theme_name)
        # Özel renk ayarlarını uygula