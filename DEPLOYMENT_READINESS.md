# DEPLOYMENT_READINESS.md

## CPU/RAM Estimate
- CPU: 0.5 vCPU (minimal processing for data analysis)
- RAM: 512 MB (sufficient for pandas operations and in-memory trace storage)

## Runtime Dependencies
- Python 3.11+
- pandas
- fastapi
- uvicorn
- pydantic

## Deployment Steps
1. Clone repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run service: `python api.py` or `./startup.sh`
4. Service starts on port 8000

## Ports Used
- 8000: HTTP API endpoint

## Replay Behavior
- Replay endpoint verifies hash identity for deterministic reproduction
- Exact same output guaranteed for same trace_id

## Observability Notes
- Logs written to observability.log with trace_id, timestamp, stage, verdict, hash
- Structured JSON format for log aggregation

## Scaling Considerations
- Stateless service (traces stored in memory, persist to files)
- Horizontal scaling possible with shared storage for truth_store.json and observability.log