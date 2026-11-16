#!/usr/bin/env python3
"""
Zero-Maintenance Multi-Cloud Storage & Egress Fee Sync Engine (sync_egress_fees.py)
-----------------------------------------------------------------------------------
Fetches live AWS Price List API metadata (`AmazonS3/current/region_index.json`), probes
live HTTP status/latency across 18 Cloud Object Storage & Zero-Egress CDN providers,
computes FinOps TCO across reference workloads (`10TB + 50TB/mo` & `20TB + 50TB/mo`),
enforces a `>= 15` provider circuit breaker, and writes `public/egress_fees.json` plus
daily snapshots in `public/history/YYYY-MM-DD.json`.
"""
from __future__ import annotations

import concurrent.futures
import json
import os
import re
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PUBLIC_DIR = BASE_DIR / "public"
OUT_JSON = PUBLIC_DIR / "egress_fees.json"
HISTORY_DIR = PUBLIC_DIR / "history"

AWS_S3_INDEX_URL = "https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonS3/current/region_index.json"
USER_AGENT = "Mozilla/5.0 (compatible; CloudEgressFeesBot/1.0; +https://cloudegressfees.com)"
CIRCUIT_BREAKER_MIN_PROVIDERS = 15


def _p(
    pid: str, name: str, category: str, zero_egress: bool, s3: bool, eu: bool,
    url: str, probe_url: str, storage_gb: float, egress_gb: float, egress_label: str, policy_note: str,
    base_usd: float = 0.0, incl_storage_gb: int = 0, free_egress_gb: int = 0,
    free_mult: float = 0.0, fair_mult: float = 0.0,
) -> dict[str, object]:
    return {
        "id": pid, "name": name, "category": category, "zero_egress": zero_egress,
        "s3_compatible": s3, "eu_sovereign": eu, "url": url, "probe_url": probe_url,
        "storage_per_gb": storage_gb, "egress_per_gb": egress_gb, "base_monthly_usd": base_usd,
        "included_storage_gb": incl_storage_gb, "free_egress_gb": free_egress_gb,
        "free_egress_mult": free_mult, "fair_use_mult": fair_mult,
        "egress_label": egress_label, "policy_note": policy_note,
    }


