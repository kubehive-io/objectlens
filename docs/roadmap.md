# Roadmap

ObjectLens is developed iteratively. Below is the active tracking manifest outline for completed features, active designs, and upcoming product cycles.

---

## Phase 1: PoC (Completed)

- [x] **Nuxt 4 Frontend:** Single-page dashboard built with Lang="ts" composition API and Lucide vectors.
- [x] **FastAPI Backend:** Fully asynchronous REST engine built with Pydantic validations.
- [x] **Ceph RGW Integration:** Specialized high-performance S3 client integration.
- [x] **Garage Provider:** Lightweight, air-gapped file storage client support.
- [x] **SQLite Catalog Index:** Local database-backed prefix and object metadata caching.
- [x] **Manual Bucket Scanning:** Synchronous S3 crawler to build active SQLite search records.
- [x] **Presigned Downloads:** On-the-fly secure download links generation.
- [x] **Inline File Previews:** View CSV, JSON, Parquet, and Image documents natively.
- [x] **Rich Text & Source Code Previews:** Inline viewing for UTF-8 logs, configs (`.yaml`, `.toml`), and code sources.

---

## Phase 2: Platform Integration & Security

- [x] **Declarative User Manifests:** Standard user YAML configs supporting custom roles.
- [x] **Granular RBAC Enforcements:** Stateless Basic Auth privilege separation between `admin` and `viewer` roles.
- [x] **Multi-Provider Connections:** Hot-swapping dynamically loaded connections configs.
- [x] **DB-Backed Audit Logs:** Persistent operation logging tracking directory deletions and uploads.
- [ ] **Background Workers:** Asynchronous task queue integration (Celery/RQ) to process scanning.
- [ ] **Kubernetes Helm Chart:** Standardised packaging for deployment (Available under `chart/`).
- [ ] **Postgres Metadata DB:** Support PostgreSQL for shared, clustered metadata deployments.
- [ ] **OIDC Login:** OpenID Connect authentication backend support.

---

## Phase 3: Scaling & Analytics

- [ ] **OpenSearch Metadata Integration:** Offload metadata search to OpenSearch clusters for large-scale operations.
- [ ] **S3 Event-Based Indexing:** Automatic, near-real-time index sync triggered by S3 bucket events.
- [ ] **Cursor-Based Pagination:** Transition from SQL offset pagination to cursor continuation tokens.
- [ ] **Virtualized UI Tables:** Render infinitely scrollable folders containing millions of records without DOM lag.
- [ ] **Active Index Refresh:** Background scheduled indexing jobs.
- [ ] **Resumable Uploads:** Chunked multi-part upload resume capability.

---

## Phase 4: Storage Intelligence & Enterprise

- [ ] **Ceph Dashboard Integration:** View Ceph cluster health, PG states, and disk utility graphs natively.
- [ ] **Storage Insights:** Identify abandoned, duplicated, or unaccessed files across prefixes automatically.
- [ ] **Lifecycle Recommendations:** Policy advice based on data coldness/access patterns.
- [ ] **Cost Visibility:** Budgeting summaries and data growth predictions.
