#!/usr/bin/env python3
"""Static PE inventory for the Anna/SAPI artifacts.

Emits one JSON document per input file. No execution, no writes to inputs.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import sys

import pefile


def u(x):
    if isinstance(x, bytes):
        return x.decode("utf-8", "replace")
    return x


def version_info(pe):
    out = []
    if not hasattr(pe, "FileInfo") or not pe.FileInfo:
        return out
    for block in pe.FileInfo:
        for entry in block:
            if not hasattr(entry, "StringTable"):
                continue
            for st in entry.StringTable:
                for k, v in st.entries.items():
                    out.append({"key": u(k), "value": u(v)})
    return out


def resources(pe):
    out = []
    if not hasattr(pe, "DIRECTORY_ENTRY_RESOURCE"):
        return out

    def walk(entries, path):
        for e in entries:
            name = u(e.name) if e.name is not None else e.id
            p = path + [str(name)]
            if hasattr(e, "directory"):
                walk(e.directory.entries, p)
            elif hasattr(e, "data"):
                d = e.data.struct
                out.append(
                    {
                        "path": p,
                        "rva": d.OffsetToData,
                        "size": d.Size,
                        "codepage": d.CodePage,
                    }
                )

    walk(pe.DIRECTORY_ENTRY_RESOURCE.entries, [])
    return out


def imports(pe):
    out = []
    for dll in getattr(pe, "DIRECTORY_ENTRY_IMPORT", []) or []:
        funcs = []
        for imp in dll.imports:
            funcs.append(
                {
                    "name": u(imp.name) if imp.name else None,
                    "ordinal": imp.ordinal,
                    "hint": imp.hint,
                    "iat_rva": imp.address - pe.OPTIONAL_HEADER.ImageBase,
                }
            )
        out.append({"dll": u(dll.dll), "functions": funcs})
    return out


def delay_imports(pe):
    out = []
    for dll in getattr(pe, "DIRECTORY_ENTRY_DELAY_IMPORT", []) or []:
        funcs = []
        for imp in dll.imports:
            funcs.append({"name": u(imp.name) if imp.name else None, "ordinal": imp.ordinal})
        out.append({"dll": u(dll.dll), "functions": funcs})
    return out


def exports(pe):
    out = []
    if not hasattr(pe, "DIRECTORY_ENTRY_EXPORT") or not pe.DIRECTORY_ENTRY_EXPORT:
        return out
    for e in pe.DIRECTORY_ENTRY_EXPORT.symbols:
        out.append(
            {
                "name": u(e.name) if e.name else None,
                "ordinal": e.ordinal,
                "rva": e.address,
                "forwarder": u(e.forwarder) if e.forwarder else None,
            }
        )
    return out


def debug_entries(pe):
    out = []
    for d in getattr(pe, "DIRECTORY_ENTRY_DEBUG", []) or []:
        ent = d.entry
        rec = {
            "type": d.struct.Type,
            "timestamp": d.struct.TimeDateStamp,
            "size": d.struct.SizeOfData,
            "major": d.struct.MajorVersion,
            "minor": d.struct.MinorVersion,
        }
        pdb = getattr(ent, "PdbFileName", None)
        if pdb:
            rec["pdb"] = u(pdb)
        d1 = getattr(ent, "Signature_Data1", None)
        if d1 is not None:
            d4 = getattr(ent, "Signature_Data4", None)
            d5 = getattr(ent, "Signature_Data5", None)
            def hexbytes(x):
                if x is None:
                    return ""
                if isinstance(x, int):
                    return "%08x" % x
                try:
                    return "".join("%02x" % b for b in x)
                except TypeError:
                    return str(x)
            rec["guid"] = "%08x-%04x-%04x-%s-%s" % (
                d1,
                getattr(ent, "Signature_Data2", 0),
                getattr(ent, "Signature_Data3", 0),
                hexbytes(d4),
                hexbytes(d5),
            )
            rec["age"] = getattr(ent, "Age", None)
        out.append(rec)
    return out


def tls(pe):
    if not hasattr(pe, "DIRECTORY_ENTRY_TLS") or not pe.DIRECTORY_ENTRY_TLS:
        return None
    s = pe.DIRECTORY_ENTRY_TLS.struct
    return {
        "start": s.StartAddressOfRawData,
        "end": s.EndAddressOfRawData,
        "index": s.AddressOfIndex,
        "callbacks": s.AddressOfCallBacks,
        "size_zero_fill": s.SizeOfZeroFill,
    }


def load_config(pe):
    lc = getattr(pe, "DIRECTORY_ENTRY_LOAD_CONFIG", None)
    if not lc:
        return None
    s = lc.struct
    names = [
        "Size",
        "TimeDateStamp",
        "SecurityCookie",
        "SEHandlerTable",
        "SEHandlerCount",
        "GuardCFCheckFunctionPointer",
        "GuardCFDispatchFunctionPointer",
        "GuardCFFunctionTable",
        "GuardCFFunctionCount",
        "GuardFlags",
    ]
    return {n: getattr(s, n, None) for n in names if hasattr(s, n)}


def main(paths):
    for path in paths:
        with open(path, "rb") as f:
            data = f.read()
        pe = pefile.PE(data=data, fast_load=False)
        pe.parse_data_directories(
            directories=[
                pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"],
                pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_EXPORT"],
                pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_RESOURCE"],
                pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_DELAY_IMPORT"],
                pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_DEBUG"],
                pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_TLS"],
                pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_LOAD_CONFIG"],
                pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_SECURITY"],
            ]
        )
        fh = pe.FILE_HEADER
        oh = pe.OPTIONAL_HEADER
        rec = {
            "path": os.path.abspath(path),
            "size": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "mtime_utc": datetime.datetime.utcfromtimestamp(
                os.path.getmtime(path)
            ).isoformat()
            + "Z",
            "machine": hex(fh.Machine),
            "machine_name": pefile.MACHINE_TYPE.get(fh.Machine),
            "characteristics": hex(fh.Characteristics),
            "timestamp": fh.TimeDateStamp,
            "timestamp_utc": datetime.datetime.utcfromtimestamp(
                fh.TimeDateStamp
            ).isoformat()
            + "Z",
            "magic": hex(oh.Magic),
            "magic_name": {0x10B: "PE32", 0x20B: "PE32+"}.get(oh.Magic),
            "image_base": hex(oh.ImageBase),
            "entry_point_rva": hex(oh.AddressOfEntryPoint),
            "size_of_image": oh.SizeOfImage,
            "size_of_headers": oh.SizeOfHeaders,
            "checksum": hex(oh.CheckSum),
            "subsystem": oh.Subsystem,
            "dll_characteristics": hex(oh.DllCharacteristics),
            "os_version": "%d.%d" % (oh.MajorOperatingSystemVersion, oh.MinorOperatingSystemVersion),
            "subsystem_version": "%d.%d" % (oh.MajorSubsystemVersion, oh.MinorSubsystemVersion),
            "is_dll": bool(fh.Characteristics & 0x2000),
            "is_dotnet": bool(
                oh.DATA_DIRECTORY[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_COM_DESCRIPTOR"]].VirtualAddress
            ),
            "has_cert_table": bool(
                oh.DATA_DIRECTORY[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_SECURITY"]].VirtualAddress
            ),
            "sections": [
                {
                    "name": u(s.Name).rstrip("\x00"),
                    "va": hex(s.VirtualAddress),
                    "vsize": s.Misc_VirtualSize,
                    "raw_size": s.SizeOfRawData,
                    "raw_ptr": hex(s.PointerToRawData),
                    "characteristics": hex(s.Characteristics),
                }
                for s in pe.sections
            ],
            "version_info": version_info(pe),
            "exports": exports(pe),
            "imports": imports(pe),
            "delay_imports": delay_imports(pe),
            "resources": resources(pe),
            "debug": debug_entries(pe),
            "tls": tls(pe),
            "load_config": load_config(pe),
        }
        if hasattr(pe, "parse_rich_header"):
            try:
                rich = pe.parse_rich_header()
                if rich:
                    rec["rich_header"] = {
                        "checksum": hex(rich.get("checksum", 0)),
                        "values": rich.get("values", []),
                    }
            except Exception as exc:  # noqa: BLE001
                rec["rich_header_error"] = str(exc)
        print(json.dumps(rec, indent=2, sort_keys=False, default=str))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: pe_inventory.py FILE [FILE ...]", file=sys.stderr)
        raise SystemExit(2)
    main(sys.argv[1:])
