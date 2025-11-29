#!/usr/bin/env python3
"""
Fuzzing campaign runner for the know CLI tool.
Executes fuzzing test graphs and reports results.
"""

import subprocess
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
from dataclasses import dataclass
import signal


@dataclass
class TestResult:
    """Container for a single test result."""
    graph_path: str
    graph_type: str  # spec, code, cross
    mutation_name: str
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration: float
    crashed: bool
    timed_out: bool
    error_category: Optional[str] = None


class FuzzingCampaign:
    """Orchestrates and tracks a fuzzing campaign."""

    def __init__(self, corpus_dir: Path, know_path: Optional[Path] = None):
        """
        Initialize fuzzing campaign.

        Args:
            corpus_dir: Path to corpus directory
            know_path: Path to know CLI tool (auto-detects if not provided)
        """
        self.corpus_dir = Path(corpus_dir)
        self.results: List[TestResult] = []
        self.crashes_dir = self.corpus_dir.parent / "crashes"
        self.crashes_dir.mkdir(exist_ok=True)

        # Auto-detect know path
        if know_path is None:
            know_path = Path(__file__).parent.parent.parent / "know" / "know"
        self.know_path = Path(know_path)

        if not self.know_path.exists():
            raise FileNotFoundError(f"know CLI not found at {self.know_path}")

    def run_test(self, graph_path: Path, timeout: int = 5) -> TestResult:
        """
        Run validation on a single graph.

        Args:
            graph_path: Path to test graph
            timeout: Timeout in seconds

        Returns:
            TestResult with execution details
        """
        # Determine graph type from corpus location
        relative_path = graph_path.relative_to(self.corpus_dir)
        graph_type = relative_path.parts[0]  # spec, code, or cross

        # Extract mutation name
        stem = graph_path.stem
        if graph_type == "cross":
            # Handle cross-graph pairs (spec and code)
            if stem.endswith("_spec"):
                mutation_name = stem[:-5]  # Remove _spec suffix
            elif stem.endswith("_code"):
                mutation_name = stem[:-5]  # Remove _code suffix
            else:
                mutation_name = stem
        else:
            mutation_name = stem

        command = [str(self.know_path), "-g", str(graph_path), "validate"]
        start_time = time.time()
        crashed = False
        timed_out = False
        exit_code = 0
        stdout = ""
        stderr = ""

        try:
            # Run know.py from the know directory
            know_dir = self.know_path.parent
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=know_dir
            )
            exit_code = result.returncode
            stdout = result.stdout
            stderr = result.stderr

        except subprocess.TimeoutExpired:
            timed_out = True
            stderr = f"Test timed out after {timeout} seconds"
            exit_code = -1

        except Exception as e:
            crashed = True
            stderr = str(e)
            exit_code = -1

        duration = time.time() - start_time

        test_result = TestResult(
            graph_path=str(graph_path),
            graph_type=graph_type,
            mutation_name=mutation_name,
            command=" ".join(command),
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration=duration,
            crashed=crashed,
            timed_out=timed_out
        )

        # Categorize errors
        if crashed:
            test_result.error_category = "crash"
        elif timed_out:
            test_result.error_category = "timeout"
        elif exit_code != 0:
            test_result.error_category = "validation_failed"
            # Try to extract error message
            if "error" in stderr.lower():
                # Extract first error line
                for line in stderr.split('\n'):
                    if "error" in line.lower():
                        test_result.error_category = f"validation_error: {line[:50]}"
                        break

        return test_result

    def run_corpus(self, graph_types: Optional[List[str]] = None, timeout: int = 5) -> None:
        """
        Run fuzzing campaign on entire corpus.

        Args:
            graph_types: List of graph types to test (spec, code, cross) or None for all
            timeout: Timeout per test in seconds
        """
        corpus = self.corpus_dir

        if graph_types is None:
            graph_types = ["spec", "code", "cross"]

        all_graphs = []

        for gtype in graph_types:
            gtype_dir = corpus / gtype
            if not gtype_dir.exists():
                continue

            if gtype == "cross":
                # Cross graphs come in pairs (spec and code)
                graphs = list(gtype_dir.glob("*.json"))
            else:
                graphs = list(gtype_dir.glob("*.json"))

            all_graphs.extend(graphs)

        print(f"Running {len(all_graphs)} test graphs...")
        print()

        for i, graph_path in enumerate(sorted(all_graphs), 1):
            print(f"[{i:3d}/{len(all_graphs)}] Testing {graph_path.relative_to(self.corpus_dir)}...", end=" ", flush=True)
            result = self.run_test(graph_path, timeout=timeout)
            self.results.append(result)

            if result.crashed or result.timed_out:
                print(f"CRASH/TIMEOUT")
                self._save_crash(result)
            elif result.exit_code != 0:
                print(f"FAIL (exit: {result.exit_code})")
            else:
                print(f"OK")

    def _save_crash(self, result: TestResult) -> None:
        """Save crashing/hanging test case to crashes directory."""
        relative_path = Path(result.mutation_name).with_suffix(".json")
        crash_path = self.crashes_dir / f"{result.mutation_name}_crash.json"

        # Copy original graph
        original_graph_path = Path(result.graph_path)
        if original_graph_path.exists():
            import shutil
            shutil.copy(original_graph_path, crash_path)

        # Save detailed crash report
        report_path = crash_path.with_suffix(".crash_report.json")
        crash_report = {
            "mutation_name": result.mutation_name,
            "graph_type": result.graph_type,
            "command": result.command,
            "exit_code": result.exit_code,
            "error_category": result.error_category,
            "stdout": result.stdout[:1000],  # Truncate
            "stderr": result.stderr[:1000],
            "duration": result.duration,
            "original_graph_path": result.graph_path
        }

        with open(report_path, 'w') as f:
            json.dump(crash_report, f, indent=2)

    def generate_report(self) -> Dict:
        """Generate comprehensive fuzzing report."""
        report = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_tests": len(self.results),
            "passed": sum(1 for r in self.results if r.exit_code == 0),
            "failed": sum(1 for r in self.results if r.exit_code != 0),
            "crashed": sum(1 for r in self.results if r.crashed),
            "timed_out": sum(1 for r in self.results if r.timed_out),
            "summary_by_type": {},
            "error_categories": defaultdict(int),
            "slowest_tests": [],
            "interesting_failures": []
        }

        # Aggregate by graph type
        by_type = defaultdict(lambda: {"passed": 0, "failed": 0, "crashed": 0, "timed_out": 0})
        for result in self.results:
            gtype = result.graph_type
            if result.exit_code == 0:
                by_type[gtype]["passed"] += 1
            else:
                by_type[gtype]["failed"] += 1
            if result.crashed:
                by_type[gtype]["crashed"] += 1
            if result.timed_out:
                by_type[gtype]["timed_out"] += 1

        report["summary_by_type"] = dict(by_type)

        # Count error categories
        for result in self.results:
            if result.error_category:
                report["error_categories"][result.error_category] += 1

        # Find slowest tests
        slowest = sorted(self.results, key=lambda r: r.duration, reverse=True)[:10]
        report["slowest_tests"] = [
            {
                "mutation": r.mutation_name,
                "duration": r.duration,
                "exit_code": r.exit_code
            }
            for r in slowest
        ]

        # Identify interesting failures (non-zero exit but no crash)
        interesting = [
            {
                "mutation": r.mutation_name,
                "graph_type": r.graph_type,
                "exit_code": r.exit_code,
                "error_category": r.error_category,
                "stderr_sample": r.stderr[:200]
            }
            for r in self.results
            if r.exit_code != 0 and not r.crashed and not r.timed_out
        ]
        report["interesting_failures"] = interesting[:20]

        return report

    def print_report(self) -> None:
        """Print human-readable report."""
        report = self.generate_report()

        print()
        print("=" * 80)
        print("FUZZING CAMPAIGN REPORT")
        print("=" * 80)
        print()

        print(f"Total Tests:        {report['total_tests']}")
        print(f"Passed:             {report['passed']:<3} ({report['passed']*100//report['total_tests']}%)")
        print(f"Failed:             {report['failed']:<3}")
        print(f"  - Crashed:        {report['crashed']}")
        print(f"  - Timed out:      {report['timed_out']}")
        print()

        print("Results by Graph Type:")
        for gtype, stats in sorted(report['summary_by_type'].items()):
            total = stats['passed'] + stats['failed']
            print(f"  {gtype:8s}: {stats['passed']:3d} passed, {stats['failed']:3d} failed "
                  f"(crashed: {stats['crashed']}, timeout: {stats['timed_out']})")
        print()

        if report['error_categories']:
            print("Error Categories:")
            for category, count in sorted(report['error_categories'].items(), key=lambda x: -x[1])[:15]:
                print(f"  {category:<50s}: {count:3d}")
            print()

        if report['slowest_tests']:
            print("Slowest Tests:")
            for test in report['slowest_tests'][:5]:
                print(f"  {test['mutation']:<50s}: {test['duration']:6.3f}s")
            print()

        if report['interesting_failures']:
            print("Interesting Failures (sample):")
            for failure in report['interesting_failures'][:5]:
                print(f"  {failure['mutation']:<40s} ({failure['graph_type']}) exit={failure['exit_code']}")
                if failure['stderr_sample']:
                    print(f"    {failure['stderr_sample'][:70]}")
            print()

        print("=" * 80)

    def save_report(self, output_path: Path) -> None:
        """Save detailed report as JSON."""
        report = self.generate_report()
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            # Custom JSON encoder to handle defaultdict
            report_clean = {
                k: dict(v) if isinstance(v, defaultdict) else v
                for k, v in report.items()
            }
            json.dump(report_clean, f, indent=2)

        print(f"Report saved to {output_path}")


