# services/interfaces.py
from abc import ABC, abstractmethod
from typing import Protocol

class DocumentReaderProtocol(Protocol):
    def extract_tables(self, file_path: str) -> List: ...
    def load_document(self, file_path: str) -> bool: ...

class DataProcessorProtocol(Protocol):
    def process_dataframe(self, df: pd.DataFrame) -> List[TeknikResimKarakteri]: ...