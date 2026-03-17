# File Master 📄

MCP (Model Context Protocol) plugins for file processing and document intelligence.

## 🎯 Goals

- **PDF Reading** - Extract text, metadata, and structure from PDF documents
- **Key Information Extraction** - AI-powered extraction based on natural language queries
- **Large File Support** - Chunked processing for files up to 100MB
- **Citation Tracking** - Optional source citation for extracted information

## 🚀 Available MCP Tools

| Tool | Description | Status |
|------|-------------|--------|
| `pdf_extract` | 从 PDF 提取关键信息（V3 上下文冲突解决） | ✅ Ready |
| `pdf_info` | 获取 PDF 基本信息（页数、大小、元数据） | ✅ Ready |
| `pdf_validate` | 验证 PDF 文件是否有效 | ✅ Ready |

**V3 新特性：**
- ✅ 完整上下文保留（原文片段 + AI 理由）
- ✅ 智能冲突解决（基于上下文的 AI 判断）
- ✅ 所有候选值追踪（用于调试和审计）
- ✅ 可解释性增强（每个提取都有依据）

## 🛠️ Tech Stack

- **Runtime**: Python 3.10+
- **MCP SDK**: mcp
- **PDF**: pdfplumber (布局感知文本提取)
- **AI**: 百炼/Qwen API (qwen-plus)

## 📦 Installation

### 1. Create virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or: .venv\Scripts\activate  # Windows
```

### 2. Install dependencies

```bash
pip install -e .
```

### 3. Set API key

```bash
export DASHSCOPE_API_KEY=your_api_key_here
```

## 🔧 Usage

### Start MCP Server

```bash
# As command
file-master

# Or as module
python -m file_master.server
```

### Example Tool Calls

#### Get PDF Info
```json
{
  "name": "pdf_info",
  "arguments": {
    "file_path": "/path/to/document.pdf"
  }
}
```

#### Extract Information (V3)
```json
{
  "name": "pdf_extract",
  "arguments": {
    "file_path": "/path/to/contract.pdf",
    "query": "合同金额，签署日期，甲方乙方名称",
    "include_citations": true,
    "include_candidates": true,  // V3 新参数：包含所有候选值及上下文
    "max_pages": 50
  }
}
```

#### Validate PDF
```json
{
  "name": "pdf_validate",
  "arguments": {
    "file_path": "/path/to/file.pdf"
  }
}
```

## ⚙️ Configuration

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `DASHSCOPE_API_KEY` | 百炼 API 密钥 | (required) |
| `DASHSCOPE_MODEL` | 使用的模型 | `qwen-plus` |
| `PDF_MAX_FILE_SIZE_MB` | 最大文件大小 (MB) | `100` |
| `PDF_MAX_PAGES_PER_REQUEST` | 每批处理页数 | `20` |
| `PDF_DEFAULT_MAX_PAGES` | 默认最大页数 | `50` |

## 📁 Project Structure

```
file_master/
├── src/file_master/
│   ├── __init__.py
│   ├── server.py           # MCP Server 入口
│   ├── config.py           # 配置管理
│   ├── plugins/
│   │   └── pdf_extract.py  # PDF 抽取插件
│   └── services/
│       ├── pdf_reader.py   # PDF 读取服务
│       └── extractor.py    # AI 抽取服务
├── tests/
├── pyproject.toml
└── requirements.txt
```

## 🧪 Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/
ruff check src/
```

## 📝 License

MIT

---

*Built with OpenClaw*
