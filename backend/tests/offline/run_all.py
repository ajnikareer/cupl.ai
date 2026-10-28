import os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
fails = 0
for t in ["test_mcp_tools.py", "test_e2e_agent.py", "test_e2e_api.py", "test_e2e_voice.py"]:
    print(f"\n===== {t} =====", flush=True)
    p = subprocess.run([sys.executable, "-u", os.path.join(HERE, t)], capture_output=True, text=True, timeout=180)
    lines = [l for l in p.stdout.splitlines() if l.startswith(("PASS ", "FAIL "))]
    print("\n".join(lines))
    bad = sum(l.startswith("FAIL ") for l in lines) + (0 if "FAILS: 0" in p.stdout else 1)
    if bad:
        print(p.stderr[-3000:])
    fails += bad
if sys.stdout.encoding and sys.stdout.encoding.lower().startswith('cp'):
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding and sys.stderr.encoding.lower().startswith('cp'):
    sys.stderr.reconfigure(encoding='utf-8')

print("\nALL SUITES PASSED [OK]" if not fails else f"\n{fails} problem(s) [FAIL]")
sys.exit(1 if fails else 0)
