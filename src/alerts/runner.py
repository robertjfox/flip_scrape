import json
from datetime import datetime, timezone

from src.alerts.emailer import send_email


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_alerts(config, conn):
    min_discount = float(config.criteria.get("min_discount_pct", 0.30))

    rows = conn.execute(
        """
        SELECT u.listing_id, u.discount_pct, u.arv, l.list_price, l.url
        FROM underwrites u
        JOIN listings l ON l.id = u.listing_id
        WHERE u.discount_pct >= ?
          AND u.listing_id NOT IN (SELECT listing_id FROM alerts)
        """,
        (min_discount,),
    ).fetchall()

    results = []
    for row in rows:
        subject = f"Deal Alert: {row['discount_pct'] * 100:.1f}% below comps"
        body = (
            f"Listing ID: {row['listing_id']}\n"
            f"Discount: {row['discount_pct'] * 100:.1f}%\n"
            f"List Price: {row['list_price']}\n"
            f"ARV (est): {row['arv']}\n"
            f"URL: {row['url']}\n"
        )

        send_result = send_email(config.email, subject, body)
        if send_result.get("status") == "sent":
            conn.execute(
                """
                INSERT INTO alerts (listing_id, channel, to_address, sent_at, payload_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    row["listing_id"],
                    "email",
                    config.email.recipient,
                    _utc_now(),
                    json.dumps({
                        "subject": subject,
                        "body": body,
                    }),
                ),
            )
            conn.commit()
        results.append({"listing_id": row["listing_id"], **send_result})

    return results
