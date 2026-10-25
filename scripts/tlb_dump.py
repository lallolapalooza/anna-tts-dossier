#!/usr/bin/env python3
"""Dump a Windows type library (TLB) to JSON/markdown using comtypes.

Usage: tlb_dump.py FILE.tlb [OUT.json]
"""
from __future__ import annotations

import json
import sys

import comtypes.typeinfo as ti

VT = {
    0: "VT_EMPTY", 1: "VT_NULL", 2: "VT_I2", 3: "VT_I4", 4: "VT_R4", 5: "VT_R8",
    6: "VT_CY", 7: "VT_DATE", 8: "VT_BSTR", 9: "VT_DISPATCH", 10: "VT_ERROR",
    11: "VT_BOOL", 12: "VT_VARIANT", 13: "VT_UNKNOWN", 14: "VT_DECIMAL",
    16: "VT_I1", 17: "VT_UI1", 18: "VT_UI2", 19: "VT_UI4", 20: "VT_I8",
    21: "VT_UI8", 22: "VT_INT", 23: "VT_UINT", 24: "VT_VOID", 25: "VT_HRESULT",
    26: "VT_PTR", 27: "VT_SAFEARRAY", 28: "VT_CARRAY", 29: "VT_USERDEFINED",
    30: "VT_LPSTR", 31: "VT_LPWSTR", 36: "VT_RECORD", 37: "VT_INT_PTR",
    38: "VT_UINT_PTR", 64: "VT_FILETIME", 66: "VT_STREAM", 67: "VT_STORAGE",
    68: "VT_STREAMED_OBJECT", 69: "VT_STORED_OBJECT", 70: "VT_BLOB_OBJECT",
    71: "VT_CF", 72: "VT_CLSID", 73: "VT_VERSIONED_STREAM",
}

TYPEKIND = {
    0: "TKIND_ENUM", 1: "TKIND_RECORD", 2: "TKIND_MODULE", 3: "TKIND_INTERFACE",
    4: "TKIND_DISPATCH", 5: "TKIND_COCLASS", 6: "TKIND_ALIAS", 7: "TKIND_UNION",
}


def type_name(info, tdesc, depth=0):
    if tdesc is None or depth > 6:
        return "?"
    vt = tdesc.vt
    name = VT.get(vt, "VT_%d" % vt)
    if vt == 26:  # VT_PTR
        inner = getattr(tdesc.lptdesc, "contents", tdesc.lptdesc)
        return type_name(info, inner, depth + 1) + " *"
    if vt in (27,):  # VT_SAFEARRAY
        inner = getattr(tdesc.lptdesc, "contents", tdesc.lptdesc)
        return "SAFEARRAY(%s)" % type_name(info, inner, depth + 1)
    if vt == 29:  # VT_USERDEFINED
        try:
            ref = info.GetRefTypeInfo(tdesc.hreftype)
            return ref.GetDocumentation(-1)[0]
        except Exception:
            return "USERDEFINED(0x%x)" % tdesc.hreftype
    if vt == 28:  # VT_CARRAY
        return "CArray"
    return name


def dump_library(path):
    lib = ti.LoadTypeLibEx(path)
    attr = lib.GetLibAttr()
    out = {
        "path": path,
        "guid": str(attr.guid),
        "version": "%d.%d" % (attr.wMajorVerNum, attr.wMinorVerNum),
        "lcid": attr.lcid,
        "types": [],
    }
    for i in range(lib.GetTypeInfoCount()):
        info = lib.GetTypeInfo(i)
        ta = info.GetTypeAttr()
        name, doc, ctx, helpfile = info.GetDocumentation(-1)
        rec = {
            "index": i,
            "name": name,
            "guid": str(getattr(ta,"guid",getattr(ta,"GUID",None))),
            "kind": TYPEKIND.get(ta.typekind, str(ta.typekind)),
            "doc": doc,
            "functions": [],
            "fields": [],
            "impl": [],
        }
        for j in range(ta.cImplTypes):
            try:
                ref = info.GetRefTypeInfo(info.GetRefTypeOfImplType(j))
                rec["impl"].append(ref.GetDocumentation(-1)[0])
            except Exception as exc:  # noqa: BLE001
                rec["impl"].append("error: %s" % exc)
        for j in range(ta.cFuncs):
            fd = info.GetFuncDesc(j)
            try:
                names = list(info.GetNames(fd.memid, 1 + fd.cParams))
            except Exception:
                names = []
            fname = names[0] if names else str(fd.memid)
            params = []
            for k in range(fd.cParams):
                pname = names[1 + k] if 1 + k < len(names) else "p%d" % k
                params.append(
                    {
                        "name": pname,
                        "type": type_name(info, fd.lprgelemdescParam[k].tdesc),
                    }
                )
            rec["functions"].append(
                {
                    "name": fname,
                    "memid": fd.memid,
                    "vtable_offset": fd.oVft,
                    "invkind": fd.invkind,
                    "return": type_name(info, fd.elemdescFunc.tdesc),
                    "params": params,
                }
            )
        for j in range(ta.cVars):
            vd = info.GetVarDesc(j)
            try:
                vname = info.GetDocumentation(vd.memid)[0]
            except Exception:
                vname = str(vd.memid)
            rec["fields"].append(
                {
                    "name": vname,
                    "type": type_name(info, vd.elemdescVar.tdesc),
                    "varkind": vd.varkind,
                }
            )
        out["types"].append(rec)
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: tlb_dump.py FILE.tlb [OUT.json]", file=sys.stderr)
        raise SystemExit(2)
    data = dump_library(sys.argv[1])
    text = json.dumps(data, indent=2)
    if len(sys.argv) > 2:
        with open(sys.argv[2], "w", encoding="utf-8") as f:
            f.write(text)
    else:
        print(text)
