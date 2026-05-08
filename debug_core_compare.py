import json
from pathlib import Path
from api import strip_contract_version
from sanskar import run_sanskar
from core import run_core
from enforcement import run_enforcement

trace = json.loads(Path('trace_test2.json').read_text(encoding='utf-8-sig'))
original_input = trace['input']

rerun_sanskar = run_sanskar(original_input)
rerun_core = run_core(rerun_sanskar)

stored_core = trace['core_decision']
print('stored keys', sorted(stored_core.keys()))
print('rerun keys', sorted(rerun_core.keys()))
for key in sorted(set(stored_core.keys()) | set(rerun_core.keys())):
    if stored_core.get(key) != rerun_core.get(key):
        print('DIFF KEY:', key)
        print('stored:', stored_core.get(key))
        print('rerun: ', rerun_core.get(key))
        print('---')
