# Vector Stores CLI

Command-line tool for creating Yandex AI Studio search indexes from various file sources. Files are uploaded to Yandex Cloud, processed, and used to build a vector search index. The following types of source data are supported:

- Local files
- Atlassian Confluence
- Amazon S3-compatible object storages such as Yandex Object Storage
- MediaWiki instances

## Installation

Install the base package and optional extras based on required data sources.

```bash
# Base installation with local files and Confluence support
pip install yandex-ai-studio-sdk

# With Amazon S3 / Yandex Object Storage support
pip install "yandex-ai-studio-sdk[cli-s3]"

# With Wikipedia / MediaWiki support
pip install "yandex-ai-studio-sdk[cli-wiki]"

# All extras
pip install "yandex-ai-studio-sdk[cli-wiki,cli-s3]"
```

> **Note**: Features are split into optional extras to reduce dependencies.

## Authentication

Authentication is resolved automatically in the following order. The `--auth` flag is not required if any method below is available.

1. Explicit credentials via `--auth`, `YC_API_KEY`, or `YC_IAM_TOKEN`.
2. Yandex Cloud CLI (`yc`) — if installed and configured.
3. Compute Metadata Service — on Yandex Compute Cloud VMs (automatic).

| Option        | Environment Variable     | Description                         |
|---------------|--------------------------|-------------------------------------|
| `--folder-id` | `YC_FOLDER_ID`           | Yandex Cloud folder ID (required)   |
| `--auth`      | `YC_API_KEY` or `YC_IAM_TOKEN` | API key or IAM token for authentication |

```bash
export YC_FOLDER_ID=b1gxxxxxxxxxxxxx
export YC_API_KEY=AQVNxxxxxxxxxxxxxx
# or
export YC_IAM_TOKEN=t1.9euelZxxxxxxxxxxxxxx
```

> **Note**: `YC_API_KEY` takes precedence over `YC_IAM_TOKEN` if both are set.

## Usage

```bash
yandex-ai-studio vector-stores <subcommand> [OPTIONS] [ARGS]
```

### Subcommands

| Subcommand   | Source                                                  |
|--------------|---------------------------------------------------------|
| `local`      | Local filesystem files                                  |
| `confluence` | Atlassian Confluence (Cloud or On-premise installation) |
| `s3`         | S3 or S3-compatible object storage                      |
| `wiki`       | MediaWiki instances (e.g., Wikipedia)                   |

## Local files

The `local` subcommand creates a search index from local files.

```bash
yandex-ai-studio vector-stores local [OPTIONS] PATHS...
```

`PATHS` must be individual files. Directories are not supported. Use shell globbing to include multiple files.

### Options

| Option                | Default | Description                                   |
|-----------------------|---------|-----------------------------------------------|
| `--max-file-size INT` | —       | Skip files larger than specified size (bytes) |

### Examples

```bash
# Index a single file
yandex-ai-studio vector-stores local report.pdf

# Index multiple files
yandex-ai-studio vector-stores local docs/intro.txt docs/guide.md

# Use shell glob to include all .txt and .md files
yandex-ai-studio vector-stores local sample_docs/*.txt sample_docs/*.md

# Specify a custom name for the index
yandex-ai-studio vector-stores local report.pdf --name "Q4 Report"
```

## Atlassian Confluence

The `confluence` subcommand creates a search index from Atlassian Confluence pages.

```bash
yandex-ai-studio vector-stores confluence [OPTIONS]
```

### URL Requirements

The page URL must contain a numeric page ID:

- **Confluence Cloud**:
  ```
  https://your-domain.atlassian.net/wiki/spaces/SPACE/pages/123456/Page+Title
  ```
- **On-premise**:
  ```
  https://confluence.example.com/pages/viewpage.action?pageId=123456
  ```

> **Unsupported**: URLs in `/display/SPACE/Page+Title` format.

To find the page ID:
- **Cloud**: Extract from URL after `/pages/`.
- **On-premise**: Open page → click `...` → *Page Information* → check URL for `?pageId=NNNNNN`.

