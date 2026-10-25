# Microsoft Anna (Windows 7 SP1 x64) — architecture dossier

Static reverse-engineering notes for the Microsoft Anna SAPI5 text-to-speech stack
shipped in Windows 7 Ultimate SP1 x64.

**Scope:** architecture and data-format documentation only. No Anna voice was
recreated, cloned, synthesized, or compared for sample parity.

## What is here

| Path | Contents |
|---|---|
| `docs/00-scope.md` | scope, non-goals, acceptance criteria |
| `docs/01-sapi-host.md` | SAPI 5 host contract |
| `docs/02-components.md` | extracted components, hashes, registry, CLSIDs, type libraries |
| `docs/03-engine.md` | engine/frontend object layout, initialization, render loop, text pipeline |
| `docs/04-formats.md` | `.IDX`/`.CSD`/`.WIH`/`.LTS`/`.UDT` byte layouts, decoder, XOR key |
| `docs/05-reimplementation.md` | build spec, pseudocode, structures, acceptance checks |
| `docs/06-verification.md` | hashes, registry/TLB checks, Ghidra counts, container validation |
| `docs/07-function-map.md` | address-to-role map for engine, frontend, decoder, LTS |
| `data/artifacts.json` | SHA-256 inventory of the analyzed files |
| `data/voice-metadata.json` | validated Anna container metadata |
| `data/tlb/*.json` | parsed COM type libraries |
| `scripts/` | PE/registry/TLB parsers and Ghidra headless scripts |
| `archive/anna-session.zip` | sanitized session archive generated with [`alosslessdev/omp-archive-main`](https://github.com/alosslessdev/omp-archive-main) |

## Key findings

- Anna is a SAPI5 engine (`MSTTSEngine.dll`, version `2.00.4319.00`).
- Voice token: `MS-Anna-1033-20-DSK`
  - engine CLSID `{F51C7B23-6566-424C-94CF-2C4F83EE96FF}`
  - frontend CLSID `{55DFB4F7-4175-4B3B-B247-D9B399ADB119}`
- The frontend (`MSTTSFrontendENU.dll`) exposes `ITTSFrontend` and performs text
  normalization, pronunciation, prosody, and unit selection.
- The acoustic corpus is WMSpeech-encoded:
  - `.IDX`: 72-byte header, 450-byte blocks, `WAVEFORMATEX` (tag `0x000A`,
    16 kHz, mono, 16-bit), 66,218 decoded-length entries.
  - `.CSD`: 66,218 fixed 450-byte blocks, XOR-obfuscated with a 129-byte key.
  - Decoding uses the system **WMSpeech Decoder DMO** (`WMSPDMOD.DLL`).
- The 64-bit engine activates the 32-bit `MSTTSDecWrp.dll` through a COM surrogate
  and marshals the interface with the Global Interface Table.
- The renderer uses double-buffered unit lists, a render thread, 0x20-byte units,
  silence generation, a 200-sample overlap-add window, and SAPI
  word/phoneme/sentence/viseme events.

## Reproduce

The analysis requires a legally obtained Windows 7 Ultimate SP1 x64 image. The ISO
used for this dossier has:

```
size 3319496704
md5  88bacec0dab38dfdf84218924711ec8c
sha1 90c2e7ee664f7cca1e8ae5d912ec805bbae43261
```

Extract image 4 (`Windows 7 ULTIMATE`) and run:

```sh
python scripts/parse_voice.py \
  "extracted/win7/Program Files (x86)/Common Files/SpeechEngines/Microsoft/TTS20/en-US/enu-dsk"
```

Ghidra 12.2 + JDK 25 scripts are in `scripts/ghidra/`; examples are in
`docs/README.md`.

## Archive

`archive/anna-session.zip` is a sanitized copy of the OMP session archive produced
by `export_session_archive` from `alosslessdev/omp-archive-main`.

- The original archive contained 21 files / 5,876,997 bytes.
- Local user paths were replaced with `%USERPROFILE%`; no credentials or tokens
  were present.
- `session.jsonl`, tool logs, `agents.json`, `jobs.json`, and `viewer.html` are
  otherwise retained.

## Legal and scope

This repository is independent analysis and is not affiliated with Microsoft.

It deliberately does **not** contain the Windows 7 ISO, `install.wim`, Microsoft
DLLs/EXEs, the Anna voice data files, or the full decompiled C output. Those are
third-party binaries/corpora; obtain them from a licensed source. The session
archive is a research log, not a redistribution of those artifacts.

Microsoft, Windows, and Microsoft Anna are trademarks of Microsoft Corporation.

## Limitations

Architecture-level reimplementation is feasible from these notes. Bit-exact voice
reproduction is not established: the `.CSD` corpus and WMSpeech codec are
proprietary, and no voice was recreated. Remaining unknowns are listed in
`docs/03-engine.md` and `docs/05-reimplementation.md`.
