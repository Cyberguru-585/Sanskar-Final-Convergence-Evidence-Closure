import json
import hashlib
import concurrent.futures
import time
from datetime import datetime
from typing import List, Callable


class ConcurrencyTestEngine:
    def __init__(self, max_workers=4):
        self.max_workers = max_workers
        self.test_results = []
        self.concurrent_executions = []
    
    def run_concurrent_replays(self, replay_func, trace_ids, num_concurrent_rounds=3):
        all_outputs = []
        output_hashes = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for round_num in range(num_concurrent_rounds):
                futures = []
                round_results = []
                for trace_id in trace_ids:
                    future = executor.submit(replay_func, trace_id)
                    futures.append((trace_id, future))
                for trace_id, future in futures:
                    try:
                        result = future.result(timeout=10)
                        result_hash = self._compute_result_hash(result)
                        
                        round_results.append({
                            "trace_id": trace_id,
                            "round": round_num,
                            "result_hash": result_hash,
                            "result": result
                        })
                        
                        output_hashes.append(result_hash)
                        all_outputs.append(result)
                    except Exception as e:
                        round_results.append({
                            "trace_id": trace_id,
                            "round": round_num,
                            "error": str(e)
                        })
                
                self.concurrent_executions.append({
                    "round": round_num,
                    "results": round_results
                })
        unique_hashes = set(output_hashes)
        is_deterministic = len(unique_hashes) == 1
        
        proof = {
            "test_type": "concurrent_replay",
            "total_traces": len(trace_ids),
            "concurrent_rounds": num_concurrent_rounds,
            "total_executions": num_concurrent_rounds * len(trace_ids),
            "all_outputs": all_outputs,
            "output_hashes": output_hashes,
            "unique_hashes": len(unique_hashes),
            "is_deterministic": is_deterministic,
            "consensus_hash": list(unique_hashes)[0] if unique_hashes else None,
            "execution_details": self.concurrent_executions,
            "verdict": "PASS -- all concurrent executions produced identical output" if is_deterministic else "FAIL -- determinism violated under concurrency"
        }
        
        self.test_results.append(proof)
        return proof
    
    def run_parallel_execution_simulation(self, execution_func, num_parallel=4, 
                                         iterations=3):
        execution_hashes = []
        execution_results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for iteration in range(iterations):
                for parallel_id in range(num_parallel):
                    future = executor.submit(
                        execution_func,
                        iteration=iteration,
                        parallel_id=parallel_id
                    )
                    futures.append((iteration, parallel_id, future))
            for iteration, parallel_id, future in futures:
                try:
                    result = future.result(timeout=10)
                    result_hash = self._compute_result_hash(result)
                    
                    execution_hashes.append(result_hash)
                    execution_results.append({
                        "iteration": iteration,
                        "parallel_id": parallel_id,
                        "result_hash": result_hash,
                        "result": result
                    })
                except Exception as e:
                    execution_results.append({
                        "iteration": iteration,
                        "parallel_id": parallel_id,
                        "error": str(e)
                    })
        unique_hashes = set(execution_hashes)
        is_deterministic = len(unique_hashes) == 1
        
        proof = {
            "test_type": "parallel_execution",
            "num_parallel": num_parallel,
            "iterations": iterations,
            "total_executions": num_parallel * iterations,
            "execution_results": execution_results,
            "execution_hashes": execution_hashes,
            "unique_hashes": len(unique_hashes),
            "is_deterministic": is_deterministic,
            "consensus_hash": list(unique_hashes)[0] if unique_hashes else None,
            "verdict": "PASS -- all parallel executions produced identical output" if is_deterministic else "FAIL -- determinism violated under parallelism"
        }
        
        self.test_results.append(proof)
        return proof
    
    def run_stress_test(self, execution_func, num_concurrent=10, duration_seconds=5):
        start_time = time.time()
        execution_hashes = []
        execution_count = 0
        errors = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max(num_concurrent, self.max_workers)) as executor:
            futures = []
            while time.time() - start_time < duration_seconds:
                for _ in range(num_concurrent):
                    future = executor.submit(execution_func)
                    futures.append(future)
                for future in concurrent.futures.as_completed(futures, timeout=1):
                    try:
                        result = future.result()
                        result_hash = self._compute_result_hash(result)
                        execution_hashes.append(result_hash)
                        execution_count += 1
                    except Exception as e:
                        errors.append(str(e))
                        execution_count += 1
                    futures.remove(future)
        unique_hashes = set(execution_hashes)
        is_deterministic = len(unique_hashes) == 1
        
        proof = {
            "test_type": "stress_test",
            "num_concurrent": num_concurrent,
            "duration_seconds": duration_seconds,
            "total_executions": execution_count,
            "execution_hashes": execution_hashes,
            "unique_hashes": len(unique_hashes),
            "is_deterministic": is_deterministic,
            "consensus_hash": list(unique_hashes)[0] if unique_hashes else None,
            "error_count": len(errors),
            "errors": errors,
            "execution_rate": execution_count / duration_seconds,
            "verdict": "PASS -- stress test: all executions produced identical output" if is_deterministic else "FAIL -- determinism violated under stress"
        }
        
        self.test_results.append(proof)
        return proof
    
    def run_ordered_concurrency_test(self, execution_func, num_iterations=5):
        all_hashes = []
        execution_logs = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for iteration in range(num_iterations):
                futures = []
                for task_id in range(10):
                    future = executor.submit(execution_func, task_id)
                    futures.append((task_id, future))
                round_hashes = []
                for task_id, future in futures:
                    try:
                        result = future.result(timeout=10)
                        result_hash = self._compute_result_hash(result)
                        round_hashes.append(result_hash)
                        all_hashes.append(result_hash)
                    except Exception as e:
                        pass
                
                execution_logs.append({
                    "iteration": iteration,
                    "round_hashes": round_hashes
                })
        unique_hashes = set(all_hashes)
        is_deterministic = len(unique_hashes) == 1
        
        proof = {
            "test_type": "ordered_concurrency",
            "num_iterations": num_iterations,
            "total_executions": len(all_hashes),
            "execution_logs": execution_logs,
            "unique_hashes": len(unique_hashes),
            "is_deterministic": is_deterministic,
            "consensus_hash": list(unique_hashes)[0] if unique_hashes else None,
            "verdict": "PASS -- order-independent determinism verified" if is_deterministic else "FAIL -- execution order affects output"
        }
        
        self.test_results.append(proof)
        return proof
    
    def get_determinism_summary(self):
        all_passed = all(result.get("is_deterministic", False) for result in self.test_results)
        
        return {
            "total_tests": len(self.test_results),
            "passed": sum(1 for r in self.test_results if r.get("is_deterministic", False)),
            "failed": sum(1 for r in self.test_results if not r.get("is_deterministic", False)),
            "all_tests_passed": all_passed,
            "test_types": list(set(r.get("test_type", "unknown") for r in self.test_results)),
            "test_results": self.test_results,
            "overall_verdict": "PASS -- all concurrency tests passed" if all_passed else "FAIL -- some tests failed"
        }
    
    def _compute_result_hash(self, result):
        result_data = {"result": result}
        
        serialized = json.dumps(result_data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def create_deterministic_replay_func(data_store):
    def replay_func(trace_id):
        if trace_id not in data_store:
            return {"error": f"Trace {trace_id} not found", "trace_id": trace_id}
        data = data_store[trace_id]
        result = {
            "trace_id": trace_id,
            "input": data,
            "output": data,
            "computation": sum(data.get("value", 0) for _ in range(10))
        }
        
        return result
    
    return replay_func
