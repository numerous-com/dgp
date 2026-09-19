"""Run all offline bundle checks. Does not contact model or energy services."""
from __future__ import annotations
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from profile_support.validation import validate_record

def main() -> None:
    subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=ROOT,check=True)
    core_index=json.loads((ROOT/'examples/fixture-index.json').read_text())
    for item in core_index:
        value=json.loads((ROOT/'examples'/item['file']).read_text())
        validate_record(item['schema'],value)
    print(f'PASS: {len(core_index)} core example records.',flush=True)
    profile_index=json.loads((ROOT/'examples/profiles/fixture-index.json').read_text())
    for name,definition in profile_index.items():
        value=json.loads((ROOT/'examples/profiles'/name).read_text())
        validate_record(definition,value)
    print(f'PASS: {len(profile_index)} optional-profile/example records.',flush=True)
    subprocess.run([sys.executable,'profiles/farm-energy/validate_examples.py'],cwd=ROOT,check=True)
    node=shutil.which('node')
    if node:
        for path in ['web/app.js','bindings/graphql/validate.mjs']:
            subprocess.run([node,'--check',path],cwd=ROOT,check=True)
        print('PASS: JavaScript syntax for browser app and optional GraphQL validator.',flush=True)
    else:
        print('NOT RUN: JavaScript syntax checks; Node.js is not installed.',flush=True)
    print('NOT RUN: GraphQL SDL/document validation (external graphql package), live GraphQL/MCP, paid providers, and energy simulation.',flush=True)
    print('Bundle checks completed.',flush=True)

if __name__=='__main__':main()
