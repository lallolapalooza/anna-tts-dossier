#!/usr/bin/env python3
"""Parse the Anna voice container metadata (no audio decoding).

Usage: parse_voice.py VOICE_DIR [--json]
"""
from __future__ import annotations

import json
import os
import struct
import sys


def parse_idx(path: str) -> dict:
    data = open(path, "rb").read()
    header_size, block_size, format_size = struct.unpack_from("<IHH", data, 0)
    fmt = data[8 : 8 + format_size]
    tag, channels, rate, avg, align, bits, cb_size = struct.unpack_from(
        "<HHIIHHH", fmt, 0
    )
    table = data[header_size:]
    lengths = struct.unpack_from("<%dH" % (len(table) // 2), table, 0)
    return {
        "header_size": header_size,
        "block_size": block_size,
        "format_size": format_size,
        "wave_format": {
            "format_tag": tag,
            "channels": channels,
            "samples_per_sec": rate,
            "avg_bytes_per_sec": avg,
            "block_align": align,
            "bits_per_sample": bits,
            "cb_size": cb_size,
            "extra": fmt[18 : 18 + cb_size].hex(),
        },
        "block_count": len(lengths),
        "decoded_samples": sum(lengths),
        "decoded_seconds": sum(lengths) / rate if rate else None,
        "length_min": min(lengths) if lengths else None,
        "length_max": max(lengths) if lengths else None,
        "first_lengths": list(lengths[:16]),
    }


def parse_wih(path: str) -> dict:
    data = open(path, "rb").read(64)
    version, fmt, rate, bps, channels = struct.unpack_from("<IIIHH", data, 0)
    return {
        "version": version,
        "format": fmt,
        "sample_rate": rate,
        "bytes_per_sample": bps,
        "channels": channels,
        "header_hex": data[:16].hex(),
    }


def parse_udt(path: str) -> dict:
    data = open(path, "rb").read(64)
    magic = data[:4]
    version = struct.unpack_from("<I", data, 4)[0]
    count = struct.unpack_from("<I", data, 8)[0]
    lcid = struct.unpack_from("<H", data, 12)[0]
    return {
        "magic": magic.hex(),
        "version": version,
        "entry_count": count,
        "lcid": hex(lcid),
        "header_hex": data[:32].hex(),
    }


def main(voice_dir: str) -> dict:
    out = {"dir": voice_dir, "files": {}}
    for name in sorted(os.listdir(voice_dir)):
        path = os.path.join(voice_dir, name)
        if not os.path.isfile(path):
            continue
        rec = {"size": os.path.getsize(path)}
        low = name.lower()
        try:
            if low.endswith(".idx"):
                rec.update(parse_idx(path))
            elif low.endswith(".wih"):
                rec.update(parse_wih(path))
            elif low.endswith(".udt"):
                rec.update(parse_udt(path))
        except Exception as exc:  # noqa: BLE001
            rec["error"] = str(exc)
        out["files"][name] = rec
    idx = out["files"].get("M1033DSK.IDX") or {}
    csd = out["files"].get("M1033DSK.CSD") or {}
    if idx and csd:
        out["validation"] = {
            "csd_size": csd.get("size"),
            "expected_csd_size": idx.get("block_count", 0) * idx.get("block_size", 0),
            "size_matches": csd.get("size")
            == idx.get("block_count", 0) * idx.get("block_size", 0),
        }
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "usage: parse_voice.py VOICE_DIR [--json]",
            file=sys.stderr,
        )
        raise SystemExit(2)
    result = main(sys.argv[1])
    print(json.dumps(result, indent=2))
