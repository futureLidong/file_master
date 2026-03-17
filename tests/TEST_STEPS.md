# File Master 测试步骤文档

**文档版本：** 1.0  
**创建日期：** 2026-03-17  
**最后更新：** 2026-03-17 10:29 GMT+8  

---

## 📋 测试目标

验证 `file_master` 项目的核心功能：
1. PDF 文件读取能力
2. AI 信息抽取准确性（甲乙方、合同有效期等）
3. JSON 格式输出正确性
4. 百炼 API 集成可用性

---

## 🧪 测试环境

| 项目 | 配置 |
|------|------|
| 操作系统 | Alibaba Cloud Linux 3 |
| Python 版本 | 3.6.8+ |
| API 提供商 | 百炼 (DashScope) |
| 使用模型 | qwen-plus |
| 测试文件 | `sample_contract.pdf` |

---

## 📄 测试文件

**文件名：** `sample_contract.pdf`  
**位置：** `/root/.openclaw/workspace/sample_contract.pdf`  
**大小：** 1.1KB  
**页数：** 1 页  

**文件内容：**
```
EMPLOYMENT CONTRACT
Date: January 1, 2025
Employer: ABC Technology Co., Ltd.
Employee: John Smith
TERMS:
1. Position: Senior Software Engineer
2. Salary: RMB 500,000 per annum
3. Start Date: February 1, 2025
4. Payment: Monthly bank transfer
SIGNATURES:
Employer: _________________ Date: 2025-01-01
Employee: _________________ Date: 2025-01-01
```

---

## 🔬 测试步骤

### 前置准备

**步骤 0：确认测试文件存在**

```bash
cd /root/.openclaw/workspace
ls -l sample_contract.pdf
```

**预期输出：**
```
-rw-r--r-- 1 root root 1126 Mar 17 10:04 sample_contract.pdf
```

---

### 测试 1：提取甲乙方信息

**目标：** 验证 AI 能够准确识别并提取合同的甲方（Employer）和乙方（Employee）

**步骤 1.1：运行测试脚本**

```bash
cd /root/.openclaw/workspace

python3 << 'EOF'
import requests
import json
import re

# API 配置
api_key = "sk-93947c4a61294a37aef9d592a0e155f1"
api_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"

# 读取 PDF 内容
with open('sample_contract.pdf', 'rb') as f:
    content = f.read().decode('latin-1')
text_matches = re.findall(r'\(([^)]+)\)', content)
text = '\n'.join(text_matches)

print("📖 PDF 内容:")
print(text)
print()

# 构建提示词
prompt = f"""你是一位专业的文档信息抽取专家。请从以下文本中提取关键信息。

## 抽取目标
提取甲方（Employer）和乙方（Employee）的名称

## 文档内容
{text}

## 输出要求
1. 请严格按照 JSON 格式输出
2. 只返回提取到的信息，不要包含其他解释
3. 使用中文作为字段名

## 提取结果（JSON 格式）
"""

# 调用 API
response = requests.post(
    api_url,
    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    json={
        "model": "qwen-plus",
        "input": {"messages": [{"role": "user", "content": prompt}]},
        "parameters": {"max_tokens": 1000, "temperature": 0.1, "result_format": "message"}
    },
    timeout=30,
)

result = response.json()
ai_response = result["output"]["choices"][0]["message"]["content"]
extracted = json.loads(ai_response.strip('```json').strip('```').strip())

print("✅ 提取结果:")
for key, value in extracted.items():
    print(f"   {key}: {value}")
EOF
```

**预期输出：**
```
📖 PDF 内容:
EMPLOYMENT CONTRACT
Date: January 1, 2025
Employer: ABC Technology Co., Ltd.
Employee: John Smith
TERMS:
1. Position: Senior Software Engineer
2. Salary: RMB 500,000 per annum
3. Start Date: February 1, 2025
4. Payment: Monthly bank transfer
SIGNATURES:
Employer: _________________ Date: 2025-01-01
Employee: _________________ Date: 2025-01-01

✅ 提取结果:
   甲方：ABC Technology Co., Ltd.
   乙方：John Smith
```