### Options

| Option                     | Environment Variable       | Default | Description |
|----------------------------|----------------------------|---------|-------------|
| `--page-url URL`           | —                          | —       | Page URL (required, repeatable) |
| `--base-url URL`           | —                          | auto    | Confluence base URL (auto-detected from first `--page-url`) |
| `--username TEXT`          | `CONFLUENCE_USERNAME`      | —       | Email address (required for private instances) |
| `--api-token TEXT`         | `CONFLUENCE_API_TOKEN`     | —       | API token (required for private instances) |
| `--export-format TEXT`     | —                          | `pdf`   | Export format: `pdf`, `html`, or `markdown` |
| `--no-verify`              | —                          | `false` | Disable SSL certificate verification |

> **Note**: For Confluence Cloud, use email and API token. For on-premise, use local credentials unless otherwise configured.

### Examples

```bash
# Public Confluence page (no auth)
yandex-ai-studio vector-stores confluence \
  --page-url "https://cwiki.apache.org/confluence/pages/viewpage.action?pageId=34840000"

# Multiple pages
yandex-ai-studio vector-stores confluence \
  --page-url "https://your-domain.atlassian.net/wiki/spaces/ENG/pages/111/Overview" \
  --page-url "https://your-domain.atlassian.net/wiki/spaces/ENG/pages/222/Architecture"

# Private instance with environment variables
export CONFLUENCE_USERNAME=alice@example.com
export CONFLUENCE_API_TOKEN=ATATT3xFf...xxx
yandex-ai-studio vector-stores confluence \
  --page-url "https://your-domain.atlassian.net/wiki/spaces/ENG/pages/123456/Design"

# Export as HTML
yandex-ai-studio vector-stores confluence \
  --page-url "https://your-domain.atlassian.net/wiki/spaces/ENG/pages/123456/Design" \
  --export-format html
```

## Amazon S3-compatible object storages

The `s3` subcommand creates a search index from an S3-compatible bucket.

> **Requirement**: Install with `cli-s3` extra.

```bash
yandex-ai-studio vector-stores s3 [OPTIONS] BUCKET
```

### Options

| Option                      | Environment Variable         | Default | Description |
|-----------------------------|------------------------------|---------|-------------|
| `--prefix TEXT`             | —                            | `""`    | Filter objects by prefix (folder path) |
| `--endpoint-url URL`        | —                            | —       | Custom S3 endpoint (e.g., for Yandex Object Storage) |
| `--aws-access-key-id TEXT`  | `AWS_ACCESS_KEY_ID`          | —       | AWS/S3 access key ID |
| `--aws-secret-access-key TEXT` | `AWS_SECRET_ACCESS_KEY`   | —       | AWS/S3 secret access key |
| `--region-name TEXT`        | `AWS_DEFAULT_REGION`         | —       | AWS region name |
| `--include-pattern GLOB`    | —                            | —       | Include only keys matching glob pattern (can be repeated) |
| `--exclude-pattern GLOB`    | —                            | —       | Exclude keys matching glob pattern (can be repeated) |
| `--max-file-size INT`       | —                            | —       | Skip files larger than specified size (bytes) |

> **Note**: If credentials are not provided, the tool attempts to use AWS CLI configuration or IAM roles (on EC2/Yandex VMs).

### Examples

```bash
# Index entire bucket
yandex-ai-studio vector-stores s3 my-bucket

# Index only a specific prefix
yandex-ai-studio vector-stores s3 my-bucket --prefix docs/

# Include only PDF files
yandex-ai-studio vector-stores s3 my-bucket --include-pattern "*.pdf"

# Use Yandex Object Storage
yandex-ai-studio vector-stores s3 my-bucket \
  --endpoint-url https://storage.yandexcloud.net \
  --region-name ru-central1
```

## `wiki`

The `wiki` subcommand creates a search index from MediaWiki pages (e.g., Wikipedia).

> **Requirement**: Install with `cli-wiki` extra.

