# config/app_config.py
@dataclass
class AppConfig:
    # UI Settings
    WINDOW_WIDTH: int = 1400
    WINDOW_HEIGHT: int = 900
    THEME: str = "dark"

    # File Settings
    SUPPORTED_FORMATS: List[str] = field(default_factory=lambda: [".docx", ".doc"])
    AUTO_SAVE_INTERVAL: int = 30

    # Measurement Settings
    DEFAULT_INSPECTION_LEVEL: str = "100%"
    DECIMAL_SEPARATOR: str = "."