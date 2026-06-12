# OPERATOR RUNBOOK - SANSKAR
**Purpose**: Step-by-step procedures for operating SANSKAR independently

---

## PROCEDURE 1: Starting SANSKAR

**Duration**: 2 minutes
**Prerequisites**: Python 3.14+ installed, TASK 6 directory available

### Steps

1. Open terminal/PowerShell
2. Navigate to workspace:
   ```bash
   cd c:\Users\saksh\Downloads\TASK 6
   ```
3. Start API server:
   ```bash
   python api.py
   ```
4. Verify startup:
   ```bash
   # New terminal:
   curl http://localhost:8000/health
   ```
5. Expected response:
   ```json
   {"status": "healthy", "pid": 318988, "checks": {...}}
   ```

### Troubleshooting
- **Port 8000 already in use**: Kill existing process or use different port
- **Python not found**: Verify Python 3.14+ installed in PATH
- **Import errors**: Run `pip install -r requirements.txt`

---

## PROCEDURE 2: Sending a Signal

**Duration**: 5 seconds
**Prerequisites**: SANSKAR running (api.py)

### Steps

1. Prepare input signal (CSV data):
   ```json
   {
     "regions": ["Region_A", "Region_B", "Region_C"],
     "data": {
       "Region_A": {
         "rainfall_mm": 750,
         "temperature_c": 22,
         "irrigation_hours": 120,
         ...
       }
     }
   }
   ```

2. Send signal to SANSKAR:
   ```bash
   curl -X POST http://localhost:8000/signal \
     -H "Content-Type: application/json" \
     -d @signal.json
   ```

3. Verify response:
   ```json
   {
     "entities": ["Region_A", "Region_B", "Region_C"],
     "ranking": [
       {"region": "Region_C", "score": 0.85, "rank": 1},
       ...
     ],
     "confidence": {...}
   }
   ```

### Troubleshooting
- **Connection refused**: SANSKAR not running, start with PROCEDURE 1
- **400 Bad Request**: Invalid signal format, verify JSON structure
- **500 Server Error**: Check observability.log for details

---

## PROCEDURE 3: Verifying Trace Integrity

**Duration**: 1 minute
**Prerequisites**: Full execution completed

### Steps

1. Verify trace file exists:
   ```bash
   ls -la event_store.json
   ```

2. Run verification script:
   ```bash
   python verify_convergence.py
   ```

3. Expected output:
   ```text
   ✅ Event 0 integrity verified
   ✅ Event 1 integrity verified
   ✅ Event 2 integrity verified
   ✅ All events verified
   ✅ TRACE_VALID
   ```

4. If verification fails:
   ```text
   ❌ Event 3 integrity FAILED
   ❌ TRACE_CORRUPTED
   ```
   → Follow PROCEDURE 8: Handling Trace Corruption

---

## PROCEDURE 4: Replaying an Execution

**Duration**: 10 seconds
**Prerequisites**: Previous execution stored in event_store.json

### Steps

1. Start replay mode:
   ```bash
   python full_chain_executor.py --replay-mode
   ```

2. Wait for completion (should be <100ms)

3. Compare outputs:
   ```bash
   # Original: ecosystem_convergence_proof.json
   # Replay: (new output)
   diff ecosystem_convergence_proof.json replay_output.json
   ```

4. Expected: No differences (determinism verified)

### Troubleshooting
- **Differences found**: Possible non-determinism, escalate to developer
- **Replay slower than expected**: Check system load, verify dependencies available
- **Replay fails**: Check observability.log for specific error

---

## PROCEDURE 5: Health Check

**Duration**: 5 seconds
**Prerequisites**: SANSKAR running

### Steps

1. Query health endpoint:
   ```bash
   curl http://localhost:8000/health
   ```

2. Verify response structure:
   ```json
   {
     "status": "healthy",     // ← Should be "healthy"
     "pid": 318988,           // ← Should be positive number
     "uptime_seconds": 42,    // ← Should be positive
     "checks": {
       "process": "OK",       // ← All should be "OK"
       "trace_infrastructure": "OK",
       "governance": "OK"
     }
   }
   ```

