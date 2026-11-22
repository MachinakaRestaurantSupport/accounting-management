# Design: accounting-management 初期MVP

## 1. アーキテクチャ概要

FastAPI を用いた軽量 REST API サービスとして実装する。データ永続化は MVP としてインメモリストア（`PaymentStore`）を採用し、外部マイクロサービス（注文管理・顧客管理・売上管理）との HTTP 通信は `httpx.Client` をラップしたクライアントクラス群（`OrderClient`, `GuestClient`, `SalesClient`）に分離して `create_app()` から依存性注入可能とする。

## 2. USDM 要求トレーサビリティ

| USDM 要求ID | 要求概要 | 実装モジュール / エンドポイント |
| --- | --- | --- |
| `AccountingManagement_R01.DM01-01` | `POST /payments` による決済完了・お釣り計算・レシート情報返却（I-3） | `main.py` (`POST /payments`), `models.py` (`PaymentCreate`, `Payment`), `clients.py` (`OrderClient`) |
| `AccountingManagement_R01.DM01-02` | 会計完了時の注文支払済み更新（I-3）・席清掃要求（I-6）・売上計上（I-4） | `main.py` (`POST /payments`), `clients.py` (`OrderClient`, `GuestClient`, `SalesClient`) |
| `AccountingManagement_R01.DM01-03` | `GET /payments/{payment_id}` による会計履歴・帳票データ取得 | `main.py` (`GET /payments/{payment_id}`), `store.py` (`PaymentStore`) |

## 3. モジュール構成

- `src/accounting_management/models.py`: Pydantic スキーマ（`PaymentMethod`, `PaymentCreate`, `Payment`, `HealthResponse`）
- `src/accounting_management/store.py`: スレッドセーフ/シンプルなインメモリ決済ストア（`PaymentStore`）
- `src/accounting_management/clients.py`: `httpx.Client` ベースの外部連携クライアント（`OrderClient`, `GuestClient`, `SalesClient`）。`base_url` と `transport` の注入に対応
- `src/accounting_management/main.py`: `create_app(order_client=None, guest_client=None, sales_client=None)` ファクトリおよび `app` インスタンス
- `tests/test_payments.py`: `httpx.MockTransport` を用いた単体試験

## 4. API 仕様と処理フロー

1. `GET /health`: `{"status": "ok", "service": "accounting-management"}` を返却。
2. `POST /payments`:
   - `OrderClient.get_order(order_id)` で注文取得（存在しない場合は 404）。
   - `order["paid"] == True` の場合は HTTP 409 Conflict を返却。
   - `received_amount < order["total_amount"]` の場合は HTTP 422 Unprocessable Entity を返却。
   - `OrderClient.mark_paid(order_id)` を呼び出し。
   - `order.get("source") == "dine_in"` かつ `order.get("table_id")` がある場合は `GuestClient.request_cleaning(table_id)` を呼び出し。
   - `SalesClient.record_sale(...)` を呼び出し、`order_id`, `payment_id`, `channel=order["source"]`, `amount=total_amount`, `recorded_at=paid_at` を送信。
   - `Payment` をストアに保存し HTTP 201 で返却。
3. `GET /payments/{payment_id}`: ストアから取得し返却（未登録は 404）。
