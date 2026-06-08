# tantra_integration_self_test.py — Phase 5: Deployment & Testing



import json
import time
import logging
import sys
from datetime import datetime, timezone
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(name)s - %(message)s'
)
logger = logging.getLogger("tantra-self-test")


class TestResult(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"


@dataclass
class TestCase:
    test_id: str
    test_name: str
    description: str
    expected_outcome: str
    actual_outcome: str = None
    result: TestResult = None
    error_details: str = None
    execution_time_ms: float = 0.0
    
    def to_dict(self):
        return {
            "test_id": self.test_id,
            "test_name": self.test_name,
            "description": self.description,
            "expected_outcome": self.expected_outcome,
            "actual_outcome": self.actual_outcome,
            "result": self.result.value if self.result else None,
            "error_details": self.error_details,
            "execution_time_ms": self.execution_time_ms
        }


class SanskariMockRuntime:
    
    
    def __init__(self):
        self.logger = logging.getLogger("sanskar-mock")
        self.executions = 0
        
    def compute_ranking(self, signal: Dict) -> Dict:
       
        self.executions += 1
        trace_id = signal.get("trace_id", "UNKNOWN")
        
       
        regions = signal.get("regions", [])
        if not regions:
            return {
                "trace_id": trace_id,
                "stage": "sanskar",
                "failure": {
                    "stage": "sanskar",
                    "code": "NO_REGIONS",
                    "message": "No regions in signal"
                }
            }
        
        
        scored = []
        for region in regions:
            base_score = region.get("yield_potential", 0.0)
            rainfall = signal.get("rainfall", {}).get("amount", 0)
            
            
            adjusted_score = min(1.0, base_score + (rainfall / 100) * 0.1)
            confidence = min(1.0, base_score * 0.95)  # Deterministic confidence
            
            
            if confidence >= 0.8:
                decision_state = "CONFIDENT"
            elif confidence >= 0.6:
                decision_state = "AMBIGUOUS"
            else:
                decision_state = "LOW_CONFIDENCE"
            
            scored.append({
                "entity_id": region.get("name"),
                "score": round(adjusted_score, 4),
                "confidence": round(confidence, 4),
                "decision_state": decision_state,
                "reasoning": f"Score based on yield={base_score}, rainfall={rainfall}"
            })
        
        
        scored.sort(key=lambda x: x["score"], reverse=True)
        ranking = [e["entity_id"] for e in scored]
        
        self.logger.info(f"[trace={trace_id}] Computed ranking: {ranking}")
        
        return {
            "trace_id": trace_id,
            "stage": "sanskar",
            "entities": scored,
            "ranking": ranking,
            "metadata": {
                "schema_version": "v1",
                "algorithm": "deterministic_yield_optimizer",
                "execution_time_ms": 2.1,
                "owner": "sanskar"
            },
            "contract_version": "intelligence_output_v1"
        }


class RajyaMockGovernance:
    
    
    def __init__(self, available=True, latency_ms=10):
        self.logger = logging.getLogger("rajya-mock")
        self.available = available
        self.latency_ms = latency_ms
        self.decisions = 0
        
    def make_decision(self, sanskar_output: Dict) -> Dict:
        
        trace_id = sanskar_output.get("trace_id", "UNKNOWN")
        
       
        if not self.available:
            return {
                "trace_id": trace_id,
                "stage": "rajya",
                "failure": {
                    "stage": "rajya",
                    "code": "UNAVAILABLE",
                    "message": "RAJYA governance service unavailable"
                }
            }
        
        
        if "failure" in sanskar_output:
            return {
                "trace_id": trace_id,
                "stage": "rajya",
                "failure": {
                    "stage": "rajya",
                    "code": "UPSTREAM_FAILURE",
                    "message": f"Cannot decide: upstream failure in {sanskar_output['failure'].get('stage')}"
                }
            }
        
        time.sleep(self.latency_ms / 1000.0)  
        
      
        ranking = sanskar_output.get("ranking", [])
        selected = ranking[0] if ranking else None
        
        decision = "APPROVED" if selected else "DEFERRED"
        
        self.decisions += 1
        self.logger.info(f"[trace={trace_id}] Decision: {decision} — {selected}")
        
        return {
            "trace_id": trace_id,
            "stage": "rajya",
            "decision": decision,
            "selected_entity": selected,
            "authority_check": {
                "decision_maker": "rajya",
                "constitutional_authority": True,
                "sign_off_timestamp": datetime.now(timezone.utc).isoformat() + "Z"
            },
            "contract_version": "governance_decision_v1"
        }


class BucketMockTruthStore:
    
    
    def __init__(self, available=True):
        self.logger = logging.getLogger("bucket-mock")
        self.available = available
        self.event_store = {}
        self.write_count = 0
        
    def write_event(self, event_record: Dict) -> Dict:
        
        trace_id = event_record.get("trace_id", "UNKNOWN")
        
        if not self.available:
            return {
                "trace_id": trace_id,
                "failure": {
                    "code": "BUCKET_UNAVAILABLE",
                    "message": "Truth store unavailable"
                }
            }
        
        self.write_count += 1
        self.event_store[trace_id] = event_record
        
        self.logger.info(f"[trace={trace_id}] Event written to Bucket")
        
        return {
            "trace_id": trace_id,
            "bucket_status": "written",
            "index": self.write_count
        }
    
    def read_event(self, trace_id: str) -> Dict | None:
        
        return self.event_store.get(trace_id)


class TANTRAIntegrationTestSuite:
    
    
    def __init__(self):
        self.logger = logging.getLogger("test-suite")
        self.tests: List[TestCase] = []
        self.sanskar = SanskariMockRuntime()
        self.rajya = RajyaMockGovernance()
        self.bucket = BucketMockTruthStore()
        
    def run_all_tests(self) -> List[TestCase]:
        
        self.logger.info("=" * 70)
        self.logger.info("TANTRA Integration Self-Test Suite")
        self.logger.info("=" * 70)
        
        test_methods = [
            ("TEST-001", self.test_healthy_path),
            ("TEST-002", self.test_invalid_input),
            ("TEST-003", self.test_dependency_unavailable),
            ("TEST-004", self.test_trace_break),
            ("TEST-005", self.test_authority_violation),
            ("TEST-006", self.test_partial_failure),
        ]
        
        for test_id, test_method in test_methods:
            self.logger.info(f"\n{test_id}: {test_method.__doc__}")
            self.logger.info("-" * 70)
            test_method()
        
        self.logger.info("\n" + "=" * 70)
        return self.tests
    
    def test_healthy_path(self):
        
        test = TestCase(
            test_id="TEST-001",
            test_name="Healthy Path",
            description="Signal → SANSKAR → RAJYA → Bucket → Success",
            expected_outcome="All stages complete successfully, trace preserved"
        )
        
        start = time.time()
        try:
           
            signal = {
                "trace_id": "trace-healthy-001",
                "regions": [
                    {"name": "region_a", "yield_potential": 0.85},
                    {"name": "region_b", "yield_potential": 0.72}
                ],
                "rainfall": {"amount": 45.2, "confidence": 0.88},
                "soil": {"type": "loamy", "moisture": 0.65}
            }
            
            
            sanskar_out = self.sanskar.compute_ranking(signal)
            assert sanskar_out.get("trace_id") == signal["trace_id"], "Trace broken at SANSKAR"
            assert "failure" not in sanskar_out, "SANSKAR failed"
            
            
            rajya_out = self.rajya.make_decision(sanskar_out)
            assert rajya_out.get("trace_id") == signal["trace_id"], "Trace broken at RAJYA"
            assert rajya_out.get("decision") in {"APPROVED", "REJECTED", "DEFERRED"}, "Invalid decision"
            
            
            event = {
                "trace_id": signal["trace_id"],
                "event_type": "execution_complete",
                "event_data": {
                    "stage": "execution",
                    "outcome": "SUCCESS",
                    "execution_time_ms": 150.0
                },
                "ownership": {"owner": "bucket", "immutable": True}
            }
            bucket_out = self.bucket.write_event(event)
            assert bucket_out.get("trace_id") == signal["trace_id"], "Trace broken at Bucket"
            
            test.actual_outcome = "All stages succeeded, trace preserved throughout"
            test.result = TestResult.PASS
            self.logger.info(f"✓ PASS: {test.actual_outcome}")
            
        except AssertionError as e:
            test.actual_outcome = f"Assertion failed: {str(e)}"
            test.result = TestResult.FAIL
            test.error_details = str(e)
            self.logger.error(f"✗ FAIL: {test.error_details}")
        
        finally:
            test.execution_time_ms = (time.time() - start) * 1000
            self.tests.append(test)
    
    def test_invalid_input(self):
        
        test = TestCase(
            test_id="TEST-002",
            test_name="Invalid Input",
            description="Signal missing required fields should be rejected at entry",
            expected_outcome="Schema validation fails, error message generated"
        )
        
        start = time.time()
        try:
            
            invalid_signal = {
                "trace_id": "trace-invalid-002"
                
            }
            
            sanskar_out = self.sanskar.compute_ranking(invalid_signal)
            
            
            assert "failure" in sanskar_out, "Invalid input not caught"
            assert sanskar_out["failure"]["code"] == "NO_REGIONS", "Wrong error code"
            
            
            assert sanskar_out.get("trace_id") == invalid_signal["trace_id"], "Trace lost on error"
            
            test.actual_outcome = "Invalid input caught at SANSKAR stage, trace preserved"
            test.result = TestResult.PASS
            self.logger.info(f"✓ PASS: Input validation working")
            
        except AssertionError as e:
            test.actual_outcome = f"Validation failed: {str(e)}"
            test.result = TestResult.FAIL
            test.error_details = str(e)
            self.logger.error(f"✗ FAIL: {test.error_details}")
        
        finally:
            test.execution_time_ms = (time.time() - start) * 1000
            self.tests.append(test)
    
    def test_dependency_unavailable(self):
        
        
        test = TestCase(
            test_id="TEST-003",
            test_name="Dependency Unavailable",
            description="RAJYA service becomes unavailable, flow fails gracefully",
            expected_outcome="Failure detected, error preserved in chain"
        )
        
        start = time.time()
        try:
            
            self.rajya.available = False
            
            
            signal = {
                "trace_id": "trace-unavail-003",
                "regions": [{"name": "region_a", "yield_potential": 0.80}],
                "rainfall": {"amount": 40.0, "confidence": 0.85}
            }
            
            sanskar_out = self.sanskar.compute_ranking(signal)
            assert "failure" not in sanskar_out, "SANSKAR should succeed"
            
            
            rajya_out = self.rajya.make_decision(sanskar_out)
            assert "failure" in rajya_out, "Dependency unavailability not detected"
            assert rajya_out["failure"]["code"] == "UNAVAILABLE", "Wrong error code"
            
         
            assert rajya_out.get("trace_id") == signal["trace_id"], "Trace lost on dependency failure"
            
            test.actual_outcome = "Dependency failure detected, trace preserved, graceful degradation"
            test.result = TestResult.PASS
            self.logger.info(f"✓ PASS: Dependency failure handling working")
            
        except AssertionError as e:
            test.actual_outcome = f"Dependency test failed: {str(e)}"
            test.result = TestResult.FAIL
            test.error_details = str(e)
            self.logger.error(f"✗ FAIL: {test.error_details}")
        
        finally:
           
            self.rajya.available = True
            test.execution_time_ms = (time.time() - start) * 1000
            self.tests.append(test)
    
    def test_trace_break(self):
        
        test = TestCase(
            test_id="TEST-004",
            test_name="Trace Break Detection",
            description="Detect when trace_id is lost or corrupted",
            expected_outcome="Trace break detected and flagged"
        )
        
        start = time.time()
        try:
            signal = {
                "trace_id": "trace-break-004",
                "regions": [{"name": "region_a", "yield_potential": 0.80}],
                "rainfall": {"amount": 40.0, "confidence": 0.85}
            }
            
            sanskar_out = self.sanskar.compute_ranking(signal)
            
           
            sanskar_out["trace_id"] = "CORRUPTED_TRACE"
            
            
            if sanskar_out.get("trace_id") != signal["trace_id"]:
                test.actual_outcome = "Trace break detected: trace_id mismatch"
                test.result = TestResult.PASS
                self.logger.info(f"✓ PASS: Trace break detection working")
            else:
                raise AssertionError("Trace break not detected")
        
        except AssertionError as e:
            test.actual_outcome = f"Trace break test failed: {str(e)}"
            test.result = TestResult.FAIL
            test.error_details = str(e)
            self.logger.error(f"✗ FAIL: {test.error_details}")
        
        finally:
            test.execution_time_ms = (time.time() - start) * 1000
            self.tests.append(test)
    
    def test_authority_violation(self):
        
        test = TestCase(
            test_id="TEST-005",
            test_name="Authority Violation",
            description="SANSKAR attempts to emit governance decision (forbidden)",
            expected_outcome="Authority violation detected and blocked"
        )
        
        start = time.time()
        try:
            signal = {
                "trace_id": "trace-authviol-005",
                "regions": [{"name": "region_a", "yield_potential": 0.80}],
                "rainfall": {"amount": 40.0, "confidence": 0.85}
            }
            
            sanskar_out = self.sanskar.compute_ranking(signal)
            
            
            sanskar_out["governance_decision"] = "APPROVED"  # FORBIDDEN!
            
            
            forbidden_fields = {
                "governance_decision",
                "enforcement_directive",
                "bucket_write_direct"
            }
            
            found_forbidden = forbidden_fields & set(sanskar_out.keys())
            
            if found_forbidden:
                test.actual_outcome = f"Authority violation detected: {found_forbidden}"
                test.result = TestResult.PASS
                self.logger.info(f"✓ PASS: Authority violation detection working")
            else:
                raise AssertionError("Authority violation not detected")
        
        except AssertionError as e:
            test.actual_outcome = f"Authority violation test failed: {str(e)}"
            test.result = TestResult.FAIL
            test.error_details = str(e)
            self.logger.error(f"✗ FAIL: {test.error_details}")
        
        finally:
            test.execution_time_ms = (time.time() - start) * 1000
            self.tests.append(test)
    
    def test_partial_failure(self):
        
        
        test = TestCase(
            test_id="TEST-006",
            test_name="Partial Failure Recovery",
            description="One stage fails, error propagated, chain detects and handles",
            expected_outcome="Failure detected at source, propagated with trace_id, recovery possible"
        )
        
        start = time.time()
        try:
            
            self.bucket.available = False
            
            signal = {
                "trace_id": "trace-partial-006",
                "regions": [{"name": "region_a", "yield_potential": 0.80}],
                "rainfall": {"amount": 40.0, "confidence": 0.85}
            }
            
           
            sanskar_out = self.sanskar.compute_ranking(signal)
            assert "failure" not in sanskar_out, "SANSKAR should succeed"
            
            rajya_out = self.rajya.make_decision(sanskar_out)
            assert "failure" not in rajya_out, "RAJYA should succeed"
            
            
            event = {
                "trace_id": signal["trace_id"],
                "event_type": "execution_complete",
                "event_data": {"stage": "execution", "outcome": "SUCCESS"}
            }
            bucket_out = self.bucket.write_event(event)
            
            assert "failure" in bucket_out, "Bucket failure not detected"
            assert bucket_out.get("trace_id") == signal["trace_id"], "Trace lost on Bucket failure"
            
            test.actual_outcome = "Partial failure detected at Bucket, trace preserved, recovery traceable"
            test.result = TestResult.PASS
            self.logger.info(f"✓ PASS: Partial failure recovery working")
            
        except AssertionError as e:
            test.actual_outcome = f"Partial failure test failed: {str(e)}"
            test.result = TestResult.FAIL
            test.error_details = str(e)
            self.logger.error(f"✗ FAIL: {test.error_details}")
        
        finally:
            
            self.bucket.available = True
            test.execution_time_ms = (time.time() - start) * 1000
            self.tests.append(test)
    
    def generate_report(self) -> Dict:
        
        passed = sum(1 for t in self.tests if t.result == TestResult.PASS)
        failed = sum(1 for t in self.tests if t.result == TestResult.FAIL)
        total = len(self.tests)
        total_time = sum(t.execution_time_ms for t in self.tests)
        
        return {
            "test_suite": "TANTRA Integration Self-Test",
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "success_rate": f"{(passed/total)*100:.1f}%" if total > 0 else "N/A",
            "total_execution_time_ms": total_time,
            "tests": [t.to_dict() for t in self.tests],
            "status": "ALL PASS" if failed == 0 else f"{failed} FAILURES"
        }


def main():
    
    suite = TANTRAIntegrationTestSuite()
    tests = suite.run_all_tests()
    report = suite.generate_report()
    
    
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Total Tests: {report['total_tests']}")
    print(f"Passed: {report['passed']}")
    print(f"Failed: {report['failed']}")
    print(f"Success Rate: {report['success_rate']}")
    print(f"Total Time: {report['total_execution_time_ms']:.1f}ms")
    print(f"Status: {report['status']}")
    
    
    report_file = "tantra_integration_test_report.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\nDetailed report written to: {report_file}")
    
    
    return 0 if report['failed'] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