PROVIDERS: list[dict[str, object]] = [
    _p("aws_s3", "AWS S3 Standard", "Hyperscaler", False, True, False,
       "https://aws.amazon.com/s3/pricing/", "https://aws.amazon.com/s3/pricing/",
       0.023, 0.09, "$0.09/GB (after 100 GB free)",
       "100 GB/mo free internet egress; $0.09/GB headline tier ($0.085/GB 10-50 TB tiered); PUT/GET ops extra.", free_egress_gb=100),
    _p("gcp_gcs", "Google Cloud Storage Standard", "Hyperscaler", False, True, False,
       "https://cloud.google.com/storage/pricing", "https://cloud.google.com/storage/pricing",
       0.020, 0.12, "$0.12/GB internet egress",
       "Standard NA/EU internet egress $0.12/GB (higher in APAC); Class A/B ops & inter-region replication extra."),
    _p("azure_blob", "Microsoft Azure Blob Hot", "Hyperscaler", False, False, False,
       "https://azure.microsoft.com/en-us/pricing/details/storage/blobs/", "https://prices.azure.com/api/retail/prices?%24top=1",
       0.018, 0.087, "$0.087/GB (after 100 GB free)",
       "First 100 GB/mo internet egress free, then $0.087/GB; native Azure Blob REST API (S3 via gateway).", free_egress_gb=100),
    _p("cloudflare_r2", "Cloudflare R2", "Zero-Egress S3", True, True, False,
       "https://developers.cloudflare.com/r2/pricing/", "https://developers.cloudflare.com/r2/pricing/",
       0.015, 0.0, "$0.00/GB Zero Egress",
       "Unconditional $0.00/GB internet egress (no egress-to-storage ratio cap); Class A $4.50/M & Class B $0.36/M ops."),
    _p("wasabi", "Wasabi Hot Cloud Storage", "Zero-Egress S3", True, True, False,
       "https://wasabi.com/pricing", "https://wasabi.com/pricing",
       0.00699, 0.0, "$0.00/GB Zero Egress*",
       "$0 egress & $0 API calls; 90-day minimum storage retention policy; fair-use targets monthly egress <= active stored volume.", fair_mult=1.0),
    _p("backblaze_b2", "Backblaze B2 Cloud Storage", "Zero-Egress S3", True, True, False,
       "https://www.backblaze.com/cloud-storage/pricing", "https://www.backblaze.com/cloud-storage/pricing",
       0.006, 0.01, "$0.00/GB up to 3x stored ($0.01/GB over)",
       "Free egress up to 3x monthly stored data ($0.01/GB beyond); unlimited $0 egress via Cloudflare/Fastly/Bunny CDN.", free_mult=3.0),
    _p("tigris", "Tigris Data", "Zero-Egress S3", True, True, False,
       "https://www.tigrisdata.com/", "https://www.tigrisdata.com/",
       0.020, 0.0, "$0.00/GB Global Zero Egress",
       "Globally distributed S3-compatible edge object storage with automatic geo-caching and $0.00/GB egress worldwide."),
    _p("storj", "Storj", "Low-Egress Cloud", False, True, False,
       "https://www.storj.io/pricing", "https://www.storj.io/pricing",
       0.004, 0.007, "$0.007/GB (92% below AWS)",
       "Distributed S3-compatible object storage at $4/TB storage + flat $7/TB global egress; per-segment fee on tiny objects."),
    _p("impossible_cloud", "Impossible Cloud", "Zero-Egress S3", True, True, True,
       "https://www.impossiblecloud.com/pricing", "https://www.impossiblecloud.com/pricing",
       0.0079, 0.0, "$0.00/GB Zero Egress (EU)",
       "GDPR/ISO-certified EU sovereign S3 storage; $0 egress & $0 API call fees; 30-90 day minimum retention by plan.", fair_mult=1.0),
    _p("hetzner", "Hetzner Object Storage", "Low-Egress Cloud", False, True, True,
       "https://www.hetzner.com/storage/object-storage/", "https://www.hetzner.com/storage/object-storage/",
       0.0053, 0.0011, "1 TB incl., then ~$0.0011/GB",
       "EU S3-compatible storage (FSN1/HEL1/NBG1); 1 TB/mo free egress included, then ~EUR 1/TB (~$0.0011/GB).", free_egress_gb=1000),
    _p("vultr", "Vultr Object Storage", "Low-Egress Cloud", False, True, False,
       "https://www.vultr.com/pricing/#cloud-storage", "https://api.vultr.com/v2/regions",
       0.018, 0.01, "1 TB incl., then $0.01/GB",
       "Base tier starts at $18/mo (1 TB storage + 1 TB egress included), $0.018/GB storage & $0.01/GB outbound overage.", free_egress_gb=1000),
    _p("digitalocean", "DigitalOcean Spaces", "Low-Egress Cloud", False, True, False,
       "https://www.digitalocean.com/pricing/spaces-object-storage", "https://www.digitalocean.com/pricing/spaces-object-storage",
       0.020, 0.01, "1 TB incl. ($5 base), then $0.01/GB",
       "$5/mo base includes 250 GB storage + 1 TB outbound transfer (Spaces CDN included); $0.02/GB storage & $0.01/GB overage.",
       base_usd=5.0, incl_storage_gb=250, free_egress_gb=1000),
    _p("bunny_net", "Bunny.net Edge Storage + CDN", "CDN & Edge Storage", False, True, True,
       "https://bunny.net/pricing/", "https://bunny.net/pricing/",
       0.010, 0.01, "$0.01/GB NA/EU CDN ($0.005 Volume)",
       "$0.01/GB single-zone storage (+$0.005/GB per replication zone); $0 origin egress into Bunny CDN ($0.01/GB NA/EU)."),
    _p("gcore", "Gcore Object Storage", "CDN & Edge Storage", False, True, True,
       "https://gcore.com/pricing/storage", "https://gcore.com/pricing/storage",
       0.0108, 0.01, "~$0.01/GB ($0 to Gcore CDN)",
       "S3-compatible storage in EU/US/Asia; $0 origin egress when delivered through Gcore CDN (~$0.01/GB blended egress)."),
    _p("scaleway", "Scaleway Object Storage", "Low-Egress Cloud", False, True, True,
       "https://www.scaleway.com/en/pricing/storage/", "https://status.scaleway.com/api/v2/status.json",
       0.011, 0.011, "75 GB free, then ~$0.011/GB",
       "EU sovereign Multi-AZ S3 (Paris/Amsterdam/Warsaw); first 75 GB/mo egress free, $0 transfer to Scaleway instances.", free_egress_gb=75),
    _p("ovhcloud", "OVHcloud Object Storage", "Low-Egress Cloud", False, True, True,
       "https://us.ovhcloud.com/public-cloud/prices/", "https://us.ovhcloud.com/public-cloud/prices/",
       0.0073, 0.011, "$0.011/GB public ($0 internal)",
       "Standard S3 object storage at $0.0073/GB; $0 internal vRack traffic and flat $0.011/GB public internet egress."),
    _p("akamai_linode", "Akamai / Linode Object Storage", "Low-Egress Cloud", False, True, False,
       "https://www.linode.com/pricing/", "https://api.linode.com/v4/object-storage/types",
       0.020, 0.005, "1 TB incl., then $0.005/GB",
       "Starts at $5/mo (250 GB + 1 TB outbound); pooled global outbound allowance with $0.005/GB ($5/TB) Akamai overage.", free_egress_gb=1000),
    _p("fastly", "Fastly Object Storage", "CDN & Edge Storage", True, True, False,
       "https://www.fastly.com/pricing", "https://www.fastly.com/pricing",
       0.015, 0.0, "$0.00/GB to Fastly CDN",
       "S3-compatible origin storage with $0.00/GB origin egress & $0 API request charges when fronted by Fastly CDN."),
]


