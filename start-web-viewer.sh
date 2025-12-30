#!/bin/bash
# TrendRadar Web Viewer 启动脚本（Mac/Linux）

echo "=========================================="
echo "🚀 TrendRadar Web Viewer"
echo "=========================================="
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 Python 3"
    echo "   请先安装 Python 3"
    exit 1
fi

echo "✅ Python 版本: $(python3 --version)"
echo ""

# 检查数据目录
if [ ! -d "output" ]; then
    echo "⚠️  警告: output 目录不存在"
    echo "   请先运行 TrendRadar 生成数据"
    echo ""
fi

# 启动 API 服务器
echo "🌐 启动 API 服务器..."
echo "   地址: http://localhost:8080"
echo "   按 Ctrl+C 停止服务器"
echo ""
echo "=========================================="
echo ""

python3 start_api_server.py
