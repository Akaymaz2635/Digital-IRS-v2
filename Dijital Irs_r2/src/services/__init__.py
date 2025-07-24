"""
Servis katmanı - Gelişmiş özellikler dahil
Tüm business logic bu katmanda yer alır
"""

from .word_reader import WordReaderService
from .data_processor import DataProcessorService, TeknikResimKarakteri
from .word_save_as import WordSaveAsService
from .auto_save_recovery import AutoSaveRecoveryService

# Yeni servisler
from .project_manager import ProjectManager
from .data_source_manager import (
    DataSourceManager, 
    JSONDataSource, 
    ExcelDataSource, 
    SQLiteDataSource, 
    CSVDataSource,
    LotDataAdapter
)
from .lot_detail_manager import LotDetailManager, LotDetailDialog

__all__ = [
    # Mevcut servisler
    'WordReaderService', 
    'DataProcessorService', 
    'TeknikResimKarakteri',
    'WordSaveAsService',
    'AutoSaveRecoveryService',
    
    # Yeni servisler
    'ProjectManager',
    'DataSourceManager',
    'JSONDataSource',
    'ExcelDataSource', 
    'SQLiteDataSource',
    'CSVDataSource',
    'LotDataAdapter',
    'LotDetailManager',
    'LotDetailDialog'
]
