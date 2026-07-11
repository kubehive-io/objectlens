# User Guide

Welcome to the ObjectLens User Guide. This guide covers how to browse S3 buckets, query and preview files, execute direct storage operations, and sign in securely when Role-Based Access Control (RBAC) is enabled.

---

## 1. Authentication & Security

Depending on how your ObjectLens administrator has configured the deployment, you will experience one of two security modes:

### Bypassed Authentication (`none`)
If `OBJECTLENS_AUTH_TYPE` is set to `none`, you will bypass the login screen entirely. You are granted full administrator privileges implicitly.

### Local User Authentication (`local`)
If `OBJECTLENS_AUTH_TYPE` is set to `local`, a full-screen login overlay secures the dashboard. You must log in using a standard YAML user manifest placed inside the `backend/data/users` configuration folder.

Default accounts populated on initial startup:
- **Administrator:** `admin` / `adminpassword` (Full read, index scan, upload, move, rename, and delete privileges).
- **Viewer:** `viewer` / `viewerpassword` (Read-only listing, global search, downloads, and previews).

---

## 2. Navigating Providers & Buckets

Once signed in, the **Overview Dashboard** serves as your control center.

### Discovering Storage Connections
ObjectLens dynamically aggregates configured storage providers (like AWS, Ceph, and Garage). 
* Click **Providers** in the sidebar to see connection endpoint details and SSL certificate status.
* Click **Buckets** to view all visible storage buckets dynamically fetched using your active S3 credentials.

### File Browser Navigation
Clicking any bucket opens the **S3-Style Pathing Browser**:
* **Subdirectories:** Folders are represented with a folder icon. Click any folder name to traverse deeper into the prefix path.
* **Breadcrumbs:** A borderless, inline breadcrumb navigation bar tracking the active location is pinned above the file table. Click any parent folder segment in the breadcrumb to traverse backward.

---

## 3. High-Fidelity Insights & Metrics

To view detailed statistics for any bucket, click **Details & Policies** inside the browser header.

The redesigned **Bucket Details** dashboard exposes:
* **Storage Metrics:** Styled summary cards outlining cached SQLite metadata records, total catalog sizes, and last indexing scan dates.
* **S3 Safe Settings Manifest:** Evaluates bucket versioning states, object lifecycles, and security policies.
* **Insight Columns:**
  * **Recent Changes:** A timeline representing recently uploaded or modified files.
  * **Largest Files:** Lists the largest storage items matching active indexes.
  * **Subdirectories:** Breaks down child prefix directory sizes.
  * *Tip: Click the arrow icon next to any listed item inside details to jump directly to its parent directory in the browser.*

---

## 4. Object Actions & Previews

ObjectLens provides standard, local file operations designed to keep latency minimal.

### Content Previews
You can preview supported formats inline without downloading files to your computer. Click **View Content Preview** inside the drawer to examine:
* **Text / Code:** View raw logs, Markdown, YAML configs, or programming sources (`.py`, `.go`, `.js`, etc.) with clean formatting.
* **Structured Data:** Renders beautiful interactive tables for CSV and JSON schemas.
* **Parquet:** Views large-scale tabular parquet datasets.
* **Images:** Renders PNG, JPEG, SVG, GIF, and WEBP formats directly.

### Uploading Files
1. Navigate to the desired bucket path in the browser.
2. Click **Upload Files** to open the wizard or simply **drag-and-drop** files directly anywhere over the browser dropzone.
3. Review your files, configure global S3 metadata headers (like `Cache-Control`), and click **Sign In/Upload** to start the transfer.

### Renaming & Moving Files
S3 does not support a native rename/move action. ObjectLens executes a safe "Copy-then-Delete" transaction under the hood:
* **Rename:** Click **Rename** to provide a new destination key or folder path.
* **Move:** Select multiple items, click **Move**, and input a target directory prefix. ObjectLens copies all items, validates the target sizes, and deletes the originals recursively.

### Prefix Merging
To merge directory branches, select folders, click **Merge**, and define a destination path. Specify conflict strategies (`fail`, `skip`, `overwrite`) to safeguard data integrity.

### Recursive Prefix Deletion
To purge an entire prefix directory tree, select a folder in the table and click **Delete**. ObjectLens recursively deletes S3 objects matching that prefix and automatically purges cached metadata catalog records inside SQLite.
