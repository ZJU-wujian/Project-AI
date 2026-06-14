# TopScholar - 学术社交与论文发现平台

## 📋 项目状态

- ✅ 产品需求文档：已制定
- ✅ 技术架构设计：已完成
- ✅ 后端代码：已创建
- ✅ 初始化脚本：已创建
- 🚧 开发中：服务器启动测试

## 🚀 快速启动

### 环境准备

```bash
# 检查 Python 版本
python3 --version  # 需要 Python 3.9+

# 安装依赖
pip3 install -r TopScholar/backend/requirements.txt
```

### 初始化数据库

```bash
# 初始化数据库
python3 TopScholar/backend/scripts/init_db.py

# 填充示例数据
python3 TopScholar/backend/scripts/populate_data.py
```

### 启动服务器

```bash
# 启动开发服务器
python3 TopScholar/backend/server.py --reload

# 或直接使用 uvicorn
uvicorn TopScholar.backend.app.main:app --reload
```

### 访问 API

- 主页: http://localhost:8000
- API 文档: http://localhost:8000/docs
- Redoc: http://localhost:8000/redoc

### 测试账户

- 用户名: `researcher1` / 密码: `password123`
- 用户名: `researcher2` / 密码: `password123`
- 用户名: `prof_smith` / 密码: `password123`

## 📦 项目结构

```
TopScholar/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI 主入口
│   │   ├── config.py            # 配置管理
│   │   ├── database.py          # 数据库连接
│   │   │
│   │   ├── models/              # 数据模型
│   │   │   ├── user.py
│   │   │   ├── journal.py
│   │   │   ├── paper.py
│   │   │   ├── post.py
│   │   │   └── interaction.py
│   │   │
│   │   ├── schemas/             # Pydantic 模型
│   │   │   ├── auth.py
│   │   │   ├── paper.py
│   │   │   ├── social.py
│   │   │   └── recommendation.py
│   │   │
│   │   ├── routers/             # API 路由
│   │   │   ├── auth.py
│   │   │   ├── papers.py
│   │   │   └── social.py
│   │   │
│   │   ├── services/            # 业务逻辑
│   │   │   ├── auth_service.py
│   │   │   ├── paper_service.py
│   │   │   ├── recommendation_service.py
│   │   │   ├── post_service.py
│   │   │   └── social_service.py
│   │   │
│   │   ├── crawlers/            # 爬虫模块
│   │   │   └── nature_crawler.py
│   │   │
│   │   ├── tasks/               # 异步任务
│   │   │   ├── crawl_tasks.py
│   │   │   └── embed_tasks.py
│   │   │
│   │   └── utils/               # 工具函数
│   │       ├── jwt_handler.py
│   │       └── embedding_utils.py
│   │
│   ├── scripts/                 # 脚本
│   │   ├── init_db.py
│   │   └── populate_data.py
│   │
│   ├── requirements.txt
│   └── server.py                # 启动脚本
│
├── frontend/
│   ├── web/                     # 网页版 (Next.js)
│   └── miniapp/                 # 小程序版 (Taro)
│
└── init.sh                      # 项目初始化脚本
```

## 🛠️ 核心功能

### 1. 论文发现
- 自动爬取 Nature, Science, Cell 等期刊
- 期刊封面瀑布流展示
- 论文元数据（标题、摘要、作者、DOI、影响因子）
- 关键词提取与索引

### 2. 智能推荐
- 基于语义相似度的推荐（Sentence Transformers）
- 用户行为建模（点赞、收藏、阅读历史）
- 向量相似度检索（pgvector）
- 引文图谱推荐

### 3. 学术社交
- 用户注册/登录（JWT 认证）
- 发布阅读心得（类朋友圈）
- 点赞、收藏、评论
- 关注/好友系统
- 好友动态流

### 4. 论文阅读
- 论文详情页
- 引文/被引关系
- 引用数统计
- PDF 在线阅读（待实现）

## 📊 技术栈

### 后端
- **框架**: FastAPI (Python)
- **数据库**: SQLite/PostgreSQL + pgvector
- **认证**: JWT + bcrypt
- **爬虫**: httpx + BeautifulSoup4
- **向量化**: Sentence Transformers + 自定义 TF-IDF
- **异步任务**: Celery (预留)

### 前端
- **网页版**: Next.js + React + TypeScript
- **小程序**: Taro + React + NutUI
- **UI 框架**: TailwindCSS
- **状态管理**: Zustand

## 🔧 开发命令

```bash
# 初始化项目
./TopScholar/init.sh

# 运行服务器
cd TopScholar/backend
python3 server.py --reload

# 运行爬虫
python3 app/tasks/crawl_tasks.py

# 生成 embedding
python3 app/tasks/embed_tasks.py
```

## 📝 TODO

- [ ] 创建网页版前端（Next.js）
- [ ] 创建小程序版前端（Taro）
- [ ] 实现全文 PDF 阅读器
- [ ] 实现引文图谱可视化
- [ ] 集成 MinIO 文件存储
- [ ] 实现邮件通知系统
- [ ] 部署到生产环境

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

---

**TopScholar** - 让学术发现更简单！