**验证标准：**
- ✅ 甲方 = `ABC Technology Co., Ltd.`
- ✅ 乙方 = `John Smith`
- ✅ 输出为有效 JSON 格式

---

### 测试 2：提取合同有效期

**目标：** 验证 AI 能够提取合同相关的日期信息（开始日期、结束日期、签署日期）

**步骤 2.1：运行测试脚本**

```bash
cd /root/.openclaw/workspace

python3 << 'EOF'
import requests
import json
import re

# API 配置
api_key = "sk-93947c4a61294a37aef9d592a0e155f1"
api_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"

# 读取 PDF 内容
with open('sample_contract.pdf', 'rb') as f:
    content = f.read().decode('latin-1')
text_matches = re.findall(r'\(([^)]+)\)', content)
text = '\n'.join(text_matches)

# 构建提示词
prompt = f"""你是一位专业的文档信息抽取专家。请从以下文本中提取关键信息。

## 抽取目标
提取合同有效期、开始日期、结束日期、签署日期

## 文档内容
{text}

## 输出要求
1. 请严格按照 JSON 格式输出
2. 只返回提取到的信息，不要包含其他解释
3. 如果某个信息不存在，返回 null

## 提取结果（JSON 格式）
"""

# 调用 API
response = requests.post(
    api_url,
    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    json={
        "model": "qwen-plus",
        "input": {"messages": [{"role": "user", "content": prompt}]},
        "parameters": {"max_tokens": 1000, "temperature": 0.1, "result_format": "message"}
    },
    timeout=30,
)

result = response.json()
ai_response = result["output"]["choices"][0]["message"]["content"]
extracted = json.loads(ai_response.strip('```json').strip('```').strip())

print("✅ 提取结果:")
for key, value in extracted.items():
    print(f"   {key}: {value}")
EOF
```

**预期输出：**
```
✅ 提取结果:
   合同有效期：None
   开始日期：2025-02-01
   结束日期：None
   签署日期：2025-01-01
```

**验证标准：**
- ✅ 开始日期 = `2025-02-01`（来自 "Start Date: February 1, 2025"）
- ✅ 签署日期 = `2025-01-01`（来自 "Date: January 1, 2025"）
- ⚠️ 合同有效期 = `None`（测试文件中无此信息，属正常）
- ⚠️ 结束日期 = `None`（测试文件中无此信息，属正常）

---

### 测试 3：综合提取（完整测试）

**目标：** 一次性提取合同的所有关键信息，验证完整流程

**步骤 3.1：运行完整测试脚本**