3. If any check is not "OK":
   → Proceed to PROCEDURE 7: Recovering from Failure

---

## PROCEDURE 6: Reading Logs

**Duration**: 2 minutes
**Prerequisites**: Execution completed

### Steps

1. View last 50 log lines:
   ```bash
   tail -50 observability.log
   ```

2. Search for specific event:
   ```bash
   grep "AUTHORITY_VIOLATION" observability.log
   grep "ERROR" observability.log
   grep "Stage complete" observability.log
   ```

3. Read full log:
   ```bash
   cat observability.log | less
   ```

4. Log structure:
   ```text
   [2026-06-12T07:14:02.495111Z] PHASE_1_EXECUTION_START
     - skip_restart: False
     - workspace: C:\Users\saksh\Downloads\TASK 6
   ```

### Common Log Patterns
- `STAGE_SANSKAR_COMPLETE` - Ranking complete
- `STAGE_RAJYA_COMPLETE` - Governance decision made
- `STAGE_ENFORCEMENT_COMPLETE` - Actions generated
- `AUTHORITY_VIOLATION` - Boundary violation attempted
- `ERROR` - Error occurred

---

## PROCEDURE 7: Recovering from Process Failure

**Duration**: 1-2 minutes
**Trigger**: SANSKAR exits unexpectedly

### Steps

1. Confirm process is dead:
   ```bash
   curl http://localhost:8000/health
   # Should fail: Connection refused
   ```

2. Check if process is still running:
   ```bash
   # Windows:
   tasklist | findstr python

   # Linux/Mac:
   ps aux | grep sanskar
   ```

3. Kill any zombie processes:
   ```bash
   taskkill /F /IM python.exe  # Windows
   pkill -f sanskar             # Linux
   ```

4. Review logs:
   ```bash
   tail -20 observability.log
   ```

5. Restart SANSKAR:
   ```bash
   python api.py
   ```

6. Verify recovery:
   ```bash
   curl http://localhost:8000/health
   ```

### Data Preservation
- Trace log (`event_store.json`): Preserved 
- Events recorded: Preserved 
- State: Recovered from checkpoint 

---

## PROCEDURE 8: Handling Trace Corruption

**Duration**: 5-10 minutes
**Trigger**: Trace verification fails (PROCEDURE 3)

### Steps

1. Verify corruption:
   ```bash
   python verify_convergence.py
   # Output: ❌ TRACE_CORRUPTED at event #5
   ```

2. Identify last valid event:
   ```bash
   # In the output, find last verified event
   # Example: Event #4 verified, Event #5 failed
   # → Last valid = event #4
   ```

3. Create backup of corrupted trace:
   ```bash
   cp event_store.json event_store.json.corrupted
   ```

4. Truncate to last valid event:
   ```bash
   python truncate_trace.py --last-valid-event 4
   ```

5. Re-verify trace:
   ```bash
   python verify_convergence.py
   # Should now show: ✅ TRACE_VALID
   ```

6. From last checkpoint, re-execute:
   ```bash
   python replay_from_checkpoint.py --event 4
   ```

### Prevention
- Don't manually edit event_store.json
- Don't interrupt execution with SIGKILL
- Always use SIGTERM for graceful shutdown

---

## PROCEDURE 9: Understanding Authority Errors

**Duration**: 2-3 minutes
**Trigger**: See "AUTHORITY_VIOLATION" in logs

### Steps

1. Find violation in logs:
   ```bash
   grep -n "AUTHORITY_VIOLATION" observability.log
   # Example: Line 127: AUTHORITY_VIOLATION - SANSKAR cannot write to BUCKET
   ```

2. Understand the boundary:
   ```bash
   cat authority_violation_proof.json | jq '.authority_matrix.SANSKAR'
   # Shows what SANSKAR can/cannot do
   ```

3. Assess if legitimate operation:
   - If operation was SANSKAR trying to write to Bucket: ✓ Correctly rejected
   - If operation was ranking input signal: ✓ Should be allowed, check logs

4. Decision:
   - **If correctly rejected**: No action needed, system working as designed
   - **If should be allowed**: Document and escalate to governance team

