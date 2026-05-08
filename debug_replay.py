import json
from pathlib import Path
from api import strip_contract_version
from sanskar import run_sanskar
from core import run_core
from enforcement import run_enforcement
from tantra import compute_chain_hash

trace = json.loads(Path('trace_test2.json').read_text(encoding='utf-8-sig'))
original_input = trace['input']

rerun_sanskar = run_sanskar(original_input)
rerun_core = run_core(rerun_sanskar)
rerun_enforcement = run_enforcement(rerun_core)

print('sanskar_equal', rerun_sanskar == trace['sanskar_output'])
print('core_equal', rerun_core == trace['core_decision'])
print('enforcement_equal', rerun_enforcement == trace['enforcement'])

chain_data = {
    'input': strip_contract_version(original_input),
    'sanskar': rerun_sanskar,
    'core': rerun_core,
    'enforcement': rerun_enforcement,
}
print('rerun_hash', compute_chain_hash(chain_data))
print('stored_hash', trace['truth']['pipeline_hash'])