```bash
cd /root/.openclaw/workspace

python3 << 'EOF'
import requests
import json
import re

print("=" * 60)
print("📄 File Master 集成测试 - 合同信息抽取")
print("=" * 60)

# API 配置
api_key = "sk-93947c4a61294a37aef9d592a0e155f1"
api_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"

# 读取 PDF 内容
with open('sample_contract.pdf', 'rb') as f:
    content = f.read().decode('latin-1')
text_matches = re.findall(r'\(([^)]+)\)', content)
text = '\n'.join(text_matches)

print(f"\n📂 测试文件：sample_contract.pdf")
print(f"📖 PDF 内容:\n{text}")

# 测试 1：提取甲乙方
print("\n" + "=" * 60)
print("🧪 测试 1：提取甲乙方信息")
print("=" * 60)

prompt1 = """你是一位专业的文档信息抽取专家。请从以下文本中提取关键信息。

## 抽取目标
提取甲方（Employer）和乙方（Employee）的名称

## 文档内容
""" + text + """

## 输出要求
1. 请严格按照 JSON 格式输出
2. 只返回提取到的信息，不要包含其他解释
3. 使用中文作为字段名

## 提取结果（JSON 格式）
"""

response1 = requests.post(
    api_url,
    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    json={
        "model": "qwen-plus",
        "input": {"messages": [{"role": "user", "content": prompt1}]},
        "parameters": {"max_tokens": 1000, "temperature": 0.1, "result_format": "message"}
    },
    timeout=30,
)

result1 = response1.json()
ai_response1 = result1["output"]["choices"][0]["message"]["content"]
extracted1 = json.loads(ai_response1.strip('```json').strip('```').strip())

print("\n✅ 提取结果:")
for key, value in extracted1.items():
    print(f"   {key}: {value}")

# 测试 2：提取合同有效期
print("\n" + "=" * 60)
print("🧪 测试 2：提取合同有效期")
print("=" * 60)

prompt2 = """你是一位专业的文档信息抽取专家。请从以下文本中提取关键信息。

## 抽取目标
提取合同有效期、开始日期、结束日期、签署日期

## 文档内容
""" + text + """

## 输出要求
1. 请严格按照 JSON 格式输出
2. 只返回提取到的信息，不要包含其他解释
3. 如果某个信息不存在，返回 null

## 提取结果（JSON 格式）
"""

response2 = requests.post(
    api_url,
    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    json={
        "model": "qwen-plus",
        "input": {"messages": [{"role": "user", "content": prompt2}]},
        "parameters": {"max_tokens": 1000, "temperature": 0.1, "result_format": "message"}
    },
    timeout=30,
)

result2 = response2.json()
ai_response2 = result2["output"]["choices"][0]["message"]["content"]
extracted2 = json.loads(ai_response2.strip('```json').strip('```').strip())

print("\n✅ 提取结果:")
for key, value in extracted2.items():
    print(f"   {key}: {value}")

# 汇总
print("\n" + "=" * 60)
print("📊 测试汇总")
print("=" * 60)
print("\n甲方（Employer）:", extracted1.get("甲方", "N/A"))
print("乙方（Employee）:", extracted1.get("乙方", "N/A"))
print("\n合同有效期信息:")
for key, value in extracted2.items():
    print(f"   {key}: {value}")

print("\n✅ 测试完成")
print("=" * 60)
EOF
```

**预期输出：**
```
============================================================
📄 File Master 集成测试 - 合同信息抽取
============================================================

📂 测试文件：sample_contract.pdf
📖 PDF 内容:
EMPLOYMENT CONTRACT
Date: January 1, 2025
Employer: ABC Technology Co., Ltd.
Employee: John Smith
TERMS:
1. Position: Senior Software Engineer
2. Salary: RMB 500,000 per annum
3. Start Date: February 1, 2025
4. Payment: Monthly bank transfer
SIGNATURES:
Employer: _________________ Date: 2025-01-01
Employee: _________________ Date: 2025-01-01

============================================================
🧪 测试 1：提取甲乙方信息
============================================================

✅ 提取结果:
   甲方：ABC Technology Co., Ltd.
   乙方：John Smith

============================================================
🧪 测试 2：提取合同有效期
============================================================

✅ 提取结果:
   合同有效期：None
   开始日期：2025-02-01
   结束日期：None
   签署日期：2025-01-01

============================================================
📊 测试汇总
============================================================

甲方（Employer）: ABC Technology Co., Ltd.
乙方（Employee）: John Smith

合同有效期信息:
   合同有效期：None
   开始日期：2025-02-01
   结束日期：None
   签署日期：2025-01-01

✅ 测试完成
============================================================
```

---

## 📊 测试结果记录

### 测试 1：甲乙方信息提取

| 字段 | 预期值 | 实际值 | 状态 |
|------|--------|--------|------|
| 甲方（Employer） | `ABC Technology Co., Ltd.` | `ABC Technology Co., Ltd.` | ✅ PASS |
| 乙方（Employee） | `John Smith` | `John Smith` | ✅ PASS |

**通过率：** 100%

---

### 测试 2：合同有效期提取

