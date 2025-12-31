#!/usr/bin/env python3
# coding=utf-8
"""
TrendRadar Web API Server

提供 RESTful API 接口，从 SQLite 数据库读取数据
"""

import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import webbrowser

# 配置
PORT = int(os.environ.get("PORT", 8080))
HOST = os.environ.get("HOST", "0.0.0.0")  # 0.0.0.0 允许 Docker 容器接受外部连接
OUTPUT_DIR = Path("output")


class TrendRadarAPIHandler(BaseHTTPRequestHandler):
    """TrendRadar API 请求处理器"""

    def do_GET(self):
        """处理 GET 请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query_params = parse_qs(parsed_path.query)

        # 路由
        if path == "/":
            self.serve_html()
        elif path == "/api/news":
            self.serve_news_data(query_params)
        elif path == "/api/rss":
            self.serve_rss_data(query_params)
        elif path == "/api/all":
            self.serve_all_data(query_params)
        elif path == "/api/stats":
            self.serve_stats(query_params)
        else:
            self.send_error(404, "Not Found")

    def do_OPTIONS(self):
        """处理 OPTIONS 请求（CORS 预检）"""
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def send_cors_headers(self):
        """发送 CORS 头"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def send_json_response(self, data, status=200):
        """发送 JSON 响应"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8'))

    def serve_html(self):
        """提供 HTML 页面"""
        html_file = Path("web_viewer.html")
        if html_file.exists():
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_cors_headers()
            self.end_headers()
            with open(html_file, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404, "web_viewer.html not found")

    def serve_news_data(self, query_params):
        """提供热榜新闻数据"""
        date = query_params.get('date', [self.get_today()])[0]
        try:
            news_data = self.load_news_from_db(date)
            self.send_json_response({
                "success": True,
                "data": news_data,
                "date": date,
                "count": len(news_data)
            })
        except Exception as e:
            self.send_json_response({
                "success": False,
                "error": str(e)
            }, status=500)

    def serve_rss_data(self, query_params):
        """提供 RSS 数据"""
        date = query_params.get('date', [self.get_today()])[0]
        try:
            rss_data = self.load_rss_from_db(date)
            self.send_json_response({
                "success": True,
                "data": rss_data,
                "date": date,
                "count": len(rss_data)
            })
        except Exception as e:
            self.send_json_response({
                "success": False,
                "error": str(e)
            }, status=500)

    def serve_all_data(self, query_params):
        """提供所有数据"""
        date = query_params.get('date', [self.get_today()])[0]
        try:
            news_data = self.load_news_from_db(date)
            rss_data = self.load_rss_from_db(date)
            self.send_json_response({
                "success": True,
                "news": news_data,
                "rss": rss_data,
                "date": date,
                "updateTime": datetime.now().isoformat()
            })
        except Exception as e:
            self.send_json_response({
                "success": False,
                "error": str(e)
            }, status=500)

    def serve_stats(self, query_params):
        """提供统计数据"""
        date = query_params.get('date', [self.get_today()])[0]
        try:
            news_data = self.load_news_from_db(date)
            rss_data = self.load_rss_from_db(date)

            # 统计数据源
            news_sources = set(item['source'] for item in news_data)
            rss_sources = set(item['source'] for item in rss_data)

            self.send_json_response({
                "success": True,
                "stats": {
                    "newsCount": len(news_data),
                    "rssCount": len(rss_data),
                    "totalCount": len(news_data) + len(rss_data),
                    "sourceCount": len(news_sources | rss_sources),
                    "newsSources": list(news_sources),
                    "rssSources": list(rss_sources)
                },
                "date": date
            })
        except Exception as e:
            self.send_json_response({
                "success": False,
                "error": str(e)
            }, status=500)

    def load_news_from_db(self, date):
        """从 SQLite 数据库加载热榜新闻"""
        db_path = OUTPUT_DIR / "news" / f"{date}.db"

        if not db_path.exists():
            return []

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT platform_id, title, rank, url, mobile_url,
                       first_crawl_time, last_crawl_time
                FROM news_items
                ORDER BY last_crawl_time DESC
            """)

            news_list = []
            for row in cursor.fetchall():
                news_list.append({
                    "title": row['title'],
                    "source": row['platform_id'],
                    "sourceId": row['platform_id'],
                    "rank": row['rank'],
                    "url": row['url'],
                    "mobileUrl": row['mobile_url'],
                    "time": row['last_crawl_time']
                })

            return news_list
        finally:
            conn.close()

    def load_rss_from_db(self, date):
        """从 SQLite 数据库加载 RSS 数据"""
        db_path = OUTPUT_DIR / "rss" / f"{date}.db"

        if not db_path.exists():
            return []

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT feed_id, feed_name, title, url, published_at,
                       summary, author, crawl_time
                FROM rss_items
                ORDER BY published_at DESC
            """)

            rss_list = []
            for row in cursor.fetchall():
                rss_list.append({
                    "title": row['title'],
                    "source": row['feed_name'],
                    "feedId": row['feed_id'],
                    "url": row['url'],
                    "publishedAt": row['published_at'],
                    "summary": row['summary'],
                    "author": row['author'],
                    "time": row['published_at'] or row['crawl_time']
                })

            return rss_list
        finally:
            conn.close()

    def get_today(self):
        """获取今天的日期（美东时间）"""
        # 这里简化处理，实际应该根据配置的时区
        return datetime.now().strftime('%Y-%m-%d')

    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[{self.log_date_time_string()}] {format % args}")


def main():
    """启动 API 服务器"""
    # 切换到项目根目录
    project_root = Path(__file__).parent
    os.chdir(project_root)

    print("=" * 60)
    print("🚀 TrendRadar Web API Server")
    print("=" * 60)
    print(f"📂 工作目录: {project_root}")
    print(f"📂 数据目录: {OUTPUT_DIR}")
    print(f"🌐 服务地址: http://{HOST}:{PORT}")
    print("=" * 60)
    print("📡 API 端点:")
    print(f"  - GET  /                    查看界面")
    print(f"  - GET  /api/news?date=YYYY-MM-DD   热榜新闻")
    print(f"  - GET  /api/rss?date=YYYY-MM-DD    RSS 订阅")
    print(f"  - GET  /api/all?date=YYYY-MM-DD    所有数据")
    print(f"  - GET  /api/stats?date=YYYY-MM-DD  统计信息")
    print("=" * 60)
    print("💡 提示:")
    print("  - 按 Ctrl+C 停止服务器")
    print("  - 浏览器会自动打开查看界面")
    print("  - 确保已运行 TrendRadar 生成数据")
    print("=" * 60)
    print()

    # 创建服务器
    server = HTTPServer((HOST, PORT), TrendRadarAPIHandler)

    # 自动打开浏览器
    url = f"http://{HOST}:{PORT}/"
    print(f"🌐 正在打开浏览器: {url}")
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"⚠️  无法自动打开浏览器: {e}")
        print(f"   请手动访问: {url}")

    print(f"\n✅ 服务器已启动，监听端口 {PORT}...")
    print("   等待请求中...\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 正在停止服务器...")
        server.shutdown()
        print("✅ 服务器已停止")


if __name__ == "__main__":
    main()
