#!/usr/bin/env python3
"""Live US Google Autocomplete & GSC Query Poller + Guardrailed Subpage Auto-Expander for CloudEgressFees.com."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import urllib.parse
import urllib.request

ROOT_DIR = Path(__file__).resolve().parent.parent
PUBLIC_DIR = ROOT_DIR / "public"
FEES_PATH = PUBLIC_DIR / "egress_fees.json"
TARGETS_PATH = PUBLIC_DIR / "seo_targets.json"
SIGNALS_PATH = PUBLIC_DIR / "live_search_signals.json"
SITE_PROP = "sc-domain:cloudegressfees.com"

SEED_PREFIXES: tuple[str, ...] = (
    "cloud egress ",
    "aws s3 egress ",
    "gcp egress ",
    "azure egress ",
    "zero egress ",
    "cloudflare r2 vs ",
    "wasabi vs ",
    "backblaze b2 vs ",
    "cdn bandwidth pricing",
    "hetzner storage ",
    "storj pricing",
)

BLUEPRINT_POOL: tuple[dict[str, object], ...] = (
    {
        "trigger_tokens": ["gcp egress", "azure egress", "aws s3 egress"],
        "min_providers": 4,
        "page": {
            "slug": "aws-vs-gcp-vs-azure-egress",
            "hub_badge": "BIG-3 HYPERSCALERS",
            "hub_label": "AWS vs GCP vs Azure Egress",
            "hub_summary": "Compare AWS S3 ($0.09/GB), GCP ($0.12/GB), and Azure ($0.087/GB) bandwidth bills against R2 & B2.",
            "target_keyword": "AWS vs GCP vs Azure Cloud Egress Fees Calculator",
            "title": "AWS vs GCP vs Azure Cloud Egress Fees Calculator (2026 Live)",
            "h1": "AWS vs GCP vs Azure Outbound Cloud Egress Fees Calculator",
            "meta_description": "Compare AWS S3 ($0.09/GB), Google Cloud Storage ($0.12/GB), and Azure Blob ($0.087/GB) outbound internet egress bills against zero-egress S3 alternatives.",
            "hero_subtitle": "Side-by-side FinOps comparison of AWS, Google Cloud, and Microsoft Azure public internet egress rates versus Cloudflare R2 and Backblaze B2.",
            "filter_mode": "explicit_ids",
            "provider_ids": ["aws_s3", "gcp_gcs", "azure_blob", "cloudflare_r2", "backblaze_b2"],
            "sort_mode": "monthly_asc",
            "default_stored_tb": 20,
            "default_egress_tb": 50,
            "focus_kpis": ["cloudflare_r2", "azure_blob", "gcp_gcs"],
            "caveats": [
                "Hyperscaler Public Internet Tiers: GCP Standard bills $0.12/GB ($77,040/yr at 20 TB + 50 TB/mo), AWS S3 bills $0.09/GB ($59,412/yr), and Azure Blob Hot bills $0.087/GB ($57,109/yr).",
                "Free-Tier Allowances: AWS S3 and Azure include 100 GB/mo free internet egress, which offsets less than 0.2% of a 50 TB/mo production workload.",
                "Multi-Cloud Origin Offload: Syncing public read buckets to Cloudflare R2 ($3,600/yr) or Backblaze B2 ($1,440/yr) eliminates 94%–98% of hyperscaler bandwidth spend.",
            ],
            "faqs": [
                {
                    "q": "Which of AWS, GCP, or Azure has the highest cloud egress fees?",
                    "a": "On standard public internet routing, Google Cloud Storage is highest at $0.12/GB ({gcp_yr}/yr for 20 TB stored + 50 TB/mo egress), followed by AWS S3 at $0.09/GB ({aws_yr}/yr) and Azure Blob Hot at $0.087/GB ({azure_yr}/yr).",
                },
                {
                    "q": "How much can enterprises save moving public egress off AWS, GCP, or Azure?",
                    "a": "Offloading 20 TB stored + 50 TB/mo public downloads to {page_best_name} ({page_best_yr}/yr) saves {page_max_save_yr}/yr versus AWS S3 and over $73,000/yr versus GCP Standard.",
                },
            ],
        },
    },
    {
        "trigger_tokens": ["cdn bandwidth", "bunny", "fastly"],
        "min_providers": 4,
        "page": {
            "slug": "cdn-bandwidth-pricing",
            "hub_badge": "CDN & EDGE STORAGE",
            "hub_label": "CDN Bandwidth Pricing",
            "hub_summary": "Compare Bunny.net ($0.01/GB), Fastly ($0 egress), Gcore, and Cloudflare R2 edge delivery bills.",
            "target_keyword": "CDN Bandwidth & Edge Object Storage Egress Pricing",
            "title": "CDN Bandwidth & Edge Object Storage Egress Pricing (2026 Live)",
            "h1": "CDN Bandwidth & Edge Object Storage Egress Pricing",
            "meta_description": "Compare live CDN bandwidth and edge object storage pricing across Cloudflare R2, Fastly, Bunny.net ($0.01/GB), Gcore, DigitalOcean Spaces, and AWS S3.",
            "hero_subtitle": "Model high-throughput media, AI weight distribution, and software download TCO across zero-egress edge storage and $0.01/GB global CDNs.",
            "filter_mode": "explicit_ids",
            "provider_ids": ["cloudflare_r2", "fastly", "tigris", "bunny_net", "gcore", "aws_s3"],
            "sort_mode": "monthly_asc",
            "default_stored_tb": 20,
            "default_egress_tb": 50,
            "focus_kpis": ["cloudflare_r2", "fastly", "bunny_net"],
            "caveats": [
                "Zero-Egress Edge Storage (Cloudflare R2, Fastly, Tigris): $0.00/GB outbound transfer with global edge caching for static assets and model shards.",
                "Pay-Per-GB Volume CDNs (Bunny.net & Gcore): Flat ~$0.01/GB NA/EU delivery (~89% below AWS S3 direct origin egress) with predictable regional volume tiers.",
            ],
            "faqs": [
                {
                    "q": "How do Bunny.net, Fastly, and Cloudflare R2 compare on 50 TB/mo bandwidth?",
                    "a": "At 20 TB stored + 50 TB/mo transfer, Cloudflare R2 and Fastly Object Storage cost $3,600/yr ($0 egress), while Bunny.net costs $8,400/yr ($0.01/GB NA/EU CDN)—all drastically below {aws_yr}/yr on AWS S3.",
                },
            ],
        },
    },
)


def _fetch_us_autocomplete(prefix: str) -> list[dict[str, object]]:
    url = "https://suggestqueries.google.com/complete/search?client=chrome&hl=en&gl=us&q=" + urllib.parse.quote(prefix)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=8) as resp:
        data = json.loads(resp.read().decode("utf-8", errors="replace"))
    queries = list(data[1] or [])[:8]
    rels = list(((data[4] if len(data) > 4 and isinstance(data[4], dict) else {}).get("google:suggestrelevance")) or [])
    return [
        {"query": str(q).strip().lower(), "score": int(rels[i]) if i < len(rels) else max(500, 900 - i * 50), "source": "google_us_autocomplete", "seed": prefix.strip()}
        for i, q in enumerate(queries)
    ]


def _fetch_gsc_api_if_configured() -> list[dict[str, object]]:
    cid = os.environ.get("GSC_CLIENT_ID", "").strip()
    csec = os.environ.get("GSC_CLIENT_SECRET", "").strip()
    rtok = os.environ.get("GSC_REFRESH_TOKEN", "").strip()
    if not (cid and csec and rtok):
        return []
    tbody = urllib.parse.urlencode({"client_id": cid, "client_secret": csec, "refresh_token": rtok, "grant_type": "refresh_token"}).encode("utf-8")
    treq = urllib.request.Request("https://oauth2.googleapis.com/token", data=tbody, method="POST")
    with urllib.request.urlopen(treq, timeout=10) as tresp:
        atok = json.loads(tresp.read().decode("utf-8"))["access_token"]
    end_d = datetime.now(timezone.utc).date()
    start_d = end_d - timedelta(days=28)
    api_url = f"https://www.googleapis.com/webmasters/v3/sites/{urllib.parse.quote(SITE_PROP, safe='')}/searchAnalytics/query"
    qbody = json.dumps({"startDate": str(start_d), "endDate": str(end_d), "dimensions": ["query"], "rowLimit": 50}).encode("utf-8")
    qreq = urllib.request.Request(api_url, data=qbody, headers={"Authorization": f"Bearer {atok}", "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(qreq, timeout=10) as qresp:
        rows = json.loads(qresp.read().decode("utf-8")).get("rows") or []
    return [
        {
            "query": str((r.get("keys") or [""])[0]).lower(),
            "impressions": int(r.get("impressions") or 0),
            "clicks": int(r.get("clicks") or 0),
            "position": round(float(r.get("position") or 0.0), 1),
            "score": 1000 + int(r.get("impressions") or 0) * 20,
            "source": "google_search_console_api",
        }
        for r in rows
    ]


def run_discovery() -> dict[str, object]:
    now_dt = datetime.now(timezone.utc)
    iso_week = f"{now_dt.isocalendar()[0]}-W{now_dt.isocalendar()[1]:02d}"
    now_utc = now_dt.strftime("%Y-%m-%d %H:%M UTC")

    seen: dict[str, dict[str, object]] = {}
    for pref in SEED_PREFIXES:
        try:
            for item in _fetch_us_autocomplete(pref):
                q = str(item["query"])
                if q not in seen or int(item["score"]) > int(seen[q]["score"]):
                    seen[q] = item
        except Exception:
            continue
    try:
        for item in _fetch_gsc_api_if_configured():
            seen[str(item["query"])] = item
    except Exception:
        pass

    ranked_signals = sorted(seen.values(), key=lambda x: int(x.get("score") or 0), reverse=True)
    providers = list(json.loads(FEES_PATH.read_text(encoding="utf-8")).get("providers") or [])
    prov_ids = {str(p.get("id")) for p in providers}
    targets_cfg = json.loads(TARGETS_PATH.read_text(encoding="utf-8"))
    guard = dict(targets_cfg.get("anti_spam_guardrails") or {})
    pages = list(targets_cfg.get("pages") or [])
    existing_slugs = {str(p.get("slug")) for p in pages}
    promotions = list(targets_cfg.get("auto_promotions") or [])

    max_weekly = int(guard.get("max_new_pages_per_week") or 2)
    max_total = int(guard.get("max_total_pages") or 15)
    added_this_week = sum(1 for x in promotions if str(x.get("iso_week")) == iso_week)
    newly_promoted: list[dict[str, object]] = []

    for bp in BLUEPRINT_POOL:
        if len(pages) >= max_total or added_this_week >= max_weekly:
            break
        page_def = dict(bp["page"])  # type: ignore[arg-type]
        slug = str(page_def["slug"])
        if slug in existing_slugs:
            continue
        req_ids = [str(x) for x in (page_def.get("provider_ids") or []) if str(x) in prov_ids]
        if len(req_ids) < int(bp.get("min_providers") or 3):
            continue
        tokens = [str(t).lower() for t in (bp.get("trigger_tokens") or [])]
        matched = [s for s in ranked_signals if any(tok in str(s["query"]) for tok in tokens) and int(s.get("score") or 0) >= 550]
        if not matched:
            continue
        best = matched[0]
        pages.append(page_def)
        existing_slugs.add(slug)
        rec = {
            "slug": slug,
            "iso_week": iso_week,
            "promoted_at_utc": now_utc,
            "trigger_query": best["query"],
            "trigger_score": best["score"],
            "trigger_source": best["source"],
            "live_providers_verified": len(req_ids),
        }
        promotions.append(rec)
        newly_promoted.append(rec)
        added_this_week += 1

    targets_cfg["pages"] = pages
    targets_cfg["auto_promotions"] = promotions
    targets_cfg["observed_gsc_queries"] = ranked_signals[:25]
    TARGETS_PATH.write_text(json.dumps(targets_cfg, indent=2) + "\n", encoding="utf-8")

    SIGNALS_PATH.write_text(
        json.dumps(
            {
                "site": "CloudEgressFees.com",
                "updated_at_utc": now_utc,
                "iso_week": iso_week,
                "total_signals_collected": len(ranked_signals),
                "active_subpages_count": len(pages),
                "newly_promoted_this_run": newly_promoted,
                "top_live_queries": ranked_signals[:30],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return {"signals": len(ranked_signals), "active_pages": len(pages), "newly_promoted": newly_promoted}


if __name__ == "__main__":
    print(json.dumps(run_discovery()))
