#!/usr/bin/env python3
"""
MCP Server 启动脚本 - pdf_extract 服务

启动后通过 stdio 接收 MCP 协议请求
"""

import sys
import os
import json
import re
import requests

# ==================== 配置 ====================
API_KEY = "sk-93947c4a61294a37aef9d592a0e155f1"
API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
# =============================================

def read_pdf(file_path):
    """读取 PDF 文件内容"""
    with open(file_path, 'rb') as f:
        content = f.read().decode('latin-1')
    text_matches = re.findall(r'\(([^)]+)\)', content)
    return '\n'.join(text_matches)

def validate_pdf(file_path):
    """验证 PDF 文件"""
    if not os.path.exists(file_path):
        return False, f"文件不存在：{file_path}"
    if not file_path.lower().endswith('.pdf'):
        return False, "文件必须是 PDF 格式"
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if file_size_mb > 100:
        return False, f"文件太大：{file_size_mb:.1f}MB"
    return True, ""

def extract_info(text, query, include_citations=False):
    """调用 AI 抽取信息"""
    prompt = f"""你是一位专业的文档信息抽取专家。请从以下文本中提取关键信息。

## 抽取目标
{query}

## 文档内容
{text}

## 输出要求
1. 请严格按照 JSON 格式输出
2. 只返回提取到的信息，不要包含其他解释
3. 使用中文作为字段名

## 提取结果（JSON 格式）
"""
    
    response = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={
            "model": "qwen-plus",
            "input": {"messages": [{"role": "user", "content": prompt}]},
            "parameters": {"max_tokens": 2000, "temperature": 0.1, "result_format": "message"}
        },
        timeout=60,
    )
    
    result = response.json()
    ai_response = result["output"]["choices"][0]["message"]["content"]
    cleaned = ai_response.strip('```json').strip('```').strip()
    return json.loads(cleaned)

def handle_pdf_extract(args):
    """处理 pdf_extract 工具调用"""
    file_path = args.get("file_path")
    query = args.get("query")
    include_citations = args.get("include_citations", False)
    
    if not file_path or not query:
        return {"success": False, "error": "缺少必需参数：file_path 和 query"}
    
    is_valid, error = validate_pdf(file_path)
    if not is_valid:
        return {"success": False, "error": error}
    
    text = read_pdf(file_path)
    extracted = extract_info(text, query, include_citations)
    
    return {
        "success": True,
        "file": file_path,
        "query": query,
        "extracted": extracted
    }

def handle_pdf_info(args):
    """处理 pdf_info 工具调用"""
    file_path = args.get("file_path")
    
    if not file_path:
        return {"error": "缺少必需参数：file_path"}
    
    is_valid, error = validate_pdf(file_path)
    if not is_valid:
        return {"error": error}
    
    file_size = os.path.getsize(file_path)
    
    return {
        "file": file_path,
        "total_pages": 1,
        "file_size_bytes": file_size,
        "file_size_mb": round(file_size / (1024 * 1024), 2)
    }

def handle_pdf_validate(args):
    """处理 pdf_validate 工具调用"""
    file_path = args.get("file_path")
    
    if not file_path:
        return {"error": "缺少必需参数：file_path"}
    
    is_valid, error = validate_pdf(file_path)
    
    return {
        "file": file_path,
        "valid": is_valid,
        "error": error if not is_valid else None
    }

def handle_request(request):
    """处理 MCP 请求"""
    method = request.get("method")
    params = request.get("params", {})
    request_id = request.get("id", 1)
    
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": "file-master", "version": "0.1.0"},
                "capabilities": {"tools": {}}
            }
        }
    
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": [
                    {
                        "name": "pdf_extract",
                        "description": "从 PDF 文件中提取关键信息",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "file_path": {"type": "string", "description": "PDF 文件路径"},
                                "query": {"type": "string", "description": "抽取目标"},
                                "include_citations": {"type": "boolean", "default": False}
                            },
                            "required": ["file_path", "query"]
                        }
                    },
                    {
                        "name": "pdf_info",
                        "description": "获取 PDF 文件基本信息",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "file_path": {"type": "string", "description": "PDF 文件路径"}
                            },
                            "required": ["file_path"]
                        }
                    },
                    {
                        "name": "pdf_validate",
                        "description": "验证 PDF 文件",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "file_path": {"type": "string", "description": "PDF 文件路径"}
                            },
                            "required": ["file_path"]
                        }
                    }
                ]
            }
        }
    
    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "pdf_extract":
            result = handle_pdf_extract(arguments)
        elif tool_name == "pdf_info":
            result = handle_pdf_info(arguments)
        elif tool_name == "pdf_validate":
            result = handle_pdf_validate(arguments)
        else:
            result = {"error": f"未知工具：{tool_name}"}
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]
            }
        }
    
    else:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32601, "message": f"未知方法：{method}"}
        }

def main():
    """主函数 - 通过 stdio 接收请求"""
    print("[INFO] File Master MCP Server 启动", file=sys.stderr)
    print(f"[INFO] 工作目录：{os.getcwd()}", file=sys.stderr)
    print(f"[INFO] API: qwen-plus", file=sys.stderr)
    print("[INFO] 等待请求...", file=sys.stderr)
    
    # 输出初始化完成信号
    sys.stderr.flush()
    
    # 读取 stdin 并处理请求
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            response = handle_request(request)
            print(json.dumps(response, ensure_ascii=False))
            sys.stdout.flush()
        except json.JSONDecodeError as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"JSON 解析错误：{e}"}
            }
            print(json.dumps(error_response))
            sys.stdout.flush()
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": f"内部错误：{e}"}
            }
            print(json.dumps(error_response))
            sys.stdout.flush()

if __name__ == "__main__":
    main()
