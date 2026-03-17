"""PDF information extraction MCP plugin."""

import json
from typing import Any, Optional

from mcp.types import Tool, TextContent, ErrorContent

from ..config import Config
from ..services import PDFReader, Extractor, validate_pdf_file


class PDFExtractPlugin:
    """
    MCP plugin for PDF information extraction.
    
    Features:
    - Large file support (chunked processing)
    - Natural language queries
    - Optional citation extraction
    - Progress tracking
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.extractor = Extractor(config)
    
    def get_tools(self) -> list[Tool]:
        """Return list of available tools."""
        return [
            Tool(
                name="pdf_extract",
                description="从 PDF 文件中提取关键信息。支持自然语言查询和关键词匹配，可处理大文件（分页处理）。",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "PDF 文件路径"
                        },
                        "query": {
                            "type": "string",
                            "description": "抽取目标：可以是关键词列表或自然语言描述",
                            "examples": [
                                "合同金额，签署日期，甲方乙方",
                                "找出所有关于付款条款的内容",
                                "提取摘要和结论部分",
                                "文档中提到的所有人名和职位"
                            ]
                        },
                        "include_citations": {
                            "type": "boolean",
                            "description": "是否包含原文引用",
                            "default": False
                        },
                        "max_pages": {
                            "type": "integer",
                            "description": "最大处理页数（0=全部，受配置限制）",
                            "default": 0
                        },
                        "chunk_size": {
                            "type": "integer",
                            "description": "每批处理的页数（大文件调小此值）",
                            "default": 10
                        }
                    },
                    "required": ["file_path", "query"]
                }
            ),
            Tool(
                name="pdf_info",
                description="获取 PDF 文件的基本信息（页数、大小、元数据等）",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "PDF 文件路径"
                        }
                    },
                    "required": ["file_path"]
                }
            ),
            Tool(
                name="pdf_validate",
                description="验证 PDF 文件是否有效且可处理",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "PDF 文件路径"
                        }
                    },
                    "required": ["file_path"]
                }
            )
        ]
    
    async def handle_tool(
        self,
        name: str,
        arguments: Optional[dict[str, Any]] = None,
    ) -> list[TextContent | ErrorContent]:
        """Handle tool call."""
        args = arguments or {}
        
        try:
            if name == "pdf_extract":
                return await self._handle_extract(args)
            elif name == "pdf_info":
                return await self._handle_info(args)
            elif name == "pdf_validate":
                return await self._handle_validate(args)
            else:
                return [ErrorContent(type="text", text=f"Unknown tool: {name}")]
        except FileNotFoundError as e:
            return [ErrorContent(type="text", text=str(e))]
        except Exception as e:
            return [ErrorContent(type="text", text=f"Error: {e}")]
    
    async def _handle_extract(
        self,
        args: dict[str, Any],
    ) -> list[TextContent | ErrorContent]:
        """Handle pdf_extract tool."""
        file_path = args.get("file_path")
        query = args.get("query")
        include_citations = args.get("include_citations", False)
        max_pages = args.get("max_pages", 0)
        chunk_size = args.get("chunk_size", 10)
        
        if not file_path or not query:
            return [ErrorContent(
                type="text",
                text="Missing required arguments: file_path and query"
            )]
        
        # Validate file
        is_valid, error = validate_pdf_file(
            file_path,
            max_size_mb=self.config.max_file_size_mb,
        )
        if not is_valid:
            return [ErrorContent(type="text", text=error)]
        
        # Apply page limits
        if max_pages == 0:
            max_pages = self.config.default_max_pages
        max_pages = min(max_pages, self.config.hard_max_pages)
        
        # Process PDF
        with PDFReader(file_path) as reader:
            total_pages = reader.total_pages
            
            # Check if chunked processing is needed
            if total_pages > self.config.max_pages_per_request:
                # Chunked processing for large files
                chunks = list(reader.iter_page_chunks(
                    chunk_size=chunk_size,
                    overlap=self.config.chunk_overlap_pages,
                    max_pages=max_pages,
                ))
                
                result = self.extractor.extract_from_chunks(
                    chunks,
                    query,
                    include_citations,
                )
            else:
                # Single request for small files
                pages = list(reader.iter_pages(max_pages=max_pages))
                text = "\n\n".join(
                    f"--- 第{p.page_number}页 ---\n{p.text}"
                    for p in pages
                )
                result = self.extractor.extract(
                    text,
                    query,
                    include_citations,
                )
        
        # Build response
        response_data = {
            "success": result.error is None,
            "file": file_path,
            "query": query,
            "total_pages": total_pages,
            "processed_pages": min(max_pages, total_pages),
            "extracted": result.extracted,
        }
        
        if include_citations and result.citations:
            response_data["citations"] = result.citations
        
        if result.error:
            response_data["error"] = result.error
        
        return [TextContent(
            type="text",
            text=json.dumps(response_data, ensure_ascii=False, indent=2),
        )]
    
    async def _handle_info(
        self,
        args: dict[str, Any],
    ) -> list[TextContent | ErrorContent]:
        """Handle pdf_info tool."""
        file_path = args.get("file_path")
        
        if not file_path:
            return [ErrorContent(
                type="text",
                text="Missing required argument: file_path"
            )]
        
        is_valid, error = validate_pdf_file(file_path)
        if not is_valid:
            return [ErrorContent(type="text", text=error)]
        
        with PDFReader(file_path) as reader:
            meta = reader.get_metadata()
        
        response_data = {
            "file": file_path,
            "total_pages": meta.total_pages,
            "file_size_bytes": meta.file_size_bytes,
            "file_size_mb": round(meta.file_size_bytes / (1024 * 1024), 2),
            "metadata": {
                "title": meta.title,
                "author": meta.author,
                "subject": meta.subject,
            }
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(response_data, ensure_ascii=False, indent=2),
        )]
    
    async def _handle_validate(
        self,
        args: dict[str, Any],
    ) -> list[TextContent | ErrorContent]:
        """Handle pdf_validate tool."""
        file_path = args.get("file_path")
        
        if not file_path:
            return [ErrorContent(
                type="text",
                text="Missing required argument: file_path"
            )]
        
        is_valid, error = validate_pdf_file(
            file_path,
            max_size_mb=self.config.max_file_size_mb,
        )
        
        response_data = {
            "file": file_path,
            "valid": is_valid,
            "error": error if not is_valid else None,
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(response_data, ensure_ascii=False, indent=2),
        )]
