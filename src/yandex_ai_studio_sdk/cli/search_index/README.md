# vector-stores CLI

Command-line tool for creating Yandex AI Studio search indexes from various
file sources. Files are uploaded to Yandex Cloud and a vector search index
is built from them.

## Installation

```bash
# Base installation (local files and Confluence sources)
pip install yandex-ai-studio-sdk

# With Wikipedia / MediaWiki support
pip install "yandex-ai-studio-sdk[cli-wiki]"

# With Amazon S3 / Yandex Object Storage support
pip install "yandex-ai-studio-sdk[cli-s3]"

# All extras
pip install "yandex-ai-studio-sdk[cli-wiki,cli-s3]"
```

## Authentication

Every command requires a Yandex Cloud folder ID. Authentication is resolved
automatically in the following order — no `--auth` flag is required if any of
these is available:

1. `--auth` flag / `YC_API_KEY` / `YC_IAM_TOKEN` environment variable
2. `yc` CLI — if the [Yandex Cloud CLI](https://yandex.cloud/docs/cli/) is
   installed and configured, its credentials are used automatically
3. Compute metadata service — on Yandex Compute Cloud VMs authentication works
   out of the box with no configuration

| Option | Environment variable | Description |
|--------|----------------------|-------------|
| `--folder-id` | `YC_FOLDER_ID` | Yandex Cloud folder ID |
| `--auth` | `YC_API_KEY` | API key for explicit authentication |
| `--auth` | `YC_IAM_TOKEN` | IAM token for explicit authentication |

```bash
export YC_FOLDER_ID=b1g...
export YC_API_KEY=AQVN...
# or
export YC_IAM_TOKEN=t1.9euelZ...
```

## Usage

```
yandex-ai-studio vector-stores <subcommand> [OPTIONS] [ARGS]
```

### Subcommands

| Subcommand | Source |
|------------|--------|
| `local` | Local filesystem files |
| `s3` | Amazon S3 or S3-compatible object storage |
| `wiki` | MediaWiki instances (Wikipedia, etc.) |
| `confluence` | Atlassian Confluence (Cloud and on-premise) |

---

## local

Create a search index from local files.

```
yandex-ai-studio vector-stores local [OPTIONS] PATHS...
```

`PATHS` must be individual files. Directories are not accepted. Use shell
glob expansion to pass multiple files at once.

**Options**

| Option | Default | Description |
|--------|---------|-------------|
| `--max-file-size INT` | — | Skip files larger than this many bytes |

**Examples**

```bash
# Single file
yandex-ai-studio vector-stores local report.pdf

# Multiple files
yandex-ai-studio vector-stores local docs/intro.txt docs/guide.md

# All .txt and .md files via shell glob
yandex-ai-studio vector-stores local sample_docs/*.txt sample_docs/*.md

# Name the resulting index
yandex-ai-studio vector-stores local report.pdf --name "Q4 Report"
```

---

## s3

Create a search index from an S3 or S3-compatible bucket.

Requires the `cli-s3` extra (`pip install "yandex-ai-studio-sdk[cli-s3]"`).

```
yandex-ai-studio vector-stores s3 [OPTIONS] BUCKET
```

**Options**

| Option | Env var | Default | Description |
|--------|---------|---------|-------------|
| `--prefix TEXT` | — | `""` | Path prefix (folder) inside the bucket |
| `--endpoint-url URL` | — | — | Custom endpoint for S3-compatible storage |
| `--aws-access-key-id TEXT` | `AWS_ACCESS_KEY_ID` | — | Access key |
| `--aws-secret-access-key TEXT` | `AWS_SECRET_ACCESS_KEY` | — | Secret key |
| `--region-name TEXT` | `AWS_DEFAULT_REGION` | — | Region |
| `--include-pattern GLOB` | — | — | Include only matching keys (repeatable) |
| `--exclude-pattern GLOB` | — | — | Exclude matching keys (repeatable) |
| `--max-file-size INT` | — | — | Skip files larger than this many bytes |

**Examples**

```bash
# Entire bucket
yandex-ai-studio vector-stores s3 my-bucket

# Specific prefix
yandex-ai-studio vector-stores s3 my-bucket --prefix docs/

# Only PDF files
yandex-ai-studio vector-stores s3 my-bucket --include-pattern "*.pdf"

# Yandex Object Storage
yandex-ai-studio vector-stores s3 my-bucket \
  --endpoint-url https://storage.yandexcloud.net \
  --region-name ru-central1
```

---

## wiki

Create a search index from MediaWiki pages (Wikipedia and other wikis).

Requires the `cli-wiki` extra (`pip install "yandex-ai-studio-sdk[cli-wiki]"`).

```
yandex-ai-studio vector-stores wiki [OPTIONS] PAGE_URLS...
```

`PAGE_URLS` are standard MediaWiki page URLs containing `/wiki/` in the
path. Pass multiple URLs to include several pages in one index.

Authentication is optional for public wikis.

**Options**

| Option | Env var | Default | Description |
|--------|---------|---------|-------------|
| `--username TEXT` | `WIKI_USERNAME` | — | Wiki login (optional for public wikis) |
| `--password TEXT` | `WIKI_PASSWORD` | — | Wiki password (optional for public wikis) |
| `--export-format` | — | `text` | Page content format: `text`, `html`, or `markdown` |

**Examples**

```bash
# Single Wikipedia page
yandex-ai-studio vector-stores wiki \
  https://en.wikipedia.org/wiki/Machine_learning

# Multiple pages
yandex-ai-studio vector-stores wiki \
  https://en.wikipedia.org/wiki/Machine_learning \
  https://en.wikipedia.org/wiki/Neural_network \
  https://en.wikipedia.org/wiki/Transformer_(deep_learning_architecture)

# Export as Markdown
yandex-ai-studio vector-stores wiki \
  "https://en.wikipedia.org/wiki/Python_(programming_language)" \
  --export-format markdown

# Private wiki with credentials
yandex-ai-studio vector-stores wiki \
  https://wiki.example.com/wiki/Internal_docs \
  --username alice \
  --password secret
```

---

## confluence

Create a search index from Atlassian Confluence pages.

```
yandex-ai-studio vector-stores confluence [OPTIONS]
```

Authentication is optional for public Confluence instances.

**URL requirements.** The page URL must contain a numeric page ID in one
of the following positions:

```
# Confluence Cloud
https://your-domain.atlassian.net/wiki/spaces/SPACE/pages/123456/Page+Title

# On-premise viewpage URL
https://confluence.example.com/pages/viewpage.action?pageId=123456
```

URLs in the `/display/SPACE/Page+Title` format are **not** supported.

To find the numeric ID of a page:
- **Confluence Cloud**: the ID appears in the URL after `/pages/`.
- **On-premise**: open the page, click `...` (ellipsis) → *Page Information*.
  The URL in your browser will contain `?pageId=NNNNNN`.

**Options**

| Option | Env var | Default | Description |
|--------|---------|---------|-------------|
| `--page-url URL` | — | — | Page URL (required, repeatable) |
| `--base-url URL` | — | auto | Confluence root URL. Extracted from the first `--page-url` if omitted. |
| `--username TEXT` | `CONFLUENCE_USERNAME` | — | Email address (optional for public instances) |
| `--api-token TEXT` | `CONFLUENCE_API_TOKEN` | — | API token (optional for public instances) |
| `--export-format` | — | `pdf` | Page format: `pdf`, `html`, or `markdown` |
| `--no-verify` | — | false | Disable SSL certificate verification |

**Examples**

```bash
# Public Confluence page (no auth required)
yandex-ai-studio vector-stores confluence \
  --page-url "https://cwiki.apache.org/confluence/pages/viewpage.action?pageId=34840000"

# Multiple pages
yandex-ai-studio vector-stores confluence \
  --page-url "https://your-domain.atlassian.net/wiki/spaces/ENG/pages/111/Overview" \
  --page-url "https://your-domain.atlassian.net/wiki/spaces/ENG/pages/222/Architecture"

# Private instance with credentials
export CONFLUENCE_USERNAME=alice@example.com
export CONFLUENCE_API_TOKEN=ATATTxxx...
yandex-ai-studio vector-stores confluence \
  --page-url "https://your-domain.atlassian.net/wiki/spaces/ENG/pages/123456/Design"

# Export as HTML instead of PDF
yandex-ai-studio vector-stores confluence \
  --page-url "https://your-domain.atlassian.net/wiki/spaces/ENG/pages/123456/Design" \
  --export-format html
```

---

## Common options

All subcommands accept the following options.

### Connection

| Option | Env var | Description |
|--------|---------|-------------|
| `--folder-id TEXT` | `YC_FOLDER_ID` | Yandex Cloud folder ID |
| `--auth TEXT` | `YC_API_KEY` or `YC_IAM_TOKEN` | Authentication credential (optional, see [Authentication](#authentication)) |
| `--endpoint URL` | — | Custom API endpoint |

### Index settings

| Option | Default | Description |
|--------|---------|-------------|
| `--name TEXT` | — | Name for the created search index |
| `--metadata KEY=VALUE` | — | Metadata key-value pair (repeatable, max 16) |
| `--expires-after-days INT` | — | Index TTL in days |
| `--expires-after-anchor` | — | TTL start: `created_at` or `last_active_at` |
| `--max-chunk-size-tokens INT` | `800` | Maximum tokens per chunk |
| `--chunk-overlap-tokens INT` | `400` | Token overlap between adjacent chunks |
| `--poll-timeout INT` | `3600` | Seconds to wait for index creation to complete |

### Upload settings

| Option | Default | Description |
|--------|---------|-------------|
| `--max-concurrent-uploads INT` | `4` | Parallel upload tasks |
| `--skip-on-error` | false | Skip failed files instead of aborting |
| `--file-expires-after-seconds INT` | — | Uploaded file TTL in seconds |
| `--file-expires-after-anchor` | — | File TTL start: `created_at` or `last_active_at` |

### Output

| Option | Default | Description |
|--------|---------|-------------|
| `-v / -vv` | — | Increase log verbosity (INFO / DEBUG) |
| `--format` | `text` | Output format: `text` or `json` |

---

## Output

On success the command prints the search index ID and name:

```
Search index created successfully!
Search Index ID: fvt...
Name: my-index
```

With `--format json`:

```json
{"status": "success", "folder_id": "b1g...", "search_index": {"id": "fvt...", "name": "my-index"}}
```
