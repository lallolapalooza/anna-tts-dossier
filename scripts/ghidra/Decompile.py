#@category Anna.RE
# Decompile functions matching an optional regex.
# Usage: Decompile.py <outdir> [regex] [max_functions] [seconds_per_function]
import json
import os
import re

from ghidra.app.decompiler import DecompInterface, DecompileOptions
from ghidra.util.task import ConsoleTaskMonitor

args = [str(a) for a in getScriptArgs()]
outdir = args[0]
pattern = args[1] if len(args) > 1 and args[1] else None
limit = int(args[2]) if len(args) > 2 and args[2] else 0
timeout = int(args[3]) if len(args) > 3 and args[3] else 120

fm = currentProgram.getFunctionManager()
monitor = ConsoleTaskMonitor()

ifc = DecompInterface()
ifc.setOptions(DecompileOptions())
if not ifc.openProgram(currentProgram):
    print("failed to open program in decompiler")
    raise SystemExit(1)

rx = re.compile(pattern) if pattern else None
if not os.path.isdir(outdir):
    os.makedirs(outdir)

index = []
count = 0
for f in fm.getFunctions(True):
    if f.isExternal() or f.isThunk():
        continue
    name = f.getName()
    if rx is not None and not rx.search(name):
        continue
    if limit and count >= limit:
        break
    entry = f.getEntryPoint().toString()
    try:
        res = ifc.decompileFunction(f, timeout, monitor)
    except Exception as exc:
        index.append({"entry": entry, "name": name, "error": "decompile exception: %s" % exc})
        continue
    rec = {
        "entry": entry,
        "name": name,
        "namespace": str(f.getParentNamespace()),
        "signature": str(f.getSignature().getPrototypeString()),
        "body_size": f.getBody().getNumAddresses(),
        "parameters": f.getParameterCount(),
        "completed": bool(res.decompileCompleted()),
    }
    if res.decompileCompleted():
        ctext = res.getDecompiledFunction().getC()
        rec["decompiled_chars"] = len(ctext)
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", name)[:80]
        fn = os.path.join(outdir, "%s_%s.c" % (entry.replace(":", ""), safe))
        with open(fn, "w") as fh:
            fh.write(ctext)
        rec["file"] = fn
    else:
        rec["error"] = str(res.getErrorMessage())
    index.append(rec)
    count += 1

with open(os.path.join(outdir, "index.json"), "w") as fh:
    json.dump(index, fh, indent=2, default=str)
print("decompiled %d functions into %s" % (count, outdir))
