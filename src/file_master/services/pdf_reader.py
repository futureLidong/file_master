"""PDF reading service with large file support."""

import os
from dataclasses import dataclass
from typing import Iterator, Optional
import pdfplumber


@dataclass
class PageData:
    """Data extracted from a single PDF page."""
    page_number: int
    text: str
    metadata: dict
    
    @property
    def token_estimate(self) -> int:
        """Estimate token count (rough: 1 token ≈ 4 chars for Chinese)."""
        return len(self.text) // 4


@dataclass
class PDFMetadata:
    """PDF document metadata."""
    total_pages: int
    file_size_bytes: int
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None


class PDFReader:
    """
    PDF reader optimized for large files.
    
    Features:
    - Stream pages instead of loading entire file
    - Chunk-based processing for AI API
    - Memory efficient
    """
    
    def __init__(self, file_path: str):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        self.file_path = file_path
        self.file_size = os.path.getsize(file_path)
        self._pdf: Optional[pdfplumber.PDF] = None
    
    def __enter__(self):
        self._pdf = pdfplumber.open(self.file_path)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._pdf:
            self._pdf.close()
    
    @property
    def total_pages(self) -> int:
        """Get total number of pages."""
        if not self._pdf:
            with pdfplumber.open(self.file_path) as pdf:
                return len(pdf.pages)
        return len(self._pdf.pages)
    
    def get_metadata(self) -> PDFMetadata:
        """Extract PDF metadata."""
        if not self._pdf:
            with pdfplumber.open(self.file_path) as pdf:
                meta = pdf.metadata or {}
                return PDFMetadata(
                    total_pages=len(pdf.pages),
                    file_size_bytes=self.file_size,
                    title=meta.get("Title"),
                    author=meta.get("Author"),
                    subject=meta.get("Subject"),
                )
        
        meta = self._pdf.metadata or {}
        return PDFMetadata(
            total_pages=len(self._pdf.pages),
            file_size_bytes=self.file_size,
            title=meta.get("Title"),
            author=meta.get("Author"),
            subject=meta.get("Subject"),
        )
    
    def iter_pages(
        self,
        start_page: int = 0,
        max_pages: Optional[int] = None,
    ) -> Iterator[PageData]:
        """
        Iterate over pages lazily (memory efficient).
        
        Args:
            start_page: Starting page number (0-indexed)
            max_pages: Maximum number of pages to yield
        """
        if not self._pdf:
            raise RuntimeError("PDF not opened. Use context manager.")
        
        end_page = self.total_pages
        if max_pages:
            end_page = min(end_page, start_page + max_pages)
        
        for i in range(start_page, end_page):
            page = self._pdf.pages[i]
            text = page.extract_text() or ""
            
            # Extract page-level metadata
            page_meta = {
                "width": page.width,
                "height": page.height,
                "page_number": i + 1,  # 1-indexed for human readability
            }
            
            yield PageData(
                page_number=i + 1,
                text=text,
                metadata=page_meta,
            )
    
    def get_page_text(self, page_number: int) -> str:
        """Get text from a specific page (1-indexed)."""
        if not self._pdf:
            with pdfplumber.open(self.file_path) as pdf:
                return pdf.pages[page_number - 1].extract_text() or ""
        return self._pdf.pages[page_number - 1].extract_text() or ""
    
    def iter_page_chunks(
        self,
        chunk_size: int = 10,
        overlap: int = 2,
        max_pages: Optional[int] = None,
    ) -> Iterator[tuple[list[int], str]]:
        """
        Iterate over page chunks for batch processing.
        
        Args:
            chunk_size: Number of pages per chunk
            overlap: Number of overlapping pages between chunks
            max_pages: Maximum total pages to process
        
        Yields:
            Tuple of (page_numbers, combined_text)
        """
        pages = list(self.iter_pages(max_pages=max_pages))
        
        if not pages:
            return
        
        start = 0
        while start < len(pages):
            end = min(start + chunk_size, len(pages))
            chunk_pages = pages[start:end]
            
            # Combine text with page markers
            texts = []
            page_nums = []
            for page in chunk_pages:
                texts.append(f"--- 第{page.page_number}页 ---\n{page.text}")
                page_nums.append(page.page_number)
            
            combined = "\n\n".join(texts)
            yield (page_nums, combined)
            
            # Move to next chunk with overlap
            start = end - overlap if end < len(pages) else end


def validate_pdf_file(file_path: str, max_size_mb: int = 100) -> tuple[bool, str]:
    """
    Validate a PDF file before processing.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not os.path.exists(file_path):
        return False, f"File not found: {file_path}"
    
    if not file_path.lower().endswith(".pdf"):
        return False, "File must be a PDF (.pdf)"
    
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if file_size_mb > max_size_mb:
        return False, f"File too large: {file_size_mb:.1f}MB (max: {max_size_mb}MB)"
    
    # Try to open and validate
    try:
        with pdfplumber.open(file_path) as pdf:
            _ = len(pdf.pages)
    except Exception as e:
        return False, f"Invalid PDF file: {e}"
    
    return True, ""
