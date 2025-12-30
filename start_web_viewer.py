#!/usr/bin/env python3
# coding=utf-8
"""
TrendRadar Web Viewer Server

简单的 HTTP 服务器，用于查看 TrendRadar 数据
"""

import os
import http.server
import socketserver
import webbrowser
from pathlib import Path

# 配置
PORT = 8080
HOST = "localhost"

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """自定义 HTTP 请求处理器"""

    def end_headers(self):
        # 添加 CORS 头，允许跨域访问
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def log_message(self, format, *args):
        # 自定义日志格式
        print(f"[{self.log_date_time_string()}] {format % args}")


def main():
    """启动 Web 服务器"""
    # 切换到项目根目录
    project_root = Path(__file__).parent
    os.chdir(project_root)

    print("=" * 60)
    print("🚀 TrendRadar Web Viewer Server")
    print("=" * 60)
    print(f"📂 工作目录: {project_root}")
    print(f"🌐 服务地址: http://{HOST}:{PORT}")
    print(f"📊 查看界面: http://{HOST}:{PORT}/web_viewer.html")
    print("=" * 60)
    print("💡 提示:")
    print("  - 按 Ctrl+C 停止服务器")
    print("  - 浏览器会自动打开查看界面")
    print("  - 数据每5分钟自动刷新")
    print("=" * 60)
    print()

    # 创建服务器
    with socketserver.TCPServer((HOST, PORT), CustomHTTPRequestHandler) as httpd:
        # 自动打开浏览器
        url = f"http://{HOST}:{PORT}/web_viewer.html"
        print(f"🌐 正在打开浏览器: {url}")
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"⚠️  无法自动打开浏览器: {e}")
            print(f"   请手动访问: {url}")

        print(f"\n✅ 服务器已启动，监听端口 {PORT}...")
        print("   等待请求中...\n")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n🛑 正在停止服务器...")
            httpd.shutdown()
            print("✅ 服务器已停止")


if __name__ == "__main__":
    main()
