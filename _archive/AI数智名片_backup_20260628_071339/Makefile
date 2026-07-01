# ──────────────────────────────────────────────
# Makefile — AI 数字名片 本地开发命令
# ──────────────────────────────────────────────

.PHONY: help install install-backend install-frontend dev dev-backend dev-frontend \
        build build-backend build-frontend test test-backend lint lint-backend lint-frontend \
        clean clean-backend clean-frontend docker-up docker-down docker-build \
        check

# 显示帮助信息
help:
	@echo "╔══════════════════════════════════════════╗"
	@echo "║   AI 数字名片 - 开发命令                 ║"
	@echo "╚══════════════════════════════════════════╝"
	@echo ""
	@echo "🛠  安装依赖:"
	@echo "  make install         安装前后端所有依赖"
	@echo "  make install-backend 安装后端 Python 依赖"
	@echo "  make install-frontend安装前端 Node 依赖"
	@echo ""
	@echo "🚀 本地开发:"
	@echo "  make dev             同时启动前后端开发服务器"
	@echo "  make dev-backend     启动后端开发服务器 (uvicorn)"
	@echo "  make dev-frontend    启动前端开发服务器 (vite)"
	@echo ""
	@echo "📦 构建:"
	@echo "  make build           构建前后端生产版本"
	@echo "  make build-backend   构建后端 Docker 镜像"
	@echo "  make build-frontend  构建前端静态文件"
	@echo ""
	@echo "🧪 测试:"
	@echo "  make test            运行后端测试 (pytest)"
	@echo "  make test-backend    同上"
	@echo ""
	@echo "🔍 代码检查:"
	@echo "  make lint            运行前后端代码检查"
	@echo "  make lint-backend    ruff 检查"
	@echo "  make lint-frontend   TypeScript 类型检查"
	@echo ""
	@echo "🧹 清理:"
	@echo "  make clean           清理所有构建产物"
	@echo "  make clean-backend   清理 Python 缓存"
	@echo "  make clean-frontend  清理 dist 目录"
	@echo ""
	@echo "🐳 Docker:"
	@echo "  make docker-up       启动 Docker Compose 服务"
	@echo "  make docker-down     停止 Docker Compose 服务"
	@echo "  make docker-build    重新构建 Docker 镜像"
	@echo ""

# ── 安装 ──────────────────────────────────────

install: install-backend install-frontend

install-backend:
	@echo "📦 安装后端 Python 依赖..."
	cd backend && pip install -r requirements.txt
	@echo "✅ 后端依赖安装完成"

install-frontend:
	@echo "📦 安装前端 Node 依赖..."
	cd frontend && npm install
	@echo "✅ 前端依赖安装完成"

# ── 本地开发 ──────────────────────────────────

dev-backend:
	@echo "🚀 启动后端开发服务器 (http://localhost:8201)..."
	cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8201

dev-frontend:
	@echo "🚀 启动前端开发服务器 (http://localhost:3000)..."
	cd frontend && npm run dev

dev:
	@echo "🚀 同时启动前后端开发服务器..."
	@trap 'kill 0' EXIT; \
		$(MAKE) dev-backend & \
		$(MAKE) dev-frontend & \
		wait

# ── 构建 ──────────────────────────────────────

build: build-frontend build-backend

build-backend:
	@echo "📦 构建后端 Docker 镜像..."
	docker build -t ai-digital-card-backend:latest backend/
	@echo "✅ 后端镜像构建完成"

build-frontend:
	@echo "📦 构建前端静态文件..."
	cd frontend && npm run build
	@echo "✅ 前端构建完成 (frontend/dist/)"

# ── 测试 ──────────────────────────────────────

test: test-backend

test-backend:
	@echo "🧪 运行后端测试..."
	cd backend && python -m pytest -v --tb=short
	@echo "✅ 测试完成"

# ── 代码检查 ──────────────────────────────────

lint: lint-backend lint-frontend

lint-backend:
	@echo "🔍 运行 ruff 代码检查..."
	cd backend && ruff check .
	@echo "✅ Ruff 检查通过"

lint-frontend:
	@echo "🔍 运行 TypeScript 类型检查..."
	cd frontend && npm run lint
	@echo "✅ TypeScript 类型检查通过"

# ── 清理 ──────────────────────────────────────

clean: clean-backend clean-frontend

clean-backend:
	@echo "🧹 清理 Python 缓存..."
	find backend -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find backend -type f -name "*.pyc" -delete
	rm -rf backend/.pytest_cache
	@echo "✅ 后端清理完成"

clean-frontend:
	@echo "🧹 清理前端构建产物..."
	cd frontend && rm -rf dist
	@echo "✅ 前端清理完成"

# ── Docker Compose ────────────────────────────

docker-build:
	@echo "🐳 构建 Docker 镜像..."
	docker compose build

docker-up:
	@echo "🐳 启动 Docker Compose 服务..."
	docker compose up -d
	@echo "✅ 服务已启动 (后端: http://localhost:8201, 前端: http://localhost:8200)"

docker-down:
	@echo "🐳 停止 Docker Compose 服务..."
	docker compose down
	@echo "✅ 服务已停止"

docker-logs:
	docker compose logs -f

# ── 综合检查 ──────────────────────────────────

check: lint test build
	@echo "✅ 全部检查通过！"
