#@category Anna.RE
# Dump a Ghidra program inventory as JSON.
# Usage (headless): DumpInventory.py <out.json>
import json
import os

from ghidra.program.model.data import Composite
from ghidra.program.model.symbol import SymbolType

args = [str(a) for a in getScriptArgs()]
out_path = args[0] if args else None

prog = currentProgram
fm = prog.getFunctionManager()
st = prog.getSymbolTable()
listing = prog.getListing()
mem = prog.getMemory()
monitor = monitor


def astr(a):
    return a.toString() if a is not None else None


def jstr(x):
    return x if x is None else str(x)


def function_record(f):
    body = f.getBody()
    try:
        calls = [astr(c.getEntryPoint()) for c in f.getCalledFunctions(monitor)]
    except Exception:
        calls = []
    try:
        callers = [astr(c.getEntryPoint()) for c in f.getCallingFunctions(monitor)]
    except Exception:
        callers = []
    try:
        sig = f.getSignature().getPrototypeString()
    except Exception:
        sig = None
    return {
        "entry": astr(f.getEntryPoint()),
        "name": f.getName(),
        "namespace": jstr(f.getParentNamespace()),
        "signature": sig,
        "calling_convention": jstr(f.getCallingConventionName()),
        "body_size": body.getNumAddresses() if body is not None else 0,
        "is_thunk": bool(f.isThunk()),
        "is_external": bool(f.isExternal()),
        "is_inline": bool(f.isInline()),
        "no_return": bool(f.hasNoReturn()),
        "stack_frame_size": f.getStackFrame().getFrameSize() if f.getStackFrame() else None,
        "parameter_count": f.getParameterCount(),
        "comment": jstr(f.getComment()),
        "repeatable_comment": jstr(f.getRepeatableComment()),
        "called_functions": calls,
        "calling_functions": callers,
    }


funcs = []
for f in fm.getFunctions(True):
    funcs.append(function_record(f))

exports = []
it = st.getExternalEntryPointIterator()
while it.hasNext():
    ea = it.next()
    syms = st.getSymbols(ea)
    names = [s.getName() for s in syms]
    exports.append({"address": astr(ea), "symbols": names})

imports = []
for s in st.getExternalSymbols():
    ns = s.getParentNamespace()
    imports.append(
        {
            "name": s.getName(),
            "namespace": jstr(ns),
            "library": jstr(ns.getName()) if ns is not None else None,
            "type": jstr(s.getSymbolType()),
        }
    )

strings = []
for d in listing.getDefinedData(True):
    val = d.getValue()
    if val is None:
        continue
    if 'String' not in d.getDataType().getName() and 'Unicode' not in d.getDataType().getName():
        continue
    refs = []
    refmgr = prog.getReferenceManager()
    for r in refmgr.getReferencesTo(d.getAddress()):
        refs.append(
            {
                "from": astr(r.getFromAddress()),
                "type": jstr(r.getReferenceType()),
            }
        )
    strings.append(
        {
            "address": astr(d.getAddress()),
            "value": str(val),
            "length": len(str(val)),
            "data_type": jstr(d.getDataType().getName()),
            "references": refs,
        }
    )

blocks = []
for b in mem.getBlocks():
    blocks.append(
        {
            "name": b.getName(),
            "start": astr(b.getStart()),
            "end": astr(b.getEnd()),
            "size": b.getSize(),
            "initialized": bool(b.isInitialized()),
            "execute": bool(b.isExecute()),
            "read": bool(b.isRead()),
            "write": bool(b.isWrite()),
            "volatile": bool(b.isVolatile()),
            "comment": jstr(b.getComment()),
        }
    )

composites = []
dtm = prog.getDataTypeManager()
for dt in dtm.getAllDataTypes():
    if isinstance(dt, Composite):
        comps = []
        try:
            for c in dt.getComponents():
                comps.append(
                    {
                        "offset": c.getOffset(),
                        "name": c.getFieldName(),
                        "type": jstr(c.getDataType().getName()),
                        "length": c.getLength(),
                        "comment": jstr(c.getComment()),
                    }
                )
        except Exception as exc:
            comps = [{"error": str(exc)}]
        composites.append(
            {
                "name": dt.getName(),
                "path": jstr(dt.getPathName()),
                "length": dt.getLength(),
                "components": comps,
            }
        )

record = {
    "program": prog.getName(),
    "executable_path": jstr(prog.getExecutablePath()),
    "language": jstr(prog.getLanguageID()),
    "compiler": jstr(prog.getCompilerSpec().getCompilerSpecID()),
    "image_base": astr(prog.getImageBase()),
    "format": jstr(prog.getExecutableFormat()),
    "functions": funcs,
    "exports": exports,
    "imports": imports,
    "strings": strings,
    "memory_blocks": blocks,
    "composites": composites,
}

text = json.dumps(record, indent=2, default=str)
if out_path:
    f = open(out_path, "w")
    try:
        f.write(text)
    finally:
        f.close()
    print("wrote %s" % out_path)
else:
    print(text)
