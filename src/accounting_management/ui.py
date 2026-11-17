"""HTML UI router for accounting-management."""

from html import escape
from typing import Any

import httpx
from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse

from accounting_management.clients import OrderClient
from accounting_management.store import PaymentStore

PORTAL_LINKS = [
    ("portal", "ポータル", "/ui/portal"),
    ("product", "商品管理", "/ui/products"),
    ("menu", "メニュー", "/ui/menus"),
    ("guest", "座席・顧客", "/ui/tables"),
    ("order", "注文かんばん", "/ui/orders/kanban"),
    ("accounting", "会計", "/ui/accounting/checkout"),
    ("sales", "売上", "/ui/sales/daily"),
    ("dine_in", "店内QR", "/ui/dine-in/session"),
    ("takeout", "持ち帰り", "/ui/takeout/login"),
]

METHOD_LABELS = {"cash": "現金", "card": "クレジットカード", "qr": "QRコード決済"}


def _safe_orders(order_client: OrderClient) -> list[dict[str, Any]]:
    try:
        res = order_client.list_orders()
        return res if isinstance(res, list) else []
    except (httpx.HTTPError, TypeError, ValueError):
        return []


def _render_shell(*, title: str, subtitle: str, active_subtab: str, body_html: str) -> str:
    nav_html = "".join(
        f'<a class="nav-pill{" active" if key == "accounting" else ""}" href="{href}">'
        f"{escape(label)}</a>"
        for key, label, href in PORTAL_LINKS
    )
    subtabs = [
        ("checkout", "1. 会計対象・請求確認", "/ui/accounting/checkout"),
        ("payment", "2. 決済方法・お釣り計算", "/ui/accounting/payment"),
        ("receipt", "3. 領収書・連携履歴", "/ui/accounting/receipt"),
    ]
    subtab_html = "".join(
        f'<a class="subtab{" active" if key == active_subtab else ""}" href="{href}">'
        f"{escape(label)}</a>"
        for key, label, href in subtabs
    )
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape(title)} | まちなか飲食店サポート</title>
  <style>
    :root {{ --bg:#f8fafc; --surface:#fff; --navy:#0f172a; --slate:#334155;
      --muted:#64748b; --border:#e2e8f0; --accent:#ea580c; --accent-soft:#fff7ed; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--bg); color:var(--navy); line-height:1.5;
      font-family:"Noto Sans CJK JP","Hiragino Kaku Gothic ProN","Yu Gothic",sans-serif; }}
    .topbar {{ background:var(--navy); color:#fff; padding:0 24px; height:54px;
      display:flex; align-items:center; justify-content:space-between; gap:16px; }}
    .brand {{ display:flex; align-items:center; gap:10px; font-weight:700;
      font-size:15px; white-space:nowrap; }}
    .brand-badge {{ background:var(--accent); color:#fff; padding:2px 8px;
      border-radius:6px; font-size:11px; }}
    .nav-links {{ display:flex; gap:4px; overflow-x:auto; }}
    .nav-pill {{ color:#cbd5e1; text-decoration:none; font-size:12px; font-weight:600;
      padding:6px 10px; border-radius:6px; white-space:nowrap; }}
    .nav-pill.active {{ background:var(--accent); color:#fff; }}
    .subbar {{ background:var(--surface); border-bottom:1px solid var(--border);
      padding:12px 24px; display:flex; align-items:center; justify-content:space-between;
      gap:16px; }}
    .subbar h1 {{ margin:0; font-size:18px; }}
    .subbar .subtitle {{ margin:2px 0 0; font-size:12px; color:var(--muted); }}
    .subtabs {{ display:flex; gap:8px; }}
    .subtab {{ text-decoration:none; color:var(--slate); font-size:13px; font-weight:600;
      padding:7px 14px; border-radius:8px; border:1px solid var(--border); background:#fff; }}
    .subtab.active {{ background:var(--accent-soft); color:var(--accent);
      border-color:#fdba74; }}
    .container {{ max-width:1220px; margin:0 auto; padding:20px 24px 28px; }}
    .kpi-grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-bottom:18px; }}
    .grid-2 {{ display:grid; grid-template-columns:1.1fr 1fr; gap:18px; }}
    .card {{ background:var(--surface); border:1px solid var(--border); border-radius:12px;
      padding:16px 18px; box-shadow:0 1px 2px rgba(15,23,42,.04); }}
    .kpi-label {{ font-size:12px; color:var(--muted); font-weight:600; }}
    .kpi-value {{ font-size:24px; font-weight:800; margin-top:4px; }}
    .badge {{ display:inline-block; padding:2px 9px; border-radius:999px;
      font-size:11px; font-weight:700; }}
    .btn {{ display:inline-block; text-decoration:none; font-size:13px; font-weight:700;
      padding:8px 14px; border-radius:8px; border:none; cursor:pointer; }}
    .btn-primary {{ background:var(--accent); color:#fff; }}
    .btn-secondary {{ background:#f1f5f9; color:var(--slate); border:1px solid var(--border); }}
    table {{ width:100%; border-collapse:collapse; font-size:13px; }}
    th {{ text-align:left; padding:10px 12px; background:#f8fafc; color:var(--muted);
      font-size:12px; border-bottom:1px solid var(--border); }}
    td {{ padding:10px 12px; border-bottom:1px solid var(--border); }}
    .receipt-box {{ border:2px dashed #94a3b8; border-radius:12px; padding:18px;
      background:#fff; max-width:440px; margin:0 auto; }}
    label {{ font-size:12px; font-weight:700; color:var(--slate); display:block;
      margin-bottom:4px; }}
    input, select {{ width:100%; padding:8px 10px; border:1px solid #cbd5e1;
      border-radius:8px; font-size:13px; font-family:inherit; }}
  </style>
</head>
<body>
  <header class="topbar">
    <div class="brand">
      <span>🍽️ まちなか飲食店サポート</span>
      <span class="brand-badge">店長・スタッフ共通ポータル</span>
    </div>
    <nav class="nav-links">{nav_html}</nav>
  </header>
  <section class="subbar">
    <div>
      <h1>{escape(title)}</h1>
      <p class="subtitle">{escape(subtitle)}</p>
    </div>
    <div class="subtabs">{subtab_html}</div>
  </section>
  <main class="container">{body_html}</main>
</body>
</html>
"""


def create_ui_router(store: PaymentStore, order_client: OrderClient) -> APIRouter:
    """Create FastAPI router providing HTML UI screens for accounting-management."""
    router = APIRouter(tags=["ui"])

    @router.get("/ui/accounting/checkout", response_class=HTMLResponse)
    def checkout_page() -> str:
        orders = _safe_orders(order_client)
        payments = store.list_all()
        unpaid = [o for o in orders if not o.get("paid")]
        unpaid_total = sum(int(o.get("total_amount", 0)) for o in unpaid)
        paid_total = sum(p.amount for p in payments)

        rows = []
        for o in orders:
            oid = str(o.get("order_id", "-"))
            paid = bool(o.get("paid"))
            status_badge = (
                '<span class="badge" style="background:#dcfce7;color:#166534">会計完了</span>'
                if paid
                else '<span class="badge" style="background:#fef3c7;color:#92400e">未会計</span>'
            )
            action = (
                '<a class="btn btn-secondary" style="padding:4px 10px;font-size:12px" '
                'href="/ui/accounting/receipt">領収書</a>'
                if paid
                else f'<a class="btn btn-primary" style="padding:4px 10px;font-size:12px" '
                f'href="/ui/accounting/payment?order_id={escape(oid)}">レジ決済へ</a>'
            )
            rows.append(
                f"<tr><td><code>{escape(oid)}</code></td>"
                f"<td>{escape(str(o.get('source', '-')))}</td>"
                f"<td>{escape(str(o.get('table_id') or o.get('customer_id') or '-'))}</td>"
                f"<td><strong>¥{int(o.get('total_amount', 0)):,}</strong></td>"
                f"<td>{status_badge}</td>"
                f"<td>{action}</td></tr>"
            )
        rows_html = "".join(rows) or (
            '<tr><td colspan="6" style="text-align:center;color:#64748b">'
            "連携された注文データはありません。</td></tr>"
        )
        body = f"""
        <div class="kpi-grid">
          <div class="card"><div class="kpi-label">未会計注文数</div>
            <div class="kpi-value">{len(unpaid)} 件</div></div>
          <div class="card"><div class="kpi-label">未精算金額合計</div>
            <div class="kpi-value" style="color:#ea580c">¥{unpaid_total:,}</div></div>
          <div class="card"><div class="kpi-label">本日決済完了件数</div>
            <div class="kpi-value">{len(payments)} 件</div></div>
          <div class="card"><div class="kpi-label">決済済み総額</div>
            <div class="kpi-value" style="color:#166534">¥{paid_total:,}</div></div>
        </div>
        <div class="card">
          <div style="display:flex;justify-content:space-between;align-items:center;
            margin-bottom:14px">
            <h2 style="margin:0;font-size:16px">注文別 会計対象一覧（I-3 注文管理連携）</h2>
            <a class="btn btn-primary" href="/ui/accounting/payment">レジ決済画面へ</a>
          </div>
          <table>
            <thead><tr><th>注文ID</th><th>チャネル</th><th>席 / 顧客</th>
              <th>請求金額</th><th>状態</th><th>操作</th></tr></thead>
            <tbody>{rows_html}</tbody>
          </table>
        </div>
        """
        return _render_shell(
            title="会計管理 › 会計対象・請求確認",
            subtitle="注文管理サービスから未会計・精算済み注文を取得し、レジ決済へ誘導します",
            active_subtab="checkout",
            body_html=body,
        )

    @router.get("/ui/accounting/payment", response_class=HTMLResponse)
    def payment_page(order_id: str | None = Query(default=None)) -> str:
        orders = _safe_orders(order_client)
        unpaid = [o for o in orders if not o.get("paid")]
        selected = next((o for o in orders if o.get("order_id") == order_id), None)
        if selected is None:
            selected = unpaid[0] if unpaid else (orders[0] if orders else None)
        sel_oid = str(selected.get("order_id", "ord-sample")) if selected else "ord-sample"
        sel_amt = int(selected.get("total_amount", 1200)) if selected else 1200

        body = f"""
        <div class="grid-2">
          <div class="card">
            <h2 style="margin:0 0 12px;font-size:16px">POS レジ決済・預り金計算</h2>
            <div style="margin-bottom:12px">
              <label>対象注文ID</label>
              <input type="text" id="pay-oid" value="{escape(sel_oid)}">
            </div>
            <div style="margin-bottom:12px">
              <label>支払方法（cash / card / qr）</label>
              <select id="pay-method">
                <option value="cash">現金 (cash)</option>
                <option value="card">クレジットカード (card)</option>
                <option value="qr">QRコード決済 (qr)</option>
              </select>
            </div>
            <div style="margin-bottom:12px">
              <label>預り金額（円）</label>
              <input type="number" id="pay-recv" value="{max(sel_amt, 2000)}" min="0">
            </div>
            <div style="display:flex;justify-content:flex-end;gap:10px;margin-top:16px">
              <a class="btn btn-secondary" href="/ui/accounting/checkout">一覧へ戻る</a>
              <button class="btn btn-primary" onclick="submitPayment()">会計を確定する</button>
            </div>
          </div>
          <div class="card">
            <h2 style="margin:0 0 12px;font-size:16px">請求・連動アクション確認</h2>
            <div style="background:#f8fafc;border-radius:10px;padding:14px;margin-bottom:14px">
              <div style="font-size:12px;color:#64748b">ご請求金額</div>
              <div style="font-size:28px;font-weight:800;color:#ea580c">¥{sel_amt:,}</div>
              <div style="font-size:12px;color:#475569;margin-top:4px">
                お釣り目安: ¥{max(max(sel_amt, 2000) - sel_amt, 0):,}
              </div>
            </div>
            <ul style="font-size:12px;color:#475569;padding-left:18px;margin:0">
              <li>I-3: 注文管理へ支払済み通知（mark-paid）を送信</li>
              <li>I-6: 店内注文完了時は顧客管理へ席清掃（request-cleaning）を要求</li>
              <li>I-4: 売上管理へ売上実績（POST /sales/records）を即時供給</li>
            </ul>
          </div>
        </div>
        <script>
          async function submitPayment() {{
            const res = await fetch('/payments', {{
              method: 'POST', headers: {{'Content-Type': 'application/json'}},
              body: JSON.stringify({{
                order_id: document.getElementById('pay-oid').value,
                method: document.getElementById('pay-method').value,
                received_amount: Number(document.getElementById('pay-recv').value)
              }})
            }});
            if (res.ok) window.location.href = '/ui/accounting/receipt';
          }}
        </script>
        """
        return _render_shell(
            title="会計管理 › 決済処理・お釣り計算",
            subtitle="現金・カード・QRの決済を受け付け、お釣り計算と関連サービス通知を実行します",
            active_subtab="payment",
            body_html=body,
        )

    @router.get("/ui/accounting/receipt", response_class=HTMLResponse)
    def receipt_page() -> str:
        payments = store.list_all()
        latest = payments[-1] if payments else None
        if latest is not None:
            receipt_html = (
                f'<div class="receipt-box">'
                f'<div style="text-align:center;border-bottom:1px dashed #cbd5e1;'
                f'padding-bottom:10px;margin-bottom:10px">'
                f'<div style="font-weight:800;font-size:16px">領収書 / RECEIPT</div>'
                f'<div style="font-size:12px;color:#64748b">まちなか飲食店サポート本店</div>'
                f'<div style="font-size:11px;color:#64748b">{escape(latest.receipt_number)}</div>'
                f"</div>"
                f'<div style="font-size:13px">'
                f'<div style="display:flex;justify-content:space-between;margin-bottom:4px">'
                f"<span>注文ID</span><code>{escape(latest.order_id)}</code></div>"
                f'<div style="display:flex;justify-content:space-between;margin-bottom:4px">'
                f"<span>支払方法</span>"
                f"<span>{escape(METHOD_LABELS.get(latest.method, latest.method))}</span></div>"
                f'<div style="display:flex;justify-content:space-between;margin-bottom:4px">'
                f"<span>お買上金額</span><strong>¥{latest.amount:,}</strong></div>"
                f'<div style="display:flex;justify-content:space-between;margin-bottom:4px">'
                f"<span>お預り</span><span>¥{latest.received_amount:,}</span></div>"
                f'<div style="display:flex;justify-content:space-between;font-weight:700;'
                f'color:#ea580c;border-top:1px dashed #cbd5e1;padding-top:8px;margin-top:8px">'
                f"<span>お釣り</span><span>¥{latest.change_amount:,}</span></div>"
                f"</div></div>"
            )
        else:
            receipt_html = '<p style="color:#64748b">決済完了レシートはまだありません。</p>'

        history_rows = "".join(
            f"<tr><td><code>{escape(p.receipt_number)}</code></td>"
            f"<td><code>{escape(p.order_id)}</code></td>"
            f"<td>{escape(METHOD_LABELS.get(p.method, p.method))}</td>"
            f"<td><strong>¥{p.amount:,}</strong></td>"
            f"<td>¥{p.change_amount:,}</td></tr>"
            for p in payments
        ) or '<tr><td colspan="5" style="text-align:center;color:#64748b">決済履歴なし</td></tr>'

        body = f"""
        <div class="grid-2">
          <div class="card">
            <h2 style="margin:0 0 12px;font-size:16px">最新発行レシートプレビュー</h2>
            {receipt_html}
          </div>
          <div class="card">
            <h2 style="margin:0 0 12px;font-size:16px">決済・連携完了履歴</h2>
            <table>
              <thead><tr><th>レシート番号</th><th>注文ID</th><th>方法</th>
                <th>金額</th><th>お釣り</th></tr></thead>
              <tbody>{history_rows}</tbody>
            </table>
          </div>
        </div>
        """
        return _render_shell(
            title="会計管理 › 領収書・決済履歴",
            subtitle="発行された領収書プレビューと過去の会計処理履歴を確認します",
            active_subtab="receipt",
            body_html=body,
        )

    return router
