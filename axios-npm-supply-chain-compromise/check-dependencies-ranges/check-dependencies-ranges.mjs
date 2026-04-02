#!/usr/bin/env node
// Usage: node check-dep-ranges.mjs [--target <dir>] <package> <version1> [version2...]
// Example: node check-dep-ranges.mjs --target ./my-project axios 0.30.4 1.14.1
//
// Checks if any dependency in your lockfile uses a version range
// that could resolve to the specified versions.
// Supports: package-lock.json, yarn.lock (classic + Berry), pnpm-lock.yaml

import { readFileSync, existsSync } from "fs";
import { join } from "path";
import { createRequire } from "module";

const require = createRequire(import.meta.url);
let satisfies;
try {
  satisfies = require("semver/functions/satisfies");
} catch {
  console.error("semver is required: npm install semver (or npx to run)");
  process.exit(1);
}

const args = process.argv.slice(2);
let targetDir = ".";
if (args[0] === "--target") {
  args.shift();
  targetDir = args.shift();
  if (!targetDir) {
    console.error("--target requires a directory path");
    process.exit(1);
  }
}

const [pkg, ...targets] = args;
if (!pkg || targets.length === 0) {
  console.error("Usage: node check-dep-ranges.mjs [--target <dir>] <package> <version1> [version2...]");
  process.exit(1);
}

function escapeRegex(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

// Returns Map<range, string[]> (range -> list of dependents)
function extractFromNpmLock() {
  const lock = JSON.parse(readFileSync(join(targetDir, "package-lock.json"), "utf8"));
  const ranges = new Map();

  const packages = lock.packages || {};
  for (const [path, entry] of Object.entries(packages)) {
    const allDeps = {
      ...entry.dependencies,
      ...entry.devDependencies,
      ...entry.optionalDependencies,
    };
    if (!allDeps[pkg]) continue;
    const range = allDeps[pkg];
    const source = path ? path.replace(/^node_modules\//, "") : "(root)";
    if (!ranges.has(range)) ranges.set(range, []);
    ranges.get(range).push(source);
  }

  return ranges;
}

function extractFromYarnLock() {
  const content = readFileSync(join(targetDir, "yarn.lock"), "utf8");
  const ranges = new Map();
  const escaped = escapeRegex(pkg);
  const lines = content.split("\n");

  // Berry format: "pkg@npm:^x.y.z" in resolution keys
  for (const m of content.matchAll(new RegExp(`${escaped}@npm:([^\\s",]+)`, "g"))) {
    const range = m[1];
    if (!ranges.has(range)) ranges.set(range, []);
  }

  // Classic format: find dependency blocks and track which package they belong to
  let currentBlock = null;
  for (const line of lines) {
    // Top-level block header (not indented), e.g.: some-package@^1.0.0:
    if (/^\S/.test(line) && line.endsWith(":")) {
      currentBlock = line.replace(/:$/, "").replace(/^["']|["']$/g, "");
    }
    // Indented dependency line, e.g.:   axios "^1.6.0"
    const depMatch = line.match(new RegExp(`^\\s+${escaped}\\s+"([^"]+)"`));
    if (depMatch) {
      const range = depMatch[1];
      if (!ranges.has(range)) ranges.set(range, []);
      if (currentBlock) {
        const source = currentBlock.replace(/@[^@]+$/, "");
        if (!ranges.get(range).includes(source)) {
          ranges.get(range).push(source);
        }
      }
    }
  }

  return ranges;
}

function extractFromPnpmLock() {
  const content = readFileSync(join(targetDir, "pnpm-lock.yaml"), "utf8");
  const ranges = new Map();
  const escaped = escapeRegex(pkg);
  const lines = content.split("\n");

  // Track current top-level package context for dependents
  let currentPkg = null;
  for (const line of lines) {
    // Top-level package entry (not indented or single-indent), e.g.: /some-package@1.0.0:
    const pkgMatch = line.match(/^  \/?([^:\s]+?)@[^:]+:/);
    if (pkgMatch) {
      currentPkg = pkgMatch[1];
    }
    // Dependency line, e.g.:     axios: ^1.6.0
    const depMatch = line.match(new RegExp(`['"]?${escaped}['"]?:\\s+([^\\s#]+)`));
    if (depMatch) {
      const range = depMatch[1].replace(/^['"]|['"]$/g, "");
      if (/^\d+\.\d+\.\d+$/.test(range)) continue;
      if (!ranges.has(range)) ranges.set(range, []);
      if (currentPkg && !ranges.get(range).includes(currentPkg)) {
        ranges.get(range).push(currentPkg);
      }
    }
  }

  return ranges;
}

// Detect lockfile and extract ranges
let ranges;
let lockType;
if (existsSync(join(targetDir, "package-lock.json"))) {
  lockType = "package-lock.json";
  ranges = extractFromNpmLock();
} else if (existsSync(join(targetDir, "yarn.lock"))) {
  lockType = "yarn.lock";
  ranges = extractFromYarnLock();
} else if (existsSync(join(targetDir, "pnpm-lock.yaml"))) {
  lockType = "pnpm-lock.yaml";
  ranges = extractFromPnpmLock();
} else {
  console.error(`No lockfile found in ${targetDir} (package-lock.json, yarn.lock, or pnpm-lock.yaml)`);
  process.exit(1);
}

console.log(`Lockfile: ${lockType}`);
console.log(`Checking ranges for "${pkg}" against: ${targets.join(", ")}\n`);

if (ranges.size === 0) {
  console.log(`No dependency on "${pkg}" found in ${lockType}`);
  process.exit(0);
}

let found = false;
for (const [range, dependents] of ranges) {
  const matching = targets.filter((v) => satisfies(v, range));
  if (matching.length > 0) {
    found = true;
    console.log(`🚨 ${range} → VULNERABLE (matches ${matching.join(", ")})`);
    if (dependents.length > 0) {
      for (const dep of dependents) {
        console.log(`   └── required by: ${dep}`);
      }
    }
  } else {
    console.log(`✅ ${range} → ok`);
    if (dependents.length > 0) {
      console.log(`   └── from: ${dependents.join(", ")}`);
    }
  }
}

process.exit(found ? 1 : 0);
