# utils/error_handler.py
class ErrorHandler:
    @staticmethod
    def handle_service_error(error: Exception, operation: str) -> None:
        logger.error(f"Error in {operation}: {str(error)}")
        # Kullanıcıya uygun mesaj göster
        messagebox.showerror("İşlem Hatası", f"{operation} sırasında hata: {str(error)}")

    @staticmethod
    def handle_validation_error(field: str, value: str) -> None:
        messagebox.showwarning("Veri Hatası", f"{field} geçersiz: {value}")