| 字段 | 预期值 | 实际值 | 状态 | 说明 |
|------|--------|--------|------|------|
| 开始日期 | `2025-02-01` | `2025-02-01` | ✅ PASS | 来自 "Start Date" |
| 签署日期 | `2025-01-01` | `2025-01-01` | ✅ PASS | 来自 "Date" |
| 合同有效期 | `N/A` | `None` | ✅ PASS | 文件中无此信息 |
| 结束日期 | `N/A` | `None` | ✅ PASS | 文件中无此信息 |

**通过率：** 100%

---

## 📈 性能指标

| 指标 | 数值 |
|------|------|
| PDF 文件大小 | 1.1 KB |
| PDF 页数 | 1 页 |
| 提取文本长度 | ~300 字符 |
| API 响应时间 | ~2 秒 |
| Token 消耗（测试 1） | ~260 tokens |
| Token 消耗（测试 2） | ~280 tokens |
| 总成本 | ~¥0.002 |

---

## 🐛 常见问题排查

### 问题 1：`ModuleNotFoundError: No module named 'dataclasses'`

**原因：** Python 版本低于 3.7

**解决方案：**
```bash
# 检查 Python 版本
python3 --version

# 如果版本 < 3.7，使用简单脚本测试（不需要 dataclasses）
# 或使用上面的内联脚本进行测试
```

---

### 问题 2：`401 Unauthorized`

**原因：** API Key 无效或未设置

**解决方案：**
```bash
# 检查 API Key
echo $DASHSCOPE_API_KEY

# 在脚本中直接使用有效 API Key
api_key = "sk-93947c4a61294a37aef9d592a0e155f1"
```

---

### 问题 3：`FileNotFoundError: sample_contract.pdf`

**原因：** 测试文件不存在

**解决方案：**
```bash
# 确认当前目录
pwd

# 确认文件存在
ls -l sample_contract.pdf

# 如果文件不存在，重新创建
# （参见项目根目录的 PDF 创建脚本）
```

---

## 📝 测试脚本复用

**保存为独立测试文件：**

```bash
# 创建测试脚本
cat > tests/run_integration_test.py << 'TESTEOF'
#!/usr/bin/env python3
"""Integration test for PDF information extraction."""

import requests
import json
import re
import sys
import os

def run_test():
    """Run integration test."""
    api_key = os.getenv("DASHSCOPE_API_KEY", "sk-93947c4a61294a37aef9d592a0e155f1")
    api_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    
    # Read PDF
    with open('sample_contract.pdf', 'rb') as f:
        content = f.read().decode('latin-1')
    text = '\n'.join(re.findall(r'\(([^)]+)\)', content))
    
    # Test 1: Extract parties
    prompt = f"从以下文本中提取甲方和乙方名称，返回 JSON 格式:\n{text}"
    
    response = requests.post(
        api_url,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": "qwen-plus",
            "input": {"messages": [{"role": "user", "content": prompt}]},
            "parameters": {"max_tokens": 1000, "temperature": 0.1}
        },
        timeout=30,
    )
    
    result = response.json()
    extracted = json.loads(result["output"]["choices"][0]["message"]["content"])
    
    print("✅ 提取结果:")
    for key, value in extracted.items():
        print(f"   {key}: {value}")
    
    return extracted

if __name__ == "__main__":
    run_test()
TESTEOF

chmod +x tests/run_integration_test.py
```

---

## ✅ 测试通过标准

所有测试必须满足以下条件：

1. ✅ PDF 文件能够成功读取
2. ✅ API 调用成功（HTTP 200）
3. ✅ 返回有效 JSON 格式
4. ✅ 甲乙方信息提取准确率 100%
5. ✅ 日期信息提取准确率 100%
6. ✅ 响应时间 < 5 秒

---

## 📚 相关文档

- [TEST_REPORT.md](TEST_REPORT.md) - 详细测试报告
- [TEST_GUIDE.md](TEST_GUIDE.md) - 开发者测试指南
- [../README.md](../README.md) - 项目说明文档

---

**文档维护者：** futureLidong  
**最后测试日期：** 2026-03-17  
**测试状态：** ✅ 通过
