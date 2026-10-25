> **Evidence note.** This public repository intentionally excludes the Windows 7
> image, Microsoft binaries, Anna voice corpora, and the full decompiled C output.
> Paths such as `out/decomp/` and `out/ghidra/` refer to the local analysis
> workspace; the documents and parsed data here are self-contained. The sanitized
> session archive under `archive/` retains the research transcript.

# Anna dossier index

Target: Microsoft Anna SAPI5 voice as shipped in
`Microsoft Windows 7 Ultimate with Service Pack 1 (64-bit)`
(archive.org item `microsoft-windows-7-ultimate-with-service-pack-1-64-bit`).

Constraint: architecture documentation only. No voice recreation, cloning, or
sample-parity claim.

## Read in order

| Doc | Contents |
|---|---|
| [00-scope.md](00-scope.md) | scope, non-goals, acceptance criteria |
| [01-sapi-host.md](01-sapi-host.md) | SAPI 5 host contract and COM interfaces |
| [02-components.md](02-components.md) | extracted files, hashes, registry, CLSIDs, embedded type libraries |
| [03-engine.md](03-engine.md) | engine/frontend object layout, initialization, render loop, text pipeline, formats |
| [04-formats.md](04-formats.md) | byte-level `.IDX`/`.CSD`/`.WIH`/`.LTS`/`.UDT` layouts, decoder and XOR key |
| [05-reimplementation.md](05-reimplementation.md) | build spec, pseudocode, structures, acceptance checks, feasibility |
| [06-verification.md](06-verification.md) | hashes, registry/TLB checks, Ghidra counts, container validation |
| [07-function-map.md](07-function-map.md) | address-to-role map for engine, frontend, decoder, LTS |

## Artifacts

| Path | Meaning |
|---|---|
| `extracted/win7/` | files extracted from image index 4 (Ultimate) |
| `extracted/sources/install.wim` | original WIM (not modified) |
| `out/artifacts.json` | SHA-256 inventory |
| `out/win7-software.json` | SAPI voice/CLSID registry dump |
| `out/tlb/*.tlb`, `out/tlb/*.json` | extracted type libraries and full interface dumps |
| `out/ghidra/*.json` | Ghidra inventories (functions, strings, imports, composites) |
| `out/decomp/engine64/` | 409 decompiled engine functions |
| `out/decomp/frontend64/` | 484 decompiled frontend functions |
| `out/decomp/decwrp32/` | 297 decompiled decoder-wrapper functions |
| `out/decomp/common64/` | 103 decompiled LTS functions |
| `scripts/parse_voice.py` | container parser/validator |
| `scripts/pe_inventory.py` | PE metadata -> JSON |
| `scripts/hive_dump.py`, `scripts/tlb_dump.py` | registry and TLB evidence |
| `scripts/ghidra/` | headless inventory/decompile scripts |

## Reproduce

```sh
# container metadata
python scripts/parse_voice.py \
  "extracted/win7/Program Files (x86)/Common Files/SpeechEngines/Microsoft/TTS20/en-US/enu-dsk"

# type library dumps
for f in engine frontend common decwrp; do
  python scripts/tlb_dump.py out/tlb/$f.tlb out/tlb/$f.json
done

# PE inventory
python scripts/pe_inventory.py \
  "extracted/win7/Program Files/Common Files/SpeechEngines/Microsoft/TTS20/MSTTSEngine.dll"

# Ghidra (JDK 25, Ghidra 12.2)
export JAVA_HOME="$PWD/tools/jdk-25.0.4.1+1"
export GHIDRA_INSTALL_DIR="$PWD/tools/ghidra_12.2_PUBLIC"
python -m pyghidra --install-dir "$GHIDRA_INSTALL_DIR" \
  --project-path proj --project-name AnnaEngine64 \
  "extracted/win7/Program Files/Common Files/SpeechEngines/Microsoft/TTS20/MSTTSEngine.dll" \
  scripts/ghidra/DumpInventory.py out/ghidra/engine64.json
```

## Verification status

- ISO size, MD5 and SHA-1 match the archive metadata.
- `install.wim` image 4 is `Windows 7 ULTIMATE` x64, build 7601 SP1.
- Registry token and both 32/64-bit views agree.
- Embedded type libraries parse and match the registry CLSIDs.
- `parse_voice.py` validates all container invariants (see `04-formats.md`).
- No audio was decoded or generated for this dossier.
