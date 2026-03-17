"""AI-powered information extraction service - V2 with smart merging."""

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
    candidates: dict[str, list[dict]] = field(default_factory=dict)  # 所有候选值
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "extracted": self.extracted,
            "citations": self.citations,
            "confidence": self.confidence,
            "error": self.error,
            "candidates": self.candidates,  # 包含所有候选值
        }


class ExtractorV2:
    """
    Enhanced extractor with smart merging for multi-chunk extraction.
    
    Features:
    - Collect all candidates from chunks
    - Score candidates automatically
    - AI judgment for uncertain fields
    - Cost-effective merging
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.api_url = f"{config.api_base_url}/services/aigc/text-generation/generation"
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        })
    
    def extract_from_chunks(
        self,
        chunks: list[tuple[list[int], str]],
        query: str,
        include_citations: bool = False,
    ) -> ExtractionResult:
        """
        Extract from multiple chunks with smart merging.
        
        Strategy:
        1. Extract from each chunk independently
        2. Collect all candidates for each field
        3. Auto-score candidates
        4. Use AI judgment only for uncertain fields (confidence < 0.7)
        """
        all_results = []
        
        # Step 1: Extract from each chunk
        for page_nums, text in chunks:
            result = self.extract(text, query, include_citations)
            if result.error:
                continue
            all_results.append({
                "pages": page_nums,
                "extracted": result.extracted,
                "citations": result.citations,
            })
        
        if not all_results:
            return ExtractionResult(
                extracted={},
                error="All chunk extractions failed",
            )
        
        # Step 2: Collect candidates for each field
        field_candidates = {}
        for result in all_results:
            for field_name, value in result["extracted"].items():
                if field_name not in field_candidates:
                    field_candidates[field_name] = []
                
                candidate = {
                    "value": value,
                    "pages": result["pages"],
                    "score": self._score_candidate(value, result["pages"]),
                }
                
                if include_citations:
                    for citation in result["citations"]:
                        if citation.get("field") == field_name:
                            candidate["citation"] = citation
                            break
                
                field_candidates[field_name].append(candidate)
        
        # Step 3: Merge with smart selection
        final_extracted = {}
        final_citations = []
        low_confidence_fields = []
        
        for field_name, candidates in field_candidates.items():
            # Sort by score
            candidates.sort(key=lambda c: c["score"], reverse=True)
            best = candidates[0]
            
            if best["score"] >= 0.7:
                # High confidence - use directly
                final_extracted[field_name] = best["value"]
                if "citation" in best:
                    final_citations.append(best["citation"])
            else:
                # Low confidence - need AI judgment
                low_confidence_fields.append((field_name, candidates))
        
        # Step 4: AI judgment for uncertain fields
        if low_confidence_fields:
            ai_selected = self._ai_judge_fields(query, low_confidence_fields)
            for field_name, value in ai_selected.items():
                final_extracted[field_name] = value
        
        return ExtractionResult(
            extracted=final_extracted,
            citations=final_citations,
            confidence=0.9 if not low_confidence_fields else 0.7,
            candidates=field_candidates,  # All candidates for reference
        )
    
    def _score_candidate(self, value: str, pages: list[int]) -> float:
        """
        Score a candidate value automatically.
        
        Scoring criteria:
        - Position (first/last pages are often more important)
        - Completeness (longer values often more complete)
        - Specificity (contains numbers, dates, etc.)
        - Has citation
        """
        score = 0.5  # Base score
        
        # Position score (0.0-0.2)
        if 1 in pages:  # Appears in first page
            score += 0.15
        if pages and pages[-1] > 50:  # Appears near end
            score += 0.1
        
        # Completeness score (0.0-0.2)
        if len(value) > 30:
            score += 0.2
        elif len(value) > 15:
            score += 0.1
        
        # Specificity score (0.0-0.2)
        if re.search(r'\d+', value):  # Contains numbers
            score += 0.1
        if re.search(r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?', value):  # Contains date
            score += 0.1
        if re.search(r'[万仟佰拾元角分]', value):  # Contains Chinese money words
            score += 0.1
        
        # Cap at 1.0
        return min(score, 1.0)
    
    def _ai_judge_fields(
        self,
        query: str,
        low_confidence_fields: list[tuple[str, list[dict]]],
    ) -> dict[str, Any]:
        """
        Use AI to select best values for uncertain fields.
        
        Args:
            query: Original extraction query
            low_confidence_fields: List of (field_name, candidates)
        
        Returns:
            Selected values for each field
        """
        # Build prompt
        candidates_text = ""
        for field_name, candidates in low_confidence_fields:
            candidates_text += f"\n【{field_name}】的候选值:\n"
            for i, c in enumerate(candidates):
                candidates_text += f"  {i+1}. \"{c['value']}\" (页码：{c['pages']}, 评分：{c['score']:.2f})\n"
        
        prompt = f"""请为以下字段选择最准确完整的提取值。

