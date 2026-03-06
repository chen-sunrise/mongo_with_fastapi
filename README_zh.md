<p align="left">
    <a href="README.md">English</a> ｜ 中文
</p>

# FastAPI Backend Project

这是一个基于 **FastAPI** 框架的后端项目，数据库使用`MongoDB`，采用 `Docker` 和 `docker-compose` 进行管理，并通过 `Traefik` 作为反向代理进行负载均衡。本项目结构包含应用的 API、数据模型、CRUD 操作、依赖配置、用户认证和安全设置等模块，适用于开发和生产环境。

## 目录结构
```
.
├── README.md                   # 项目说明
├── backend                     # 后端应用代码和配置
│   ├── Dockerfile              # 后端 Docker 镜像构建文件
│   ├── app                     # FastAPI 应用目录
│   │   ├── api                 # API 路由和依赖配置
│   │   │   ├── endpoints       # API 路由定义
│   │   ├── core                # 核心配置和安全设置
│   │   ├── crud                # 数据库 CRUD 操作
│   │   ├── models              # 数据库模型定义
│   │   ├── schemas             # 数据传输模型定义
│   │   ├── utils               # 实用工具模块
│   │   └── main.py             # FastAPI 应用主入口
│   ├── gunicorn_conf.py        # Gunicorn 配置文件
│   └── scripts                 # 启动脚本
├── docker-compose.yml          # Docker Compose 配置文件
├── docker-compose.traefik.yml  # Docker Compose 配置文件（Traefik）
├── poetry.lock                 # Poetry 锁文件
├── pyproject.toml              # Poetry 项目配置文件
├── run.sh                      # 应用启动脚本
├── run.traefik.sh              # 使用 Traefik 启动的脚本
└── tests                       # 测试代码目录
```

## 功能

- **API 端点**：提供用户注册、登录、获取信息等接口。
- **API v2**：新增统一响应结构（`data`、`meta`、`error`）和 cursor 分页能力。
- **用户认证**：支持 JWT 令牌的认证与授权。
- **CRUD 操作**：封装了数据操作的基本功能。
- **运行时稳健性**：生命周期托管 Mongo/Redis 客户端，支持超时保护、限流和降级。
- **健康检查与监控**：新增 `/health/live`、`/health/ready`、`/metrics` 端点。
- **反向代理**：利用 Traefik 进行服务的动态路由和负载均衡。
- **配置管理**：Gunicorn 用于生产环境的应用部署。
- **测试支持**：包含测试文件，便于扩展自动化测试。

## 部署与运行

### 本地运行（无 Traefik）

```bash
# 启动 Docker 服务
./run.sh
```

### 使用 Traefik 部署

```bash
# 启动 Docker 服务（Traefik 支持）
./run.traefik.sh
```

### 配置说明

### Docker 环境变量

配置位于 .env 文件中，包含以下参数：

- **MONGO_DB_URI**：Mongo 副本集连接地址，例如 `mongodb://mongo1:27017,mongo2:27017,mongo3:27017/?replicaSet=rs0`
- **MONGO_DB_DATABASE**：Mongo 数据库名
- **MONGO_DB_USER_COLLECTION**：用户集合名
- **MONGO_DB_ITEM_COLLECTION**：物品集合名
- **SECRET_KEY**：JWT 加密密钥
- **ACCESS_TOKEN_EXPIRE_MINUTES**：访问令牌过期时间（分钟）
- **REDIS_URL**：Redis 连接地址，例如 `redis://redis:6379/0`
- **CACHE_TTL_SECONDS**：缓存 TTL（秒）
- **RATE_LIMIT_PER_MINUTE**：读请求限流
- **LOGIN_RATE_LIMIT_PER_MINUTE**：登录限流
- **REQUEST_TIMEOUT_MS**：请求超时阈值（毫秒）

Traefik 反向代理

使用 docker-compose.traefik.yml 配置文件，通过 Traefik 管理服务路由。将应用部署在 docker network 中，方便其他容器访问。

### 新增运行时端点

- `GET /health/live`
- `GET /health/ready`
- `GET /metrics`
- `POST /api/v2/users/access-token`
- `POST /api/v2/users/register`
- `GET /api/v2/users/me`
- `GET /api/v2/items/list?cursor=<id>&limit=<n>`

### 性能与发布资产

- 压测脚本：`tests/load/k6_baseline.js`
- 基线与 SLO 模板：`docs/perf/baseline.md`
- 灰度发布手册：`docs/rollout/gray-release.md`
