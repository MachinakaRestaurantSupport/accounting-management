# Tasks: accounting-management 初期MVP実装

## 1. 基盤・アプリケーション実装

- [x] 1.1 Python プロジェクト基盤 (`pyproject.toml`) を作成し、pytest / ruff 設定を定義する
- [ ] 1.2 データモデル・インメモリストア・外部クライアント (`models.py`, `store.py`, `clients.py`) を実装する [AccountingManagement_R01.DM01-01, DM01-02, DM01-03]
- [ ] 1.3 FastAPI アプリケーションと決済・ヘルスチェック API (`main.py`) を実装する [AccountingManagement_R01.DM01-01, DM01-02, DM01-03]

## 2. 単体試験・品質検証

- [ ] 2.1 `httpx.MockTransport` を用いた決済・連携・異常系単体試験 (`tests/test_payments.py`) を実装し、全テストパスを確認する [AccountingManagement_R01.DM01-01, DM01-02, DM01-03]
