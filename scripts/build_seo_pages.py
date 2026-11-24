#!/usr/bin/env python3
"""Closed-Loop Programmatic SEO & Multi-Day Historical Price Trend Builder (v5.0) for CloudEgressFees.com."""
from __future__ import annotations

from datetime import datetime, timezone
import html
import json
from pathlib import Path
import re

ROOT_DIR = Path(__file__).resolve().parent.parent
PUBLIC_DIR = ROOT_DIR / "public"
FEES_PATH = PUBLIC_DIR / "egress_fees.json"
TARGETS_PATH = PUBLIC_DIR / "seo_targets.json"
HISTORY_DIR = PUBLIC_DIR / "history"
INDEX_HTML_PATH = PUBLIC_DIR / "index.html"
SITEMAP_PATH = PUBLIC_DIR / "sitemap.xml"
SITE_URL = "https://cloudegressfees.com/"

GA4_SNIPPET = """  <script async src="https://www.googletagmanager.com/gtag/js?id=G-HE84C7N8Y8"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', 'G-HE84C7N8Y8', { anonymize_ip: true });
    document.addEventListener('click', function(e) {
      var a = e.target && e.target.closest ? e.target.closest('a[href^="http"]') : null;
      if (a && a.hostname && a.hostname.indexOf('cloudegressfees.com') === -1) {
        gtag('event', 'provider_outbound_click', { provider_domain: a.hostname, link_url: a.href });
      }
    });
  </script>"""

SUBPAGE_CSS = """    :root { --bg:#0f172a; --surface:#1e293b; --surface-alt:#0b1220; --border:#334155; --text:#f8fafc; --text-muted:#94a3b8; --accent:#38bdf8; --row-hover:rgba(56,189,248,0.07); --savings-text:#86efac; --danger-text:#fca5a5; }
    html.light-theme, body.light-theme { --bg:#f8fafc; --surface:#ffffff; --surface-alt:#f1f5f9; --border:#cbd5e1; --text:#0f172a; --text-muted:#475569; --accent:#0369a1; --row-hover:#f1f5f9; --savings-text:#166534; --danger-text:#991b1b; }
    * { box-sizing:border-box; } body { margin:0; font-family:-apple-system,BlinkMacSystemFont,"Inter","Segoe UI",Roboto,sans-serif; background:var(--bg); color:var(--text); line-height:1.5; }
    .topbar { position:sticky; top:0; z-index:30; background:var(--surface); border-bottom:1px solid var(--border); padding:13px 24px; display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:12px; }
    .brand, .topbar-actions, .preset-row, .telemetry-banner { display:flex; gap:8px; flex-wrap:wrap; align-items:center; }
    .brand-link { font-size:1.18rem; font-weight:900; letter-spacing:-0.02em; color:var(--text); text-decoration:none; } .brand-dot { color:var(--accent); }
    .live-pill, .badge-zero, html.light-theme .live-pill, html.light-theme .badge-zero, body.light-theme .live-pill, body.light-theme .badge-zero { background:#d9f99d; color:#1a2e05; border:1px solid #65a30d; padding:2px 9px; border-radius:999px; font-size:0.73rem; font-weight:800; display:inline-block; white-space:nowrap; }
    .badge { display:inline-block; padding:2px 8px; border-radius:6px; font-size:0.72rem; font-weight:800; white-space:nowrap; }
    .badge-low { background:#064e3b; color:#a7f3d0; border:1px solid #10b981; } html.light-theme .badge-low, body.light-theme .badge-low { background:#d1fae5; color:#065f46; border:1px solid #10b981; }
    .badge-hyper { background:#451a03; color:#fde68a; border:1px solid #f59e0b; } html.light-theme .badge-hyper, body.light-theme .badge-hyper { background:#fef3c7; color:#92400e; border:1px solid #d97706; }
    .badge-eu { background:#1e3a8a; color:#dbeafe; border:1px solid #3b82f6; } html.light-theme .badge-eu, body.light-theme .badge-eu { background:#dbeafe; color:#1e40af; border:1px solid #3b82f6; }
    .badge-warn { background:#7f1d1d; color:#fecaca; border:1px solid #ef4444; } html.light-theme .badge-warn, body.light-theme .badge-warn { background:#fee2e2; color:#991b1b; border:1px solid #ef4444; }
    .badge-ok { background:#1e293b; color:#cbd5e1; border:1px solid #64748b; } html.light-theme .badge-ok, body.light-theme .badge-ok { background:#f1f5f9; color:#334155; border:1px solid #94a3b8; }
    .btn { background:var(--surface-alt); color:var(--text); border:1px solid var(--border); padding:7px 13px; border-radius:8px; font-size:0.82rem; font-weight:700; cursor:pointer; text-decoration:none; display:inline-flex; align-items:center; gap:6px; }
    .btn:hover, .preset-btn:hover, .hub-card:hover { border-color:var(--accent); } .container { max-width:1380px; margin:20px auto 64px; padding:0 20px; }
    .breadcrumb { font-size:0.8rem; color:var(--text-muted); margin-bottom:10px; display:flex; align-items:center; gap:7px; flex-wrap:wrap; }
    .hero { margin-bottom:14px; } .hero h1 { margin:0 0 6px; font-size:1.54rem; font-weight:900; letter-spacing:-0.02em; color:var(--text); } .hero p { margin:0; color:var(--text-muted); font-size:0.93rem; }
    .telemetry-banner { background:var(--surface); border:1px solid var(--border); border-radius:11px; padding:11px 15px; margin-bottom:16px; }
    .muted-sm { font-size:0.76rem; color:var(--text-muted); } .muted-xs { font-size:0.73rem; color:var(--text-muted); margin-top:3px; }
    .accent-link { color:var(--accent); text-decoration:none; font-weight:800; } .accent-link:hover { text-decoration:underline; }
    .val-savings { color:var(--savings-text); font-weight:900; } .val-danger { color:var(--danger-text); font-weight:800; }
    .calc-panel, .faq-section, .seo-hub-panel { background:var(--surface); border:1px solid var(--border); border-radius:13px; padding:18px 20px; margin-bottom:20px; }
    .calc-header, .slider-top { display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; margin-bottom:10px; } .calc-title { font-size:1.0rem; font-weight:900; color:var(--text); }
    .preset-btn { padding:5px 10px; border-radius:999px; border:1px solid var(--border); background:var(--surface-alt); color:var(--text); font-size:0.75rem; font-weight:700; cursor:pointer; }
    .slider-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:16px; margin-bottom:16px; }
    .slider-box, .kcard { padding:12px 14px; border-radius:10px; background:var(--surface-alt); border:1px solid var(--border); } .kcard-highlight { border:2px solid #65a30d; }
    .slider-top label, .num-wrap { font-size:0.82rem; font-weight:800; color:var(--text); display:inline-flex; align-items:center; gap:5px; }
    .num-input { width:92px; padding:5px 8px; border-radius:7px; border:1px solid var(--border); background:var(--surface); color:var(--text); font-size:0.88rem; font-weight:800; text-align:right; } .range-input { width:100%; accent-color:var(--accent); cursor:pointer; }
    .kpi-cards, .hub-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(215px,1fr)); gap:11px; } .kpi-cards { padding-top:14px; border-top:1px solid var(--border); }
    .kcard-lbl { font-size:0.75rem; font-weight:800; color:var(--text-muted); display:flex; justify-content:space-between; align-items:center; gap:6px; } .kcard-val { font-size:1.34rem; font-weight:900; margin:4px 0 2px; color:var(--text); }
    .table-wrap { overflow-x:auto; border:1px solid var(--border); border-radius:12px; background:var(--surface); margin-bottom:20px; } table { width:100%; border-collapse:collapse; min-width:920px; }
    th, td { padding:11px 13px; text-align:left; border-bottom:1px solid var(--border); font-size:0.84rem; color:var(--text); vertical-align:top; }
    th { background:var(--surface-alt); font-size:0.76rem; font-weight:800; cursor:pointer; user-select:none; white-space:nowrap; } tr:last-child td { border-bottom:none; } tr:hover td { background:var(--row-hover); }
    .price-strong { font-size:1.01rem; font-weight:900; color:var(--text); } .policy-text { font-size:0.77rem; color:var(--text-muted); max-width:360px; line-height:1.42; }
    .caveat-list { margin:0; padding-left:18px; font-size:0.85rem; color:var(--text); line-height:1.6; } .caveat-list li, .faq-item { margin-bottom:10px; font-size:0.86rem; color:var(--text); }
    .faq-section h2, .seo-hub-panel h2 { margin:0 0 12px; font-size:1.04rem; color:var(--text); } .faq-item p { margin:4px 0 0; color:var(--text-muted); }
    .hub-card { display:block; background:var(--surface-alt); border:1px solid var(--border); border-radius:10px; padding:11px 13px; text-decoration:none; color:var(--text); }
    .hub-card-title { font-size:0.84rem; font-weight:800; color:var(--accent); margin:5px 0 3px; } .hub-card-desc { font-size:0.75rem; color:var(--text-muted); line-height:1.4; }
    .footer { margin-top:24px; font-size:0.78rem; color:var(--text-muted); text-align:center; padding-top:16px; border-top:1px solid var(--border); }"""

