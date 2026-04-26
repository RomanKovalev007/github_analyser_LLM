import os
import httpx
import base64
from mcp_server.tools.cache import cached

GITHUB_API = "https://api.github.com"
FILE_SIZE_LIMIT = 100_000  # 100 KB

_headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
if token := os.getenv("GITHUB_TOKEN"):
    _headers["Authorization"] = f"Bearer {token}"


def _parse_repo(repo_url: str) -> tuple[str, str]:
    parts = repo_url.rstrip("/").split("/")
    return parts[-2], parts[-1]


async def _github_get(url: str) -> dict | list:
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=_headers, follow_redirects=True)
        r.raise_for_status()
        return r.json()


def _flatten_tree(tree: list) -> str:
    lines = []
    for item in sorted(tree, key=lambda x: (x["type"] == "blob", x["path"])):
        if item["type"] == "tree":
            prefix = "📁 "
        else:
            "📄 "
        lines.append(f"{prefix}{item['path']}")
    return "\n".join(lines)


@cached("structure")
async def get_repo_structure(repo_url: str) -> str:
    owner, repo = _parse_repo(repo_url)
    data = await _github_get(f"{GITHUB_API}/repos/{owner}/{repo}/git/trees/HEAD?recursive=1")
    if data.get("truncated"):
        return _flatten_tree(data["tree"]) + "\n\n⚠️ Tree truncated (repo too large)"
    return _flatten_tree(data["tree"])


@cached("file")
async def read_file(repo_url: str, file_path: str) -> str:
    owner, repo = _parse_repo(repo_url)
    data = await _github_get(f"{GITHUB_API}/repos/{owner}/{repo}/contents/{file_path}")

    if isinstance(data, list):
        return f"Path '{file_path}' is a directory, not a file"

    size = data.get("size", 0)
    if size > FILE_SIZE_LIMIT:
        return f"File too large ({size} bytes > {FILE_SIZE_LIMIT} limit). Consider reading a specific section."

    content = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
    return content


@cached("search")
async def search_files(repo_url: str, pattern: str) -> str:
    owner, repo = _parse_repo(repo_url)
    data = await _github_get(f"{GITHUB_API}/repos/{owner}/{repo}/git/trees/HEAD?recursive=1")
    pattern_lower = pattern.lower()
    matches = [
        item["path"]
        for item in data["tree"]
        if item["type"] == "blob" and pattern_lower in item["path"].lower()
    ]
    if not matches:
        return f"No files found matching '{pattern}'"
    return "\n".join(matches)


@cached("readme")
async def get_readme(repo_url: str) -> str:
    owner, repo = _parse_repo(repo_url)
    data = await _github_get(f"{GITHUB_API}/repos/{owner}/{repo}/readme")
    return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
