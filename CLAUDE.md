# CLAUDE.md

This file gives Claude Code project context when working in this repo.

## Project: Ecosystem Valuation Engine (EVE)

EVE is a Streamlit-based geospatial analysis app for environmental researchers. It measures ecosystem growth by economically valuing ecosystem services (provisioning, regulating, cultural, supporting) across user-selected geographic areas, integrating satellite imagery with peer-reviewed economic valuation coefficients (ESVD/TEEB) to track changes over time.

Refer to `replit.md` for the full product/architecture description; this file is a quick map of the code.

## Tech stack

- Python 3.11 (`runtime.txt`, `pyproject.toml` requires `>=3.11`)
- Streamlit web UI, Folium + `streamlit-folium` for maps, Plotly for charts
- Pandas / NumPy for data; rasterio, pyproj, pystac-client for geospatial
- PostgreSQL via SQLAlchemy + psycopg2; Alembic for migrations
- Earth Engine / geemap, USGS landsatxplore, OpenLandMap STAC for satellite/landcover data
- Dependency manager: `uv` (lockfile at `uv.lock`); also a `Dockerfile` and `.replit` config

## Run / deploy

- Local dev: `streamlit run app.py --server.port 5000`
- Docker: `Dockerfile` builds the same Streamlit app
- Replit: workflow `🌱 Ecosystem Valuation Engine` runs the same command (`.replit`)
- Streamlit config: `.streamlit/config.toml`

## Environments and deployment workflow

Two Cloud Run environments live in GCP project `eve-solutions-482317`, region `us-central1`.

| | Production | Staging |
|---|---|---|
| Web service | `eve-valuation-engine` | `eve-valuation-engine-staging` |
| URL | https://eve-valuation-engine-1025191764754.us-central1.run.app | https://eve-valuation-engine-staging-1025191764754.us-central1.run.app |
| Access | public (`--allow-unauthenticated`) | **IAM-locked** (`--no-allow-unauthenticated`); needs `roles/run.invoker` |
| Lifecycle Job | `eve-account-lifecycle` (02:00 UTC) | `eve-account-lifecycle-staging` (03:00 UTC) |
| DB instance | `eve-db` (Cloud SQL) | same instance |
| DB database | `neondb` | `eve_staging` |
| Git branch | `main` | `staging` |
| Version | `vX.Y.Z beta` | `vX.Y.Z beta` (incremented per iteration) |

**Workflow:**

```
feature-branch → PR → staging → (test on staging URL) → PR → main
                       │                                   │
                       ↓ bash scripts/deploy_staging.sh    ↓ bash scripts/deploy_prod.sh
                staging service                       prod service
```

1. Work on a feature branch.
2. Open PR into `staging`, merge.
3. From `staging` branch: bump the version to the next `vX.Y.Z beta`, push, run `bash scripts/deploy_staging.sh`.
4. Test on the staging URL (need to be authenticated — see "Accessing staging" below).
5. When green: open PR `staging` → `main`. Merge.
6. From `main`: bump the version to the release `vX.Y.Z beta` — set the clean X.Y.Z release number, but **keep the `beta` suffix** (the app is still beta-stage) — push, run `bash scripts/deploy_prod.sh`.
7. If schema changed: run Alembic migration against the prod DB **before** the prod deploy (see `reference_local_migration.md` memory). Same migration must already have been run against `eve_staging` during step 3 testing.

Both deploy scripts use `cloudbuild.yaml` + Kaniko with registry-backed
layer caching, which makes code-only deploys finish in ~60–90 s instead
of 4–6 min. The cache lives in the
`cloud-run-source-deploy/eve-valuation-engine/cache` Artifact Registry
repo and is shared between staging and prod (same Dockerfile, same
deps, so warming the cache from a staging deploy also speeds up the
next prod deploy).

**Accessing staging (IAM-locked):**

Browser access requires Cloud IAP + Load Balancer (not set up); for now use one of:
- `gcloud run services proxy eve-valuation-engine-staging --region us-central1` → open `http://localhost:8080`
- Curl with auth header: `curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" <STAGING_URL>`

To grant another user access:
```
gcloud run services add-iam-policy-binding eve-valuation-engine-staging \
    --region us-central1 --member="user:someone@example.com" --role="roles/run.invoker"
```

**Deploy / setup scripts (`scripts/`):**

- `setup_staging_db.ps1` — one-time: creates `eve_staging` DB, runs Alembic up to head, revokes IP authorization.
- `setup_staging.sh` — one-time: creates staging Cloud Run service + Job + Scheduler, copies env vars from prod with `DATABASE_URL` repointed at `eve_staging` and `APP_BASE_URL` set to the staging URL.
- `deploy_staging.sh` — ongoing: builds via `cloudbuild.yaml` + Kaniko cache, then redeploys the staging service and Job from the resulting image.
- `deploy_prod.sh` — ongoing: same Kaniko build, redeploys the prod service.
- `deploy_staging.ps1` — PowerShell wrapper: runs `deploy_staging.sh`, then auto-launches the `gcloud run services proxy` in a new window and opens `http://localhost:8080` in the browser. Use `.\scripts\deploy_staging.ps1` from a PowerShell terminal in the repo root. `-SkipDeploy` opens the proxy + browser without re-deploying; `-Port 8090` changes the local port.
- `setup_lifecycle_job.sh` — one-time / re-runnable: prod lifecycle Job setup.
- `check_unverified.py` — entry point for both lifecycle Jobs (`python -m scripts.check_unverified`).

**Version bumping rule:** always bump the version string in **both** `app.py` (`version-text` span) and `utils/auth.py` (`<p class="ver">`) before any deploy — AND add a matching newest-first entry to `utils/changelog.py` (`CHANGELOG`) describing the user-visible changes in plain, non-technical language. The version bump and the changelog entry are a single inseparable step: never bump the version without adding the changelog entry. (The changelog feeds the "📋 Version Changelog" expander in Analysis Settings.)

