# Test Plan

## Unit Tests
- `pytest -q` runs geometry integrity checks, dimensional contracts, variant alignment, CLI matrix, documentation lint, determinism, performance, and hypothesis-based fuzzing.

## CLI
- Default artifacts: `python 3d-models/generate_tag.py --out 3d-models/outputs/`
- Islands split: `python 3d-models/generate_tag.py --variant islands --out 3d-models/outputs/islands`

## Fuzzing
- Hypothesis generates random parameter sets within safe ranges to verify watertightness and bounding box dimensions.

## Determinism
- Builds the same model twice and compares SHA-256 hashes of vertices and faces.

## Performance
- Ensures cold build ≤ 8 s, warm build ≤ 4 s, memory usage < 500 MB.

Run `pytest -q` after installing dependencies with `pip install -r requirements.txt`.
