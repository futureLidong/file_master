# OpenClaw 第三方大模型配置手册 🍃

*最后更新：2026-03-16 | 作者：李安*

---

## 📋 目录

1. [支持的模型提供商](#支持的模型提供商)
2. [配置步骤](#配置步骤)
3. [切换模型](#切换模型)
4. [常用模型配置示例](#常用模型配置示例)
5. [验证配置](#验证配置)
6. [故障排查](#故障排查)

---

## 支持的模型提供商

OpenClaw 支持多种大模型提供商，通过 OpenAI 兼容 API 接入：

| 提供商 | 适用地区 | 需要翻墙 | 推荐模型 |
|--------|----------|----------|----------|
| **阿里云百炼** | 中国大陆 ✅ | 否 | qwen-turbo, qwen-plus |
| **DeepSeek** | 中国大陆 ✅ | 否 | deepseek-chat, deepseek-coder |
| **Moonshot (Kimi)** | 中国大陆 ✅ | 否 | moonshot-v1-8k/32k/128k |
| **OpenAI** | 海外 | 是 | gpt-4o, gpt-4-turbo |
| **Anthropic** | 海外 | 是 | claude-3-5-sonnet, claude-3-opus |
| **Google Gemini** | 海外 | 是 | gemini-1.5-pro |
| **智谱 AI** | 中国大陆 ✅ | 否 | glm-4, glm-4-flash |
| **MiniMax** | 中国大陆 ✅ | 否 | abab6.5, abab6.5s |

---

## 配置步骤

### 方式一：使用 CLI 命令（推荐）

```bash
# 添加新模型提供商
openclaw models add <provider-name>

# 按提示输入：
# 1. Base URL (API 端点)
# 2. API Key
# 3. 模型列表（可选，会自动发现）
```

### 方式二：手动编辑配置文件

配置文件位置：`~/.openclaw/openclaw.json`

```bash
# 编辑前备份
cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.bak

# 编辑配置
nano ~/.openclaw/openclaw.json
# 或
vim ~/.openclaw/openclaw.json
```

---

## 切换模型

### 查看当前可用模型

```bash
openclaw models list
```

### 切换默认模型

```bash
# 方式 1：使用 CLI
openclaw models use <provider/model-name>

# 方式 2：编辑配置文件
# 修改 agents.defaults.models.primary
```

### 临时使用不同模型（单次对话）

在对话中指定：
```
/model <provider/model-name> 你的问题
```

---

## 常用模型配置示例

### 1. 阿里云百炼（当前配置）

```json
{
  "providers": {
    "bailianNew": {
      "baseUrl": "https://dashscope.aliyuncs.com/compatible-mode/v1",
      "apiKey": "sk-你的 API_KEY",
      "api": "openai-completions",
      "models": [
        {"id": "qwen-turbo", "name": "Qwen Turbo"},
        {"id": "qwen-plus", "name": "Qwen Plus"},
        {"id": "qwen-max", "name": "Qwen Max"}
      ]
    }
  }
}
```

**获取 API Key：** https://dashscope.console.aliyun.com/apiKey

---

### 2. DeepSeek（推荐用于代码）

```json
{
  "providers": {
    "deepseek": {
      "baseUrl": "https://api.deepseek.com/v1",
      "apiKey": "你的 DeepSeek API_KEY",
      "api": "openai-completions",
      "models": [
        {"id": "deepseek-chat", "name": "DeepSeek Chat"},
        {"id": "deepseek-coder", "name": "DeepSeek Coder"}
      ]
    }
  }
}
```

**获取 API Key：** https://platform.deepseek.com/api_keys

**特点：** 代码能力强，价格低廉，适合编程任务

---

### 3. Moonshot (Kimi)

```json
{
  "providers": {
    "moonshot": {
      "baseUrl": "https://api.moonshot.cn/v1",
      "apiKey": "你的 Moonshot API_KEY",
      "api": "openai-completions",
      "models": [
        {"id": "moonshot-v1-8k", "name": "Kimi 8K"},
        {"id": "moonshot-v1-32k", "name": "Kimi 32K"},
        {"id": "moonshot-v1-128k", "name": "Kimi 128K"}
      ]
    }
  }
}
```

**获取 API Key：** https://platform.moonshot.cn/console/api-keys

**特点：** 超长上下文，适合长文档分析

---

### 4. OpenAI

```json
{
  "providers": {
    "openai": {
      "baseUrl": "https://api.openai.com/v1",
      "apiKey": "sk-你的 OpenAI API_KEY",
      "api": "openai-completions",
      "models": [
        {"id": "gpt-4o", "name": "GPT-4o"},
        {"id": "gpt-4-turbo", "name": "GPT-4 Turbo"},
        {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo"}
      ]
    }
  }
}
```

**获取 API Key：** https://platform.openai.com/api-keys

**注意：** 中国大陆需要代理才能访问

---

### 5. 智谱 AI

```json
{
  "providers": {
    "zhipu": {
      "baseUrl": "https://open.bigmodel.cn/api/paas/v4",
      "apiKey": "你的 智谱 API_KEY",
      "api": "openai-completions",
      "models": [
        {"id": "glm-4", "name": "GLM-4"},
        {"id": "glm-4-flash", "name": "GLM-4 Flash"},
        {"id": "glm-4-air", "name": "GLM-4 Air"}
      ]
    }
  }
}
```

**获取 API Key：** https://open.bigmodel.cn/usercenter/apikeys

---

## 验证配置

### 1. 列出所有模型

```bash
openclaw models list
```

预期输出：
```
Model                                      Input      Ctx      Local Auth  Tags
provider/model-name                        text       128k     no    yes   default,configured
```

### 2. 测试模型连接

```bash
# 发送测试消息
openclaw test --model <provider/model-name> "Hello, are you working?"
```

### 3. 检查当前配置

```bash
cat ~/.openclaw/openclaw.json | jq '.models'
```

---

## 故障排查

### 问题 1：API Key 无效

**错误信息：** `401 Unauthorized` 或 `Invalid API key`

**解决：**
1. 检查 API Key 是否正确复制（无空格）
2. 确认 API Key 未过期
3. 检查账户余额

### 问题 2：连接超时

**错误信息：** `Connection timed out` 或 `ETIMEDOUT`

**解决：**
1. 检查网络连接
2. 海外模型需要配置代理
3. 尝试更换 API 端点（部分提供商有多个区域）

### 问题 3：模型不存在

**错误信息：** `Model not found` 或 `404`

**解决：**
1. 确认模型 ID 拼写正确
2. 检查该模型是否在你的账户可用
3. 运行 `openclaw models sync` 同步最新模型列表

### 问题 4：速率限制

**错误信息：** `429 Too Many Requests`

**解决：**
1. 降低请求频率
2. 升级账户套餐
3. 使用多个 API Key 轮换

---

## 快速参考：模型选择建议

| 使用场景 | 推荐模型 | 理由 |
|----------|----------|------|
| **日常对话** | Qwen-Plus / GLM-4 | 平衡性能和成本 |
| **代码编写** | DeepSeek-Coder / GPT-4o | 代码能力强 |
| **长文档分析** | Kimi-128K / Qwen-Max | 超长上下文 |
| **创意写作** | GPT-4o / Claude-3.5 | 文采好 |
| **快速响应** | Qwen-Turbo / GLM-4-Flash | 延迟低 |
| **复杂推理** | GPT-4o / Qwen-Max | 推理能力强 |

---

## 附录：配置文件完整示例

```json
{
  "models": {
    "mode": "merge",
    "providers": {
      "bailianNew": {
        "baseUrl": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "apiKey": "sk-xxx",
        "api": "openai-completions"
      },
      "deepseek": {
        "baseUrl": "https://api.deepseek.com/v1",
        "apiKey": "sk-xxx",
        "api": "openai-completions"
      }
    }
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "deepseek/deepseek-coder"
      }
    }
  }
}
```

---

*有任何问题，随时叫我！* 🍃
