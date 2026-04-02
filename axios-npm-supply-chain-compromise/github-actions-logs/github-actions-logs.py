# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Fetch GitHub Actions jobs and logs for a repository (or entire org) within a date range."""

import argparse
import json
import subprocess
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path

DEFAULT_WORKERS = 10
DEFAULT_PUSHED_WITHIN_DAYS = 7


def gh_api_json(endpoint: str) -> dict:
    result = subprocess.run(
        ["gh", "api", endpoint], capture_output=True, text=True, check=True
    )
    return json.loads(result.stdout)


def gh_api_bytes(endpoint: str) -> bytes:
    result = subprocess.run(
        ["gh", "api", endpoint], capture_output=True, check=True
    )
    return result.stdout


def fetch_org_repos(org: str, pushed_after: str) -> list[str]:
    repos: list[str] = []
    page = 1
    cutoff = datetime.fromisoformat(pushed_after.replace("Z", "+00:00"))
    while True:
        data = gh_api_json(
            f"orgs/{org}/repos?sort=pushed&direction=desc&per_page=100&page={page}"
        )
        if not data:
            break
        for repo in data:
            pushed_at = datetime.fromisoformat(repo["pushed_at"].replace("Z", "+00:00"))
            if pushed_at < cutoff:
                return repos
            if not repo.get("archived", False):
                repos.append(repo["full_name"])
        page += 1
    return repos


def fetch_all_runs(repo: str, start: str, end: str) -> list[dict]:
    runs: list[dict] = []
    page = 1
    while True:
        data = gh_api_json(
            f"repos/{repo}/actions/runs?created={start}..{end}&per_page=100&page={page}"
        )
        batch = data.get("workflow_runs", [])
        if not batch:
            break
        runs.extend(batch)
        page += 1
    return runs


def fetch_jobs(repo: str, run_id: int) -> list[dict]:
    data = gh_api_json(f"repos/{repo}/actions/runs/{run_id}/jobs?per_page=100")
    return data.get("jobs", [])


def download_logs(repo: str, run_id: int, dest: Path) -> bool:
    try:
        raw = gh_api_bytes(f"repos/{repo}/actions/runs/{run_id}/logs")
        with zipfile.ZipFile(BytesIO(raw)) as zf:
            zf.extractall(dest)
        return True
    except (subprocess.CalledProcessError, zipfile.BadZipFile):
        return False


def safe_dirname(name: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in name)


def process_repo(repo: str, start: str, end: str, output_dir: Path, workers: int):
    runs = fetch_all_runs(repo, start, end)
    if not runs:
        return

    print(f"\n{'='*60}")
    print(f"  {repo} — {len(runs)} run(s)")
    print(f"{'='*60}")

    for r in runs:
        conclusion = r.get("conclusion") or "in_progress"
        print(f"  Run #{r['run_number']} | ID: {r['id']} | {r['name']} | {r['status']}/{conclusion} | {r['created_at']}")

    print(f"\n  --- Jobs ---")
    with ThreadPoolExecutor(max_workers=workers) as pool:
        future_to_run = {
            pool.submit(fetch_jobs, repo, r["id"]): r for r in runs
        }
        for future in as_completed(future_to_run):
            r = future_to_run[future]
            for j in future.result():
                conclusion = j.get("conclusion") or "in_progress"
                completed = j.get("completed_at") or "running"
                print(f"    [#{r['run_number']} {r['name']}] {j['name']} | {j['status']}/{conclusion} | {j['started_at']} -> {completed}")

    repo_dir = output_dir / safe_dirname(repo)
    print(f"\n  --- Downloading logs to {repo_dir} ---")
    with ThreadPoolExecutor(max_workers=workers) as pool:
        future_to_run = {
            pool.submit(download_logs, repo, r["id"], repo_dir / safe_dirname(f"{r['run_number']}_{r['name']}")): r
            for r in runs
        }
        for future in as_completed(future_to_run):
            r = future_to_run[future]
            dirname = safe_dirname(f"{r['run_number']}_{r['name']}")
            if future.result():
                print(f"    Run #{r['run_number']} ({r['name']}) -> {repo_dir / dirname}")
            else:
                print(f"    Run #{r['run_number']} ({r['name']}) -> Failed (expired or still running)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("-r", "--repo", help="Single repo (owner/repo)")
    target.add_argument("--org", help="GitHub org — scans all non-archived repos")
    parser.add_argument("-s", "--start", required=True, help="Start UTC datetime (e.g. 2026-03-01T00:00:00Z)")
    parser.add_argument("-e", "--end", required=True, help="End UTC datetime (e.g. 2026-03-02T00:00:00Z)")
    parser.add_argument("-o", "--output", default="./gh-actions-logs", help="Output directory for logs")
    parser.add_argument("-w", "--workers", type=int, default=DEFAULT_WORKERS, help=f"Parallel threads (default: {DEFAULT_WORKERS})")
    parser.add_argument(
        "--pushed-within-days", type=int, default=DEFAULT_PUSHED_WITHIN_DAYS,
        help=f"Org mode: only consider repos pushed within this many days before --start (default: {DEFAULT_PUSHED_WITHIN_DAYS})",
    )
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.repo:
        repos = [args.repo]
    else:
        start_dt = datetime.fromisoformat(args.start.replace("Z", "+00:00"))
        cutoff = (start_dt - timedelta(days=args.pushed_within_days)).strftime("%Y-%m-%dT%H:%M:%SZ")
        print(f"Discovering repos in org '{args.org}' pushed after {cutoff} ...")
        repos = fetch_org_repos(args.org, cutoff)
        print(f"Found {len(repos)} candidate repo(s).")
        if not repos:
            return

    for repo in repos:
        process_repo(repo, args.start, args.end, output_dir, args.workers)

    print(f"\nDone. Logs saved in {output_dir}")


if __name__ == "__main__":
    main()
