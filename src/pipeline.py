from src.config import load_config, ensure_data_dirs
from src.db.sqlite import connect, init_db
from src.ingest.runner import run_ingest
from src.underwrite.scoring import score_listing
from src.alerts.runner import run_alerts


def run_underwriting(conn, criteria):
    rows = conn.execute(
        """
        SELECT l.id
        FROM listings l
        WHERE l.id NOT IN (SELECT listing_id FROM underwrites)
        """
    ).fetchall()

    results = []
    for row in rows:
        payload = score_listing(conn, row["id"], criteria)
        if payload:
            results.append(payload)
    return results


def main():
    config = load_config()
    ensure_data_dirs(config)

    conn = connect(config.db_path)
    init_db(conn)

    ingest_result = run_ingest(config, conn)
    underwrite_results = run_underwriting(conn, config.criteria)
    alert_results = run_alerts(config, conn)

    print("Ingest:", ingest_result)
    print("Underwrite:", len(underwrite_results))
    print("Alerts:", len(alert_results))


if __name__ == "__main__":
    main()
