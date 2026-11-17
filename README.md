# accounting-management

各席および持ち帰り注文の会計を完了し、注文管理の支払済み更新（I-3）、来客管理の席清掃移行（I-6）、売上管理の売上供給（I-4）を連動させるツールです。  
店長・スタッフ共通ポータル（[ポータル画面イメージ](reference/system-integration/docs/images/portal/01-portal-dashboard.png)）のレジ会計業務を担当します。

## 画面遷移図

縮小画面キャプチャを用いた `accounting-management` の画面遷移図です（draw.io 編集用ソース: [transition.drawio](reference/system-integration/docs/images/accounting_management/transition.drawio)）。

![accounting-management 画面遷移図](reference/system-integration/docs/images/accounting_management/transition.svg)

## 代表機能イメージ

### 1. 会計対象・請求確認 (`GET /ui/accounting/checkout`)
注文管理サービスから連携された未会計・会計済み注文の一覧と未精算総額を確認し、決済対象を選択できます。

![会計対象・請求確認](reference/system-integration/docs/images/accounting_management/01-checkout-bill.png)

### 2. 決済処理・お釣り計算 (`GET /ui/accounting/payment`)
現金（`cash`）・クレジットカード（`card`）・QRコード決済（`qr`）の選択、預り金額入力によるお釣り計算を行い、`POST /payments` で決済および後続サービス連携を確定します。

![決済処理・お釣り計算](reference/system-integration/docs/images/accounting_management/02-payment-method.png)

### 3. 領収書・決済履歴 (`GET /ui/accounting/receipt`)
発行されたレシート番号（`RCP-...`）・預り金額・お釣りの領収書プレビューおよび完了済み決済履歴を確認できます。

![領収書・決済履歴](reference/system-integration/docs/images/accounting_management/03-payment-receipt.png)

## 提供 API・UI エンドポイント

| 種別 | メソッド & パス | 機能概要 |
|---|---|---|
| API | `GET /health` | ヘルスチェック |
| API | `POST /payments` | 決済実行・注文支払済化・席清掃要求・売上連携 |
| API | `GET /payments/{payment_id}` | 決済・領収書詳細取得 |
| UI | `GET /ui/accounting/checkout` | 会計対象・請求確認画面 |
| UI | `GET /ui/accounting/payment` | 決済処理・お釣り計算画面 |
| UI | `GET /ui/accounting/receipt` | 領収書・決済履歴画面 |

## テスト・静的解析の実行

```bash
../.venv/bin/python3 -m pytest -v
../.venv/bin/ruff check .
```