def main():
    """Main entry point for fuzzing campaign."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Run fuzzing campaign on know CLI validation"
    )
    parser.add_argument(
        "--corpus",
        type=Path,
        default=Path(__file__).parent / "corpus",
        help="Path to test corpus directory"
    )
    parser.add_argument(
        "--know",
        type=Path,
        help="Path to know CLI tool (auto-detects if not provided)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=5,
        help="Timeout per test in seconds"
    )
    parser.add_argument(
        "--types",
        nargs="+",
        choices=["spec", "code", "cross"],
        help="Graph types to test (default: all)"
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="Path to save JSON report"
    )

    args = parser.parse_args()

    # First, generate corpus if it doesn't exist
    if not (args.corpus / "spec").exists():
        print("Generating test corpus...")
        from generator import generate_corpus
        generate_corpus(args.corpus.parent)
        print()

    # Run campaign
    campaign = FuzzingCampaign(args.corpus, know_path=args.know)
    campaign.run_corpus(graph_types=args.types, timeout=args.timeout)

    # Report results
    campaign.print_report()

    if args.report:
        campaign.save_report(args.report)

    # Exit with failure code if there were crashes
    if campaign.results:
        crashes = sum(1 for r in campaign.results if r.crashed)
        if crashes > 0:
            sys.exit(1)


if __name__ == "__main__":
    main()
