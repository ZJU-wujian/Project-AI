#!/usr/bin/env python3
"""
TopScholar 后端服务器
"""
import sys
import os

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.main import app

def main():
    import argparse
    parser = argparse.ArgumentParser(description="TopScholar Backend Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    parser.add_argument("--init-db", action="store_true", help="Initialize database")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    
    args = parser.parse_args()
    
    import uvicorn
    print(f"🚀 Starting TopScholar API on {args.host}:{args.port}")
    print(f"📚 API Docs: http://localhost:{args.port}/docs")
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )

if __name__ == "__main__":
    main()