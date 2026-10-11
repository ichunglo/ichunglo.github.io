"""Check whether release evidence URLs still respond, without changing the data."""

from __future__ import annotations

import csv
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "data/generated/landscape.json"
ACCESS_AUDIT = ROOT / "data/curated/source-link-access-audit.csv"


def check(url: str) -> tuple[str, int | str, str]:
    request = Request(url, method="HEAD", headers={"User-Agent": "Mozilla/5.0 (compatible; landscape-source-audit/1.0)"})
    try:
        with urlopen(request, timeout=12) as response:
            return url, response.status, response.url
    except HTTPError as exc:
        if exc.code not in (403, 405):
            return url, exc.code, exc.url
    except (URLError, TimeoutError) as exc:
        return url, "unverified", str(exc.reason if isinstance(exc, URLError) else exc)

    # Some publication sites disallow HEAD even when their pages work.
    request = Request(url, method="GET", headers={"User-Agent": "Mozilla/5.0 (compatible; landscape-source-audit/1.0)", "Range": "bytes=0-0"})
    try:
        with urlopen(request, timeout=12) as response:
            return url, response.status, response.url
    except HTTPError as exc:
        return url, exc.code, exc.url
    except (URLError, TimeoutError) as exc:
        return url, "unverified", str(exc.reason if isinstance(exc, URLError) else exc)


def main() -> None:
    payload = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    urls = sorted({row["url"] for row in payload["sources"]})
    pubmed_urls = [url for url in urls if urlparse(url).netloc == "pubmed.ncbi.nlm.nih.gov"]
    invalid_pubmed = [url for url in pubmed_urls if not re.fullmatch(r"https://pubmed\.ncbi\.nlm\.nih\.gov/\d+/", url)]
    if invalid_pubmed:
        raise SystemExit(f"Malformed PubMed source URL: {invalid_pubmed}")
    # Avoid repeated live requests to NCBI, which rate-limited follow-up sweeps.
    probed_urls = [url for url in urls if url not in pubmed_urls]
    source_by_id = {row["source_id"]: row for row in payload["sources"]}
    with ACCESS_AUDIT.open(encoding="utf-8", newline="") as handle:
        reviewed = list(csv.DictReader(handle))
    if len({row["source_id"] for row in reviewed}) != len(reviewed):
        raise SystemExit("Duplicate source ID in the access audit")
    unknown = [row["source_id"] for row in reviewed if row["source_id"] not in source_by_id]
    if unknown:
        raise SystemExit(f"Access audit references unknown sources: {unknown}")
    reviewed_urls = {source_by_id[row["source_id"]]["url"] for row in reviewed if row["identity_result"] == "matched"}
    results = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(check, url) for url in probed_urls]
        for future in as_completed(futures):
            results.append(future.result())
    results.sort()
    accessible = [row for row in results if isinstance(row[1], int) and 200 <= row[1] < 400]
    broken = [row for row in results if row[1] in (404, 410)]
    restricted = [row for row in results if row[1] in (401, 403)]
    rate_limited = [row for row in results if row[1] == 429]
    restricted_reviewed = [row for row in restricted if row[0] in reviewed_urls]
    restricted_unreviewed = [row for row in restricted if row[0] not in reviewed_urls]
    other = [row for row in results if row not in accessible and row not in broken and row not in restricted and row not in rate_limited]
    print(json.dumps({
        "source_rows": len(payload["sources"]),
        "unique_urls": len(urls),
        "pubmed_urls_syntax_checked_not_live_probed": len(pubmed_urls),
        "accessible": len(accessible),
        "broken_404_or_410": broken,
        "access_restricted_count": len(restricted),
        "access_restricted_identity_matched": len(restricted_reviewed),
        "access_restricted_unreviewed": restricted_unreviewed,
        "rate_limited_count": len(rate_limited),
        "other_unverified": other,
    }, indent=2))
    if broken:
        raise SystemExit("One or more source URLs returned 404 or 410")
    if restricted_unreviewed:
        raise SystemExit("One or more access-restricted source URLs lack a citation-identity audit")


if __name__ == "__main__":
    main()
