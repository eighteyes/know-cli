#!/usr/bin/env python3
# heatmap.py — Codemap Heat Index Generator
# Enriches codemap.json with deterministic hot/warm/cool scores per file and method.
#
# Responsibilities:
# - Gather git churn and recency data (file-level and method-level via diff-hunk intersection)
# - Compute LOC-based complexity from codemap line ranges
# - Build import graph from codemap imports and compute fan-in/fan-out centrality
# - Compute connectivity ripple from neighbor recency
# - Produce composite heat scores (0.0–1.0) bucketed to hot/warm/cool
#
# Usage:
#   python3 heatmap.py codemap.json --source-dir know/src --output codemap-heated.json
#   python3 heatmap.py codemap.json --source-dir know/src  # overwrites in place
#   cat codemap.json | python3 heatmap.py - --source-dir know/src

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone

WEIGHTS = {
    "churn": 0.30,
    "recency": 0.25,
    "complexity": 0.15,
    "centrality": 0.15,
    "ripple": 0.15,
}

WINDOW_DAYS = 90
HALF_LIFE_DAYS = 14


def _git_toplevel(source_dir):
    """Return (repo_root, prefix) where prefix is source_dir relative to repo root."""
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, cwd=source_dir,
    )
    if result.returncode != 0:
        return source_dir, ""
    root = result.stdout.strip()
    abs_source = os.path.abspath(source_dir)
    prefix = os.path.relpath(abs_source, root)
    if prefix == ".":
        prefix = ""
    else:
        prefix = prefix + "/"
    return root, prefix


def run_git(args, cwd):
    """Run a git command and return stdout lines."""
    result = subprocess.run(
        ["git"] + args,
        capture_output=True, text=True, cwd=cwd,
    )
    if result.returncode != 0:
        return []
    return result.stdout.strip().splitlines()


def _strip_prefix(path, prefix):
    """Strip source_dir prefix from git path to match codemap relative paths."""
    if prefix and path.startswith(prefix):
        return path[len(prefix):]
    return path


def gather_git_churn(source_dir, window_days=WINDOW_DAYS):
    """Return {relative_path: commit_count} for files changed in the window."""
    _, prefix = _git_toplevel(source_dir)
    lines = run_git(
        ["log", f"--since={window_days} days ago", "--format=format:", "--name-only", "--", "."],
        cwd=source_dir,
    )
    counts = defaultdict(int)
    for line in lines:
        line = _strip_prefix(line.strip(), prefix)
        if line:
            counts[line] += 1
    return dict(counts)


def gather_git_recency(source_dir):
    """Return {relative_path: days_since_last_commit}."""
    now = datetime.now(timezone.utc)
    _, prefix = _git_toplevel(source_dir)
    lines = run_git(
        ["log", "--format=%aI", "--name-only", "--", "."],
        cwd=source_dir,
    )
    last_date = {}
    current_date = None
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if re.match(r"^\d{4}-\d{2}-\d{2}T", line):
            current_date = line
        elif current_date and line:
            stripped = _strip_prefix(line, prefix)
            if stripped not in last_date:
                last_date[stripped] = current_date
    result = {}
    for path, date_str in last_date.items():
        try:
            dt = datetime.fromisoformat(date_str)
            days = (now - dt).total_seconds() / 86400
            result[path] = max(0, days)
        except (ValueError, TypeError):
            pass
    return result


def gather_method_git_history(source_dir, modules):
    """Use file-level diffs with line-range intersection for method-level history.

    Returns {(file, method_name): {"commits": int, "last_days": float}}
    """
    now = datetime.now(timezone.utc)
    method_ranges = {}  # {file: [(name, start, end), ...]}
    for mod in modules:
        path = mod["path"]
        entries = _all_callable_entries(mod)
        if not entries:
            continue
        # Estimate end_line: next function's start - 1, or start + 20 fallback
        sorted_entries = sorted(entries, key=lambda e: e["line"])
        ranges = []
        for i, entry in enumerate(sorted_entries):
            start = entry["line"]
            if i + 1 < len(sorted_entries):
                end = sorted_entries[i + 1]["line"] - 1
            else:
                end = start + 50  # fallback for last function
            ranges.append((entry["name"], start, end))
        method_ranges[path] = ranges

    result = {}
    for path, ranges in method_ranges.items():
        # Get diff hunks for this file in the window
        lines = run_git(
            ["log", f"--since={WINDOW_DAYS} days ago", "-p", "--format=%aI", "--", path],
            cwd=source_dir,
        )
        # Parse commits and their changed line ranges
        # Track per-method: which commit IDs touched it, and earliest date seen
        method_commits: dict[tuple[str, str], set[int]] = {}
        method_last_date: dict[tuple[str, str], str] = {}
        current_date = None
        current_commit_id = 0

        for line in lines:
            if re.match(r"^\d{4}-\d{2}-\d{2}T", line):
                current_date = line.strip()
                current_commit_id += 1
                continue

            # Diff hunk header: @@ -old,len +new,len @@
            hunk_match = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", line)
            if hunk_match:
                hunk_start = int(hunk_match.group(1))
                hunk_len = int(hunk_match.group(2) or 1)
                hunk_end = hunk_start + hunk_len - 1
                for name, mstart, mend in ranges:
                    if hunk_start <= mend and hunk_end >= mstart:
                        key = (path, name)
                        if key not in method_commits:
                            method_commits[key] = set()
                        method_commits[key].add(current_commit_id)
                        if key not in method_last_date and current_date:
                            method_last_date[key] = current_date

        for key, commits in method_commits.items():
            days = 999.0
            date_str = method_last_date.get(key)
            if date_str:
                try:
                    dt = datetime.fromisoformat(date_str)
                    days = max(0.0, (now - dt).total_seconds() / 86400)
                except (ValueError, TypeError):
                    pass
            result[key] = {"commits": len(commits), "last_days": days}

    return result


