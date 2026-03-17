#!/usr/bin/env python3
"""
MCP Server 后台守护版本

以 HTTP 方式运行，可长期后台服务
"""

import sys
import os
import json
import re
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import logging

# ==================== 配置 ====================
API_KEY = "sk-93947c4a61294a37aef9d592a0e155f1"
API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
HOST = "127.0.0.1"
PORT = 8765
# =============================================

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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


class MCPRequestHandler(BaseHTTPRequestHandler):
    """HTTP 请求处理器"""
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        logger.info(f"{self.address_string()} - {format % args}")
    
    def do_GET(self):
        """处理 GET 请求"""
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response = {"status": "ok", "service": "file-master-mcp"}
            self.wfile.write(json.dumps(response).encode())
        
        elif self.path == "/tools":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            tools = {
                "tools": [
                    {
                        "name": "pdf_extract",
                        "description": "从 PDF 文件中提取关键信息",
                        "endpoint": "/call/pdf_extract"
                    },
                    {
                        "name": "pdf_info",
                        "description": "获取 PDF 文件基本信息",
                        "endpoint": "/call/pdf_info"
                    },
                    {
                        "name": "pdf_validate",
                        "description": "验证 PDF 文件",
                        "endpoint": "/call/pdf_validate"
                    }
                ]
            }
            self.wfile.write(json.dumps(tools, ensure_ascii=False).encode())
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        """处理 POST 请求"""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        
        try:
            request = json.loads(body)
        except json.JSONDecodeError:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            error = {"error": "无效的 JSON 格式"}
            self.wfile.write(json.dumps(error).encode())
            return
        
        # 处理 MCP 协议请求
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id", 1)
        
        if method == "tools/list":
            response = {
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
                                    "file_path": {"type": "string"},
                                    "query": {"type": "string"},
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
                                    "file_path": {"type": "string"}
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
                                    "file_path": {"type": "string"}
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
            
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]
                }
            }
        
        else:
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"未知方法：{method}"}
            }
        
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode())


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("🚀 File Master MCP Server (HTTP 守护版)")
    logger.info("=" * 60)
    logger.info(f"📍 监听地址：http://{HOST}:{PORT}")
    logger.info(f"🔑 API: qwen-plus")
    logger.info(f"📂 工作目录：{os.getcwd()}")
    logger.info("=" * 60)
    
    server = HTTPServer((HOST, PORT), MCPRequestHandler)
    
    logger.info("✅ 服务启动成功")
    logger.info("📡 等待请求...")
    logger.info("")
    logger.info("可用端点:")
    logger.info(f"  GET  http://{HOST}:{PORT}/health    - 健康检查")
    logger.info(f"  GET  http://{HOST}:{PORT}/tools     - 工具列表")
    logger.info(f"  POST http://{HOST}:{PORT}/          - MCP 协议调用")
    logger.info("")
    logger.info("示例调用:")
    logger.info(f'  curl http://{HOST}:{PORT}/health')
    logger.info(f'  curl -X POST http://{HOST}:{PORT}/ \\')
    logger.info(f'    -H "Content-Type: application/json" \\')
    logger.info(f'    -d \'{{"jsonrpc":"2.0","id":1,"method":"tools/list"}}\'')
    logger.info("=" * 60)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("\n👋 收到退出信号，关闭服务...")
        server.shutdown()
        logger.info("✅ 服务已停止")


if __name__ == "__main__":
    main()
