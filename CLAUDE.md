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
| Version | `vX.Y.Z` | `vX.Y.Z-rcN` (release candidates) |

**Workflow:**

```
feature-branch → PR → staging → (test on staging URL) → PR → main
                       │                                   │
                       ↓ bash scripts/deploy_staging.sh    ↓ gcloud run deploy …
                staging service                       prod service
```

1. Work on a feature branch.
2. Open PR into `staging`, merge.
3. From `staging` branch: bump version to next `rcN`, push, run `bash scripts/deploy_staging.sh`.
4. Test on the staging URL (need to be authenticated — see "Accessing staging" below).
5. When green: open PR `staging` → `main`. Merge.
6. From `main`: bump version to clean `vX.Y.Z`, push, run prod deploy:
   ```
   gcloud run deploy eve-valuation-engine --source . --region us-central1 --platform managed --quiet
   ```
7. If schema changed: run Alembic migration against the prod DB **before** the prod deploy (see `reference_local_migration.md` memory). Same migration must already have been run against `eve_staging` during step 3 testing.

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
- `deploy_staging.sh` — ongoing: rebuilds Docker image + redeploys the staging service and Job.
- `deploy_staging.ps1` — PowerShell wrapper: runs `deploy_staging.sh`, then auto-launches the `gcloud run services proxy` in a new window and opens `http://localhost:8080` in the browser. Use `.\scripts\deploy_staging.ps1` from a PowerShell terminal in the repo root. `-SkipDeploy` opens the proxy + browser without re-deploying; `-Port 8090` changes the local port.
- `setup_lifecycle_job.sh` — one-time / re-runnable: prod lifecycle Job setup.
- `check_unverified.py` — entry point for both lifecycle Jobs (`python -m scripts.check_unverified`).

**Version bumping rule:** always bump the version string in **both** `app.py` (`version-text` span) and `utils/auth.py` (`<p class="ver">`) before any deploy.

## Repo layout

- `app.py` — main Streamlit entrypoint; the multi-ecosystem calculation pathway lives here (see "Multi-Ecosystem Calculation Architecture" in `replit.md`)
- `database.py` — SQLAlchemy models / DB access for `ecosystem_analyses`, `saved_areas`, `analysis_history`, `natural_capital_baselines`, `natural_capital_trends`
- `utils/` — active modules. Notable ones:
  - `precomputed_esvd_coefficients.py` — pre-computed ESVD coefficients (the engine's economic core); `calculate_ecosystem_values()` is the primary calc entry point
  - `ecosystem_services.py` — older calc helpers; per `replit.md`, several functions here are inactive/bypassed by the main flow in `app.py`
  - `country_gdp_2024.py` — World Bank 2024 GDP per capita data for regional adjustment (income elasticity method, bounded 0.4–2.5x)
  - `openlandmap_integration.py`, `openlandmap_stac_api.py`, `esa_landcover_codes.py` — land cover / ecosystem-type detection
  - `satellite_data.py`, `enhanced_satellite_simulator.py` — satellite bands + simulation for quality adjustment (NDVI, NDWI water masking)
  - `eei_api.py` — Ecosystem Ecological Integrity API client (https://api.ecosystemintegrity.com); per-point EEI feeds default intactness multipliers
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
- Open water is excluded from natural capital totals via NDWI masking — preserve this exclusion when changing sampling/calc code
- `unused/` exists because of a long iterative history; prefer the active `utils/` modules and `app.py` pathways. Many filenames in `unused/` look authoritative (e.g. `precomputed_esvd_coefficients_backup.py`) — they are not
- App name in user-facing copy: "Ecosystem Valuation Engine" or "EVE" (not "Natural Capital Measurement Tool")

## When making changes

- Coefficient or methodology changes should be reflected in `replit.md` and the `*_mappings.txt` provenance files where relevant
- DB schema changes: use Alembic migrations (the dependency is present; check for an existing `alembic/` setup before adding one)
- Don't add new files into `unused/`. If something is being retired, leave a note in the commit message rather than moving it
