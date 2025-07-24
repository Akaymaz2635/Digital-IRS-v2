# services/async_processor.py
import asyncio
from concurrent.futures import ThreadPoolExecutor


class AsyncDocumentProcessor:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def process_document_async(self, file_path: str):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self._process_document, file_path)

    def _process_document(self, file_path: str):
        # CPU-intensive işlem
        pass