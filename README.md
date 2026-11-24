# 💸 CloudEgressFees.com — Live Cloud Egress & Zero-Egress S3 Storage Index

Open, neutral FinOps benchmark and interactive bandwidth calculator comparing per-GB object storage rates, outbound internet egress fees (`$/GB`), free-egress multipliers, and retention caveats across 18 Cloud Object Storage, S3-compatible, and CDN providers.

- **Live Web Calculator**: [https://cloudegressfees.com](https://cloudegressfees.com)
- **Live JSON Feed**: [`/egress_fees.json`](https://cloudegressfees.com/egress_fees.json) (updated every 6 hours via GitHub Actions)
- **Daily Historical Snapshots**: `/history/YYYY-MM-DD.json`
- **Focused FinOps Benchmarks (`v5.0`)**: [`/zero-egress-cloud-storage/`](https://cloudegressfees.com/zero-egress-cloud-storage/) · [`/data-egress-costs/`](https://cloudegressfees.com/data-egress-costs/) · [`/cloudflare-r2-vs-aws-s3/`](https://cloudegressfees.com/cloudflare-r2-vs-aws-s3/) · [`/wasabi-vs-backblaze-b2/`](https://cloudegressfees.com/wasabi-vs-backblaze-b2/) · [`/eu-sovereign-s3-storage/`](https://cloudegressfees.com/eu-sovereign-s3-storage/)

## Tracked Cloud Storage & CDN Providers (18)
- **Zero-Egress S3 & Edge Storage**: Cloudflare R2, Wasabi Hot Cloud Storage, Backblaze B2, Tigris Data, Impossible Cloud, Fastly Object Storage.
- **Low-Egress Cloud & CDN Origins**: Storj, Hetzner Object Storage, Bunny.net Edge Storage + CDN, Gcore Object Storage, Scaleway Object Storage, OVHcloud Object Storage, Akamai / Linode Object Storage, Vultr Object Storage, DigitalOcean Spaces.
- **Hyperscaler Baselines**: AWS S3 Standard, Google Cloud Storage Standard, Microsoft Azure Blob Hot.

## Methodology
- Uses `1 TB = 1,000 GB` standard decimal cloud billing units.
- Queries the official public AWS Price List API (`AmazonS3/current/region_index.json`) for current publication metadata and probes official pricing/API endpoints every 6 hours.
- Surfaces objective engineering caveats alongside headline rates, including 90-day minimum storage retention policies, `3×` monthly stored free-egress multipliers, 1:1 active storage fair-use policies, and Class A/B API operation charges.
