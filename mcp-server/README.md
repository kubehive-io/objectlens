# ObjectLens MCP Server

A Model Context Protocol (MCP) server that connects Large Language Models (LLMs) to the ObjectLens REST API. This allows AI assistants to browse S3-compatible buckets, search indexed S3 object metadata, and preview object contents directly.

## Configuration

The server is configured using environment variables:

| Environment Variable | Description | Default |
|---|---|---|
| `OBJECTLENS_API_URL` | Base URL of the ObjectLens REST API | `http://localhost:8000` |
| `OBJECTLENS_USERNAME` | Username for HTTP Basic Authentication | None |
| `OBJECTLENS_PASSWORD` | Password for HTTP Basic Authentication | None |

## Exposed Tools

The server exposes the following tools to the LLM:

- `list_providers`: List configured S3 storage providers.
- `get_default_provider`: Get connection details of the default/active provider.
- `list_buckets`: List S3 buckets for a specific provider.
- `list_bucket_objects`: List or search objects in a specific bucket with prefix and pagination.
- `get_object_metadata`: Retrieve detailed metadata (size, content-type, ETag, etc.) of an object.
- `get_object_preview`: Read the content/preview of an object (supports text, JSON, CSV, code, etc.).
- `search_objects`: Query indexed metadata globally or scoped to a bucket.
- `scan_bucket`: Trigger S3 bucket metadata scanning to sync metadata into ObjectLens database.
- `list_activities`: Fetch recent activity logs/operations from ObjectLens.

## Installation and Run

### Run with UV

You can run the server directly using `uv`:

```bash
# From this directory
uv run python server.py
```

Or run it remotely:

```bash
uv run --path /path/to/objectlens/mcp-server/server.py
```

### Docker

Build the Docker image:

```bash
docker build -t objectlens-mcp-server .
```

Run the container:

```bash
docker run -i --rm \
  -e OBJECTLENS_API_URL="http://host.docker.internal:8000" \
  objectlens-mcp-server
```

*(The `-i` flag is required because the MCP server communicates over standard input/output).*

## Integration

### Claude Desktop

To integrate this server with Claude Desktop, add it to your configuration file:

* **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
* **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "objectlens": {
      "command": "uv",
      "args": [
        "run",
        "--path",
        "/path/to/objectlens/mcp-server/server.py"
      ],
      "env": {
        "OBJECTLENS_API_URL": "http://localhost:8000"
      }
    }
  }
}
```
