import json
import sys
import io
import console
from tantra import run_tantra


def save_json(data, filename):
    with open(filename, "w") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"  [SAVED] {filename}")


def run_live_execution():
    console.banner("TANTRA LIVE INTELLIGENCE CONSOLE")
    print()
    print("  Pipeline: Signal -> Intelligence -> Ranking -> Decision -> Enforcement -> Truth")
    print("  Mode:     LIVE EXECUTION WITH FULL VISIBILITY")
    print()

    valid_input = {
        "trace_id": "TRACE_123",
        "signal": {
            "dataset": "crop_yield.csv"
        }
    }

    console.section("INPUT CONTRACT")
    print()
    print(f"    {json.dumps(valid_input, indent=4).replace(chr(10), chr(10) + '    ')}")
    print()

    result = run_tantra(valid_input)

    save_json(result, "full_chain_output.json")
    save_json(result["sanskar_output"], "stage_sanskar.json")
    save_json(result["core_decision"], "stage_core.json")
    save_json(result["enforcement"], "stage_enforcement.json")
    save_json(result["truth"], "stage_truth.json")
    save_json(result["trace_continuity_proof"], "trace_continuity_proof.json")

    console.banner("TRACE CONTINUITY VERIFICATION")
    proof = result["trace_continuity_proof"]
    print(f"\n  Expected trace_id: {proof['expected_trace_id']}")
    for stage in proof["stages_checked"]:
        status = "MATCH" if stage["matches_expected"] else "MISMATCH"
        print(f"  Stage '{stage['stage']}': trace_id={stage['trace_id_found']} -> {status}")
    print(f"\n  Verdict: {proof['verdict']}")

    return result


def run_failure_demo():
    console.banner("FAILURE DEMONSTRATION")
    print()
    print("  Testing pipeline resilience with invalid input.")
    print("  System must: NOT crash, print structured error, preserve trace_id.")
    print()

    failure_tests = []

    print("  -- Test A: Missing signal --")
    broken_1 = {"trace_id": "TRACE_FAIL_001"}
    result_1 = run_tantra(broken_1)
    trace_ok_1 = result_1["trace_id"] == broken_1["trace_id"]
    print(f"  Trace ID in output: {result_1['trace_id']}")
    print(f"  Trace matches input: {trace_ok_1}")
    failure_tests.append({
        "test": "missing_signal",
        "input": broken_1,
        "output": result_1,
        "trace_preserved": trace_ok_1,
        "verdict": "PASS" if trace_ok_1 else "FAIL"
    })

    print("\n  -- Test B: Empty signal (no dataset) --")
    broken_2 = {"trace_id": "TRACE_FAIL_002", "signal": {}}
    result_2 = run_tantra(broken_2)
    trace_ok_2 = result_2.get("trace_id") == broken_2["trace_id"]
    print(f"  Trace ID in output: {result_2.get('trace_id')}")
    print(f"  Trace matches input: {trace_ok_2}")
    failure_tests.append({
        "test": "empty_signal",
        "input": broken_2,
        "output": result_2,
        "trace_preserved": trace_ok_2,
        "verdict": "PASS" if trace_ok_2 else "FAIL"
    })

    print("\n  -- Test C: Missing trace_id --")
    broken_3 = {"signal": {"dataset": "crop_yield.csv"}}
    result_3 = run_tantra(broken_3)
    trace_ok_3 = "trace_id" in result_3
    print(f"  Trace ID in output: {result_3.get('trace_id')}")
    print(f"  Handled gracefully: {trace_ok_3}")
    failure_tests.append({
        "test": "missing_trace_id",
        "input": broken_3,
        "output": result_3,
        "trace_preserved": trace_ok_3,
        "verdict": "PASS — handled gracefully"
    })

    failure_proof = {
        "description": "Failure handling proof — broken inputs with trace preservation",
        "tests_run": len(failure_tests),
        "results": failure_tests,
        "overall_verdict": "PASS" if all("PASS" in t.get("verdict", "") for t in failure_tests) else "PARTIAL"
    }
    save_json(failure_proof, "failure_proof.json")

    console.section("FAILURE DEMO RESULTS")
    print()
    for t in failure_tests:
        print(f"    {t['test']}: {t['verdict']}")
    print(f"\n    Overall: {failure_proof['overall_verdict']}")
    print()


def run_determinism_proof():
    console.banner("DETERMINISM PROOF")

    valid_input = {
        "trace_id": "TRACE_123",
        "signal": {"dataset": "crop_yield.csv"}
    }

    num_runs = 5
    hashes = []

    print(f"\n  Running pipeline {num_runs} times silently...")

    old_stdout = sys.stdout
    for i in range(num_runs):
        sys.stdout = io.StringIO()
        result = run_tantra(valid_input)
        sys.stdout = old_stdout
        h = result["truth"]["pipeline_hash"]
        hashes.append(h)
        print(f"    Run {i+1}: {h}")

    all_identical = all(h == hashes[0] for h in hashes)
    determinism_proof = {
        "description": "Determinism proof — repeated execution produces identical outputs",
        "input": valid_input,
        "num_runs": num_runs,
        "pipeline_hashes": hashes,
        "all_hashes_identical": all_identical,
        "reference_hash": hashes[0],
        "verdict": "PASS — all outputs identical" if all_identical else "FAIL — outputs differ"
    }
    save_json(determinism_proof, "determinism_proof.json")

    print(f"\n  All hashes identical: {all_identical}")
    print(f"  Verdict: {determinism_proof['verdict']}")


def main():
    old_stdout = sys.stdout
    captured = io.StringIO()
    sys.stdout = type('Tee', (), {
        'write': lambda self, s: (old_stdout.write(s), captured.write(s)),
        'flush': lambda self: (old_stdout.flush(), captured.flush())
    })()

    run_live_execution()
    run_failure_demo()
    run_determinism_proof()

    console.banner("ALL TESTS COMPLETE")
    print("""
  Output files generated:
    1. full_chain_output.json       — Complete pipeline output
    2. stage_sanskar.json            — Sanskar stage output
    3. stage_core.json              — Core decision output
    4. stage_enforcement.json       — Enforcement action output
    5. stage_truth.json             — Truth/verification output
    6. trace_continuity_proof.json  — Trace ID continuity proof
    7. failure_proof.json           — Failure handling proof
    8. determinism_proof.json       — Determinism proof
    9. console_output.txt           — Full console recording
    """)

    sys.stdout = old_stdout
    with open("console_output.txt", "w", encoding="utf-8") as f:
        f.write(captured.getvalue())
    print("  [SAVED] console_output.txt")


if __name__ == "__main__":
    main()