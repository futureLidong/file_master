# File Master 测试指南

**项目：** file_master v0.1.0  
**最后更新：** 2026-03-17  

---

## 📁 项目结构

```
file_master/
├── src/file_master/
│   ├── server.py           # MCP Server 入口
│   ├── config.py           # 配置管理
│   ├── plugins/
│   │   └── pdf_extract.py  # PDF 抽取插件（3 个 MCP 工具）
│   └── services/
│       ├── pdf_reader.py   # PDF 读取服务
│       └── extractor.py    # AI 抽取服务
├── tests/
│   ├── test_pdf_extract.py # 单元测试
│   ├── TEST_REPORT.md      # 测试报告
│   └── TEST_GUIDE.md       # 测试指南（本文档）
├── examples/
│   └── extract_contract.py # 使用示例
└── sample_contract.pdf     # 测试文件
```

---

## 🎯 核心方法

### 1. PDFReader 类（`services/pdf_reader.py`）

**功能：** PDF 文件读取和文本提取

| 方法 | 说明 | 参数 | 返回值 |
|------|------|------|--------|
| `__init__(file_path)` | 初始化 PDF 读取器 | `file_path`: PDF 文件路径 | - |
| `total_pages` | 获取总页数（属性） | - | `int` |
| `get_metadata()` | 获取 PDF 元数据 | - | `PDFMetadata` |
| `iter_pages(start_page, max_pages)` | 迭代页面（流式） | `start_page`: 起始页<br>`max_pages`: 最大页数 | `Iterator[PageData]` |
| `get_page_text(page_number)` | 获取单页文本 | `page_number`: 页码（1-indexed） | `str` |
| `iter_page_chunks(chunk_size, overlap, max_pages)` | 分块迭代（大文件） | `chunk_size`: 每块页数<br>`overlap`: 重叠页数<br>`max_pages`: 最大页数 | `Iterator[tuple[list[int], str]]` |

**使用示例：**
```python
from file_master.services import PDFReader

# 使用上下文管理器（推荐）
with PDFReader("sample.pdf") as reader:
    print(f"总页数：{reader.total_pages}")
    
    # 获取元数据
    meta = reader.get_metadata()
    print(f"标题：{meta.title}")
    
    # 迭代所有页面
    for page in reader.iter_pages():
        print(f"第{page.page_number}页：{page.text[:100]}")
    
    # 分块处理（适合大文件）
    for page_nums, text in reader.iter_page_chunks(chunk_size=10):
        print(f"处理页码：{page_nums}")
        # 发送到 AI 处理...
```

---

### 2. Extractor 类（`services/extractor.py`）

**功能：** AI 信息抽取

| 方法 | 说明 | 参数 | 返回值 |
|------|------|------|--------|
| `__init__(config)` | 初始化抽取器 | `config`: Config 对象 | - |
| `extract(text, query, include_citations, max_tokens)` | 从文本抽取信息 | `text`: 输入文本<br>`query`: 抽取目标<br>`include_citations`: 是否包含引用<br>`max_tokens`: 最大输出 token | `ExtractionResult` |
| `extract_from_chunks(chunks, query, include_citations)` | 从多个块抽取并合并 | `chunks`: `(页码列表，文本)` 元组列表<br>`query`: 抽取目标<br>`include_citations`: 是否包含引用 | `ExtractionResult` |
| `_clean_json_response(text)` | 清理 JSON 响应（内部方法） | `text`: AI 原始响应 | `str` |

**使用示例：**
```python
from file_master.config import Config
from file_master.services import Extractor

# 初始化
config = Config.from_env()  # 从环境变量加载
extractor = Extractor(config)

# 简单抽取
result = extractor.extract(
    text="合同金额：100 万元，甲方：ABC 公司",
    query="提取合同金额和甲方名称",
    include_citations=False
)

if result.error:
    print(f"错误：{result.error}")
else:
    print(f"提取结果：{result.extracted}")
    # 输出：{'合同金额': '100 万元', '甲方': 'ABC 公司'}

# 带引用的抽取
result = extractor.extract(
    text="...",
    query="提取所有金额",
    include_citations=True
)
for citation in result.citations:
    print(f"[{citation['field']}] {citation['text']}")
```

---

### 3. PDFExtractPlugin 类（`plugins/pdf_extract.py`）

**功能：** MCP 插件封装

| 方法 | 说明 | 参数 | 返回值 |
|------|------|------|--------|
| `get_tools()` | 获取可用工具列表 | - | `list[Tool]` |
| `handle_tool(name, arguments)` | 处理工具调用 | `name`: 工具名<br>`arguments`: 参数 dict | `list[TextContent\|ErrorContent]` |

