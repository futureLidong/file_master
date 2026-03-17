#!/usr/bin/env python3
"""
MCP Server 简化版 - 用于本地测试

由于 Python 3.6 不支持 mcp 包，这个脚本直接调用插件方法进行测试。
功能等同于 MCP Server 的 tools/call 接口。
"""

import sys
import os
import json

# 添加 src 到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

print("=" * 60)
print("🚀 File Master MCP Server (简化测试版)")
print("=" * 60)

# 设置 API Key
os.environ["DASHSCOPE_API_KEY"] = "sk-93947c4a61294a37aef9d592a0e155f1"

print(f"\n📂 工作目录：{os.getcwd()}")
print(f"🔑 API Key: sk-93947c4a61294a37aef9d592a0e155f1")
print(f"📄 测试文件：../sample_contract.pdf")
print()

# 导入模块
try:
    from file_master.config import Config
    from file_master.plugins import PDFExtractPlugin
    print("✅ 模块加载成功")
except Exception as e:
    print(f"❌ 模块加载失败：{e}")
    print("\n提示：Python 3.6 不支持 dataclasses，需要 Python 3.10+")
    sys.exit(1)

# 初始化插件
config = Config.from_env()
plugin = PDFExtractPlugin(config)
print("✅ PDF 插件初始化成功")

# 显示可用工具
print("\n" + "=" * 60)
print("🛠️  可用工具:")
print("=" * 60)
tools = plugin.get_tools()
for tool in tools:
    print(f"  • {tool.name}: {tool.description}")

# 交互式调用
print("\n" + "=" * 60)
print("📋 测试调用示例:")
print("=" * 60)

async def run_tests():
    """运行测试用例"""
    
    # 测试 1: pdf_validate
    print("\n🧪 测试 1: 验证 PDF 文件")
    print("-" * 60)
    result = await plugin.handle_tool("pdf_validate", {
        "file_path": "../sample_contract.pdf"
    })
    for r in result:
        if hasattr(r, 'text'):
            data = json.loads(r.text)
            print(f"   文件有效：{data['valid']}")
    
    # 测试 2: pdf_info
    print("\n🧪 测试 2: 获取 PDF 信息")
    print("-" * 60)
    result = await plugin.handle_tool("pdf_info", {
        "file_path": "../sample_contract.pdf"
    })
    for r in result:
        if hasattr(r, 'text'):
            data = json.loads(r.text)
            print(f"   总页数：{data['total_pages']}")
            print(f"   文件大小：{data['file_size_mb']} MB")
    
    # 测试 3: pdf_extract (甲乙方)
    print("\n🧪 测试 3: 提取甲乙方信息")
    print("-" * 60)
    result = await plugin.handle_tool("pdf_extract", {
        "file_path": "../sample_contract.pdf",
        "query": "提取甲方（Employer）和乙方（Employee）的名称",
        "include_citations": False
    })
    for r in result:
        if hasattr(r, 'text'):
            data = json.loads(r.text)
            if data.get('extracted'):
                print("   ✅ 提取结果:")
                for key, value in data['extracted'].items():
                    print(f"      {key}: {value}")
            if data.get('error'):
                print(f"   ❌ 错误：{data['error']}")
    
    # 测试 4: pdf_extract (合同有效期)
    print("\n🧪 测试 4: 提取合同有效期")
    print("-" * 60)
    result = await plugin.handle_tool("pdf_extract", {
        "file_path": "../sample_contract.pdf",
        "query": "提取合同有效期、开始日期、结束日期、签署日期",
        "include_citations": False
    })
    for r in result:
        if hasattr(r, 'text'):
            data = json.loads(r.text)
            if data.get('extracted'):
                print("   ✅ 提取结果:")
                for key, value in data['extracted'].items():
                    if value:
                        print(f"      {key}: {value}")
            if data.get('error'):
                print(f"   ❌ 错误：{data['error']}")
    
    # 测试 5: pdf_extract (综合信息)
    print("\n🧪 测试 5: 提取综合信息")
    print("-" * 60)
    result = await plugin.handle_tool("pdf_extract", {
        "file_path": "../sample_contract.pdf",
        "query": "提取合同金额、职位、付款方式、签署日期",
        "include_citations": True
    })
    for r in result:
        if hasattr(r, 'text'):
            data = json.loads(r.text)
            if data.get('extracted'):
                print("   ✅ 提取结果:")
                for key, value in data['extracted'].items():
                    if value:
                        print(f"      {key}: {value}")
            if data.get('citations'):
                print("   📎 原文引用:")
                for c in data['citations'][:3]:
                    print(f"      [{c['field']}] {c['text'][:50]}...")
            if data.get('error'):
                print(f"   ❌ 错误：{data['error']}")

# 运行测试
import asyncio
asyncio.run(run_tests())

print("\n" + "=" * 60)
print("✅ 所有测试完成")
print("=" * 60)

print("\n💡 提示:")
print("   - 完整 MCP Server 需要 Python 3.10+ 和 mcp 包")
print("   - 当前使用简化版直接调用插件方法")
print("   - 功能测试结果与 MCP 协议调用相同")