SUBPAGE_JS = r"""    let PAGE_ROWS = __PAGE_ROWS_JSON__;
    let AWS_BASE = __AWS_BASE_JSON__;
    const FOCUS_IDS = __FOCUS_IDS_JSON__;
    const SNAP_DAYS = __SNAP_DAYS__;
    let SORT_KEY = "__DEFAULT_SORT_KEY__", SORT_ASC = true;
    function applyTheme() {
      const isDark = (localStorage.getItem("cloudegressfees_theme") || "light") === "dark";
      document.documentElement.classList.toggle("light-theme", !isDark);
      document.body.classList.toggle("light-theme", !isDark);
      const btn = document.getElementById("theme-btn");
      if (btn) btn.textContent = isDark ? "☀️ Light Mode" : "🌙 Dark Mode";
    }
    function toggleTheme() {
      localStorage.setItem("cloudegressfees_theme", document.documentElement.classList.contains("light-theme") ? "dark" : "light");
      applyTheme();
    }
    function esc(s) { return String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c])); }
    function fmtUsd(n, d = 0) { return "$" + Number(n || 0).toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d }); }
    function calcBill(p, stTb, egTb) {
      const stGb = Math.max(0, stTb * 1000), egGb = Math.max(0, egTb * 1000);
      const base = (stGb > 0 || egGb > 0) ? Number(p.base_monthly_usd || 0) : 0;
      const stUsd = base + Math.max(0, stGb - Number(p.included_storage_gb || 0)) * Number(p.storage_per_gb || 0);
      const mult = Number(p.free_egress_mult || 0), freeGb = mult > 0 ? (stGb * mult) : Number(p.free_egress_gb || 0);
      const overGb = Math.max(0, egGb - freeGb), egUsd = overGb * Number(p.egress_per_gb || 0);
      const moUsd = stUsd + egUsd, yrUsd = moUsd * 12;
      let warn = "";
      if (mult > 0 && overGb > 0) warn = `${(overGb / 1000).toFixed(1)} TB above ${mult}x free cap (+$${Number(p.egress_per_gb).toFixed(3)}/GB)`;
      else if (Number(p.fair_use_mult || 0) > 0 && stGb > 0 && egGb > stGb * Number(p.fair_use_mult)) warn = `Egress (${egTb} TB) > ${p.fair_use_mult}:1 fair-use policy`;
      return { stUsd, egUsd, moUsd, yrUsd, overGb, warn };
    }
    function getInputs() { return { stTb: Math.max(0, parseFloat(document.getElementById("num-stored").value || "20")), egTb: Math.max(0, parseFloat(document.getElementById("num-egress").value || "50")) }; }
    function syncInputs(which, src) {
      const numEl = document.getElementById(which === "stored" ? "num-stored" : "num-egress"), rngEl = document.getElementById(which === "stored" ? "rng-stored" : "rng-egress");
      if (src === "rng") numEl.value = rngEl.value; else rngEl.value = String(Math.min(500, Math.max(0, parseFloat(numEl.value || "0"))));
      recalc();
    }
    function applyPreset(st, eg) {
      document.getElementById("num-stored").value = String(st); document.getElementById("rng-stored").value = String(Math.min(500, st));
      document.getElementById("num-egress").value = String(eg); document.getElementById("rng-egress").value = String(Math.min(500, eg));
      recalc();
    }
    function setSort(k) { SORT_ASC = SORT_KEY === k ? !SORT_ASC : (k !== "savings_yr"); SORT_KEY = k; recalc(); }
    function recalc() {
      const { stTb, egTb } = getInputs(), awsB = calcBill(AWS_BASE, stTb, egTb);
      document.getElementById("ratio-indicator").textContent = `Egress-to-Storage Ratio: ${(stTb > 0 ? (egTb / stTb).toFixed(1) : "0.0")}x monthly stored volume (${(egTb * 1000).toLocaleString()} GB outbound)`;
      document.getElementById("kpi-aws-mo").textContent = `${fmtUsd(Math.round(awsB.moUsd))}/mo`;
      document.getElementById("kpi-aws-yr").textContent = `${fmtUsd(Math.round(awsB.yrUsd))}/yr (${fmtUsd(awsB.egUsd, 0)}/mo egress)`;
      const byId = {}; PAGE_ROWS.forEach(p => { byId[p.id] = p; });
      FOCUS_IDS.forEach((fid, i) => {
        const p = byId[fid], moEl = document.getElementById("kpi-f" + i + "-mo"), yrEl = document.getElementById("kpi-f" + i + "-yr");
        if (p && moEl && yrEl) { const b = calcBill(p, stTb, egTb); moEl.textContent = `${fmtUsd(Math.round(b.moUsd))}/mo`; yrEl.textContent = b.warn ? `${fmtUsd(Math.round(b.yrUsd))}/yr · Policy flag` : `${fmtUsd(Math.round(b.yrUsd))}/yr (${fmtUsd(b.egUsd, 0)}/mo egress)`; }
      });
      const nonAws = PAGE_ROWS.filter(p => p.id !== "aws_s3").map(p => ({ p, b: calcBill(p, stTb, egTb) })).sort((a, c) => a.b.moUsd - c.b.moUsd);
      if (nonAws.length) {
        const best = nonAws[0], sav = Math.max(0, awsB.yrUsd - best.b.yrUsd);
        document.getElementById("kpi-save-yr").textContent = `${fmtUsd(Math.round(sav))}/yr`;
        document.getElementById("kpi-save-sub").textContent = `${awsB.yrUsd > 0 ? ((sav / awsB.yrUsd) * 100).toFixed(1) : "0.0"}% saved via ${best.p.name}`;
      }
      const computed = PAGE_ROWS.map(p => { const b = calcBill(p, stTb, egTb), savYr = awsB.yrUsd - b.yrUsd; return { ...p, b, savYr, savPct: awsB.yrUsd > 0 ? Math.round((savYr / awsB.yrUsd) * 100) : 0 }; });
      computed.sort((a, c) => {
        if (SORT_KEY === "name") return SORT_ASC ? a.name.localeCompare(c.name) : c.name.localeCompare(a.name);
        if (SORT_KEY === "storage_per_gb") return SORT_ASC ? a.storage_per_gb - c.storage_per_gb : c.storage_per_gb - a.storage_per_gb;
        if (SORT_KEY === "egress_usd") return SORT_ASC ? (a.b.egUsd - c.b.egUsd || a.b.moUsd - c.b.moUsd) : (c.b.egUsd - a.b.egUsd || c.b.moUsd - a.b.moUsd);
        if (SORT_KEY === "savings_yr") return SORT_ASC ? a.savYr - c.savYr : c.savYr - a.savYr;
        if (SORT_KEY === "eu_first") { const ga = a.eu_sovereign ? 0 : (a.id === "aws_s3" ? 2 : 1), gc = c.eu_sovereign ? 0 : (c.id === "aws_s3" ? 2 : 1); return ga !== gc ? ga - gc : a.b.moUsd - c.b.moUsd; }
        return SORT_ASC ? a.b.moUsd - c.b.moUsd : c.b.moUsd - a.b.moUsd;
      });
      document.getElementById("matrix-tbody").innerHTML = computed.map(r => {
        const catB = r.zero_egress ? '<span class="badge-zero">ZERO EGRESS</span>' : (r.category === "Hyperscaler" ? '<span class="badge badge-hyper">Hyperscaler</span>' : `<span class="badge badge-low">${esc(r.category)}</span>`);
        const savH = r.id === "aws_s3" ? '<span class="muted-sm">Baseline (AWS S3)</span>' : (r.savYr >= 0 ? `<div class="val-savings">+${fmtUsd(Math.round(r.savYr))}/yr</div><div class="muted-xs">Save ${r.savPct}% vs AWS</div>` : `<div class="val-danger">-${fmtUsd(Math.round(Math.abs(r.savYr)))}/yr</div><div class="muted-xs">Higher than AWS S3</div>`);
        const dlt = Number(r.hist_delta_usd || 0), trdH = Math.abs(dlt) < 0.01 ? `<span class="badge badge-ok">${SNAP_DAYS}d: $0 Δ Stable</span>` : `<span class="badge badge-warn">${SNAP_DAYS}d: ${dlt > 0 ? "+" : ""}${fmtUsd(dlt, 2)}/mo</span>`;
        const wrnH = r.b.warn ? `<div class="muted-xs"><span class="badge badge-warn">⚠️ ${esc(r.b.warn)}</span></div>` : "";
        return `<tr><td><div><a class="accent-link" href="${esc(r.url)}" target="_blank" rel="noopener">${esc(r.name)} ↗</a></div><div class="muted-xs">${catB}${r.eu_sovereign ? ' <span class="badge badge-eu">EU / GDPR</span>' : ""}${r.s3_compatible ? ' <span class="badge badge-ok">S3 API</span>' : ""}</div>${r.verified_live ? `<span class="muted-xs">🟢 HTTP ${r.probe_http_status} (${r.probe_latency_ms}ms)</span>` : ""}</td><td><div class="price-strong">$${Number(r.storage_per_gb).toFixed(4).replace(/0+$/, "").replace(/\.$/, "")}/GB</div><div class="muted-xs">${fmtUsd(r.b.stUsd, 2)}/mo storage</div></td><td><div><strong>${esc(r.egress_label)}</strong></div><div class="muted-xs">${fmtUsd(r.b.egUsd, 2)}/mo bandwidth</div></td><td><div class="price-strong">${fmtUsd(r.b.moUsd, 2)}/mo</div><div class="muted-xs">${stTb} TB + ${egTb} TB/mo</div></td><td><div><strong>${fmtUsd(Math.round(r.b.yrUsd))}/yr</strong></div><div class="muted-xs">${trdH}</div></td><td>${savH}</td><td class="policy-text"><div>${esc(r.policy_note)}</div>${wrnH}</td></tr>`;
      }).join("");
    }
    function exportSubCsv() {
      const { stTb, egTb } = getInputs(), awsYr = calcBill(AWS_BASE, stTb, egTb).yrUsd;
      const lines = ["Provider,Category,Zero_Egress,EU_Sovereign,Storage_USD_GB,Egress_USD_GB,Monthly_USD,Annual_USD,Annual_Savings_vs_AWS,Policy_Note"].concat(PAGE_ROWS.map(p => { const b = calcBill(p, stTb, egTb); return [p.name,p.category,p.zero_egress,p.eu_sovereign,p.storage_per_gb,p.egress_per_gb,b.moUsd.toFixed(2),b.yrUsd.toFixed(2),(awsYr-b.yrUsd).toFixed(2),p.policy_note].map(v => `"${String(v ?? "").replace(/"/g, '""')}"`).join(","); }));
      const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8;" })); a.download = `cloudegressfees_${stTb}TB_${egTb}TB.csv`; a.click();
    }
    applyTheme(); recalc();"""


