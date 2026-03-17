"""AI-powered information extraction service - V3 with full context preservation."""

import json
import re
from dataclasses import dataclass, field
from typing import Any, Optional
import requests

from ..config import Config


@dataclass
class CandidateValue:
    """A candidate value with full context."""
    value: str                    # 提取的值
    pages: list[int]              # 页码范围
    raw_text: str                 # 原文片段（上下文）
    extraction_prompt: str        # 提取时使用的 prompt
    ai_reasoning: str             # AI 提取时的判断依据
    confidence: float             # 提取时的置信度
    position_info: dict           # 详细位置信息
    
    def to_dict(self) -> dict:
        return {
            "value": self.value,
            "pages": self.pages,
            "raw_text": self.raw_text,
            "extraction_prompt": self.extraction_prompt,
            "ai_reasoning": self.ai_reasoning,
            "confidence": self.confidence,
            "position_info": self.position_info,
        }


@dataclass
class ExtractionResult:
    """Result with all candidates and context."""
    extracted: dict[str, Any]
    citations: list[dict] = field(default_factory=list)
    candidates: dict[str, list[CandidateValue]] = field(default_factory=dict)
    error: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "extracted": self.extracted,
            "citations": self.citations,
            "candidates": {
                k: [c.to_dict() for c in v] 
                for k, v in self.candidates.items()
            },
            "error": self.error,
        }


class ExtractorV3:
    """
    Extractor with full context preservation for accurate merging.
    
    Key improvements:
    1. Preserve original text snippets for each extraction
    2. Include AI reasoning for each candidate
    3. Use context-aware scoring
    4. AI judgment with full context
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.api_url = f"{config.api_base_url}/services/aigc/text-generation/generation"
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        })
    
    def extract_with_context(
        self,
        text: str,
        query: str,
        page_numbers: list[int],
        include_reasoning: bool = True,
    ) -> ExtractionResult:
        """
        Extract with full context and reasoning.
        
        Args:
            text: Document text
            query: Extraction query
            page_numbers: Page numbers for this text chunk
            include_reasoning: Whether to include AI reasoning for each field
        """
        # Build prompt that asks for reasoning and context
        prompt = self._build_contextual_prompt(text, query, include_reasoning)
        
        try:
            response = self._call_api(prompt, max_tokens=3000)
            result = self._parse_with_context(response, text, page_numbers)
            return result
        except Exception as e:
            return ExtractionResult(extracted={}, error=str(e))
    
    def _build_contextual_prompt(self, text: str, query: str, include_reasoning: bool) -> str:
        """Build prompt that requests context and reasoning."""
        
        reasoning_instruction = ""
        if include_reasoning:
            reasoning_instruction = """
对于每个提取的字段，请同时提供：
- reason: 提取依据（引用原文或说明判断理由）
- confidence: 置信度（0.0-1.0）
- context: 原文片段（包含该信息的完整句子或段落，最多 100 字）
"""
        
        return f"""你是一位专业的文档信息抽取专家。请从以下文本中提取关键信息。

## 抽取目标
{query}

## 文档内容
{text}

## 输出要求
1. 请严格按照 JSON 格式输出
2. 对每个字段，提供完整结构：
   {{
     "字段名": {{
       "value": "提取值",
       "reason": "判断依据",
       "confidence": 0.9,
       "context": "原文片段"
     }}
   }}
