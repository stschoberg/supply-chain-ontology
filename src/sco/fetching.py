"""HTTP and provenance helpers shared by the data/<source>/fetch.py scripts."""

import hashlib
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

import truststore

# Use the OS certificate store, so fetches work behind proxies the OS already trusts.
truststore.inject_into_ssl()

USER_AGENT = "sco-pipelines (+https://github.com/stschoberg/supply-chain-ontology)"
RETRY_STATUSES = {429, 500, 502, 503, 504}


def request_json(url: str, body: dict | None = None, retries: int = 4) -> dict:
    """GET `url`, or POST `body` as JSON, retrying transient failures with exponential backoff."""
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, data=data, headers=headers)
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            if e.code not in RETRY_STATUSES or attempt == retries:
                detail = e.read().decode(errors="replace")[:500]
                raise RuntimeError(f"{e.code} from {url}: {detail}") from e
        except urllib.error.URLError:
            if attempt == retries:
                raise
        time.sleep(2**attempt)
    raise AssertionError("unreachable")


def download(url: str, dest: Path) -> None:
    """Stream `url` to `dest`, writing to a .part file first so a failed download leaves nothing."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + ".part")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=300) as resp, part.open("wb") as out:
        while chunk := resp.read(1 << 20):
            out.write(chunk)
    part.rename(dest)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest(path: Path, manifest: dict) -> None:
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
