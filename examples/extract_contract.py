#!/usr/bin/env python3
"""
Example: Extract information from a contract PDF.

Usage:
    export DASHSCOPE_API_KEY=your_key
    python examples/extract_contract.py /path/to/contract.pdf
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from file_master.config import Config
from file_master.services import PDFReader, Extractor


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_contract.py <pdf_file>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    # Check config
    config = Config.from_env()
    if not config.api_key:
        print("Error: DASHSCOPE_API_KEY not set")
        sys.exit(1)
    
    # Validate file
    from file_master.services.pdf_reader import validate_pdf_file
    is_valid, error = validate_pdf_file(pdf_path)
    if not is_valid:
        print(f"Invalid PDF: {error}")
        sys.exit(1)
    
    # Get PDF info
    with PDFReader(pdf_path) as reader:
        meta = reader.get_metadata()
        print(f"📄 PDF: {pdf_path}")
        print(f"   Pages: {meta.total_pages}")
        print(f"   Size: {meta.file_size_bytes / 1024 / 1024:.2f} MB")
        if meta.title:
            print(f"   Title: {meta.title}")
        print()
    
    # Extract contract information
    query = "合同金额，签署日期，甲方名称，乙方名称，付款方式"
    print(f"🔍 Extracting: {query}")
    print()
    
    extractor = Extractor(config)
    
    # Read PDF text (first 20 pages)
    with PDFReader(pdf_path) as reader:
        pages = list(reader.iter_pages(max_pages=20))
        text = "\n\n".join(f"--- 第{p.page_number}页 ---\n{p.text}" for p in pages)
    
    # Extract
    result = extractor.extract(text, query, include_citations=True)
    
    if result.error:
        print(f"❌ Error: {result.error}")
        sys.exit(1)
    
    # Print results
    print("✅ Extracted Information:")
    print("-" * 50)
    for key, value in result.extracted.items():
        print(f"   {key}: {value}")
    
    if result.citations:
        print()
        print("📎 Citations:")
        for citation in result.citations[:3]:  # Show first 3
            print(f"   [{citation['field']}]")
            print(f"      \"{citation['text'][:100]}...\"")
            print()


if __name__ == "__main__":
    main()
