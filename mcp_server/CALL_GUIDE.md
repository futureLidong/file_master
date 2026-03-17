# MCP Server 调用指南

**目录：** `/root/.openclaw/workspace/mcp_server`  
**最后更新：** 2026-03-17 11:28 GMT+8  

---

## 📋 两种调用方式

### 方式 1：当前环境（Python 3.6）⭐ 推荐

由于当前服务器是 Python 3.6，不支持 `mcp` 包，使用简化版脚本：

```bash
cd /root/.openclaw/workspace/mcp_server
python3 test_mcp.py
```

**特点：**
- ✅ 立即可用
- ✅ 功能完整（PDF 读取 + AI 抽取）
- ✅ 结果相同
- ⚠️ 不是标准 MCP 协议

---

### 方式 2：完整 MCP Server（需要 Python 3.10+）

**前提条件：**
```bash
# 检查 Python 版本
python3 --version  # 需要 3.10+

# 安装依赖
pip install mcp pdfplumber dashscope

# 安装项目
cd /root/.openclaw/workspace
pip install -e .
```

**启动方式：**
```bash
# 方式 A：作为模块
export DASHSCOPE_API_KEY=sk-93947c4a61294a37aef9d592a0e155f1
python -m file_master.server

# 方式 B：作为命令
file-master
```

**通信方式：** stdio（标准输入输出）

---

## 🔧 手动调用方法

### 方法 1：使用测试脚本（最简单）⭐

```bash
cd /root/.openclaw/workspace/mcp_server
python3 test_mcp.py
```

**输出：**
```
✅ 提取结果:
   甲方：ABC Technology Co., Ltd.
   乙方：John Smith
```

---

### 方法 2：交互式调用脚本

创建 `call_tool.py`：

```python
#!/usr/bin/env python3
"""交互式调用 MCP 工具"""

import sys
import os
import json
import re
import requests

API_KEY = "sk-93947c4a61294a37aef9d592a0e155f1"
API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"

def call_pdf_extract(file_path, query, include_citations=False):
    """调用 pdf_extract 工具"""
    
    # 读取 PDF
    with open(file_path, 'rb') as f:
        content = f.read().decode('latin-1')
    text = '\n'.join(re.findall(r'\(([^)]+)\)', content))
    
    # 构建提示词
    prompt = f"""从以下文本中提取信息：{query}

文档内容：
{text}

返回 JSON 格式。"""
    
    # 调用 API
    response = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={
            "model": "qwen-plus",
            "input": {"messages": [{"role": "user", "content": prompt}]},
            "parameters": {"max_tokens": 1000, "temperature": 0.1}
        },
        timeout=30,
    )
    
    result = response.json()
    return json.loads(result["output"]["choices"][0]["message"]["content"])

# 交互调用
if __name__ == "__main__":
    print("📄 PDF 信息抽取工具")
    print("=" * 60)
    
    file_path = input("PDF 文件路径：../sample_contract.pdf > ") or "../sample_contract.pdf"
    query = input("抽取目标：")
    
    result = call_pdf_extract(file_path, query)
    
    print("\n✅ 提取结果:")
    for key, value in result.items():
        print(f"   {key}: {value}")
```

**运行：**
```bash
cd /root/.openclaw/workspace/mcp_server
python3 call_tool.py
```

---

### 方法 3：MCP 协议调用（完整 Server）

**启动 Server 后，通过 stdio 发送 JSON-RPC：**

```bash
# 终端 1：启动 Server
cd /root/.openclaw/workspace
export DASHSCOPE_API_KEY=sk-xxx
python -m file_master.server
```

```bash
# 终端 2：发送请求
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python -m file_master.server
```

**请求格式（JSON-RPC 2.0）：**

```json
// 1. 获取工具列表
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list"
}

// 响应:
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      {
        "name": "pdf_extract",
        "description": "从 PDF 提取关键信息",
        "inputSchema": {...}
      }
    ]
  }
}

// 2. 调用工具
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "pdf_extract",
    "arguments": {
      "file_path": "/path/to/file.pdf",
      "query": "提取甲乙方"
    }
  }
}
```

---

### 方法 4：通过 MCP Client 集成

**Claude Desktop 配置示例：**

```json
// claude_desktop_config.json
{
  "mcpServers": {
    "file-master": {
      "command": "python",
      "args": ["-m", "file_master.server"],
      "env": {
        "DASHSCOPE_API_KEY": "sk-xxx"
      },
      "cwd": "/root/.openclaw/workspace"
    }
  }
}
```

