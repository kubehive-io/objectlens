# MCP Server Overview

The Model Context Protocol (MCP) server for ObjectLens bridges Large Language Models (LLMs) and S3-compatible cloud storage. It exposes S3 catalog information, metadata search, and file content previews directly to AI tools as native capabilities.

By connecting an MCP-compatible AI assistant (like Claude Desktop, Cursor, or Gemini CLI) to ObjectLens, the model gains the ability to query S3 buckets, search files, and read file contents in real-time.

---

## Core Capabilities

- **Bucket and Provider Browsing**: Allows models to retrieve the list of configured S3 storage providers and list available S3 buckets.
- **Path and Prefix Navigation**: Allows models to walk S3 hierarchies (folders/prefixes) dynamically.
- **Metadata Search**: Integrates directly with the local SQLite database in ObjectLens to let models search files instantly across thousands of indexed metadata records.
- **On-Demand Indexing**: Enables models to trigger S3 bucket scans to index new objects and sync the ObjectLens database dynamically.
- **Content Previews**: Exposes file contents (supporting up to 1MB of text, JSON, CSV, or code) directly to the model, allowing it to inspect, analyze, or summarize files instantly.
- **Audit Logs**: Provides models with access to ObjectLens activity logs, giving them visibility into recent index scans, uploads, and deletions.

---

## Use Cases

### 1. Interactive Data Discovery
Instead of manually clicking through a web UI or typing `aws s3` CLI commands, you can ask the AI in plain English:
> *"What buckets do we have configured on our Ceph homelab, and what's inside the backup directory?"*

### 2. Context-Aware Code and Config Generation
If you have configuration schemas, YAML templates, or data structures stored in S3, the AI can preview those files directly to gather accurate context before writing code:
> *"Search for any JSON schemas inside the `schemas/` folder of the `prod-bucket`, read the latest version, and write a Python script to validate our input against it."*

### 3. S3 Troubleshooting and Auditing
When troubleshooting issues or monitoring S3 activity, the AI can search and read ObjectLens activity logs:
> *"Check the recent ObjectLens activities and let me know if any bucket metadata sync scans failed."*