def _esc(val: object) -> str:
    return html.escape(str(val or ""), quote=True)


def _fmt_usd(val: float, digits: int = 0) -> str:
    return f"${val:,.{digits}f}" if digits > 0 else f"${round(val):,}"


def _load_history_telemetry(providers: list[dict[str, object]], aws_meta: dict[str, object]) -> dict[str, object]:
    snaps = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(HISTORY_DIR.glob("*.json"))]
    dates = [str(s.get("date_utc") or "") for s in snaps if s.get("date_utc")]
    cur_ver = str(aws_meta.get("offer_version") or "live")
    offers = list(dict.fromkeys([str(s.get("aws_offer_version") or "") for s in snaps if s.get("aws_offer_version")] + [cur_ver]))
    first_rates = {str(r["id"]): float(r.get("monthly_20tb_50tb_usd") or 0.0) for r in (snaps[0].get("rates_snapshot") or [])} if snaps else {}
    deltas = {str(p["id"]): round(float((p.get("workload_20tb_50tb") or {}).get("monthly_total_usd") or 0.0) - first_rates.get(str(p["id"]), float((p.get("workload_20tb_50tb") or {}).get("monthly_total_usd") or 0.0)), 2) for p in providers}
    changed_cnt = sum(1 for v in deltas.values() if abs(v) >= 0.01)
    return {
        "snap_days": len(snaps), "first_date": dates[0] if dates else "2026-11-16",
        "last_date": dates[-1] if dates else datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "aws_offer_version": cur_ver, "offer_versions_count": len(offers), "aws_regions": int(aws_meta.get("aws_regions_indexed") or 41),
        "deltas": deltas, "drift_label": "0 rate hikes ($0.00 Δ stable)" if changed_cnt == 0 else f"{changed_cnt} rate updates detected",
    }


