# BTC-TRACE Architecture

The BTC-TRACE system is composed of several interdependent layers designed to ingest, process, score, and visualize Bitcoin transaction data.

## 1. Data Pipeline (`ml/pipeline/`)
The ingestion pipeline handles raw data loading (CSV, JSON, XML), schema detection, field validation, normalization, and partitioning.
- **`ingest.py`**: Auto-detects formats and normalizes into a common DataFrame structure.
- **`validate.py`**: Enforces strict format and logic rules (e.g., valid IP format, non-negative amounts, 64-hex char TXIDs). Invalid data is quarantined.
- **`normalize.py`**: Standardizes timestamps (UTC), IPs, and string formatting.
- **`id_mapping.py`**: Ensures consistent, deterministic ID generation for entities across the dataset.
- **`split.py`**: Performs temporal splitting (Train/Validation/Test) to prevent data leakage in time-series forecasting.

## 2. Feature Engineering & Graph Engine (`ml/features/` & `cpp/`)
BTC-TRACE combines traditional statistical features with deep graph analytics.
- **C++ CSR Graph (`cpp/`)**: A highly optimized Compressed Sparse Row (CSR) graph engine built in C++ to handle massive transaction volumes. It efficiently computes degree statistics, shortest bounded paths, connected components, and clustering coefficients.
- **Python Feature Extractors**: Extracts temporal features (e.g., burst detection, time-of-day), network features (ASN risk, standard ports), and combines them with transaction and wallet-level statistics.

## 3. Machine Learning (`ml/models/`)
The ML layer detects anomalies and trains on labeled instances.
- **Phase 1: Unsupervised Anomaly Detection**: Uses Isolation Forest, Z-Score, and IQR methods to establish baselines of "normal" behavior.
- **Phase 2: Supervised Learning**: Uses Random Forest and XGBoost (if labels are present) to classify known malicious or high-risk transaction patterns.

## 4. Risk Scoring & Alerts (`ml/scoring/`)
Scores from various models are fused into an actionable risk metric.
- **`risk_scorer.py`**: Fuses anomaly scores, graph risk, temporal risk, and network risk using a configurable weighted formula. Evaluates data completeness to calculate a confidence score.
- **`alert_generator.py`**: Generates structured, prioritized alerts containing human-readable explanations of *why* an entity was flagged (using Shapley value proxies from Isolation Forest feature importances).

## 5. API Backend (`backend/`)
A FastAPI application that serves data to the frontend.
- Reads processed Parquet datasets and alert JSONs directly from disk.
- Provides endpoints for global metrics, alert listing, entity search, and detailed graph/transaction lookups.

## 6. Frontend Dashboard (`frontend/`)
A modern Vite + React + TypeScript + TailwindCSS SPA.
- Implements comprehensive views: Overview Dashboard, Alert Triage, Network Graph Explorer (Cytoscape), and Data Quality reports.
- Employs a dark-mode, high-contrast UI suitable for prolonged analytical investigation.

## Limitations & Future Work
- Due to the unavailability of the original dataset specified in the SIH problem statement, the pipeline currently runs on a synthetically generated dataset that mirrors the required schema.
- The C++ graph engine is currently accessed via command-line tools/files. Creating Python bindings (e.g., via `pybind11`) would reduce IO overhead.
- True real-time streaming (e.g. Kafka integration) would be necessary for production deployment instead of batch Parquet processing.