def _all_callable_entries(mod):
    """Get all functions + methods from a module."""
    entries = list(mod.get("functions", []))
    entries.extend(mod.get("methods", []))
    for cls in mod.get("classes", []):
        if isinstance(cls, dict) and "methods" in cls:
            entries.extend(cls["methods"])
    return entries


def compute_complexity(modules):
    """Return file_loc {path: line_count} and method_span {(path,name): span}."""
    file_loc = {}
    method_span = {}
    for mod in modules:
        path = mod["path"]
        entries = _all_callable_entries(mod)
        sorted_entries = sorted(entries, key=lambda e: e["line"]) if entries else []

        # File LOC: estimate from max line number
        max_line = 0
        for e in sorted_entries:
            max_line = max(max_line, e["line"])
        if max_line > 0:
            file_loc[path] = max_line + 30  # approximate: last function + some lines
        else:
            file_loc[path] = 1

        # Method span
        for i, entry in enumerate(sorted_entries):
            start = entry["line"]
            if i + 1 < len(sorted_entries):
                end = sorted_entries[i + 1]["line"] - 1
            else:
                end = start + 30
            method_span[(path, entry["name"])] = end - start

    return file_loc, method_span


def build_import_graph(modules):
    """Build fan_in/fan_out from codemap imports.

    Returns {path: {"fan_in": int, "fan_out": int}}
    """
    # Map module names/paths to canonical paths
    path_set = {mod["path"] for mod in modules}
    stem_to_path = {}
    for p in path_set:
        stem = os.path.splitext(os.path.basename(p))[0]
        stem_to_path[stem] = p

    fan_out = defaultdict(set)  # path -> set of paths it imports
    fan_in = defaultdict(set)   # path -> set of paths that import it

    for mod in modules:
        src = mod["path"]
        for imp in mod.get("imports", []):
            imp_name = imp.get("name", "")
            # Resolve to a known module path
            target = None
            if imp_name in stem_to_path:
                target = stem_to_path[imp_name]
            else:
                # Try dotted path: "graph" from "from graph import ..."
                parts = imp_name.split(".")
                for part in parts:
                    if part in stem_to_path:
                        target = stem_to_path[part]
                        break
            if target and target != src:
                fan_out[src].add(target)
                fan_in[target].add(src)

    result = {}
    for p in path_set:
        result[p] = {
            "fan_in": len(fan_in.get(p, set())),
            "fan_out": len(fan_out.get(p, set())),
        }
    return result, fan_out, fan_in


def compute_ripple(path, fan_out, fan_in, recency_scores):
    """Compute ripple score: max neighbor recency * decay factor."""
    def recency_score(p):
        days = recency_scores.get(p, 999)
        return 0.5 ** (days / HALF_LIFE_DAYS)

    upstream_max = 0.0
    for dep in fan_out.get(path, set()):
        upstream_max = max(upstream_max, recency_score(dep))

    downstream_max = 0.0
    for dep in fan_in.get(path, set()):
        downstream_max = max(downstream_max, recency_score(dep))

    return max(upstream_max * 0.5, downstream_max * 0.3)


def compute_heat(signals, weights=WEIGHTS):
    """Compute composite score and label from signal dict."""
    score = sum(weights[k] * signals.get(k, 0.0) for k in weights)
    score = min(1.0, max(0.0, score))
    if score > 0.66:
        label = "hot"
    elif score > 0.33:
        label = "warm"
    else:
        label = "cool"
    return {
        "score": round(score, 3),
        "label": label,
        "signals": {k: round(signals.get(k, 0.0), 3) for k in weights},
    }


def normalize(values, floor=0.0):
    """Normalize a dict's values to 0.0–1.0 range."""
    if not values:
        return {}
    max_val = max(values.values())
    if max_val <= 0:
        return {k: floor for k in values}
    return {k: v / max_val for k, v in values.items()}