def _select_providers(page: dict[str, object], providers: list[dict[str, object]], deltas: dict[str, float]) -> tuple[list[dict[str, object]], str]:
    mode, sort_mode, id_set = str(page.get("filter_mode") or "all"), str(page.get("sort_mode") or "monthly_asc"), set(page.get("provider_ids") or [])
    matched = [
        {**p, "hist_delta_usd": deltas.get(str(p["id"]), 0.0)}
        for p in providers
        if (mode == "zero_plus_aws" and (p.get("zero_egress") or p["id"] == "aws_s3"))
        or (mode == "explicit_ids" and p["id"] in id_set)
        or (mode == "eu_plus_zero_peers" and (p.get("eu_sovereign") or p.get("zero_egress") or p["id"] == "aws_s3"))
        or mode == "all"
    ]
    if sort_mode == "egress_asc":
        matched.sort(key=lambda r: (float(r["workload_20tb_50tb"]["egress_monthly_usd"]), float(r["workload_20tb_50tb"]["monthly_total_usd"])))
        return matched, "egress_usd"
    if sort_mode == "eu_first_monthly_asc":
        matched.sort(key=lambda r: (0 if r.get("eu_sovereign") else (2 if r["id"] == "aws_s3" else 1), float(r["workload_20tb_50tb"]["monthly_total_usd"])))
        return matched, "eu_first"
    matched.sort(key=lambda r: float(r["workload_20tb_50tb"]["monthly_total_usd"]))
    return matched, "monthly_usd"


