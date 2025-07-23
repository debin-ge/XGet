-- 创建数据库
CREATE DATABASE account_db;
CREATE DATABASE proxy_db;
CREATE DATABASE scraper_db;
CREATE DATABASE processing_db;
CREATE DATABASE storage_db;

-- 切换到账户数据库
\c account_db;

-- 创建账户表
CREATE TABLE accounts (
    id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    email_password VARCHAR(255),
    login_method VARCHAR(50),
    password VARCHAR(255),
    cookies JSONB,
    headers JSONB,
    user_agent VARCHAR(500),
    active BOOLEAN DEFAULT true,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    error_msg VARCHAR(500)
);

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
    ip VARCHAR(255) NOT NULL,
    port INTEGER NOT NULL,
    username VARCHAR(255),
    password VARCHAR(255),
    type VARCHAR(50),
    location VARCHAR(255),
    active BOOLEAN DEFAULT true,
    last_check TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建代理检查表
CREATE TABLE proxy_checks (
    id VARCHAR(36) PRIMARY KEY,
    proxy_id VARCHAR(36) REFERENCES proxies(id),
    check_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50),
    response_time INTEGER,
    error_message VARCHAR(500)
);

-- 创建代理源表
CREATE TABLE proxy_sources (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    url VARCHAR(500),
    auth_required BOOLEAN DEFAULT false,
    auth_username VARCHAR(255),
    auth_password VARCHAR(255),
    active BOOLEAN DEFAULT true,
    last_fetch TIMESTAMP,
    fetch_interval INTEGER DEFAULT 3600,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 切换到爬虫数据库
\c scraper_db;

-- 创建任务表
CREATE TABLE tasks (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    task_type VARCHAR(50) NOT NULL,
    parameters JSONB,
    status VARCHAR(50) DEFAULT 'pending',
    priority INTEGER DEFAULT 1,
    account_id VARCHAR(36),
    proxy_id VARCHAR(36),
    schedule JSONB,
    result_count INTEGER DEFAULT 0,
    progress FLOAT DEFAULT 0,
    error_message VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- 创建结果表
CREATE TABLE results (
    id VARCHAR(36) PRIMARY KEY,
    task_id VARCHAR(36) REFERENCES tasks(id),
    data_type VARCHAR(50),
    data JSONB,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建任务执行表
CREATE TABLE task_executions (
    id VARCHAR(36) PRIMARY KEY,
    task_id VARCHAR(36) REFERENCES tasks(id),
    account_id VARCHAR(36),
    proxy_id VARCHAR(36),
    status VARCHAR(50) DEFAULT 'pending',
    progress FLOAT DEFAULT 0,
    result_count INTEGER DEFAULT 0,
    error_message VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- 切换到处理服务数据库
\c processing_db;

-- 创建处理任务表
CREATE TABLE processing_tasks (
    id VARCHAR(36) PRIMARY KEY,
    task_type VARCHAR(50) NOT NULL,
    source_data_id VARCHAR(36) NOT NULL,
    parameters JSONB,
    status VARCHAR(50) DEFAULT 'pending',
    priority VARCHAR(50) DEFAULT 'normal',
    progress FLOAT DEFAULT 0,
    error_message VARCHAR(500),
    result_id VARCHAR(36),
    callback_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- 创建处理规则表
CREATE TABLE processing_rules (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    task_type VARCHAR(50) NOT NULL,
    rule_definition JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建处理结果表
CREATE TABLE processing_results (
    id VARCHAR(36) PRIMARY KEY,
    task_id VARCHAR(36) REFERENCES processing_tasks(id),
    data JSONB,
    metadata JSONB,
    storage_location VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 切换到存储服务数据库
\c storage_db;

-- 创建存储项表
CREATE TABLE storage_items (
    id VARCHAR(36) PRIMARY KEY,
    data_type VARCHAR(50) NOT NULL,
    content_hash VARCHAR(255),
    size INTEGER,
    storage_location VARCHAR(500) NOT NULL,
    storage_backend VARCHAR(50) NOT NULL,
    compression BOOLEAN DEFAULT false,
    encryption BOOLEAN DEFAULT false,
    version INTEGER DEFAULT 1,
    status VARCHAR(50) DEFAULT 'stored',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accessed_at TIMESTAMP
);

-- 创建元数据表
CREATE TABLE metadata (
    item_id VARCHAR(36) PRIMARY KEY REFERENCES storage_items(id),
    source_id VARCHAR(36),
    processing_id VARCHAR(36),
    tags JSONB,
    custom_fields JSONB,
    retention_policy VARCHAR(50),
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建存储后端表
CREATE TABLE storage_backends (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    configuration JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    priority INTEGER DEFAULT 1,
    capacity BIGINT,
    used_space BIGINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建保留策略表
CREATE TABLE retention_policies (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    active_period INTEGER NOT NULL,
    archive_period INTEGER NOT NULL,
    total_retention INTEGER NOT NULL,
    auto_delete BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
); 