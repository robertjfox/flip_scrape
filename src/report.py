import html
from datetime import datetime, timezone

from src.config import load_config
from src.db.sqlite import connect, init_db


HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Flip Scrape - Deal Report</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #0b0f0c;
      --fg: #d5f7d5;
      --muted: #7aa37a;
      --accent: #7dff7d;
      --warning: #ffd37d;
    }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--fg);
      font-family: "IBM Plex Mono", "Menlo", "Consolas", "Courier New", monospace;
    }
    .wrap {
      max-width: 1100px;
      margin: 0 auto;
      padding: 28px 24px 64px;
    }
    h1, h2 {
      margin: 0 0 12px;
      font-weight: 600;
      letter-spacing: 0.3px;
    }
    .meta {
      color: var(--muted);
      margin-bottom: 24px;
    }
    .panel {
      border: 1px solid #1f2b1f;
      padding: 16px;
      margin-bottom: 18px;
      background: rgba(255, 255, 255, 0.02);
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }
    th, td {
      text-align: left;
      padding: 8px 6px;
      border-bottom: 1px solid #1f2b1f;
      vertical-align: top;
    }
    th {
      color: var(--accent);
      font-weight: 600;
    }
    .pill {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 999px;
      border: 1px solid #274327;
      color: var(--accent);
      font-size: 12px;
    }
    .muted { color: var(--muted); }
    a { color: var(--warning); }
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Flip Scrape</h1>
    <div class="meta">Generated: {{generated_at}}</div>

    <div class="panel">
      <h2>Pipeline Summary</h2>
      <table>
        <tr><th>Listings</th><td>{{listing_count}}</td><th>Underwrites</th><td>{{underwrite_count}}</td></tr>
        <tr><th>Alerts Sent</th><td>{{alert_count}}</td><th>Last Ingest</th><td>{{last_ingest}}</td></tr>
      </table>
    </div>

    <div class="panel">
      <h2>Top Deals</h2>
      <table>
        <thead>
          <tr>
            <th>Discount</th>
            <th>List Price</th>
            <th>ARV</th>
            <th>Address</th>
            <th>City</th>
            <th>PSF</th>
            <th>Link</th>
          </tr>
        </thead>
        <tbody>
          {{deal_rows}}
        </tbody>
      </table>
    </div>
  </div>
</body>
</html>
"""


def _fmt_money(value):
    if value is None:
        return "-"
    return f"${value:,.0f}"


def _fmt_pct(value):
    if value is None:
        return "-"
    return f"{value * 100:.1f}%"


def _fmt_number(value):
    if value is None:
        return "-"
    return f"{value:,.0f}"


def _html_escape(value):
    if value is None:
        return "-"
    return html.escape(str(value))


def render_report(conn, output_path: str, limit: int = 25) -> str:
    listing_count = conn.execute("SELECT COUNT(*) AS c FROM listings").fetchone()["c"]
    underwrite_count = conn.execute("SELECT COUNT(*) AS c FROM underwrites").fetchone()["c"]
    alert_count = conn.execute("SELECT COUNT(*) AS c FROM alerts").fetchone()["c"]

    last_ingest_row = conn.execute(
        "SELECT ended_at FROM ingest_runs ORDER BY ended_at DESC LIMIT 1"
    ).fetchone()
    last_ingest = last_ingest_row["ended_at"] if last_ingest_row else "-"

    deals = conn.execute(
        """
        SELECT u.discount_pct, u.arv, l.list_price, l.psf, l.url,
               p.address, p.city
        FROM underwrites u
        JOIN listings l ON l.id = u.listing_id
        JOIN properties p ON p.id = l.property_id
        ORDER BY u.discount_pct DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()

    rows = []
    for row in deals:
        rows.append(
            "<tr>"
            f"<td><span class=\"pill\">{_fmt_pct(row['discount_pct'])}</span></td>"
            f"<td>{_fmt_money(row['list_price'])}</td>"
            f"<td>{_fmt_money(row['arv'])}</td>"
            f"<td>{_html_escape(row['address'])}</td>"
            f"<td>{_html_escape(row['city'])}</td>"
            f"<td>{_fmt_number(row['psf'])}</td>"
            f"<td>{'<a href="' + html.escape(row['url']) + '">link</a>' if row['url'] else '-'}"
            "</tr>"
        )

    html_doc = HTML_TEMPLATE
    html_doc = html_doc.replace("{{generated_at}}", datetime.now(timezone.utc).isoformat())
    html_doc = html_doc.replace("{{listing_count}}", str(listing_count))
    html_doc = html_doc.replace("{{underwrite_count}}", str(underwrite_count))
    html_doc = html_doc.replace("{{alert_count}}", str(alert_count))
    html_doc = html_doc.replace("{{last_ingest}}", _html_escape(last_ingest))
    html_doc = html_doc.replace("{{deal_rows}}", "\n".join(rows) if rows else "<tr><td colspan=\"7\" class=\"muted\">No deals yet.</td></tr>")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_doc)

    return output_path


def main():
    config = load_config()
    conn = connect(config.db_path)
    init_db(conn)

    output_path = "reports/deals.html"
    render_report(conn, output_path)
    print(f"Report written to {output_path}")


if __name__ == "__main__":
    main()
