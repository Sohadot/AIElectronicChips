# Public Launch Readiness Checklist

## Launch Status

- **Status:** Ready for quiet launch preparation
- **Audit date:** 2026-06-14
- **Sprint:** 5 — Public Launch Readiness / Indexation Hardening
- **Automated gate:** `scripts/validate_public_launch.py`

## Route Inventory

| Route | File | Indexable |
| --- | --- | --- |
| `/` | `index.html` | yes |
| `/compute-sovereignty/` | `compute-sovereignty/index.html` | yes |
| `/ai-chip-infrastructure/` | `ai-chip-infrastructure/index.html` | yes |
| `/sovereignty-stack/` | `sovereignty-stack/index.html` | yes |
| `/design-fabrication-packaging/` | `design-fabrication-packaging/index.html` | yes |
| `/hbm-memory/` | `hbm-memory/index.html` | yes |
| `/interconnects/` | `interconnects/index.html` | yes |
| `/power-and-thermal-limits/` | `power-and-thermal-limits/index.html` | yes |
| `/export-control-layer/` | `export-control-layer/index.html` | yes |
| `/chip-dependency-map/` | `chip-dependency-map/index.html` | yes |
| `/methodology/` | `methodology/index.html` | yes |
| `/sources/` | `sources/index.html` | yes |
| `/strategic-availability/` | `strategic-availability/index.html` | yes |

**Total public routes:** 13

## SEO Metadata Checklist

- [x] Every page has exactly one `h1`
- [x] Every page has a non-empty `<title>`
- [x] Every page has a `meta description`
- [x] Every page has a canonical URL on `https://aielectronicchips.com/`
- [x] Every page has `robots` meta set to `index, follow`
- [x] Every page has Open Graph basics (`og:type`, `og:site_name`, `og:title`, `og:description`, `og:url`)
- [x] Home page thesis remains visible in title and description

## Robots and Sitemap Checklist

- [x] `robots.txt` allows crawling (`Allow: /`)
- [x] `robots.txt` references `https://aielectronicchips.com/sitemap.xml`
- [x] `sitemap.xml` uses production domain URLs
- [x] All 13 public routes appear in `sitemap.xml`
- [x] No missing or extra sitemap routes
- [x] `sources/` remains indexable
- [x] `strategic-availability/` remains indexable and bounded

## GitHub Pages / Custom Domain Readiness

- [x] `CNAME` contains `aielectronicchips.com`
- [ ] GitHub Pages enabled on repository (manual)
- [ ] Custom domain configured in GitHub settings (manual)
- [ ] DNS `A` / `CNAME` records pointed to GitHub Pages (manual)
- [ ] HTTPS certificate active on custom domain (manual post-DNS)

## Accessibility Checklist

- [x] Skip link to main content on every page
- [x] Primary navigation present on every page
- [x] Pages readable without JavaScript
- [x] Heading hierarchy is reasonable (`h1` then `h2`/`h3`)
- [x] Internal links have visible text or `aria-label`
- [x] No images without alt text (no images currently used)

## Performance / Dependency Checklist

- [x] No external JavaScript
- [x] No frameworks or CDN scripts
- [x] No tracking dependencies
- [x] No external font CDN dependency
- [x] Local CSS only (`/assets/css/main.css`, `/assets/css/evidence.css`)
- [x] Inter listed only as a preferred system-ui fallback, not loaded externally

## Governance Validators Checklist

Run before launch:

```powershell
py scripts\validate_all.py
py scripts\validate_public_launch.py
py scripts\validate_source_registry.py
py scripts\validate_chip_dependency_model.py
py scripts\validate_strategic_offerings.py
```

- [x] All validators pass locally

## Pre-Launch Manual Review Checklist

- [ ] Open each route in a browser on desktop and mobile
- [ ] Confirm custom domain resolves to GitHub Pages
- [ ] Confirm canonical URLs render correctly on production host
- [ ] Submit sitemap in Google Search Console (optional, post-launch)
- [ ] Verify `agent@sohadot.com` inquiry mailto works from production
- [ ] Confirm strategic availability page still reads institutional, not sales-heavy

## Post-Launch Checks

- [ ] Crawl public routes and confirm HTTP 200
- [ ] Confirm no unexpected `noindex` on production
- [ ] Monitor Search Console indexing for core routes
- [ ] Re-run `validate_public_launch.py` after any HTML or sitemap change
- [ ] Re-run `validate_all.py` after any commercial-surface change

## Related Documents

- [Indexation Hardening Audit](INDEXATION_HARDENING_AUDIT.md)
- [Strategic Availability Trust Gate](STRATEGIC_AVAILABILITY_TRUST_GATE.md)
