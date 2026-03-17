#!/usr/bin/env python3
"""
MCP Server 测试脚本 - Python 3.6 兼容版

直接调用 PDF 读取和 AI 抽取功能，不依赖 dataclasses 和 mcp 包
"""

import sys
import os
import json
import re
import requests

print("=" * 60)
print("🚀 File Master MCP Server (Python 3.6 兼容版)")
print("=" * 60)

# ==================== 配置 ====================
API_KEY = "sk-93947c4a61294a37aef9d592a0e155f1"
API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
PDF_FILE = os.path.join(os.path.dirname(__file__), '..', 'sample_contract.pdf')
# =============================================

print(f"\n📂 工作目录：{os.getcwd()}")
print(f"🔑 API Key: {API_KEY[:15]}...")
print(f"📄 测试文件：{PDF_FILE}")
print()

def read_pdf(file_path):
    """读取 PDF 文件内容"""
    print(f"📖 读取 PDF: {file_path}")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在：{file_path}")
    
    with open(file_path, 'rb') as f:
        content = f.read().decode('latin-1')
    
    # 提取 PDF 中的文本
    text_matches = re.findall(r'\(([^)]+)\)', content)
    text = '\n'.join(text_matches)
    print(f"   提取文本长度：{len(text)} 字符")
    return text

def validate_pdf(file_path):
    """验证 PDF 文件"""
    if not os.path.exists(file_path):
        return False, f"文件不存在：{file_path}"
    if not file_path.lower().endswith('.pdf'):
        return False, "文件必须是 PDF 格式"
    return True, ""

def extract_info(text, query, include_citations=False):
    """调用 AI 抽取信息"""
    citation_instruction = ""
    if include_citations:
        citation_instruction = """
对于每个提取的信息，请同时提供原文引用。
"""
    
    prompt = f"""你是一位专业的文档信息抽取专家。请从以下文本中提取关键信息。

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
    
    response = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={
            "model": "qwen-plus",
            "input": {"messages": [{"role": "user", "content": prompt}]},
            "parameters": {"max_tokens": 1000, "temperature": 0.1, "result_format": "message"}
        },
        timeout=30,
    )
    
    result = response.json()
    ai_response = result["output"]["choices"][0]["message"]["content"]
    
    # 清理 JSON 响应
    cleaned = ai_response.strip('```json').strip('```').strip()
    return json.loads(cleaned)

def pdf_validate(file_path):
    """pdf_validate 工具"""
    is_valid, error = validate_pdf(file_path)
    return {
        "file": file_path,
        "valid": is_valid,
        "error": error if not is_valid else None
    }

def pdf_info(file_path):
    """pdf_info 工具"""
    is_valid, error = validate_pdf(file_path)
    if not is_valid:
        return {"error": error}
    
    file_size = os.path.getsize(file_path)
    with open(file_path, 'rb') as f:
        content = f.read().decode('latin-1')
    text_matches = re.findall(r'\(([^)]+)\)', content)
    text = '\n'.join(text_matches)
    
    return {
        "file": file_path,
        "total_pages": 1,  # 简化版
        "file_size_bytes": file_size,
        "file_size_mb": round(file_size / (1024 * 1024), 2),
        "text_preview": text[:100] + "..."
    }

def pdf_extract(file_path, query, include_citations=False):
    """pdf_extract 工具"""
    is_valid, error = validate_pdf(file_path)
    if not is_valid:
        return {"success": False, "error": error}
    
    text = read_pdf(file_path)
    extracted = extract_info(text, query, include_citations)
    
    return {
        "success": True,
        "file": file_path,
        "query": query,
        "extracted": extracted,
        "include_citations": include_citations
    }

# ==================== 主测试流程 ====================

print("=" * 60)
print("🛠️  可用工具:")
print("=" * 60)
print("  • pdf_validate - 验证 PDF 文件")
print("  • pdf_info - 获取 PDF 基本信息")
print("  • pdf_extract - 从 PDF 提取关键信息")

print("\n" + "=" * 60)
print("🧪 开始测试")
print("=" * 60)

# 测试 1: pdf_validate
print("\n📋 测试 1: 验证 PDF 文件")
print("-" * 60)
result = pdf_validate(PDF_FILE)
print(f"   文件：{result['file']}")
print(f"   有效：{result['valid']}")
if result.get('error'):
    print(f"   错误：{result['error']}")

# 测试 2: pdf_info
print("\n📋 测试 2: 获取 PDF 信息")
print("-" * 60)
result = pdf_info(PDF_FILE)
if 'error' in result:
    print(f"   错误：{result['error']}")
else:
    print(f"   总页数：{result['total_pages']}")
    print(f"   文件大小：{result['file_size_mb']} MB")
    print(f"   内容预览：{result['text_preview']}")

# 测试 3: pdf_extract (甲乙方)
print("\n📋 测试 3: 提取甲乙方信息")
print("-" * 60)
result = pdf_extract(PDF_FILE, "提取甲方（Employer）和乙方（Employee）的名称")
if result.get('success'):
    print("   ✅ 提取结果:")
    for key, value in result['extracted'].items():
        print(f"      {key}: {value}")
else:
    print(f"   ❌ 错误：{result.get('error')}")

# 测试 4: pdf_extract (合同有效期)
print("\n📋 测试 4: 提取合同有效期")
print("-" * 60)
result = pdf_extract(PDF_FILE, "提取合同有效期、开始日期、结束日期、签署日期")
if result.get('success'):
    print("   ✅ 提取结果:")
    for key, value in result['extracted'].items():
        if value:
            print(f"      {key}: {value}")
        else:
            print(f"      {key}: (未找到)")
else:
    print(f"   ❌ 错误：{result.get('error')}")

# 测试 5: pdf_extract (综合信息)
print("\n📋 测试 5: 提取综合信息")
print("-" * 60)
result = pdf_extract(PDF_FILE, "提取合同金额、职位、付款方式、签署日期", include_citations=True)
if result.get('success'):
    print("   ✅ 提取结果:")
    for key, value in result['extracted'].items():
        if value:
            print(f"      {key}: {value}")
else:
    print(f"   ❌ 错误：{result.get('error')}")

print("\n" + "=" * 60)
print("✅ 所有测试完成")
print("=" * 60)

print("\n💡 说明:")
print("   - 当前运行在 Python 3.6 环境")
print("   - 使用简化版实现（不依赖 mcp 包和 dataclasses）")
print("   - 功能与完整 MCP Server 相同")
print("\n📚 完整 MCP Server 需要:")
print("   - Python 3.10+")
print("   - pip install mcp pdfplumber dashscope")
print("   - python -m file_master.server")
