#!/usr/bin/env python3
"""Static HTML SSR Pre-Renderer, JSON-LD FAQ Enricher & IndexNow Notifier for CloudEgressFees.com."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import re
import urllib.request

ROOT_DIR = Path(__file__).resolve().parent.parent
PUBLIC_DIR = ROOT_DIR / "public"
JSON_PATH = PUBLIC_DIR / "egress_fees.json"
HTML_PATH = PUBLIC_DIR / "index.html"
SITEMAP_PATH = PUBLIC_DIR / "sitemap.xml"
HOST = "cloudegressfees.com"
SITE_URL = f"https://{HOST}/"
INDEXNOW_KEY = hashlib.sha256(f"indexnow:{HOST}:v1".encode("utf-8")).hexdigest()[:32]


def _esc(val: object) -> str:
    return html.escape(str(val or ""), quote=True)


def _fmt_usd(val: float, digits: int = 0) -> str:
    if digits > 0:
        return f"${val:,.{digits}f}"
    return f"${round(val):,}"


def _render_rows_html(providers: list[dict[str, object]]) -> str:
    provs = sorted(providers, key=lambda r: float((r.get("workload_20tb_50tb") or {}).get("annual_total_usd") or 0.0))
    rows_html: list[str] = []
    for r in provs:
        w = r.get("workload_20tb_50tb") or {}
        st_usd = float(w.get("storage_monthly_usd") or 0.0)
        eg_usd = float(w.get("egress_monthly_usd") or 0.0)
        mo_usd = float(w.get("monthly_total_usd") or 0.0)
        yr_usd = float(w.get("annual_total_usd") or 0.0)
        sav_yr = float(w.get("annual_savings_vs_aws_usd") or 0.0)
        sav_pct = int(w.get("savings_vs_aws_pct") or 0)

        if r.get("zero_egress"):
            cat_badge = '<span class="badge-zero">ZERO EGRESS</span>'
        elif str(r.get("category")) == "Hyperscaler":
            cat_badge = '<span class="badge badge-hyper">Hyperscaler</span>'
        else:
            cat_badge = f'<span class="badge badge-low">{_esc(r.get("category"))}</span>'
        eu_badge = ' <span class="badge badge-eu">EU / GDPR</span>' if r.get("eu_sovereign") else ""
        s3_badge = ' <span class="badge badge-ok">S3 API</span>' if r.get("s3_compatible") else ""
        live_badge = (
            f'<span class="muted-xs">🟢 HTTP {int(r.get("probe_http_status") or 200)} ({int(r.get("probe_latency_ms") or 0)}ms)</span>'
            if r.get("verified_live")
            else ""
        )
        if str(r.get("id")) == "aws_s3":
            sav_html = '<span class="muted-sm">Baseline (AWS S3)</span>'
        elif sav_yr >= 0:
            sav_html = f'<div class="val-savings">+{_fmt_usd(sav_yr)}/yr</div><div class="muted-xs">Save {sav_pct}% vs AWS</div>'
        else:
            sav_html = f'<div class="val-danger">-{_fmt_usd(abs(sav_yr))}/yr</div><div class="muted-xs">Higher than AWS S3</div>'
        st_rate = f"{float(r.get('storage_per_gb') or 0.0):.4f}".rstrip("0").rstrip(".")
        rows_html.append(
            "<tr>"
            f'<td><div><a class="accent-link" href="{_esc(r.get("url"))}" target="_blank" rel="noopener">{_esc(r.get("name"))} ↗</a></div>'
            f'<div class="muted-xs">{cat_badge}{eu_badge}{s3_badge}</div>{live_badge}</td>'
            f'<td><div class="price-strong">${st_rate}/GB</div><div class="muted-xs">{_fmt_usd(st_usd, 2)}/mo storage</div></td>'
            f'<td><div><strong>{_esc(r.get("egress_label"))}</strong></div><div class="muted-xs">{_fmt_usd(eg_usd, 2)}/mo bandwidth</div></td>'
            f'<td><div class="price-strong">{_fmt_usd(mo_usd, 2)}/mo</div><div class="muted-xs">20 TB + 50 TB/mo</div></td>'
            f'<td><div><strong>{_fmt_usd(yr_usd)}/yr</strong></div></td>'
            f"<td>{sav_html}</td>"
            f'<td class="policy-text"><div>{_esc(r.get("policy_note"))}</div></td>'
            "</tr>"
        )
    return "\n          ".join(rows_html)


def _build_ldjson(data: dict[str, object], iso_date: str) -> str:
    providers = list(data.get("providers") or [])
    cnt = len(providers) or 18
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Dataset",
                "name": f"Cloud Egress Fees & Zero-Egress Object Storage Pricing Index ({cnt} Providers)",
                "description": f"Normalized per-GB storage rates, outbound internet egress fees, free-tier multipliers, and policy caveats across {cnt} cloud object storage, S3-compatible, and CDN providers.",
                "url": SITE_URL,
                "dateModified": iso_date,
                "distribution": {"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": f"{SITE_URL}egress_fees.json"},
                "keywords": ["cloud egress fees", "cloud egress calculator", "aws s3 egress pricing", "zero egress cloud storage", "cloudflare r2 vs aws s3", "wasabi vs backblaze b2 egress"],
            },
            {
                "@type": "WebApplication",
                "name": "CloudEgressFees.com FinOps Egress Escape Calculator",
                "url": SITE_URL,
                "applicationCategory": "DeveloperApplication",
                "operatingSystem": "All",
                "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
            },
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": "How much do AWS S3, GCP, and Azure charge for cloud egress fees?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": "Standard public internet egress starts around $0.09/GB on AWS S3, $0.12/GB on Google Cloud Storage, and $0.087/GB on Azure Blob Storage. At 20 TB stored and 50 TB/mo outbound transfer, AWS S3 costs $59,412/yr compared to $1,440–$3,600/yr on Zero-Egress S3 alternatives like Backblaze B2, Cloudflare R2, and Wasabi.",
                        },
                    },
                    {
                        "@type": "Question",
                        "name": "What policy caveats apply to $0.00/GB zero-egress cloud storage providers?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": "Wasabi and Impossible Cloud enforce 30-to-90-day minimum object retention windows and active-egress fair-use ratios; Backblaze B2 includes free direct egress up to 3x average monthly stored volume ($0.01/GB over, or unlimited $0 via Cloudflare/Fastly/Bunny CDN); Cloudflare R2 charges $0 egress at any ratio with standard Class A/B API request fees.",
                        },
                    },
                ],
            },
        ],
    }
    return json.dumps(graph, indent=2)


def prerender_all(ping_indexnow: bool = False) -> dict[str, object]:
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    now_dt = datetime.now(timezone.utc)
    day_str = now_dt.strftime("%Y-%m-%d")
    iso_str = now_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    providers = list(data.get("providers") or [])

    doc = HTML_PATH.read_text(encoding="utf-8")
    doc = re.sub(
        r'(<script id="seo-ldjson" type="application/ld\+json">)(.*?)(</script>)',
        lambda m: f"{m.group(1)}\n{_build_ldjson(data, iso_str)}\n  {m.group(3)}",
        doc,
        count=1,
        flags=re.DOTALL,
    )
    doc = re.sub(
        r'(<tbody id="matrix-tbody">)(.*?)(</tbody>)',
        lambda m: f"{m.group(1)}\n          {_render_rows_html(providers)}\n        {m.group(3)}",
        doc,
        count=1,
        flags=re.DOTALL,
    )
    HTML_PATH.write_text(doc, encoding="utf-8")

    SITEMAP_PATH.write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"  <url>\n    <loc>{SITE_URL}</loc>\n    <lastmod>{day_str}</lastmod>\n    <changefreq>daily</changefreq>\n    <priority>1.0</priority>\n  </url>\n"
        f"</urlset>\n",
        encoding="utf-8",
    )
    key_file = PUBLIC_DIR / f"{INDEXNOW_KEY}.txt"
    key_file.write_text(INDEXNOW_KEY, encoding="utf-8")

    ping_status = None
    if ping_indexnow:
        body = json.dumps({
            "host": HOST,
            "key": INDEXNOW_KEY,
            "keyLocation": f"{SITE_URL}{INDEXNOW_KEY}.txt",
            "urlList": [SITE_URL],
        }).encode("utf-8")
        req = urllib.request.Request("https://api.indexnow.org/indexnow", data=body, headers={"Content-Type": "application/json; charset=utf-8"}, method="POST")
        with urllib.request.urlopen(req, timeout=12) as resp:
            ping_status = resp.status
    return {"host": HOST, "ssr_rows": len(providers), "indexnow_key": INDEXNOW_KEY, "ping_status": ping_status}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ping-indexnow", action="store_true")
    args = ap.parse_args()
    print(json.dumps(prerender_all(ping_indexnow=args.ping_indexnow)))