**提供的 MCP 工具：**

1. **`pdf_extract`** - 从 PDF 提取关键信息
2. **`pdf_info`** - 获取 PDF 基本信息
3. **`pdf_validate`** - 验证 PDF 文件

---

## 🧪 测试入口

### 方式 1：运行单元测试

```bash
cd /root/.openclaw/workspace

# 激活虚拟环境
source .venv/bin/activate

# 安装测试依赖
pip install pytest pytest-asyncio

# 运行所有测试
pytest tests/ -v

# 运行特定测试类
pytest tests/test_pdf_extract.py::TestPDFReader -v

# 运行特定测试方法
pytest tests/test_pdf_extract.py::TestExtractor::test_clean_json_response -v
```

**预期输出：**
```
============================= test session starts ==============================
tests/test_pdf_extract.py::TestPDFReader::test_validate_nonexistent_file PASSED
tests/test_pdf_extract.py::TestPDFReader::test_validate_non_pdf PASSED
tests/test_pdf_extract.py::TestExtractor::test_clean_json_response PASSED

============================== 3 passed in 0.05s ===============================
```

---

### 方式 2：运行集成测试（真实 API 调用）

**步骤 1：准备测试文件**

```bash
cd /root/.openclaw/workspace
ls -l sample_contract.pdf  # 确认测试文件存在
```

**步骤 2：设置 API Key**

```bash
export DASHSCOPE_API_KEY=sk-93947c4a61294a37aef9d592a0e155f1
```

**步骤 3：运行测试脚本**

```bash
# 方式 A：使用示例脚本
python examples/extract_contract.py sample_contract.pdf

# 方式 B：直接运行 Python 脚本
python3 << 'EOF'
import sys
sys.path.insert(0, 'src')

from file_master.config import Config
from file_master.services import PDFReader, Extractor

# 初始化
config = Config.from_env()
extractor = Extractor(config)

# 读取 PDF
with PDFReader('sample_contract.pdf') as reader:
    pages = list(reader.iter_pages(max_pages=10))
    text = "\n\n".join(f"--- 第{p.page_number}页 ---\n{p.text}" for p in pages)

# 提取信息
result = extractor.extract(
    text=text,
    query="提取甲方（Employer）和乙方（Employee）的名称",
    include_citations=True
)

# 输出结果
if result.error:
    print(f"❌ 错误：{result.error}")
else:
    print("✅ 提取结果:")
    for key, value in result.extracted.items():
        print(f"   {key}: {value}")
    
    if result.citations:
        print("\n📎 引用:")
        for c in result.citations:
            print(f"   [{c['field']}] {c['text'][:50]}...")
EOF
```

**预期输出：**
```
✅ 提取结果:
   甲方：ABC Technology Co., Ltd.
   乙方：John Smith

📎 引用:
   [甲方] Employer: ABC Technology Co., Ltd....
   [乙方] Employee: John Smith...
```

---

### 方式 3：MCP Server 测试

**步骤 1：启动 MCP Server**

```bash
cd /root/.openclaw/workspace
source .venv/bin/activate
export DASHSCOPE_API_KEY=sk-93947c4a61294a37aef9d592a0e155f1

# 启动服务器
python -m file_master.server
```

**步骤 2：从另一个终端发送测试请求**

```bash
# 使用 MCP 客户端测试（需要安装 mcp 客户端）
python3 << 'EOF'
import json

# 模拟 MCP 工具调用
request = {
    "name": "pdf_extract",
    "arguments": {
        "file_path": "/root/.openclaw/workspace/sample_contract.pdf",
        "query": "提取甲方和乙方名称",
        "include_citations": False
    }
}

print("发送请求:")
print(json.dumps(request, indent=2))
# 实际使用时通过 MCP 客户端发送
EOF
```

---

## 📋 核心方法测试清单

### PDFReader 测试

| 测试项 | 命令/代码 | 预期结果 |
|--------|----------|----------|
| 文件不存在 | `validate_pdf_file("/no/such/file.pdf")` | `(False, "not found")` |
| 非 PDF 文件 | `validate_pdf_file("test.txt")` | `(False, "must be a PDF")` |
| 获取页数 | `reader.total_pages` | `1` |
| 获取元数据 | `reader.get_metadata()` | `PDFMetadata` 对象 |
| 迭代页面 | `list(reader.iter_pages())` | `[PageData, ...]` |
| 分块处理 | `list(reader.iter_page_chunks(5))` | `[(页码列表，文本), ...]` |

