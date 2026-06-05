# AI数字名片 — Makefile
.PHONY: install test run docker docker-prod clean lint help

help: ## 显示帮助
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | 		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## 安装依赖
	cd backend && pip install -r requirements.txt

test: ## 运行测试
	cd backend && python -m pytest tests/ -v --tb=short

test-cov: ## 运行测试+覆盖率
	cd backend && python -m pytest tests/ --cov=app --cov-report=term --cov-report=html

run: ## 本地启动
	cd backend && python main.py

docker: ## Docker构建+启动
	docker-compose up -d --build

docker-prod: ## 生产Docker启动
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

docker-down: ## 停止Docker
	docker-compose down

clean: ## 清理缓存
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache

lint: ## 代码检查
	cd backend && python -m flake8 app/ --max-line-length=120 --ignore=E203,W503 2>/dev/null || \
		echo "flake8未安装, 跳过"

deploy: ## 一键部署
	bash deploy.sh

tag: ## 版本标签
	git tag v$(shell date +%Y.%m.%d) -m "Release $(shell date +%Y-%m-%d)"
