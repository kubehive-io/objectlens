# Getting Started with MCP Server

This guide walks you through configuring, running, and integrating the ObjectLens Model Context Protocol (MCP) server with your local AI clients.

---

## Prerequisites

1. **Python 3.12+**: Ensure Python is installed on your local machine.
2. **ObjectLens Running**: The MCP server connects to the ObjectLens REST API. Make sure ObjectLens is running locally (defaulting to `http://localhost:8000`):
   ```bash
   just backend
   ```

---

## Configuration

The MCP server is configured entirely using environment variables.

| Environment Variable | Description | Default |
|---|---|---|
| `OBJECTLENS_API_URL` | Base URL of the ObjectLens REST API | `http://localhost:8000` |
| `OBJECTLENS_USERNAME` | Username for HTTP Basic Authentication | None |
| `OBJECTLENS_PASSWORD` | Password for HTTP Basic Authentication | None |

---

## Running the Server

### 1. Run with UV (Recommended)

Using `uv` is the simplest way to run the server. It handles downloading and installing dependencies in an isolated virtual environment automatically:

```bash
# Navigate to the mcp-server directory
cd mcp-server

# Run the server
uv run python server.py
```

### 2. Run with Docker

You can build and run the MCP server as a local Docker container.

Build the container image:
```bash
docker build -t objectlens-mcp-server ./mcp-server
```

Run the container:
```bash
docker run -i --rm \
  -e OBJECTLENS_API_URL="http://host.docker.internal:8000" \
  objectlens-mcp-server
```

*Note: The `-i` flag is required because the MCP server communicates over standard input/output.*

---

## Client Integration

### 1. Claude Desktop

To use the MCP server inside the Claude Desktop application, add it to your configuration file:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Add the `objectlens` server to the `mcpServers` object. Replace `/path/to/objectlens` with the absolute path to your repository clone:

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

*Ensure you restart the Claude Desktop application after saving changes to the configuration file.*

### 2. Cursor

To integrate the server with Cursor:

1. Open Cursor and navigate to **Settings** > **Features** > **MCP**.
2. Click **+ Add New MCP Server**.
3. Configure the settings:
   - **Name**: `ObjectLens`
   - **Type**: `command`
   - **Command**: `uv run --path /path/to/objectlens/mcp-server/server.py`
4. Click **Save**.

---

## Verifying Integration

Once connected, you can verify that the server is working by prompting the LLM:

- *"What storage providers are configured?"*
- *"List the S3 buckets that ObjectLens has access to."*
- *"Search for all .json files in the 'demo' bucket."*
