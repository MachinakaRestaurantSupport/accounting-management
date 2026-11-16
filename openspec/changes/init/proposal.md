# Proposal: 会計管理サービス初期MVP実装

## 背景と目的

`accounting-management` は MachinakaRestaurantSupportTools における会計・決済・連携管理を担うマイクロサービスである。注文管理（I-3）、顧客管理（I-6）、売上管理（I-4）と連携し、注文に対する決済処理、レシート情報生成、二重決済・金額不足の検証、および後続システムへの状態連携を実現する初期MVPを構築する。

## スコープ

- `GET /health`: サービスヘルスチェック
- `POST /payments`: 注文取得・金額検証・お釣り計算・支払済み通知・席清掃連携・売上計上・決済履歴保存
- `GET /payments/{payment_id}`: 会計履歴・レシート情報取得
- 外部連携クライアント（`OrderClient`, `GuestClient`, `SalesClient`）の依存性注入対応と単体試験
