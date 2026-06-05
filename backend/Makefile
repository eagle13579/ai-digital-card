# ── AI数字名片 ─ Makefile ─────────────────────────────────────────────
# 本地开发命令：测试、代码检查、全量CI

.PHONY: help test lint ci install

help:
	@echo "AI数字名片 开发命令"
	@echo ""
	@echo "  make install   安装所有依赖 (pip install -r requirements.txt)"
	@echo "  make test      运行所有 pytest 测试"
	@echo "  make lint      运行 ruff 代码风格检查"
	@echo "  make ci        全量CI = lint + test"

install:
	pip install -r requirements.txt

test:
	python -m pytest tests/ -v --tb=short --no-header

test-verbose:
	python -m pytest tests/ -v --tb=long

lint:
	python -m ruff check app/ tests/ main.py

lint-fix:
	python -m ruff check --fix app/ tests/ main.py

ci: lint test
