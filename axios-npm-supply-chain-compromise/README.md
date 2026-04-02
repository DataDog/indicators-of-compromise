# Indicators of compromise for the axios npm supply chain compromise

See https://securitylabs.datadoghq.com/articles/axios-npm-supply-chain-compromise/

## Identify if you're affected

We provide two helper scripts to help you identify a potential compromise due to the malicious versions 1.14.1 and 0.30.4 of Axios: 

- [Identify transitive dependencies that could have retrieved a malicious version](#identify-transitive-dependencies-that-could-have-retrieved-a-malicious-version)
- [Retrieve logs from GitHub Actions](#retrieve-logs-from-github-actions).


### Identify transitive dependencies that could have retrieved a malicious version

The scripts under [check-dependencies-ranges/](./check-dependencies-ranges/) allow you to list transitive dependencies of a target project on your filesystem, identify which ones use Axios, and check whether any of them use a version constraint that could have resolved to a malicious Axios version.

**Supported package managers**: npm, Yarn, pnpm.

**Requirements**: `semver` npm package.

**Usage**:

```
node check-dep-ranges.mjs [--target <dir>] <package> <version1> [version2...]
```

**Sample use**:

```bash
npm install semver
node check-dependencies-ranges/check-dependencies-ranges.mjs --target ~/workspace/your-project axios 1.14.1 0.30.4
```

**Sample output**:

```
Lockfile: yarn.lock
Checking ranges for "axios" against: 1.14.1, 0.30.4

🚨 ^1.6.0 → VULNERABLE (matches 1.14.1)
🚨 ^1.8.4 → VULNERABLE (matches 1.14.1)
✅ 1.12.2 → ok
```

In this case, the output confirms that a developer who ran `yarn install` during the Axios compromise window would have installed the malicious version 1.14.1.

### Retrieve logs from GitHub Actions

The scripts under [github-actions-logs/](./github-actions-logs/) allow you to identify all GitHub Actions workflows that ran when the malicious Axios versions were published, in order to analyze their logs and look for signs of compromise.

**Requirements**: GitHub CLI installed and authenticated.

**Usage**:

```
usage: github-actions-logs.py [-h] (-r REPO | --org ORG) -s START -e END [-o OUTPUT] [-w WORKERS] [--pushed-within-days PUSHED_WITHIN_DAYS]

Fetch GitHub Actions jobs and logs for a repository (or entire org) within a date range.

options:
  -h, --help            show this help message and exit
  -r REPO, --repo REPO  Single repo (owner/repo)
  --org ORG             GitHub org — scans all non-archived repos
  -s START, --start START
                        Start UTC datetime (e.g. 2026-03-01T00:00:00Z)
  -e END, --end END     End UTC datetime (e.g. 2026-03-02T00:00:00Z)
  -o OUTPUT, --output OUTPUT
                        Output directory for logs
  -w WORKERS, --workers WORKERS
                        Parallel threads (default: 10)
  --pushed-within-days PUSHED_WITHIN_DAYS
                        Org mode: only consider repos pushed within this many days before --start (default: 7)
```

**Sample use**:

```bash
# Pull logs for a specific repository
uv run github-actions-logs/github-actions-logs.py --repo ORG/REPO -o /tmp/logs --start 2026-03-31T00:21:00Z --end 2026-03-31T03:25:00Z

# Pull all logs for a specific organization (can be slow for large organizations)
uv run github-actions-logs/github-actions-logs.py --org ORG -o /tmp/logs --start 2026-03-31T00:21:00Z --end 2026-03-31T03:25:00Z

# Only include repositories that received pushes (to any branch) in the past 14 days
uv run github-actions-logs/github-actions-logs.py --org ORG -o /tmp/logs --pushed-within-days 14 --start 2026-03-31T00:21:00Z --end 2026-03-31T03:25:00Z
```

Sample output of a GitHub Actions workflow showing an `npm install` that pulled the malicious Axios version:

```
2026-03-31T03:04:40.4092421Z added 65 packages, and audited 66 packages in 3s
2026-03-31T03:04:40.4092867Z
2026-03-31T03:04:40.4093184Z 2 packages are looking for funding
2026-03-31T03:04:40.4095033Z   run `npm fund` for details
2026-03-31T03:04:40.4114077Z
2026-03-31T03:04:40.4114552Z 1 high severity vulnerability
2026-03-31T03:04:40.4114896Z
2026-03-31T03:04:40.4115175Z To address all issues, run:
2026-03-31T03:04:40.4115469Z   npm audit fix
2026-03-31T03:04:40.4115641Z
2026-03-31T03:04:40.4115780Z Run `npm audit` for details.
2026-03-31T03:04:40.4267123Z
2026-03-31T03:04:40.4268157Z + dc-polyfill@0.1.10
2026-03-31T03:04:40.4268754Z + import-in-the-middle@3.0.0
2026-03-31T03:04:40.4275840Z + axios@1.14.1
```

## Sources

- https://osv.dev/vulnerability/MAL-2026-2307
- https://github.com/advisories/GHSA-fw8c-xr5c-95f9
- https://github.com/axios/axios/issues/10604

## Additional sources of indicators of compromise

- https://www.invictus-ir.com/news/the-poisoned-pipeline-axios-supply-chain-attack
- https://www.stepsecurity.io/blog/axios-compromised-on-npm-malicious-versions-drop-remote-access-trojan
