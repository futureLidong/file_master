"""AI-powered information extraction service."""

import json
import re
from dataclasses import dataclass, field
from typing import Any, Optional
import requests

from ..config import Config


@dataclass
class ExtractionResult:
    """Result of information extraction."""
    extracted: dict[str, Any]
    citations: list[dict] = field(default_factory=list)
    confidence: float = 1.0
    raw_response: str = ""
    error: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "extracted": self.extracted,
            "citations": self.citations,
            "confidence": self.confidence,
            "error": self.error,
        }


class Extractor:
    """
    AI-powered information extractor using Bailian/Qwen API.
    
    Features:
    - Natural language query support
    - Structured JSON output
    - Citation extraction (optional)
    - Error handling and retry
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.api_url = f"{config.api_base_url}/services/aigc/text-generation/generation"
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        })
    
    def extract(
        self,
        text: str,
        query: str,
        include_citations: bool = False,
        max_tokens: int = 4000,
    ) -> ExtractionResult:
        """
        Extract information from text based on query.
        
        Args:
            text: Input text to extract from
            query: Natural language description or keywords
            include_citations: Whether to include source citations
            max_tokens: Maximum output tokens
        
        Returns:
            ExtractionResult with extracted data
        """
        # Truncate text if too long (leave room for prompt and response)
        # Rough estimate: 1 token ≈ 4 Chinese characters
        max_text_chars = (max_tokens - 500) * 4
        if len(text) > max_text_chars:
            text = text[:max_text_chars] + "\n\n...[内容已截断]"
        
        # Build prompt
        prompt = self._build_prompt(text, query, include_citations)
        
        try:
            response = self._call_api(prompt, max_tokens)
            return self._parse_response(response, include_citations)
        except requests.exceptions.Timeout:
            return ExtractionResult(
                extracted={},
                error="API request timeout",
            )
        except requests.exceptions.RequestException as e:
            return ExtractionResult(
                extracted={},
                error=f"API request failed: {e}",
            )
        except json.JSONDecodeError as e:
            return ExtractionResult(
                extracted={},
                error=f"Failed to parse AI response: {e}",
            )
    
    def _build_prompt(
        self,
        text: str,
        query: str,
        include_citations: bool,
    ) -> str:
        """Build the extraction prompt."""
        citation_instruction = ""
        if include_citations:
            citation_instruction = """
对于每个提取的信息，请同时提供原文引用（citation），包括：
- 原文片段：直接引用相关原文
- 页码/位置：如果有的话

引用格式：
{
  "field_name": {
    "value": "提取的值",
    "citation": {
      "text": "原文片段",
      "position": "位置信息"
    }
  }
}
"""
        
        prompt = f"""你是一位专业的文档信息抽取专家。请从以下文本中提取关键信息。

## 抽取目标
{query}

## 文档内容
{text}

## 输出要求
1. 请严格按照 JSON 格式输出
2. 只返回提取到的信息，不要包含其他解释
3. 如果某个信息不存在，返回 null 或省略该字段
4. 保持字段名称简洁明了（使用中文或英文均可）
{citation_instruction}
## 提取结果（JSON 格式）
"""
        return prompt
    
    def _call_api(self, prompt: str, max_tokens: int) -> str:
        """Call Bailian API."""
        payload = {
            "model": self.config.model,
            "input": {
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个专业的信息抽取助手，输出严格的 JSON 格式，不包含 markdown 代码块标记。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            },
            "parameters": {
                "max_tokens": max_tokens,
                "temperature": 0.1,  # Low temperature for consistent extraction
                "result_format": "message",
            }
        }
        
        response = self._session.post(
            self.api_url,
            json=payload,
            timeout=self.config.api_timeout_seconds,
        )
        response.raise_for_status()
        
        result = response.json()
        return result["output"]["choices"][0]["message"]["content"]
    
    def _parse_response(
        self,
        response_text: str,
        include_citations: bool,
    ) -> ExtractionResult:
        """Parse AI response into structured result."""
        # Clean up response (remove markdown code blocks if present)
        cleaned = self._clean_json_response(response_text)
        
        # Parse JSON
        data = json.loads(cleaned)
        
        # Separate extracted data and citations
        extracted = {}
        citations = []
        
        for key, value in data.items():
            if isinstance(value, dict) and "value" in value and "citation" in value:
                # Has citation structure
                extracted[key] = value["value"]
                if include_citations:
                    citations.append({
                        "field": key,
                        "text": value["citation"].get("text", ""),
                        "position": value["citation"].get("position", ""),
                    })
            else:
                extracted[key] = value
        
        return ExtractionResult(
            extracted=extracted,
            citations=citations,
            raw_response=response_text,
        )
    
    def _clean_json_response(self, text: str) -> str:
        """Clean JSON response by removing markdown and extra whitespace."""
        # Remove markdown code blocks
        text = re.sub(r'^```json\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'^```\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^```$', '', text, flags=re.MULTILINE)
        
        # Strip whitespace
        text = text.strip()
        
        return text
    
    def extract_from_chunks(
        self,
        chunks: list[tuple[list[int], str]],
        query: str,
        include_citations: bool = False,
    ) -> ExtractionResult:
        """
        Extract information from multiple chunks and merge results.
        
        Args:
            chunks: List of (page_numbers, text) tuples
            query: Extraction query
            include_citations: Whether to include citations
        
        Returns:
            Merged ExtractionResult
        """
        all_results = []
        
        for page_nums, text in chunks:
            result = self.extract(text, query, include_citations)
            if result.error:
                continue
            all_results.append((page_nums, result))
        
        if not all_results:
            return ExtractionResult(
                extracted={},
                error="All chunk extractions failed",
            )
        
        # Merge results (later chunks override earlier for same keys)
        merged = {}
        all_citations = []
        
        for page_nums, result in all_results:
            merged.update(result.extracted)
            for citation in result.citations:
                citation["pages"] = page_nums
                all_citations.append(citation)
        
        return ExtractionResult(
            extracted=merged,
            citations=all_citations,
        )
