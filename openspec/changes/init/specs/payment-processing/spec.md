# payment-processing Specification

## Purpose

会計管理サービスにおける注文決済、金額検証、お釣り計算、レシート発行、および外部サービス（注文・顧客・売上管理）への状態連携仕様を定義する。

## ADDED Requirements

### Requirement: 決済実行と状態連携 (AccountingManagement_R01.DM01-01, DM01-02)

システムは `POST /payments` により注文決済を完了し、関連システムへ状態を連携しなければならない (SHALL)。

#### Scenario: 正常な現金決済と連携
- **WHEN** 未払いの店内注文に対して合計金額以上の現金で `POST /payments` を実行する
- **THEN** お釣りを計算して HTTP 201 で `Payment` を返し、注文支払済み更新・席清掃要求・売上計上を実行する

#### Scenario: 二重決済および金額不足の拒否
- **WHEN** 支払済み注文への決済、または請求額未満の金額で `POST /payments` を実行する
- **THEN** 支払済み注文には HTTP 409、金額不足には HTTP 422 を返す

### Requirement: 会計履歴取得 (AccountingManagement_R01.DM01-03)

システムは `GET /payments/{payment_id}` により会計履歴および帳票データを返却しなければならない (MUST)。

#### Scenario: 存在する決済IDの取得
- **WHEN** 登録済みの `payment_id` で `GET /payments/{payment_id}` を実行する
- **THEN** HTTP 200 で該当の `Payment` を返す（存在しない場合は HTTP 404）