def _atomic_write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=".egress_", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
            fh.flush()
            os.fsync(fh.fileno())
        os.chmod(tmp_path, 0o644)
        os.replace(tmp_path, str(path))
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def _calc_monthly_usd(p: dict[str, object], stored_tb: float, egress_tb: float) -> dict[str, float]:
    stored_gb = max(0.0, stored_tb * 1000.0)
    egress_gb = max(0.0, egress_tb * 1000.0)
    base_usd = float(p["base_monthly_usd"]) if (stored_gb > 0 or egress_gb > 0) else 0.0
    storage_usd = base_usd + max(0.0, stored_gb - float(p["included_storage_gb"])) * float(p["storage_per_gb"])
    mult = float(p["free_egress_mult"])
    free_cap_gb = (stored_gb * mult) if mult > 0.0 else float(p["free_egress_gb"])
    egress_usd = max(0.0, egress_gb - free_cap_gb) * float(p["egress_per_gb"])
    monthly_usd = round(storage_usd + egress_usd, 2)
    return {
        "storage_monthly_usd": round(storage_usd, 2),
        "egress_monthly_usd": round(egress_usd, 2),
        "monthly_total_usd": monthly_usd,
        "annual_total_usd": round(monthly_usd * 12.0, 2),
    }


def _fetch_aws_price_telemetry() -> dict[str, object]:
    req = urllib.request.Request(AWS_S3_INDEX_URL, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=12.0) as resp:
        raw = json.loads(resp.read(1_000_000).decode("utf-8", errors="replace"))
    us_east_url = str(((raw.get("regions") or {}).get("us-east-1") or {}).get("currentVersionUrl") or "")
    m = re.search(r"/AmazonS3/([^/]+)/", us_east_url)
    return {
        "source_url": AWS_S3_INDEX_URL,
        "format_version": str(raw.get("formatVersion") or "v1.0"),
        "publication_date_utc": str(raw.get("publicationDate") or ""),
        "offer_version": m.group(1) if m else "current",
        "aws_regions_indexed": len(raw.get("regions") or {}),
    }


def _probe_endpoint(provider: dict[str, object]) -> dict[str, object]:
    t0 = time.monotonic()
    status_code = 0
    try:
        req = urllib.request.Request(str(provider["probe_url"]), headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=8.0) as resp:
            status_code = int(getattr(resp, "status", 200))
            resp.read(512)
    except urllib.error.HTTPError as exc:
        status_code = int(exc.code)
    except Exception:
        status_code = 0
    return {"id": provider["id"], "http_status": status_code, "latency_ms": int(round((time.monotonic() - t0) * 1000)), "reachable": 200 <= status_code < 400}