5. Do NOT bypass authority boundaries

---

## PROCEDURE 10: Viewing Full Trace

**Duration**: 5 minutes
**Purpose**: Inspect complete execution trace

### Steps

1. Load trace file:
   ```python
   import json
   with open('event_store.json') as f:
       trace = json.load(f)
   ```

2. Print trace summary:
   ```python
   print(f"Trace ID: {trace['trace_id']}")
   print(f"Total events: {len(trace['events'])}")
   for i, event in enumerate(trace['events']):
       print(f"  {i}: {event['timestamp']} {event['stage']} {event['event_type']}")
   ```

3. View specific event:
   ```python
   event = trace['events'][3]  # 4th event
   print(json.dumps(event, indent=2))
   ```

4. Export to readable format:
   ```bash
   python -m json.tool event_store.json > trace_readable.json
   ```

---

## PROCEDURE 11: Resetting System State

**Duration**: 30 seconds
**Purpose**: Start fresh (clear all history)

### Warning 
**This permanently deletes all recorded traces and events. Use carefully.**

### Steps

1. Stop SANSKAR (if running):
   ```bash
   # Ctrl+C in terminal running api.py
   ```

2. Backup current state (recommended):
   ```bash
   cp event_store.json event_store.json.backup
   cp observability.log observability.log.backup
   ```

3. Delete trace history:
   ```bash
   rm event_store.json observability.log
   ```

4. Restart SANSKAR:
   ```bash
   python api.py
   ```

5. Verify fresh start:
   ```bash
   curl http://localhost:8000/health
   # Should return fresh uptime_seconds value
   ```

---

## PROCEDURE 12: Changing Configuration

**Duration**: 5-10 minutes
**Purpose**: Modify SANSKAR ranking factors

### Steps

1. Stop SANSKAR:
   ```bash
   # Ctrl+C in terminal running api.py
   ```

2. Edit sanskar.py:
   ```bash
   # Find FACTORS dict:
   # FACTORS = {
   #     "rainfall": 0.15,        ← Modify weight
   #     "temperature": 0.12,
   #     ...
   # }
   ```

3. Make desired changes (example: increase rainfall weight to 0.20)

4. Save file and restart:
   ```bash
   python api.py
   ```

5. Test with same signal:
   ```bash
   curl -X POST http://localhost:8000/signal -d @signal.json
   # Rankings should change based on new factors
   ```

6. Verify determinism:
   ```bash
   python full_chain_executor.py --replay-mode
   # Should reproduce with new factors
   ```

---

## Quick Reference

### Commands

| Task | Command |
|------|---------|
| Start | `python api.py` |
| Health | `curl http://localhost:8000/health` |
| Verify | `python verify_convergence.py` |
| Replay | `python full_chain_executor.py --replay-mode` |
| Check logs | `tail -f observability.log` |
| Reset | `rm event_store.json observability.log` |

### Files

| File | Purpose | Modify? |
|------|---------|---------|
| sanskar.py | Core logic | No |
| api.py | API | No |
| event_store.json | Trace | No (automated) |
| observability.log | Logs | No (read-only) |

### Procedures
- PROCEDURE 1: Starting SANSKAR
- PROCEDURE 2: Sending signal
- PROCEDURE 3: Verify trace
- PROCEDURE 4: Replay execution
- PROCEDURE 5: Health check
- PROCEDURE 6: Read logs
- PROCEDURE 7: Recover from failure
- PROCEDURE 8: Handle corruption
- PROCEDURE 9: Understand authority errors
- PROCEDURE 10: View full trace
- PROCEDURE 11: Reset state
- PROCEDURE 12: Change configuration

---

## Support Matrix

| Issue | Procedure | Escalate? |
|-------|-----------|-----------|
| Can't start | 1 | If fails after retries |
| Signal not processed | 2 | If data format is correct |
| Trace corrupted | 8 | After recovery |
| Process crashes | 7 | If happens >3 times |
| Auth violation | 9 | If operation should be allowed |
| Unexpected errors | Check logs | If not in known patterns |

---

End of Operator Runbook.

**You now have all procedures needed for independent operation.**

