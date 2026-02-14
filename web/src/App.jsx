import { useMemo, useState } from "react";
import data from "./data/sample.json";
import "./App.css";

const formatMoney = (value) =>
  value === null || value === undefined
    ? "-"
    : value.toLocaleString("en-US", {
        style: "currency",
        currency: "USD",
        maximumFractionDigits: 0,
      });

const formatPct = (value) =>
  value === null || value === undefined ? "-" : `${(value * 100).toFixed(1)}%`;

export default function App() {
  const [minDiscount, setMinDiscount] = useState(0.3);
  const [query, setQuery] = useState("");

  const deals = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    return data.deals
      .filter((deal) => deal.discount >= minDiscount)
      .filter((deal) => {
        if (!normalized) return true;
        return (
          deal.address.toLowerCase().includes(normalized) ||
          deal.city.toLowerCase().includes(normalized)
        );
      })
      .sort((a, b) => b.discount - a.discount);
  }, [minDiscount, query]);

  return (
    <div className="app">
      <header className="hero">
        <div>
          <p className="eyebrow">Long Island Deal Ops</p>
          <h1>Flip Scrape Dashboard</h1>
          <p className="sub">Live-style view of SFR deals for Nassau + Suffolk.</p>
        </div>
        <div className="timestamp">
          <span className="label">Last ingest</span>
          <span>{data.summary.lastIngest}</span>
        </div>
      </header>

      <section className="summary">
        <div className="card">
          <p className="label">Listings</p>
          <h2>{data.summary.listings}</h2>
        </div>
        <div className="card">
          <p className="label">Underwrites</p>
          <h2>{data.summary.underwrites}</h2>
        </div>
        <div className="card">
          <p className="label">Alerts sent</p>
          <h2>{data.summary.alerts}</h2>
        </div>
      </section>

      <section className="controls">
        <div className="control">
          <label htmlFor="minDiscount">Min discount</label>
          <input
            id="minDiscount"
            type="range"
            min="0"
            max="0.6"
            step="0.01"
            value={minDiscount}
            onChange={(event) => setMinDiscount(Number(event.target.value))}
          />
          <span className="value">{formatPct(minDiscount)}</span>
        </div>
        <div className="control">
          <label htmlFor="search">Search</label>
          <input
            id="search"
            type="text"
            placeholder="Address or city"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </div>
      </section>

      <section className="deals">
        <div className="table-header">
          <h3>Top deals</h3>
          <span className="muted">Showing {deals.length} results</span>
        </div>
        <div className="table">
          <div className="row head">
            <span>Discount</span>
            <span>List price</span>
            <span>ARV</span>
            <span>Address</span>
            <span>City</span>
            <span>PSF</span>
            <span>Link</span>
          </div>
          {deals.length === 0 ? (
            <div className="row empty">No deals match the filters.</div>
          ) : (
            deals.map((deal) => (
              <div className="row" key={deal.id}>
                <span className="pill">{formatPct(deal.discount)}</span>
                <span>{formatMoney(deal.listPrice)}</span>
                <span>{formatMoney(deal.arv)}</span>
                <span>{deal.address}</span>
                <span>{deal.city}</span>
                <span>{deal.psf}</span>
                <a href={deal.url} target="_blank" rel="noreferrer">
                  View
                </a>
              </div>
            ))
          )}
        </div>
      </section>
    </div>
  );
}