def sync_egress_fees() -> dict[str, object]:
    now_dt = datetime.now(timezone.utc)
    now_utc = now_dt.strftime("%Y-%m-%d %H:%M UTC")
    aws_meta = _fetch_aws_price_telemetry()

    with concurrent.futures.ThreadPoolExecutor(max_workers=9) as pool:
        probes = {str(res["id"]): res for res in pool.map(_probe_endpoint, PROVIDERS)}

    aws_10_50 = _calc_monthly_usd(PROVIDERS[0], 10.0, 50.0)
    aws_20_50 = _calc_monthly_usd(PROVIDERS[0], 20.0, 50.0)

    enriched: list[dict[str, object]] = []
    reachable_cnt = 0
    for p in PROVIDERS:
        pr = probes.get(str(p["id"]), {"http_status": 0, "latency_ms": 0, "reachable": False})
        reachable_cnt += int(bool(pr["reachable"]))
        w_10_50 = _calc_monthly_usd(p, 10.0, 50.0)
        w_20_50 = _calc_monthly_usd(p, 20.0, 50.0)
        ann_save = round(max(0.0, aws_20_50["annual_total_usd"] - w_20_50["annual_total_usd"]), 2)
        save_pct = int(round((ann_save / aws_20_50["annual_total_usd"]) * 100)) if aws_20_50["annual_total_usd"] > 0 else 0
        row = {k: v for k, v in p.items() if k != "probe_url"}
        row.update({
            "probe_http_status": pr["http_status"],
            "probe_latency_ms": pr["latency_ms"],
            "verified_live": bool(pr["reachable"]),
            "workload_10tb_50tb": w_10_50,
            "workload_20tb_50tb": {**w_20_50, "annual_savings_vs_aws_usd": ann_save, "savings_vs_aws_pct": save_pct},
            "annual_savings_10tb_50tb_usd": round(max(0.0, aws_10_50["annual_total_usd"] - w_10_50["annual_total_usd"]), 2),
        })
        enriched.append(row)

    if len(enriched) < CIRCUIT_BREAKER_MIN_PROVIDERS or reachable_cnt < CIRCUIT_BREAKER_MIN_PROVIDERS:
        if OUT_JSON.exists():
            prev = json.loads(OUT_JSON.read_text(encoding="utf-8"))
            prev["stale_warning"] = True
            prev["last_failed_check_utc"] = now_utc
            _atomic_write_json(OUT_JSON, prev)
            return prev
        raise RuntimeError(f"Circuit breaker tripped: reachable={reachable_cnt}/{len(enriched)} (< {CIRCUIT_BREAKER_MIN_PROVIDERS})")

    enriched.sort(key=lambda r: float((r["workload_20tb_50tb"])["monthly_total_usd"]))
    low = enriched[0]
    payload: dict[str, object] = {
        "site": "CloudEgressFees.com",
        "updated_at_utc": now_utc,
        "updated_epoch": int(now_dt.timestamp()),
        "stale_warning": False,
        "aws_price_list_telemetry": aws_meta,
        "summary": {
            "providers_tracked": len(enriched),
            "providers_verified_live": reachable_cnt,
            "zero_egress_providers": sum(1 for r in enriched if r["zero_egress"]),
            "default_workload": "20 TB stored + 50 TB/mo egress",
            "aws_s3_20tb_50tb_monthly_usd": aws_20_50["monthly_total_usd"],
            "aws_s3_10tb_50tb_monthly_usd": aws_10_50["monthly_total_usd"],
            "lowest_20tb_50tb_provider": low["name"],
            "lowest_20tb_50tb_monthly_usd": (low["workload_20tb_50tb"])["monthly_total_usd"],
            "max_annual_savings_20tb_50tb_usd": (low["workload_20tb_50tb"])["annual_savings_vs_aws_usd"],
        },
        "providers": enriched,
    }
    _atomic_write_json(OUT_JSON, payload)
    _atomic_write_json(HISTORY_DIR / f"{now_dt.strftime('%Y-%m-%d')}.json", {
        "date_utc": now_dt.strftime("%Y-%m-%d"),
        "updated_at_utc": now_utc,
        "aws_offer_version": aws_meta["offer_version"],
        "summary": payload["summary"],
        "rates_snapshot": [
            {"id": r["id"], "storage_per_gb": r["storage_per_gb"], "egress_per_gb": r["egress_per_gb"],
             "monthly_20tb_50tb_usd": (r["workload_20tb_50tb"])["monthly_total_usd"]}
            for r in enriched
        ],
    })
    return payload


if __name__ == "__main__":
    out = sync_egress_fees()
    print(json.dumps({"updated_at_utc": out["updated_at_utc"], "aws_telemetry": out["aws_price_list_telemetry"], "summary": out["summary"]}, indent=2))
    sys.exit(0)
