#!/usr/bin/env python3
"""Dump SAPI voice/CLSID registry data from a Windows SOFTWARE hive.

Usage: hive_dump.py SOFTWARE [OUT.json]
"""
from __future__ import annotations

import json
import sys

from regipy.registry import RegistryHive


KEYS = [
    r"\Microsoft\Speech\Voices\Tokens",
    r"\Microsoft\Speech\Recognizers",
    r"\Microsoft\Speech\PhoneConverters",
    r"\Microsoft\Speech\AudioOutput",
    r"\Microsoft\Speech\AudioInput",
    r"\Microsoft\Speech\AppLexicons",
    r"\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_ANNA_11.0",
    r"\Classes\CLSID",
    r"\Wow6432Node\Microsoft\Speech\Voices\Tokens",
]


def values(node):
    out = {}
    for v in node.values or []:
        out[v.name or "(default)"] = v.value
    return out


def dump_tree(hive, path, depth=0, max_depth=6):
    node = hive.get_key(path)
    rec = {"path": node.path, "values": values(node), "subkeys": []}
    if depth < max_depth:
        for sub in node.iter_subkeys():
            rec["subkeys"].append(
                dump_tree(hive, sub.path, depth + 1, max_depth)
            )
    return rec


def main(hive_path, out_path=None):
    hive = RegistryHive(hive_path)
    result = {"hive": hive_path, "keys": {}}
    for key in KEYS:
        try:
            if key.endswith("CLSID"):
                # only classes referenced by speech tokens are interesting;
                # dump the key names, not every CLSID body.
                node = hive.get_key(key)
                result["keys"][key] = {
                    "subkeys": [s.name for s in node.iter_subkeys()]
                }
            else:
                result["keys"][key] = dump_tree(hive, key)
        except Exception as exc:  # noqa: BLE001
            result["keys"][key] = {"error": str(exc)}

    # Resolve every CLSID referenced by speech voice tokens.
    resolved = {}
    try:
        tokens = hive.get_key(r"\Microsoft\Speech\Voices\Tokens")
        for tok in tokens.iter_subkeys():
            vals = values(tok)
            clsid = vals.get("CLSID")
            if not clsid:
                continue
            clsid = clsid.strip()
            p = r"\Classes\CLSID\%s" % clsid
            try:
                node = hive.get_key(p)
                rec = {"token": tok.name, "clsid": clsid, "values": values(node)}
                for sub in node.iter_subkeys():
                    rec[sub.name] = {
                        "values": values(sub),
                        "subkeys": [s.name for s in sub.iter_subkeys()],
                    }
                    for sub2 in sub.iter_subkeys():
                        rec[sub.name].setdefault("children", {})[sub2.name] = values(sub2)
                resolved[tok.name] = rec
            except Exception as exc:  # noqa: BLE001
                resolved[tok.name] = {"token": tok.name, "clsid": clsid, "error": str(exc)}
    except Exception as exc:  # noqa: BLE001
        resolved["error"] = str(exc)
    result["resolved_clsids"] = resolved

    text = json.dumps(result, indent=2, default=str)
    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)
    else:
        print(text)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: hive_dump.py SOFTWARE [OUT.json]", file=sys.stderr)
        raise SystemExit(2)
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
