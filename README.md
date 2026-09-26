# BTC-TRACE: AI-Powered Monitoring & Analysis of Bitcoin Transaction Traffic

BTC-TRACE is an offline, Linux-compatible (and macOS compatible) system for monitoring, analyzing, and scoring Bitcoin transaction traffic. It ingests transaction logs and network metadata, performs cleaning and validation, extracts complex features using a high-performance C++ graph engine, and scores transactions using an ensemble of Machine Learning models to detect anomalous or high-risk activity.

## Features

- **Robust Data Pipeline**: Ingests CSV, JSON, or XML. Validates, normalizes, and splits data.
- **High-Performance C++ Graph Engine**: Fast bidirectional graph traversal, bounded paths, degree statistics, and clustering algorithms built on a custom Compressed Sparse Row (CSR) structure.
- **Machine Learning Ensemble**: Feature engineering combining temporal, network, and graph features, fed into Isolation Forest, Z-Score, IQR, and Random Forest models.
- **Risk Scoring & Explainability**: Intelligent fusion of anomaly scores, graph features, and network indicators to generate priority-ranked alerts with clear, readable explanations.
- **Modern Local Dashboard**: A Vite + React + TypeScript frontend with dark mode, interactive graph exploration using Cytoscape, timeline views, and metric tracking.

## System Requirements
- Python 3.9+
- C++20 compliant compiler (e.g. GCC 10+, Clang 10+, Apple Clang 14+)
- CMake 3.15+
- Node.js 18+ (for frontend)
- Docker & Docker Compose (optional, for containerized running)

## Quick Start (Local Setup)

1. **Install dependencies and build the C++ Engine:**
   ```bash
   make setup
   ```

2. **Generate synthetic data, clean, split, and extract initial features:**
   ```bash
   make ingest
   ```

3. **Train the ML models and generate initial alerts:**
   ```bash
   make train
   ```

4. **Run the application (Backend at :8000, Frontend at :5173):**
   ```bash
   make run
   ```
   Or to run everything from scratch in one go:
   ```bash
   make demo
   ```

## Development & Testing
Run Python and C++ tests:
```bash
make test
```
Run performance benchmarks:
```bash
make benchmark
```
