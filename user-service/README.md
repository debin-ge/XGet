# User Service

用户管理服务，提供用户注册、认证、权限管理等功能。

## 功能特性

- 用户注册和管理
- 用户认证和授权
- JWT令牌管理
- 角色和权限管理
- 用户偏好设置
- 会话管理
- 登录历史记录

## 技术栈

- FastAPI
- SQLAlchemy
- PostgreSQL
- Redis
- JWT
- bcrypt

## 快速开始

### 环境要求

- Python 3.11+
- PostgreSQL
- Redis

### 安装依赖

```bash
pip install -r requirements.txt
```

### 环境变量配置

创建 `.env` 文件：

```env
# 数据库配置
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=user_db

# Redis配置
REDIS_URL=redis://localhost:6379/0

# JWT配置
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# 日志配置
LOG_LEVEL=INFO
```

### 运行服务

```bash
python -m uvicorn app.main:app --reload
```

服务将在 http://localhost:8000 启动

## API文档

启动服务后，访问以下地址查看API文档：

- Swagger UI: http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc

## 主要API端点

### 用户管理

- `POST /api/v1/users/register` - 用户注册
- `POST /api/v1/users/login` - 用户登录
- `GET /api/v1/users/me` - 获取当前用户信息
- `PUT /api/v1/users/me` - 更新当前用户信息
- `PUT /api/v1/users/me/password` - 修改密码
- `PUT /api/v1/users/me/preferences` - 更新偏好设置

### 认证

- `POST /api/v1/auth/refresh` - 刷新令牌
- `POST /api/v1/auth/revoke` - 撤销令牌
- `POST /api/v1/auth/logout` - 用户登出
- `GET /api/v1/auth/verify` - 验证令牌

### 角色和权限

- `GET /api/v1/roles/` - 获取角色列表
- `POST /api/v1/roles/` - 创建角色
- `PUT /api/v1/roles/{role_id}` - 更新角色
- `DELETE /api/v1/roles/{role_id}` - 删除角色
- `POST /api/v1/roles/assign` - 分配角色给用户
- `DELETE /api/v1/roles/remove` - 移除用户角色

## 数据库模型

### 用户表 (users)
- 基本信息：用户名、邮箱、密码哈希
- 状态信息：是否活跃、是否验证、是否超级用户
- 登录信息：最后登录时间、失败登录次数、锁定时间
- 偏好设置：时区、语言、自定义偏好

### 角色表 (roles)
- 角色名称和描述
- 是否活跃状态

### 权限表 (permissions)
- 权限名称和描述
- 资源类型和操作类型

### 用户角色关联表 (user_roles)
- 用户和角色的多对多关系
- 角色分配时间和过期时间

### 用户会话表 (user_sessions)
- 会话令牌和刷新令牌
- 客户端信息（IP、User-Agent）
- 会话状态和过期时间

### 登录历史表 (login_history)
- 登录时间和登出时间
- 客户端信息
- 登录成功/失败状态

## 默认角色

系统初始化时会创建以下默认角色：

### admin
- 系统管理员，拥有所有权限
- 可以管理用户、角色、账户、代理等

### user
- 普通用户，拥有基本权限
- 可以查看和更新自己的信息
- 可以管理自己的账户和代理

### guest
- 访客用户，拥有有限权限
- 只能查看基本信息

## 安全特性

- 密码强度验证
- 账户锁定机制
- JWT令牌管理
- 权限控制
- 会话管理
- 登录历史记录

## Docker部署

```bash
# 构建镜像
docker build -t user-service .

# 运行容器
docker run -p 8000:8000 user-service
```

## 开发

### 代码结构

```
app/
├── api/           # API路由
├── core/          # 核心配置
├── db/            # 数据库配置
├── models/        # 数据模型
├── schemas/       # Pydantic模式
├── services/      # 业务逻辑
└── main.py        # 应用入口
```

### 测试

```bash
# 运行测试
pytest

# 运行覆盖率测试
pytest --cov=app
``` 