## Repo layout

- `app.py` — main Streamlit entrypoint; the multi-ecosystem calculation pathway lives here (see "Multi-Ecosystem Calculation Architecture" in `replit.md`)
- `database.py` — SQLAlchemy models / DB access for `ecosystem_analyses`, `saved_areas`, `analysis_history`, `natural_capital_baselines`, `natural_capital_trends`
- `utils/` — active modules. Notable ones:
  - `precomputed_esvd_coefficients.py` — pre-computed ESVD coefficients (the engine's economic core); `calculate_ecosystem_values()` is the primary calc entry point
  - `ecosystem_services.py` — older calc helpers; per `replit.md`, several functions here are inactive/bypassed by the main flow in `app.py`
  - `country_gdp_2024.py` — World Bank 2024 GDP per capita data for regional adjustment (income elasticity method, bounded 0.4–2.5x)
  - `openlandmap_integration.py`, `openlandmap_stac_api.py`, `esa_landcover_codes.py` — land cover / ecosystem-type detection
  - `satellite_data.py`, `enhanced_satellite_simulator.py` — satellite bands + simulation for quality adjustment (NDVI, NDWI water masking)
  - `eei_api.py` — Ecosystem Ecological Integrity API client (https://eve-solutions-482317.uc.r.appspot.com); per-point EEI feeds default intactness multipliers
  - `usgs_integration.py`, `nominatim_geocoding.py` — external data clients
  - `natural_capital_metrics.py`, `analysis_helpers.py`, `sampling_utils.py`, `visualization.py`, `data_export.py`, `user_guidance.py`
- `data/` — `esvd_database.csv`, `data/sample_areas.json`
- `attached_assets/` — reference CSVs, screenshots, pasted notes; not imported by app code
- `assets/` — `header.png` used in UI
- `unused/` — legacy/backup/debug scripts and ad-hoc tests. Treat as dead code; do not edit unless explicitly asked
- `test_calculations.py` — root-level test script (the tests inside `unused/` are not part of an active suite)
- `esvd_coefficient_study_mappings.txt`, `detailed_esvd_study_value_mappings.txt` — provenance docs mapping coefficients to source studies
- `Dockerfile`, `.dockerignore`, `app.yaml`, `.replit` — deploy configs

## Conventions / things to know

- All monetary values are standardized to 2024 International dollars per hectare per year
- Regional adjustment formula: `1 + (elasticity × (country_GDP / global_GDP − 1))`, clipped to `[0.4, 2.5]`
- Multi-ecosystem path uses rounded percentages to keep calc consistent with UI display — preserve this when editing
- Default sample point count is 10 (dev speed); user-configurable 10–100
- **A scalar condition multiplier (EEI, or the manual intactness sliders) is NOT applied to cultural services.** `CONDITION_EXEMPT_CATEGORIES` in `utils/precomputed_esvd_coefficients.py` holds the exempt TEEB categories (currently `cultural`); the multiplier is applied to provisioning, regulating and supporting only. Cultural services are demand-driven — they follow the setting and who can reach it, not ecological condition — so a degraded urban park keeps its recreation value. Rationale and sources are in that constant's comment and in `replit.md`. This applies to **scalar mode only**: when an indicator set passes a per-sub-service **dict**, those are direct measurements and apply in full, cultural sub-services included. Preserve both halves when editing the service loop
- **EEI: zero ≠ missing.** A `0.0` integrity score is a real measurement (built-up land scores zero) and is applied. A *missing* value (open ocean, coverage gaps) leaves the ecosystem out of `ecosystem_eei`, which falls through to the optimistic 100% default — no conservative percentage is substituted, because none would be defensible for open ocean; the affected ecosystems are named in the EEI panel instead. Demo (fabricated) data is a third case, discarded with a conservative 50% fallback. The upstream EEI service must never use truthiness tests on integrity scores (that bug reported every city centre as null until 2026-08)
- **Urban Green/Blue multiplier (18% default) measures extent, not condition** — the share of an urban hectare that is blue-green infrastructure. EEI measures the *condition* of that share. They are orthogonal and both apply; this is not double-counting. Don't "simplify" one away
- Open water is **included** in natural capital totals. Sample points detected as ESA CCI code 210 ("Water bodies") pause the analysis and prompt the user to classify them in bulk as Ocean → `Marine`, Rivers/Lakes → `Rivers and Lakes`, or Coastal → `Coastal` (`app.py:5301-5372`); the chosen type's ESVD coefficients are then applied normally. Preserve this prompt when changing sampling/calc code. Note `Marine` points are skipped for country assignment and so receive **no** regional GDP adjustment (`app.py:960`), unlike the other two
- There is no NDWI water masking in the live calculation path. The NDWI code in `utils/natural_capital_metrics.py` (module never imported) and `utils/satellite_data.py` (reached only via `ecosystem_services.get_ecosystem_service_values`, which `app.py` imports but never calls) is dead
- `unused/` exists because of a long iterative history; prefer the active `utils/` modules and `app.py` pathways. Many filenames in `unused/` look authoritative (e.g. `precomputed_esvd_coefficients_backup.py`) — they are not
- App name in user-facing copy: "Ecosystem Valuation Engine" or "EVE" (not "Natural Capital Measurement Tool")

## When making changes

- Coefficient or methodology changes should be reflected in `replit.md` and the `*_mappings.txt` provenance files where relevant
- DB schema changes: use Alembic migrations (the dependency is present; check for an existing `alembic/` setup before adding one)
- Don't add new files into `unused/`. If something is being retired, leave a note in the commit message rather than moving it
