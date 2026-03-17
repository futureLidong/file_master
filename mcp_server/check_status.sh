#!/bin/bash
# MCP Server 状态检查脚本

echo "=============================================="
echo "📊 File Master MCP Server 状态检查"
echo "=============================================="
echo ""

# 检查进程
echo "🔍 进程状态:"
ps aux | grep "start_server.py" | grep -v grep || echo "   未找到运行中的进程"
echo ""

# 检查日志
echo "📋 最近日志:"
if [ -f "mcp_server.log" ]; then
    tail -10 mcp_server.log
else
    echo "   日志文件不存在"
fi
echo ""

# 检查文件
echo "📁 目录内容:"
ls -lh /root/.openclaw/workspace/mcp_server/
echo ""

# 测试服务
echo "🧪 测试服务响应:"
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python3 start_server.py 2>/dev/null | head -c 200
echo "..."
echo ""

echo "=============================================="