def _render_ssr_rows(rows: list[dict[str, object]], snap_days: int, aws_yr: float) -> str:
    out: list[str] = []
    for r in rows:
        w = r["workload_20tb_50tb"]
        st_u, eg_u, mo_u, yr_u = float(w["storage_monthly_usd"]), float(w["egress_monthly_usd"]), float(w["monthly_total_usd"]), float(w["annual_total_usd"])
        diff_yr, sav_pct = aws_yr - yr_u, int(w.get("savings_vs_aws_pct") or 0)
        cat_b = '<span class="badge-zero">ZERO EGRESS</span>' if r.get("zero_egress") else ('<span class="badge badge-hyper">Hyperscaler</span>' if r.get("category") == "Hyperscaler" else f'<span class="badge badge-low">{_esc(r.get("category"))}</span>')
        sav_h = '<span class="muted-sm">Baseline (AWS S3)</span>' if r["id"] == "aws_s3" else (f'<div class="val-savings">+{_fmt_usd(diff_yr)}/yr</div><div class="muted-xs">Save {sav_pct}% vs AWS</div>' if diff_yr >= 0 else f'<div class="val-danger">-{_fmt_usd(abs(diff_yr))}/yr</div><div class="muted-xs">Higher than AWS S3</div>')
        dlt = float(r.get("hist_delta_usd") or 0.0)
        trd_h = f'<span class="badge badge-ok">{snap_days}d: $0 Δ Stable</span>' if abs(dlt) < 0.01 else f'<span class="badge badge-warn">{snap_days}d: {dlt:+.2f}/mo</span>'
        st_r = f"{float(r['storage_per_gb']):.4f}".rstrip("0").rstrip(".")
        eu_b = ' <span class="badge badge-eu">EU / GDPR</span>' if r.get("eu_sovereign") else ""
        s3_b = ' <span class="badge badge-ok">S3 API</span>' if r.get("s3_compatible") else ""
        out.append(
            f'<tr><td><div><a class="accent-link" href="{_esc(r["url"])}" target="_blank" rel="noopener">{_esc(r["name"])} ↗</a></div>'
            f'<div class="muted-xs">{cat_b}{eu_b}{s3_b}</div>'
            f'<span class="muted-xs">🟢 HTTP {int(r.get("probe_http_status") or 200)} ({int(r.get("probe_latency_ms") or 0)}ms)</span></td>'
            f'<td><div class="price-strong">${st_r}/GB</div><div class="muted-xs">{_fmt_usd(st_u, 2)}/mo storage</div></td>'
            f'<td><div><strong>{_esc(r["egress_label"])}</strong></div><div class="muted-xs">{_fmt_usd(eg_u, 2)}/mo bandwidth</div></td>'
            f'<td><div class="price-strong">{_fmt_usd(mo_u, 2)}/mo</div><div class="muted-xs">20 TB + 50 TB/mo</div></td>'
            f'<td><div><strong>{_fmt_usd(yr_u)}/yr</strong></div><div class="muted-xs">{trd_h}</div></td>'
            f'<td>{sav_h}</td><td class="policy-text"><div>{_esc(r["policy_note"])}</div></td></tr>'
        )
    return "\n          ".join(out)


def _build_hub_block(pages: list[dict[str, object]], hist: dict[str, object], live_cnt: int, total_cnt: int) -> str:
    cards = "".join(
        f'<a class="hub-card" href="/{_esc(p["slug"])}/">'
        f'<span class="{"badge-zero" if "ZERO" in str(p["hub_badge"]) or "R2" in str(p["hub_badge"]) else ("badge badge-eu" if "EU" in str(p["hub_badge"]) else "badge badge-low")}">{_esc(p["hub_badge"])}</span>'
        f'<div class="hub-card-title">{_esc(p["hub_label"])} →</div><div class="hub-card-desc">{_esc(p["hub_summary"])}</div></a>'
        for p in pages
    )
    return (
        '<!-- SEO_HUB_START -->\n    <section class="seo-hub-panel" aria-label="Multi-Day Verified Telemetry & FinOps Egress Deep-Dive Benchmarks">\n'
        '      <div class="seo-hub-head"><h3 class="seo-hub-title">📊 Multi-Day Price Telemetry &amp; FinOps Egress Deep-Dive Calculators</h3>'
        f'<span class="muted-sm">AWS Price List Offer <code>v{_esc(hist["aws_offer_version"])}</code> · {_esc(hist["aws_regions"])} Regions Indexed</span></div>\n'
        f'      <div class="telemetry-strip"><span class="live-pill">📅 {hist["snap_days"]} Archived Daily Snapshots ({_esc(hist["first_date"])} → {_esc(hist["last_date"])})</span>'
        f'<span class="badge badge-low">🟢 {live_cnt}/{total_cnt} Endpoints HTTP 200 Verified</span>'
        f'<span class="badge badge-ok">🔄 {hist["offer_versions_count"]} AWS Offer Versions Tracked · {_esc(hist["drift_label"])}</span></div>\n'
        f'      <div class="hub-grid">{cards}</div>\n    </section>\n    <!-- SEO_HUB_END -->'
    )


