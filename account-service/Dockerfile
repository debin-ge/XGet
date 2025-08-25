FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖，包括 Playwright 运行 Chromium 所需的库
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    wget \
    # Playwright 依赖
    libglib2.0-0 \
    libgobject-2.0-0 \
    libnspr4 \
    libnss3 \
    libdbus-1-3 \
    libatk1.0-0 \
    libexpat1 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libxcb1 \
    libxkbcommon0 \
    libasound2 \
    # 其他必要的依赖
    libdrm2 \
    libxss1 \
    libgtk-3-0 \
    libxshmfence1 \
    libatspi2.0-0 \
    # 清理 apt 缓存，减小镜像体积
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 设置Playwright环境变量以使用无头模式
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# 安装Playwright浏览器
RUN playwright install chromium

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