def enrich_codemap(codemap, source_dir):
    """Main entry: enrich codemap dict with heat data."""
    modules = codemap.get("modules", [])
    if not modules:
        return codemap

    # 1. Git churn (file-level)
    raw_churn = gather_git_churn(source_dir)
    # Map codemap paths to git paths
    churn = {}
    for mod in modules:
        churn[mod["path"]] = raw_churn.get(mod["path"], 0)
    norm_churn = normalize(churn)

    # 2. Git recency (file-level)
    raw_recency = gather_git_recency(source_dir)
    recency_days = {}
    for mod in modules:
        recency_days[mod["path"]] = raw_recency.get(mod["path"], 999)
    recency_scores = {
        p: 0.5 ** (d / HALF_LIFE_DAYS) for p, d in recency_days.items()
    }

    # 3. Complexity (file-level)
    file_loc, method_span = compute_complexity(modules)
    norm_complexity = normalize(file_loc)

    # 4. Centrality
    centrality_data, fan_out_graph, fan_in_graph = build_import_graph(modules)
    raw_centrality = {
        p: d["fan_in"] + d["fan_out"] for p, d in centrality_data.items()
    }
    norm_centrality = normalize(raw_centrality)

    # 5. Ripple
    ripple_scores = {}
    for mod in modules:
        p = mod["path"]
        ripple_scores[p] = compute_ripple(p, fan_out_graph, fan_in_graph, recency_days)

    # 6. Method-level git history
    method_history = gather_method_git_history(source_dir, modules)
    max_method_churn = max((v["commits"] for v in method_history.values()), default=1)
    max_method_span = max(method_span.values(), default=1)

    # Enrich each module
    dist = {"hot": 0, "warm": 0, "cool": 0}
    all_file_heats = []
    all_method_heats = []

    for mod in modules:
        p = mod["path"]
        file_signals = {
            "churn": norm_churn.get(p, 0.0),
            "recency": recency_scores.get(p, 0.0),
            "complexity": norm_complexity.get(p, 0.0),
            "centrality": norm_centrality.get(p, 0.0),
            "ripple": ripple_scores.get(p, 0.0),
        }
        file_heat = compute_heat(file_signals)
        mod["heat"] = file_heat
        dist[file_heat["label"]] += 1
        all_file_heats.append((p, file_heat["score"]))

        # Method-level heat
        for fn_list_key in ("functions", "methods"):
            for fn in mod.get(fn_list_key, []):
                key = (p, fn["name"])
                mh = method_history.get(key, {"commits": 0, "last_days": 999})
                ms = method_span.get(key, 10)
                method_signals = {
                    "churn": mh["commits"] / max_method_churn if max_method_churn else 0,
                    "recency": 0.5 ** (mh["last_days"] / HALF_LIFE_DAYS),
                    "complexity": ms / max_method_span if max_method_span else 0,
                    "centrality": norm_centrality.get(p, 0.0),  # inherited
                    "ripple": ripple_scores.get(p, 0.0),  # inherited
                }
                fn_heat = compute_heat(method_signals)
                fn["heat"] = fn_heat
                all_method_heats.append((f"{p}:{fn['name']}", fn_heat["score"]))

    # Sort for top lists
    all_file_heats.sort(key=lambda x: x[1], reverse=True)
    all_method_heats.sort(key=lambda x: x[1], reverse=True)

    codemap["heat_summary"] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "window_days": WINDOW_DAYS,
        "half_life_days": HALF_LIFE_DAYS,
        "weights": WEIGHTS,
        "distribution": dist,
        "hottest_files": [p for p, _ in all_file_heats[:5]],
        "hottest_methods": [m for m, _ in all_method_heats[:5]],
    }

    return codemap


def main():
    parser = argparse.ArgumentParser(description="Enrich codemap.json with heat scores")
    parser.add_argument("codemap", help="Path to codemap.json (or - for stdin)")
    parser.add_argument("--source-dir", "-s", required=True, help="Source directory (git repo root for scanned files)")
    parser.add_argument("--output", "-o", help="Output path (default: overwrite input)")
    args = parser.parse_args()

    # Load codemap
    if args.codemap == "-":
        codemap = json.load(sys.stdin)
    else:
        with open(args.codemap) as f:
            codemap = json.load(f)

    # Enrich
    codemap = enrich_codemap(codemap, args.source_dir)

    # Write
    output_path = args.output or (args.codemap if args.codemap != "-" else None)
    if output_path:
        with open(output_path, "w") as f:
            json.dump(codemap, f, indent=2)
        print(f"Heatmap written to: {output_path}", file=sys.stderr)
    else:
        json.dump(codemap, sys.stdout, indent=2)

    # Print summary
    summary = codemap.get("heat_summary", {})
    dist = summary.get("distribution", {})
    print(f"  Hot: {dist.get('hot', 0)}  Warm: {dist.get('warm', 0)}  Cool: {dist.get('cool', 0)}", file=sys.stderr)


if __name__ == "__main__":
    main()
