-- 创建数据库
CREATE DATABASE account_db;
CREATE DATABASE proxy_db;
CREATE DATABASE scraper_db;
CREATE DATABASE user_db;
CREATE DATABASE analytics_db;

-- 切换到用户数据库
\c user_db;

-- 创建用户表
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    phone VARCHAR(20),
    avatar_url VARCHAR(255),
    
    -- 用户状态
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    is_superuser BOOLEAN DEFAULT FALSE,
    
    -- 登录相关
    last_login TIMESTAMP,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    
    -- 用户偏好设置
    preferences JSONB DEFAULT '{}',
    timezone VARCHAR(50) DEFAULT 'UTC',
    language VARCHAR(10) DEFAULT 'en',
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建用户会话表
CREATE TABLE user_sessions (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    refresh_token VARCHAR(255) UNIQUE,
    ip_address VARCHAR(45),  -- IPv6支持
    user_agent TEXT,
    device_info TEXT,
    location VARCHAR(100),
    
    -- 会话状态
    is_active BOOLEAN DEFAULT TRUE,
    is_revoked BOOLEAN DEFAULT FALSE,
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    revoked_at TIMESTAMP
);

-- 创建角色相关表
CREATE TABLE roles (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE permissions (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    resource VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE role_permissions (
    role_id VARCHAR(36) REFERENCES roles(id),
    permission_id VARCHAR(36) REFERENCES permissions(id),
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE user_roles (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(id) NOT NULL,
    role_id VARCHAR(36) REFERENCES roles(id) NOT NULL,
    assigned_by VARCHAR(36),
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- 创建索引以提高查询性能
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_refresh_token ON user_sessions(refresh_token);
CREATE INDEX idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX idx_user_roles_role_id ON user_roles(role_id);

-- 创建用户登录历史表
CREATE TABLE login_history (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(id) NOT NULL,
    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    logout_time TIMESTAMP,
    
    -- 登录信息
    ip_address VARCHAR(45),
    user_agent TEXT,
    device_info TEXT,
    location VARCHAR(100),
    
    -- 登录状态
    is_successful BOOLEAN DEFAULT TRUE,
    failure_reason TEXT,
    
    -- 会话信息
    session_id VARCHAR(36) REFERENCES user_sessions(id)
);

CREATE INDEX idx_login_history_user_id ON login_history(user_id);
CREATE INDEX idx_login_history_login_time ON login_history(login_time);

-- 切换到账户数据库
\c account_db;

-- 创建账户表
CREATE TABLE accounts (
    id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
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
    account_id VARCHAR(36),
    task_id VARCHAR(36),
    service_name VARCHAR(255),
    success VARCHAR(20) DEFAULT 'SUCCESS',
    response_time INTEGER,
    
    proxy_ip VARCHAR(255),
    proxy_port INTEGER,
    account_username_email VARCHAR(255),
    task_name VARCHAR(255),
    quality_score FLOAT,
    latency INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引以提高查询性能
CREATE INDEX idx_proxy_usage_history_proxy_id ON proxy_usage_history(proxy_id);
CREATE INDEX idx_proxy_usage_history_account_id ON proxy_usage_history(account_id);
CREATE INDEX idx_proxy_usage_history_service_name ON proxy_usage_history(service_name);
CREATE INDEX idx_proxy_usage_history_success ON proxy_usage_history(success);
CREATE INDEX idx_proxy_usage_history_created_at ON proxy_usage_history(created_at);
CREATE INDEX idx_proxy_usage_history_proxy_created ON proxy_usage_history(proxy_id, created_at);
CREATE INDEX idx_proxy_usage_history_account_email ON proxy_usage_history(account_username_email);
CREATE INDEX idx_proxy_usage_history_task_name ON proxy_usage_history(task_name);

-- 切换到爬虫数据库
\c scraper_db;

-- 创建任务表
CREATE TABLE tasks (
    id VARCHAR(36) PRIMARY KEY,
    task_name VARCHAR(255) NOT NULL,  -- 任务名称
    describe TEXT,  -- 任务描述
    task_type VARCHAR(50) NOT NULL,
    parameters JSONB NOT NULL,
    account_id VARCHAR(36),
    proxy_id VARCHAR(36),
    status VARCHAR(50) DEFAULT 'PENDING',
    error_message TEXT,  -- 错误信息
    user_id VARCHAR(36) NOT NULL,  -- 创建任务的用户ID
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

-- 切换到分析数据库
\c analytics_db;

-- 创建统计指标配置表
CREATE TABLE analytics_metrics (
    id UUID PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,  -- ACCOUNT, PROXY, TASK, RESULT
    calculation_type VARCHAR(20) NOT NULL,  -- COUNT, SUM, AVG, MAX, MIN, CUSTOM
    data_source VARCHAR(50) NOT NULL,
    dimensions JSONB DEFAULT '[]',
    filters JSONB DEFAULT '{}',
    refresh_interval INTEGER DEFAULT 3600,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建实时统计结果表
CREATE TABLE realtime_stats (
    id UUID PRIMARY KEY,
    metric_id UUID REFERENCES analytics_metrics(id),
    timestamp TIMESTAMP NOT NULL,
    value FLOAT NOT NULL,
    dimensions JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建历史聚合表
CREATE TABLE historical_aggregates (
    id UUID PRIMARY KEY,
    metric_id UUID REFERENCES analytics_metrics(id),
    period VARCHAR(20) NOT NULL,  -- hourly, daily, weekly, monthly
    timestamp TIMESTAMP NOT NULL,
    value FLOAT NOT NULL,
    dimensions JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引以提高查询性能
CREATE INDEX idx_analytics_metrics_category ON analytics_metrics(category);
CREATE INDEX idx_analytics_metrics_is_active ON analytics_metrics(is_active);
CREATE INDEX idx_realtime_stats_metric_id ON realtime_stats(metric_id);
CREATE INDEX idx_realtime_stats_timestamp ON realtime_stats(timestamp);
CREATE INDEX idx_historical_aggregates_metric_id ON historical_aggregates(metric_id);
CREATE INDEX idx_historical_aggregates_period ON historical_aggregates(period);
CREATE INDEX idx_historical_aggregates_timestamp ON historical_aggregates(timestamp);