**然后直接在 Claude 中说：**
```
帮我提取这个 PDF 的甲乙方信息：/path/to/contract.pdf
```

---

## 📝 调用示例

### 示例 1：提取甲乙方

**输入：**
```bash
cd /root/.openclaw/workspace/mcp_server
python3 -c "
import json
from test_mcp import pdf_extract

result = pdf_extract('../sample_contract.pdf', '提取甲方和乙方名称')
print(json.dumps(result, indent=2, ensure_ascii=False))
"
```

**输出：**
```json
{
  "success": true,
  "file": "../sample_contract.pdf",
  "query": "提取甲方和乙方名称",
  "extracted": {
    "甲方": "ABC Technology Co., Ltd.",
    "乙方": "John Smith"
  }
}
```

---

### 示例 2：提取合同金额

**输入：**
```bash
python3 -c "
from test_mcp import pdf_extract
import json

result = pdf_extract('../sample_contract.pdf', '提取合同金额')
print(json.dumps(result['extracted'], indent=2))
"
```

**输出：**
```json
{
  "合同金额": "RMB 500,000 per annum"
}
```

---

### 示例 3：批量提取

**创建 `batch_extract.py`：**

```python
from test_mcp import pdf_extract
import json

file_path = "../sample_contract.pdf"

queries = [
    "甲方名称",
    "乙方名称",
    "合同金额",
    "签署日期",
    "职位"
]

print("批量提取结果:")
print("=" * 60)

for query in queries:
    result = pdf_extract(file_path, query)
    print(f"\n{query}:")
    for key, value in result['extracted'].items():
        print(f"   {value}")
```

**运行：**
```bash
python3 batch_extract.py
```

---

## 🛠️ 工具参数说明

### pdf_extract

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `file_path` | string | ✅ | - | PDF 文件路径 |
| `query` | string | ✅ | - | 抽取目标 |
| `include_citations` | boolean | ❌ | false | 是否包含原文引用 |
| `max_pages` | integer | ❌ | 0 | 最大处理页数 |
| `chunk_size` | integer | ❌ | 10 | 每批页数 |

### pdf_info

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `file_path` | string | ✅ | PDF 文件路径 |

### pdf_validate

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `file_path` | string | ✅ | PDF 文件路径 |

---

## 🐛 常见问题

### Q1: 如何指定不同的 PDF 文件？

```bash
python3 -c "
from test_mcp import pdf_extract
result = pdf_extract('/path/to/your/file.pdf', '提取甲乙方')
"
```

---

### Q2: 如何提取自定义信息？

```bash
python3 -c "
from test_mcp import pdf_extract

# 自然语言描述
result = pdf_extract('../sample_contract.pdf', '找出所有关于违约金的条款')

# 或者关键词列表
result = pdf_extract('../sample_contract.pdf', '违约金，赔偿责任，争议解决')
"
```

---

### Q3: 如何获取带引用的结果？

```bash
python3 -c "
from test_mcp import pdf_extract

result = pdf_extract(
    '../sample_contract.pdf',
    '提取合同金额',
    include_citations=True  # 开启引用
)
print(result)
"
```

---

### Q4: 如何在代码中集成？

```python
# 导入工具函数
from test_mcp import pdf_extract, pdf_info, pdf_validate

# 1. 验证文件
valid, error = pdf_validate('../sample.pdf')
if not valid:
    print(f"文件无效：{error}")

# 2. 获取信息
info = pdf_info('../sample.pdf')
print(f"页数：{info['total_pages']}")

# 3. 提取内容
result = pdf_extract('../sample.pdf', '提取甲乙方')
print(f"甲方：{result['extracted']['甲方']}")
```

---

## 📚 总结

| 调用方式 | 适用场景 | 难度 |
|----------|----------|------|
| **test_mcp.py** | 快速测试 | ⭐ |
| **交互式脚本** | 手动调用 | ⭐⭐ |
| **MCP 协议** | 集成 Client | ⭐⭐⭐⭐ |
| **Python 集成** | 代码调用 | ⭐⭐ |

**推荐：** 当前环境使用 `test_mcp.py`，最简单直接！

---

**文档位置：** `/root/.openclaw/workspace/mcp_server/CALL_GUIDE.md`