**测试代码：**
```python
from file_master.services import PDFReader, validate_pdf_file

# 测试 1：验证文件
is_valid, error = validate_pdf_file("sample_contract.pdf")
assert is_valid, f"验证失败：{error}"

# 测试 2：读取元数据
with PDFReader("sample_contract.pdf") as reader:
    meta = reader.get_metadata()
    assert meta.total_pages == 1
    assert meta.file_size_bytes > 0

# 测试 3：提取文本
with PDFReader("sample_contract.pdf") as reader:
    pages = list(reader.iter_pages())
    assert len(pages) == 1
    assert "EMPLOYMENT CONTRACT" in pages[0].text

print("✅ PDFReader 测试通过")
```

---

### Extractor 测试

| 测试项 | 命令/代码 | 预期结果 |
|--------|----------|----------|
| JSON 清理 | `extractor._clean_json_response('```json{...}```')` | `' {...} '` |
| 简单抽取 | `extractor.extract(text, "提取金额")` | `ExtractionResult` |
| 带引用抽取 | `extractor.extract(text, query, include_citations=True)` | 包含 citations |
| 分块抽取 | `extractor.extract_from_chunks(chunks, query)` | 合并结果 |

**测试代码：**
```python
from file_master.config import Config
from file_master.services import Extractor

config = Config(api_key="sk-xxx")
extractor = Extractor(config)

# 测试 1：JSON 清理
assert extractor._clean_json_response('```json{"a":1}```') == '{"a":1}'

# 测试 2：AI 抽取（需要真实 API）
result = extractor.extract(
    text="合同金额：100 万元",
    query="提取合同金额"
)
assert not result.error
assert "100 万元" in str(result.extracted.values())

print("✅ Extractor 测试通过")
```

---

### PDFExtractPlugin 测试

| 测试项 | 命令/代码 | 预期结果 |
|--------|----------|----------|
| 获取工具列表 | `plugin.get_tools()` | 3 个工具 |
| 调用 pdf_extract | `handle_tool("pdf_extract", args)` | 提取结果 |
| 调用 pdf_info | `handle_tool("pdf_info", args)` | PDF 元数据 |
| 调用 pdf_validate | `handle_tool("pdf_validate", args)` | 验证结果 |

**测试代码：**
```python
from file_master.config import Config
from file_master.plugins import PDFExtractPlugin

config = Config.from_env()
plugin = PDFExtractPlugin(config)

# 测试 1：工具列表
tools = plugin.get_tools()
assert len(tools) == 3
assert tools[0].name == "pdf_extract"

# 测试 2：pdf_validate
import asyncio
result = asyncio.run(plugin.handle_tool("pdf_validate", {
    "file_path": "sample_contract.pdf"
}))
assert result[0].text contains '"valid": true'

print("✅ PDFExtractPlugin 测试通过")
```

---

## 🐛 常见问题排查

### 问题 1：PDF 读取失败

**症状：** `FileNotFoundError` 或 `Invalid PDF file`

**排查步骤：**
```bash
# 检查文件是否存在
ls -l sample_contract.pdf

# 检查文件类型
file sample_contract.pdf  # 应该是 "PDF document"

# 检查权限
chmod 644 sample_contract.pdf
```

---

### 问题 2：API 调用失败

**症状：** `401 Unauthorized` 或 `API request failed`

**排查步骤：**
```bash
# 检查 API Key 是否设置
echo $DASHSCOPE_API_KEY

# 测试 API 连接
curl -X POST https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation \
  -H "Authorization: Bearer $DASHSCOPE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen-plus","input":{"messages":[{"role":"user","content":"hi"}]}}'
```

---

### 问题 3：Python 版本不兼容

**症状：** `SyntaxError` 或 `ModuleNotFoundError`

**解决：**
```bash
# 检查 Python 版本
python3 --version  # 需要 3.10+

# 如果版本太低，使用虚拟环境
python3.10 -m venv .venv
source .venv/bin/activate
pip install -e .
```

---

## 📊 测试覆盖率目标

| 模块 | 当前覆盖率 | 目标覆盖率 |
|------|-----------|-----------|
| `pdf_reader.py` | 60% | 85% |
| `extractor.py` | 50% | 85% |
| `pdf_extract.py` | 40% | 80% |
| **总计** | **50%** | **85%** |

**提升覆盖率：**
```bash
# 安装 coverage
pip install coverage

# 运行测试并统计覆盖率
coverage run -m pytest tests/
coverage report -m
coverage html  # 生成 HTML 报告
```

---

## 🚀 下一步

1. ✅ **运行现有测试** - 确保基础功能正常
2. 🔄 **添加更多测试用例** - 覆盖边界情况
3. 🔄 **集成 CI/CD** - GitHub Actions 自动测试
4. 🔄 **性能测试** - 大文件处理性能

---

**文档维护者：** futureLidong  
**最后更新：** 2026-03-17