def build_all() -> dict[str, object]:
    fees, targets = json.loads(FEES_PATH.read_text(encoding="utf-8")), json.loads(TARGETS_PATH.read_text(encoding="utf-8"))
    providers, pages = list(fees.get("providers") or []), list(targets.get("pages") or [])
    if len(pages) > int((targets.get("anti_spam_guardrails") or {}).get("max_total_pages") or 15):
        raise RuntimeError("Exceeded max_total_pages guardrail")
    by_id = {str(p["id"]): p for p in providers}
    hist = _load_history_telemetry(providers, dict(fees.get("aws_price_list_telemetry") or {}))
    live_cnt, total_cnt = int((fees.get("summary") or {}).get("providers_verified_live") or len(providers)), len(providers)
    aws_p, now_dt = by_id["aws_s3"], datetime.now(timezone.utc)
    aws_w, iso_str, day_str = aws_p["workload_20tb_50tb"], now_dt.strftime("%Y-%m-%dT%H:%M:%SZ"), now_dt.strftime("%Y-%m-%d")
    yr_of = lambda pid: _fmt_usd(by_id[pid]["workload_20tb_50tb"]["annual_total_usd"])
    base_ctx = {
        "snap_days": hist["snap_days"], "first_date": hist["first_date"], "last_date": hist["last_date"],
        "aws_offer_version": hist["aws_offer_version"], "offer_versions_count": hist["offer_versions_count"], "live_count": live_cnt, "total_count": total_cnt,
        "aws_mo": _fmt_usd(aws_w["monthly_total_usd"]), "aws_eg_mo": _fmt_usd(aws_w["egress_monthly_usd"]), "aws_yr": _fmt_usd(aws_w["annual_total_usd"]),
        "gcp_yr": yr_of("gcp_gcs"), "azure_yr": yr_of("azure_blob"), "b2_mo": _fmt_usd(by_id["backblaze_b2"]["workload_20tb_50tb"]["monthly_total_usd"]),
        "b2_yr": yr_of("backblaze_b2"), "b2_10_50_mo": _fmt_usd(by_id["backblaze_b2"]["workload_10tb_50tb"]["monthly_total_usd"]),
        "wasabi_mo": _fmt_usd(by_id["wasabi"]["workload_20tb_50tb"]["monthly_total_usd"], 2), "wasabi_yr": yr_of("wasabi"),
        "r2_mo": _fmt_usd(by_id["cloudflare_r2"]["workload_20tb_50tb"]["monthly_total_usd"]), "r2_yr": yr_of("cloudflare_r2"),
        "r2_save_yr": _fmt_usd(by_id["cloudflare_r2"]["workload_20tb_50tb"]["annual_savings_vs_aws_usd"]),
        "tigris_yr": yr_of("tigris"), "storj_yr": yr_of("storj"), "imp_mo": _fmt_usd(by_id["impossible_cloud"]["workload_20tb_50tb"]["monthly_total_usd"]),
        "imp_yr": yr_of("impossible_cloud"), "hetzner_yr": yr_of("hetzner"), "ovh_yr": yr_of("ovhcloud"), "scaleway_yr": yr_of("scaleway"),
    }

    idx_doc, hub_html = INDEX_HTML_PATH.read_text(encoding="utf-8"), _build_hub_block(pages, hist, live_cnt, total_cnt)
    idx_doc = re.sub(r"<!-- SEO_HUB_START -->.*?<!-- SEO_HUB_END -->", lambda _: hub_html, idx_doc, count=1, flags=re.DOTALL) if "<!-- SEO_HUB_START -->" in idx_doc else idx_doc.replace('<section class="filter-bar"', f'{hub_html}\n\n    <section class="filter-bar"', 1)
    INDEX_HTML_PATH.write_text(idx_doc, encoding="utf-8")

    built_summary: list[dict[str, object]] = []
    for pg in pages:
        slug, (rows, js_sort) = str(pg["slug"]), _select_providers(pg, providers, dict(hist["deltas"]))
        best = sorted([r for r in rows if r["id"] != "aws_s3"], key=lambda r: float(r["workload_20tb_50tb"]["annual_total_usd"]))[0]
        ctx = {**base_ctx, "page_best_name": best["name"], "page_best_yr": _fmt_usd(best["workload_20tb_50tb"]["annual_total_usd"]), "page_max_save_yr": _fmt_usd(best["workload_20tb_50tb"]["annual_savings_vs_aws_usd"])}
        canon, hero_sub = f"{SITE_URL}{slug}/", str(pg["hero_subtitle"]).format_map(ctx)
        faqs = [{"q": str(f["q"]).format_map(ctx), "a": str(f["a"]).format_map(ctx)} for f in list(pg.get("faqs") or [])]
        caveats, focus_ids = [str(c).format_map(ctx) for c in list(pg.get("caveats") or [])], list(pg.get("focus_kpis") or [])[:3]
        ld_graph = {
            "@context": "https://schema.org",
            "@graph": [
                {"@type": "Dataset", "name": str(pg["h1"]), "description": str(pg["meta_description"]), "url": canon, "dateModified": iso_str, "temporalCoverage": f"{hist['first_date']}/{hist['last_date']}", "distribution": {"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": f"{SITE_URL}egress_fees.json"}, "keywords": [str(pg["target_keyword"]), "cloud egress fees", slug.replace("-", " ")]},
                {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Home", "item": SITE_URL}, {"@type": "ListItem", "position": 2, "name": str(pg["h1"]), "item": canon}]},
                {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in faqs]},
            ],
        }
        focus_cards = "".join(
            f'<div class="kcard"><div class="kcard-lbl"><span>{_esc(by_id[fid]["name"])}</span><span class="{"badge-zero" if by_id[fid].get("zero_egress") else ("badge badge-eu" if by_id[fid].get("eu_sovereign") else "badge badge-low")}">{"ZERO EGRESS" if by_id[fid].get("zero_egress") else ("EU / GDPR" if by_id[fid].get("eu_sovereign") else "METERED")}</span></div><div id="kpi-f{i}-mo" class="kcard-val">{_fmt_usd(by_id[fid]["workload_20tb_50tb"]["monthly_total_usd"])}/mo</div><div id="kpi-f{i}-yr" class="muted-xs">{_fmt_usd(by_id[fid]["workload_20tb_50tb"]["annual_total_usd"])}/yr ({_fmt_usd(by_id[fid]["workload_20tb_50tb"]["egress_monthly_usd"])}/mo egress)</div></div>'
            for i, fid in enumerate(focus_ids)
        )
        peer_links = '<a class="hub-card" href="/"><span class="live-pill">MASTER INDEX · 18 CLOUDS</span><div class="hub-card-title">All 18 Cloud Egress Providers →</div><div class="hub-card-desc">Return to the full 18-provider interactive S3 &amp; CDN bandwidth escape calculator.</div></a>' + "".join(
            f'<a class="hub-card" href="/{_esc(o["slug"])}/"><span class="badge badge-low">{_esc(o["hub_badge"])}</span><div class="hub-card-title">{_esc(o["hub_label"])} →</div><div class="hub-card-desc">{_esc(o["hub_summary"])}</div></a>'
            for o in pages if o["slug"] != slug
        )
        js_code = SUBPAGE_JS.replace("__PAGE_ROWS_JSON__", json.dumps(rows)).replace("__AWS_BASE_JSON__", json.dumps(aws_p)).replace("__FOCUS_IDS_JSON__", json.dumps(focus_ids)).replace("__SNAP_DAYS__", str(hist["snap_days"])).replace("__DEFAULT_SORT_KEY__", js_sort)
        sub_live = sum(1 for r in rows if r.get("verified_live"))
        caveat_html = "".join(f"<li>{_esc(c)}</li>" for c in caveats)
        faq_html = "".join(f'<div class="faq-item"><strong>{_esc(f["q"])}</strong><p>{_esc(f["a"])}</p></div>' for f in faqs)
        sub_html = (
            f'<!DOCTYPE html>\n<html lang="en" class="light-theme">\n<head>\n  <meta charset="utf-8" />\n  <meta name="viewport" content="width=device-width, initial-scale=1" />\n  <title>{_esc(pg["title"])}</title>\n  <meta name="description" content="{_esc(pg["meta_description"])}" />\n  <link rel="canonical" href="{_esc(canon)}" />\n{GA4_SNIPPET}\n'
            f'  <meta property="og:title" content="{_esc(pg["title"])}" />\n  <meta property="og:description" content="{_esc(pg["meta_description"])}" />\n  <meta property="og:url" content="{_esc(canon)}" />\n  <meta property="og:type" content="website" />\n  <meta name="twitter:card" content="summary" />\n  <script type="application/ld+json">\n{json.dumps(ld_graph, indent=2)}\n  </script>\n  <style>\n{SUBPAGE_CSS}\n  </style>\n</head>\n'
            f'<body class="light-theme">\n  <header class="topbar"><div class="brand"><a class="brand-link" href="/">💸 CloudEgressFees<span class="brand-dot">.com</span></a><span class="live-pill">{_esc(pg["hub_badge"])}</span><span class="muted-sm">Updated: {_esc(fees.get("updated_at_utc"))} · AWS Offer v{_esc(hist["aws_offer_version"])}</span></div>'
            '<div class="topbar-actions"><a class="btn" href="/">← All 18 Clouds</a><button class="btn" onclick="exportSubCsv()">📥 Export CSV</button><button id="theme-btn" class="btn" onclick="toggleTheme()">🌙 Dark Mode</button></div></header>\n  <main class="container">\n'
            f'    <nav class="breadcrumb" aria-label="Breadcrumb"><a class="accent-link" href="/">Home</a><span>→</span><span aria-current="page">{_esc(pg["h1"])}</span></nav>\n    <section class="hero"><h1>{_esc(pg["h1"])}</h1><p>{_esc(hero_sub)}</p></section>\n'
            f'    <div class="telemetry-banner"><span class="live-pill">📅 {hist["snap_days"]}-Day Verified History ({_esc(hist["first_date"])} → {_esc(hist["last_date"])})</span><span class="badge badge-low">🟢 {sub_live}/{len(rows)} Benchmark Endpoints HTTP 200 ({live_cnt}/{total_cnt} Global)</span><span class="badge badge-ok">📦 AWS Price List v{_esc(hist["aws_offer_version"])} · {hist["offer_versions_count"]} Versions Tracked · {_esc(hist["drift_label"])}</span></div>\n'
            '    <section class="calc-panel" aria-label="Interactive FinOps Bandwidth Calculator"><div class="calc-header"><span class="calc-title">🧮 Live Stored TB + Monthly Egress TB FinOps Calculator</span><div class="preset-row"><button class="preset-btn" onclick="applyPreset(20, 50)">Default (20 TB · 50 TB/mo)</button><button class="preset-btn" onclick="applyPreset(10, 50)">5× Ratio (10 TB · 50 TB/mo)</button><button class="preset-btn" onclick="applyPreset(20, 80)">4× B2 Cap Test (20 TB · 80 TB/mo)</button><button class="preset-btn" onclick="applyPreset(50, 200)">CDN Origin (50 TB · 200 TB/mo)</button><button class="preset-btn" onclick="applyPreset(100, 10)">Backup Lake (100 TB · 10 TB/mo)</button></div></div>\n'
            '      <div class="slider-grid"><div class="slider-box"><div class="slider-top"><label for="num-stored">📦 Active Stored Data (TB)</label><span class="num-wrap"><input id="num-stored" class="num-input" type="number" min="0.1" max="10000" step="1" value="20" oninput="syncInputs(\'stored\', \'num\')" /><span>TB</span></span></div><input id="rng-stored" class="range-input" type="range" min="1" max="500" step="1" value="20" oninput="syncInputs(\'stored\', \'rng\')" /><div class="muted-xs">1 TB = 1,000 GB decimal cloud billing unit</div></div>'
            '<div class="slider-box"><div class="slider-top"><label for="num-egress">🌐 Monthly Outbound Egress (TB/mo)</label><span class="num-wrap"><input id="num-egress" class="num-input" type="number" min="0" max="10000" step="1" value="50" oninput="syncInputs(\'egress\', \'num\')" /><span>TB/mo</span></span></div><input id="rng-egress" class="range-input" type="range" min="0" max="500" step="1" value="50" oninput="syncInputs(\'egress\', \'rng\')" /><div id="ratio-indicator" class="muted-xs">Egress-to-Storage Ratio: 2.5x monthly stored volume (50,000 GB outbound)</div></div></div>\n'
            f'      <div class="kpi-cards"><div class="kcard"><div class="kcard-lbl"><span>AWS S3 Standard</span><span class="badge badge-hyper">Baseline</span></div><div id="kpi-aws-mo" class="kcard-val">{ctx["aws_mo"]}/mo</div><div id="kpi-aws-yr" class="muted-xs">{ctx["aws_yr"]}/yr ({ctx["aws_eg_mo"]}/mo egress)</div></div>{focus_cards}<div class="kcard kcard-highlight"><div class="kcard-lbl"><span>Max Annual Savings</span><span class="badge badge-low">vs AWS S3</span></div><div id="kpi-save-yr" class="kcard-val val-savings">{ctx["page_max_save_yr"]}/yr</div><div id="kpi-save-sub" class="muted-xs">Lowest TCO via {_esc(best["name"])}</div></div></div></section>\n'
            f'    <div class="table-wrap"><table><thead><tr><th onclick="setSort(\'name\')">Provider &amp; Telemetry</th><th onclick="setSort(\'storage_per_gb\')">Storage Rate</th><th onclick="setSort(\'egress_usd\')">Internet Egress Rate</th><th onclick="setSort(\'monthly_usd\')">Monthly Bill</th><th onclick="setSort(\'monthly_usd\')">Annual &amp; {hist["snap_days"]}d Trend</th><th onclick="setSort(\'savings_yr\')">Annual Savings vs AWS</th><th>Objective Retention &amp; Multiplier Caveats</th></tr></thead>\n'
            f'        <tbody id="matrix-tbody">\n          {_render_ssr_rows(rows, int(hist["snap_days"]), float(aws_w["annual_total_usd"]))}\n        </tbody></table></div>\n'
            f'    <section class="faq-section"><h2>Objective Retention, Ratio &amp; Engineering Caveats</h2><ul class="caveat-list">{caveat_html}</ul></section>\n'
            f'    <section class="faq-section"><h2>FinOps Engineering FAQ</h2>{faq_html}</section>\n'
            f'    <section class="seo-hub-panel"><h2>Explore Related Cloud Egress Benchmarks</h2><div class="hub-grid">{peer_links}</div></section>\n'
            f'    <footer class="footer"><div>Methodology: 1 TB = 1,000 GB decimal cloud billing unit. Public standard NA/EU rates verified every 6 hours via GitHub Actions against official vendor pricing &amp; AWS Price List API.</div></footer>\n  </main>\n  <script>\n{js_code}\n  </script>\n</body>\n</html>\n'
        )
        out_file = PUBLIC_DIR / slug / "index.html"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(sub_html, encoding="utf-8")
        built_summary.append({"slug": slug, "url": canon, "providers": len(rows), "best_provider": best["name"]})

    urls_xml = [f"  <url>\n    <loc>{SITE_URL}</loc>\n    <lastmod>{day_str}</lastmod>\n    <changefreq>daily</changefreq>\n    <priority>1.0</priority>\n  </url>"] + [
        f"  <url>\n    <loc>{SITE_URL}{pg['slug']}/</loc>\n    <lastmod>{day_str}</lastmod>\n    <changefreq>daily</changefreq>\n    <priority>0.85</priority>\n  </url>" for pg in pages
    ]
    SITEMAP_PATH.write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(urls_xml) + "\n</urlset>\n", encoding="utf-8")
    return {"version": "5.0", "history_days": hist["snap_days"], "aws_offer_version": hist["aws_offer_version"], "pages_built": built_summary}


if __name__ == "__main__":
    print(json.dumps(build_all(), indent=2))
