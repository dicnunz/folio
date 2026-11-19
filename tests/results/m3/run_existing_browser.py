"""Run existing browser checks, preserving historical evidence directories."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from scripts import verify_cse22_browser as a, verify_cse23_browser as b
failed = False
for module, attribute, name in [(a, 'EVIDENCE', 'browser-cse22'), (b, 'OUT', 'browser-cse23')]:
    setattr(module, attribute, Path(__file__).resolve().parent / name)
    try:
        module.main()
    except Exception:
        import traceback
        traceback.print_exc()
        failed = True
sys.exit(int(failed))
