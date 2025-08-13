-- 创建用户服务数据库
CREATE DATABASE IF NOT EXISTS user_db;

-- 使用数据库
\c user_db;

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 注意：表结构将由SQLAlchemy自动创建
-- 这里只是创建数据库和必要的扩展 