3. 如果信息不存在，省略该字段
{reasoning_instruction}
## 提取结果（JSON 格式）
"""
    
    def _parse_with_context(
        self,
        response_text: str,
        source_text: str,
        page_numbers: list[int],
    ) -> ExtractionResult:
        """Parse response with full context."""
        cleaned = self._clean_json_response(response_text)
        data = json.loads(cleaned)
        
        extracted = {}
        candidates = {}
        citations = []
        
        for field_name, field_data in data.items():
            if isinstance(field_data, dict):
                # Structured format with context
                value = field_data.get("value", "")
                reason = field_data.get("reason", "")
                confidence = field_data.get("confidence", 0.5)
                context = field_data.get("context", "")
                
                extracted[field_name] = value
                
                candidate = CandidateValue(
                    value=value,
                    pages=page_numbers,
                    raw_text=context,
                    extraction_prompt="",  # Will be filled later
                    ai_reasoning=reason,
                    confidence=confidence,
                    position_info={
                        "context_length": len(context),
                        "value_length": len(value),
                    }
                )
                
                if field_name not in candidates:
                    candidates[field_name] = []
                candidates[field_name].append(candidate)
                
                if context:
                    citations.append({
                        "field": field_name,
                        "text": context,
                        "pages": page_numbers,
                    })
            else:
                # Simple format (backward compatibility)
                extracted[field_name] = field_data
                candidate = CandidateValue(
                    value=field_data,
                    pages=page_numbers,
                    raw_text="",
                    extraction_prompt="",
                    ai_reasoning="",
                    confidence=0.5,
                    position_info={}
                )
                if field_name not in candidates:
                    candidates[field_name] = []
                candidates[field_name].append(candidate)
        
        return ExtractionResult(
            extracted=extracted,
            citations=citations,
            candidates=candidates,
        )
    
    def merge_with_context(
        self,
        all_results: list[ExtractionResult],
        query: str,
    ) -> ExtractionResult:
        """
        Merge multiple extraction results with full context.
        
        Strategy:
        1. Collect all candidates with their context
        2. Use context-aware scoring
        3. AI judgment with full context for conflicts
        """
        # Collect all candidates
        merged_candidates: dict[str, list[CandidateValue]] = {}
        all_citations = []
        
        for result in all_results:
            for field_name, candidates in result.candidates.items():
                if field_name not in merged_candidates:
                    merged_candidates[field_name] = []
                merged_candidates[field_name].extend(candidates)
            
            all_citations.extend(result.citations)
        
        # Score and select best candidate for each field
        final_extracted = {}
        final_citations = []
        conflicts = []
        
        for field_name, candidates in merged_candidates.items():
            if len(candidates) == 1:
                # Only one candidate - use it
                final_extracted[field_name] = candidates[0].value
                if candidates[0].raw_text:
                    final_citations.append({
                        "field": field_name,
                        "text": candidates[0].raw_text,
                        "pages": candidates[0].pages,
                    })
            else:
                # Multiple candidates - need to resolve conflict
                conflicts.append((field_name, candidates))
        
        # Resolve conflicts with AI (providing full context)
        if conflicts:
            resolved = self._resolve_conflicts_with_context(query, conflicts)
            for field_name, resolution in resolved.items():
                final_extracted[field_name] = resolution["value"]
                if resolution.get("context"):
                    final_citations.append({
                        "field": field_name,
                        "text": resolution["context"],
                        "pages": resolution["pages"],
                    })
        
        return ExtractionResult(
            extracted=final_extracted,
            citations=final_citations,
            candidates=merged_candidates,
        )
    
    def _resolve_conflicts_with_context(
        self,
        query: str,
        conflicts: list[tuple[str, list[CandidateValue]]],
    ) -> dict[str, Any]:
        """
        Resolve conflicts using AI with full context.
        
        This is the key improvement: AI can see the original text
        for each candidate, not just the extracted value.
        """
        # Build detailed conflict report
        conflict_text = ""
        for field_name, candidates in conflicts:
            conflict_text += f"\n【{field_name}】的多个提取结果:\n"
            for i, c in enumerate(candidates):
                conflict_text += f"\n  候选{i+1}:\n"
                conflict_text += f"    提取值：{c.value}\n"
                conflict_text += f"    页码：{c.pages}\n"
                conflict_text += f"    原文：{c.raw_text[:200]}...\n" if len(c.raw_text) > 200 else f"    原文：{c.raw_text}\n"
                conflict_text += f"    AI 理由：{c.ai_reasoning}\n"
                conflict_text += f"    置信度：{c.confidence}\n"
        
        prompt = f"""请判断以下字段的最佳提取值。

## 原始查询
{query}

## 冲突字段及候选值{conflict_text}

## 判断标准
1. 原文上下文最清晰明确
2. 信息最完整具体
3. AI 提取理由最充分
4. 置信度评分最高

## 输出格式
返回 JSON 格式，每个字段对应最佳候选的索引（从 1 开始），并说明理由：
{{
  "字段名": {{
    "selected_index": 最佳候选索引，
    "reason": "选择理由"
  }}
}}
"""
        
        try:
            response = self._call_api(prompt, max_tokens=2000)
            selections = json.loads(response)
            
            result = {}
            for (field_name, candidates), selection_data in zip(conflicts, selections.values()):
                idx = selection_data.get("selected_index", 1)
                if 1 <= idx <= len(candidates):
                    best = candidates[idx - 1]
                    result[field_name] = {
                        "value": best.value,
                        "context": best.raw_text,
                        "pages": best.pages,
                        "selection_reason": selection_data.get("reason", ""),
                    }
                else:
                    best = candidates[0]
                    result[field_name] = {
                        "value": best.value,
                        "context": best.raw_text,
                        "pages": best.pages,
                    }
            
            return result
        except Exception as e:
            # Fallback: use highest confidence
            return {
                field_name: {
                    "value": max(candidates, key=lambda c: c.confidence).value,
                    "context": max(candidates, key=lambda c: c.confidence).raw_text,
                    "pages": max(candidates, key=lambda c: c.confidence).pages,
                }
                for field_name, candidates in conflicts
            }
    
    def extract_from_chunks(
        self,
        chunks: list[tuple[list[int], str]],
        query: str,
        include_citations: bool = True,
    ) -> ExtractionResult:
        """Extract from chunks with full context preservation."""
        all_results = []
        
        # Extract from each chunk with context
        for page_nums, text in chunks:
            result = self.extract_with_context(text, query, page_nums)
            if result.error:
                continue
            all_results.append(result)
        
        if not all_results:
            return ExtractionResult(
                extracted={},
                error="All chunk extractions failed",
            )
        
        # Merge with context-aware conflict resolution
        final = self.merge_with_context(all_results, query)
        
        if include_citations:
            return final
        else:
            return ExtractionResult(
                extracted=final.extracted,
                candidates=final.candidates,
            )
    
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
    
    def _clean_json_response(self, text: str) -> str:
        """Clean JSON response."""
        text = re.sub(r'^```json\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'^```\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^```$', '', text, flags=re.MULTILINE)
        return text.strip()