```bash
yandex-ai-studio vector-stores wiki [OPTIONS] PAGE_URLS...
```

`PAGE_URLS` must be valid MediaWiki URLs containing `/wiki/` in the path. Multiple URLs can be provided.

Authentication is optional for public wikis.

### Options

| Option               | Environment Variable | Default | Description |
|----------------------|----------------------|---------|-------------|
| `--username TEXT`    | `WIKI_USERNAME`      | —       | Wiki account username (required for private wikis) |
| `--password TEXT`    | `WIKI_PASSWORD`      | —       | Wiki account password |
| `--export-format TEXT` | —                  | `text`  | Output format: `text`, `html`, or `markdown` |

### Examples

```bash
# Index a single Wikipedia page
yandex-ai-studio vector-stores wiki https://en.wikipedia.org/wiki/Machine_learning

# Index multiple pages
yandex-ai-studio vector-stores wiki \
  https://en.wikipedia.org/wiki/Machine_learning \
  https://en.wikipedia.org/wiki/Neural_network \
  https://en.wikipedia.org/wiki/Transformer_(deep_learning_architecture)

# Export content as Markdown
yandex-ai-studio vector-stores wiki \
  "https://en.wikipedia.org/wiki/Python_(programming_language)" \
  --export-format markdown

# Access a private wiki with credentials
yandex-ai-studio vector-stores wiki \
  https://wiki.example.com/wiki/Internal_docs \
  --username alice \
  --password secret
```

## Common options

Available for all subcommands.

### Connection

| Option             | Environment Variable | Description |
|--------------------|----------------------|-------------|
| `--folder-id TEXT` | `YC_FOLDER_ID`       | Yandex Cloud folder ID (required) |
| `--auth TEXT`      | `YC_API_KEY` or `YC_IAM_TOKEN` | Explicit authentication token |
| `--endpoint URL`   | —                    | Override default API endpoint |

### Index settings

| Option                         | Default | Description |
|--------------------------------|---------|-------------|
| `--name TEXT`                  | —       | Name of the created search index |
| `--metadata KEY=VALUE`         | —       | Add metadata (up to 16 key-value pairs, repeatable) |
| `--expires-after-days INT`     | —       | Time-to-live (TTL) for the index in days |
| `--expires-after-anchor TEXT`  | —       | Start time for TTL: `created_at` or `last_active_at` |
| `--max-chunk-size-tokens INT`  | `800`   | Maximum number of tokens per text chunk |
| `--chunk-overlap-tokens INT`   | `400`   | Number of overlapping tokens between adjacent chunks |
| `--poll-timeout INT`           | `3600`  | Maximum time (seconds) to wait for index creation to complete |

### Upload settings

| Option                          | Default | Description |
|---------------------------------|---------|-------------|
| `--max-concurrent-uploads INT`  | `4`     | Maximum number of parallel file uploads |
| `--skip-on-error`               | `false` | Continue processing if a file fails to upload |
| `--file-expires-after-seconds INT` | —    | TTL for uploaded files (in seconds) |
| `--file-expires-after-anchor TEXT` | —       | Start time for file TTL: `created_at` or `last_active_at` |

### Output settings

| Option         | Default | Description |
|----------------|---------|-------------|
| `-v`           | —       | Log level: INFO |
| `-vv`          | —       | Log level: DEBUG |
| `--format TEXT`| `text`  | Output format: `text` or `json` |

## Output

On success, the command outputs the index ID and name.

### Text Output (default)

```
Search index created successfully!
Search Index ID: fvt-xxxxxxxxxxxxxxxx
Name: my-index
```

### JSON Output (`--format json`)

```json
{
  "status": "success",
  "folder_id": "b1gxxxxxxxxxxxxx",
  "search_index": {
    "id": "fvt-xxxxxxxxxxxxxxxx",
    "name": "my-index"
  }
}
```

> **Error Handling**: On failure, an error message is printed to stderr. With `--format json`, errors are returned in structured JSON format.