## 原始查询
{query}

## 候选值{candidates_text}

## 选择标准
1. 信息最完整
2. 数值最具体
3. 上下文最清晰

## 输出格式
请返回 JSON 格式，每个字段对应最佳值的索引（从 1 开始）：
{{
  "字段名": 最佳值索引
}}
"""
        
        try:
            response = self._call_api(prompt, max_tokens=500)
            selected_indices = json.loads(response)
            
            # Map indices back to values
            result = {}
            for (field_name, candidates), idx in zip(low_confidence_fields, selected_indices.values()):
                if 1 <= idx <= len(candidates):
                    result[field_name] = candidates[idx - 1]["value"]
                else:
                    result[field_name] = candidates[0]["value"]
            
            return result
        except Exception as e:
            # Fallback: use highest scored candidate
            return {
                field_name: candidates[0]["value"]
                for field_name, candidates in low_confidence_fields
            }
    
    def extract(
        self,
        text: str,
        query: str,
        include_citations: bool = False,
        max_tokens: int = 4000,
    ) -> ExtractionResult:
        """Extract from single text (same as V1)."""
        # Truncate if too long
        max_text_chars = (max_tokens - 500) * 4
        if len(text) > max_text_chars:
            text = text[:max_text_chars] + "\n\n...[内容已截断]"
        
        prompt = self._build_prompt(text, query, include_citations)
        
        try:
            response = self._call_api(prompt, max_tokens)
            return self._parse_response(response, include_citations)
        except Exception as e:
            return ExtractionResult(extracted={}, error=str(e))
    
    def _build_prompt(self, text: str, query: str, include_citations: bool) -> str:
        """Build extraction prompt."""
        citation_instruction = ""
        if include_citations:
            citation_instruction = """
对于每个提取的信息，请同时提供原文引用（citation）。
"""
        
        return f"""你是一位专业的文档信息抽取专家。请从以下文本中提取关键信息。

## 抽取目标
{query}

## 文档内容
{text}

## 输出要求
1. 请严格按照 JSON 格式输出
2. 只返回提取到的信息，不要包含其他解释
3. 使用中文作为字段名
{citation_instruction}
## 提取结果（JSON 格式）
"""
    
    def _call_api(self, prompt: str, max_tokens: int) -> str:
        """Call Bailian API."""
        payload = {
            "model": self.config.model,
            "input": {
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个专业的信息抽取助手，输出严格的 JSON 格式。"
                    },
                    {"role": "user", "content": prompt}
                ]
            },
            "parameters": {
                "max_tokens": max_tokens,
                "temperature": 0.1,
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
    
    def _parse_response(self, response_text: str, include_citations: bool) -> ExtractionResult:
        """Parse AI response."""
        cleaned = self._clean_json_response(response_text)
        data = json.loads(cleaned)
        
        extracted = {}
        citations = []
        
        for key, value in data.items():
            if isinstance(value, dict) and "value" in value and "citation" in value:
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
        """Clean JSON response."""
        text = re.sub(r'^```json\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'^```\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^```$', '', text, flags=re.MULTILINE)
        return text.strip()
