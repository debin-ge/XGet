-- 创建数据库
CREATE DATABASE account_db;
CREATE DATABASE proxy_db;
CREATE DATABASE scraper_db;
CREATE DATABASE user_db;

-- 切换到用户数据库
\c user_db;

-- 创建用户表
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'USER',
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建用户会话表
CREATE TABLE user_sessions (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(id) ON DELETE CASCADE,
    refresh_token VARCHAR(500) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引以提高查询性能
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_refresh_token ON user_sessions(refresh_token);

-- 切换到账户数据库
\c account_db;

-- 创建账户表
CREATE TABLE accounts (
    id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255),
    email VARCHAR(255),
    email_password VARCHAR(255),
    login_method VARCHAR(50),
    proxy_id VARCHAR(36),
    cookies JSONB,
    headers JSONB,
    user_agent VARCHAR(500),
    active BOOLEAN DEFAULT FALSE,
    last_used TIMESTAMP,
    error_msg VARCHAR(500),
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引以提高查询性能
CREATE INDEX idx_accounts_is_deleted ON accounts(is_deleted);

-- 创建登录历史表
CREATE TABLE login_history (
    id VARCHAR(36) PRIMARY KEY,
    account_id VARCHAR(36) REFERENCES accounts(id),
    proxy_id VARCHAR(36),
    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50),
    error_msg VARCHAR(500),
    cookies_count INTEGER DEFAULT 0,
    response_time INTEGER
);

-- 切换到代理数据库
\c proxy_db;

-- 创建代理表
CREATE TABLE proxies (
    id VARCHAR(36) PRIMARY KEY,
    type VARCHAR(50),
    ip VARCHAR(255) NOT NULL,
    port INTEGER NOT NULL,
    username VARCHAR(255),
    password VARCHAR(255),
    country VARCHAR(255),
    city VARCHAR(255),
    isp VARCHAR(255),
    latency INTEGER,
    success_rate FLOAT DEFAULT 0.0,
    last_check TIMESTAMP,
    status VARCHAR(50) DEFAULT 'INACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建代理质量监控表
CREATE TABLE proxy_qualities (
    id VARCHAR(36) PRIMARY KEY,
    proxy_id VARCHAR(36) REFERENCES proxies(id) ON DELETE CASCADE,
    total_usage INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    quality_score FLOAT DEFAULT 0.8,
    last_used TIMESTAMP,
    cooldown_time INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(proxy_id)
);

-- 创建代理使用历史记录表
CREATE TABLE proxy_usage_history (
    id VARCHAR(36) PRIMARY KEY,
    proxy_id VARCHAR(36) REFERENCES proxies(id) ON DELETE CASCADE,
    user_id VARCHAR(36),
    service_name VARCHAR(255),
    success VARCHAR(20) DEFAULT 'SUCCESS',
    response_time INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引以提高查询性能
CREATE INDEX idx_proxy_usage_history_proxy_id ON proxy_usage_history(proxy_id);
CREATE INDEX idx_proxy_usage_history_user_id ON proxy_usage_history(user_id);
CREATE INDEX idx_proxy_usage_history_service_name ON proxy_usage_history(service_name);
CREATE INDEX idx_proxy_usage_history_success ON proxy_usage_history(success);
CREATE INDEX idx_proxy_usage_history_created_at ON proxy_usage_history(created_at);
CREATE INDEX idx_proxy_usage_history_proxy_created ON proxy_usage_history(proxy_id, created_at);

-- 切换到爬虫数据库
\c scraper_db;

-- 创建任务表
CREATE TABLE tasks (
    id VARCHAR(36) PRIMARY KEY,
    task_type VARCHAR(50) NOT NULL,
    parameters JSONB NOT NULL,
    account_id VARCHAR(36),
    proxy_id VARCHAR(36),
    status VARCHAR(50) DEFAULT 'PENDING',
    progress FLOAT DEFAULT 0.0,
    result_count INTEGER DEFAULT 0,
    error_message VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- 创建任务执行表
CREATE TABLE task_executions (
    id VARCHAR(36) PRIMARY KEY,
    task_id VARCHAR(36) REFERENCES tasks(id),
    account_id VARCHAR(36),
    proxy_id VARCHAR(36),
    status VARCHAR(50),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration INTEGER,
    error_message VARCHAR(500)
);

