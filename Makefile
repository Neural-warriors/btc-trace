.PHONY: setup ingest train test benchmark run demo clean help cpp-build cpp-test

# Project directories
PROJECT_DIR := $(shell pwd)
DATA_DIR := $(PROJECT_DIR)/data
MODELS_DIR := $(PROJECT_DIR)/models
REPORTS_DIR := $(PROJECT_DIR)/reports
OUTPUTS_DIR := $(PROJECT_DIR)/outputs
CPP_DIR := $(PROJECT_DIR)/cpp
FRONTEND_DIR := $(PROJECT_DIR)/frontend
BACKEND_DIR := $(PROJECT_DIR)/backend

# Python
PYTHON := /usr/bin/python3
PIP := /usr/bin/python3 -m pip

# Colors
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m

help: ## Show this help
	@echo "$(GREEN)BTC-TRACE: AI-Powered Bitcoin Transaction Monitoring$(NC)"
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}'

setup: ## Install all dependencies and build C++ engine
	@echo "$(GREEN)[1/4] Installing Python dependencies...$(NC)"
	$(PIP) install --user -r requirements.txt
	@echo "$(GREEN)[2/4] Building C++ graph engine...$(NC)"
	cd $(CPP_DIR) && mkdir -p build && cd build && cmake .. -DCMAKE_BUILD_TYPE=Release && cmake --build . -j4
	@echo "$(GREEN)[3/4] Installing frontend dependencies...$(NC)"
	cd $(FRONTEND_DIR) && npm install
	@echo "$(GREEN)[4/4] Creating data directories...$(NC)"
	mkdir -p $(DATA_DIR)/{raw,clean,quarantine,features,splits/{train,validation,test}}
	mkdir -p $(MODELS_DIR) $(REPORTS_DIR) $(OUTPUTS_DIR)
	@echo "$(GREEN)Setup complete!$(NC)"

generate-data: ## Generate synthetic dataset
	@echo "$(GREEN)Generating synthetic dataset...$(NC)"
	cd $(PROJECT_DIR) && $(PYTHON) scripts/generate_synthetic_data.py
	@echo "$(GREEN)Synthetic data generated in data/raw/$(NC)"

ingest: generate-data ## Ingest and clean data
	@echo "$(GREEN)Running data pipeline...$(NC)"
	cd $(PROJECT_DIR) && $(PYTHON) -c "\
from ml.pipeline.clean import clean_pipeline; \
from pathlib import Path; \
result = clean_pipeline(Path('data/raw/transactions.csv'), Path('data')); \
print(f'Processed: {result.total_records} records'); \
print(f'Valid: {result.valid_records}'); \
"
	@echo "$(GREEN)Running dataset split...$(NC)"
	cd $(PROJECT_DIR) && $(PYTHON) -c "\
from ml.pipeline.split import temporal_split; \
from ml.pipeline.id_mapping import EntityMapper; \
import pandas as pd; \
from pathlib import Path; \
df = pd.read_parquet('data/clean/transactions_clean.parquet'); \
train, val, test = temporal_split(df, output_dir=Path('data/splits')); \
print(f'Train: {len(train)}, Val: {len(val)}, Test: {len(test)}'); \
mapper = EntityMapper(); \
mapper.build_from_dataframe(df); \
mapper.save(Path('data/clean/entity_mapping.json')); \
print(f'Entities mapped: {mapper.total_entities()}'); \
"
	@echo "$(GREEN)Data pipeline complete!$(NC)"

train: ## Train ML models
	@echo "$(GREEN)Training ML models...$(NC)"
	cd $(PROJECT_DIR) && $(PYTHON) scripts/train_models.py
	@echo "$(GREEN)Training complete! Models saved in models/$(NC)"

test: cpp-test ## Run all tests
	@echo "$(GREEN)Running Python tests...$(NC)"
	cd $(PROJECT_DIR) && $(PYTHON) -m pytest tests/ -v --tb=short
	@echo "$(GREEN)All tests passed!$(NC)"

cpp-build: ## Build C++ graph engine
	@echo "$(GREEN)Building C++ graph engine...$(NC)"
	cd $(CPP_DIR) && mkdir -p build && cd build && cmake .. -DCMAKE_BUILD_TYPE=Release && cmake --build . -j4

cpp-test: cpp-build ## Run C++ tests
	@echo "$(GREEN)Running C++ tests...$(NC)"
	cd $(CPP_DIR)/build && ./test_graph

benchmark: cpp-build ## Run benchmarks
	@echo "$(GREEN)Running C++ graph benchmarks...$(NC)"
	cd $(CPP_DIR)/build && ./bench_graph
	@echo ""
	@echo "$(GREEN)Running Python benchmarks...$(NC)"
	cd $(PROJECT_DIR) && $(PYTHON) scripts/benchmark.py

run: ## Start combined BTC-TRACE application
	@echo "$(GREEN)Starting BTC-TRACE...$(NC)"
	@echo ""
	@echo "$(YELLOW)App URL:  http://localhost:8000$(NC)"
	@echo "$(YELLOW)API Docs: http://localhost:8000/api/docs$(NC)"
	@echo ""
	cd $(PROJECT_DIR) && $(PYTHON) -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

run-backend: ## Start backend only
	cd $(PROJECT_DIR) && $(PYTHON) -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

run-frontend: ## Start frontend only
	cd $(FRONTEND_DIR) && npm run dev

demo: setup ingest train ## Full demo: setup, ingest, train, then run
	@$(MAKE) run

clean: ## Clean generated files
	rm -rf $(DATA_DIR)/clean/* $(DATA_DIR)/quarantine/* $(DATA_DIR)/features/*
	rm -rf $(DATA_DIR)/splits/train/* $(DATA_DIR)/splits/validation/* $(DATA_DIR)/splits/test/*
	rm -rf $(MODELS_DIR)/* $(REPORTS_DIR)/* $(OUTPUTS_DIR)/*
	rm -rf $(CPP_DIR)/build
	@echo "$(GREEN)Cleaned all generated files$(NC)"

clean-all: clean ## Clean everything including raw data and node_modules
	rm -rf $(DATA_DIR)/raw/*
	rm -rf $(FRONTEND_DIR)/node_modules
	@echo "$(GREEN)Cleaned everything$(NC)"
