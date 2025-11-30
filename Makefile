.PHONY: install run dev clean deploy help

# Python configuration
PYTHON = python3
VENV = .venv
VENV_PYTHON = $(VENV)/bin/python
VENV_PIP = $(VENV)/bin/pip
PORT = 7860

help: ## Show this help message
	@echo ""
	@echo "  🏗️  CodeAtlas - Commands"
	@echo "  ========================"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'
	@echo ""

install: ## Create venv and install dependencies
	@echo "📦 Installing system dependencies (graphviz)..."
	@if command -v apt-get >/dev/null 2>&1; then \
		sudo apt-get update -qq && sudo apt-get install -y -qq graphviz; \
	elif command -v brew >/dev/null 2>&1; then \
		brew install graphviz; \
	elif command -v yum >/dev/null 2>&1; then \
		sudo yum install -y graphviz; \
	else \
		echo "⚠️  Please install graphviz manually"; \
	fi
	@echo "📦 Creating virtual environment..."
	@$(PYTHON) -m venv $(VENV)
	@$(VENV_PIP) install --upgrade pip
	@$(VENV_PIP) install -r requirements.txt
	@echo "✅ Done! Run 'make run' to start"

run: ## Run the application
	@lsof -ti:$(PORT) | xargs kill -9 2>/dev/null || true
	@echo "🚀 Starting CodeAtlas on http://localhost:$(PORT)"
	@$(VENV_PYTHON) app.py

dev: ## Run with auto-reload
	@lsof -ti:$(PORT) | xargs kill -9 2>/dev/null || true
	@echo "🔧 Starting in dev mode..."
	@GRADIO_WATCH_DIRS=. $(VENV_PYTHON) app.py

deploy: ## Deploy backend to Modal
	@echo "☁️  Deploying to Modal..."
	@modal deploy modal_backend.py
	@echo "✅ Deployed!"

clean: ## Remove venv and cache files
	@rm -rf $(VENV) __pycache__ src/**/__pycache__ .session_state.json
	@rm -rf data/diagrams/* data/audios/* data/logs/*
	@echo "✅ Cleaned!"
