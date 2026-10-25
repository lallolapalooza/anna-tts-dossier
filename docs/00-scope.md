# 0. Scope and success criteria

## Decision

**Architecture documentation only.** No voice recreation, voice cloning, sample
synthesis, or parity claim against Anna's audio. This follows the project owner's
constraint: if a faithful reimplementation is not possible, do not recreate the voice.

## Why full parity is out of scope

Static analysis of the shipped binaries can recover control flow, interfaces, file
formats and algorithms. It cannot, by itself, lawfully reproduce the recorded speech
corpus or guarantee bit-exact output parity of a proprietary unit-selection engine.
Any claim of "100% sample parity" would require executing the original engine and
matching every rendered sample, which is not established by this dossier.

## Deliverables

1. Artifact inventory with hashes, PE metadata, registry registration and install paths.
2. SAPI 5 host contract and the exact engine interfaces Anna implements.
3. Engine architecture: COM objects, class factory, vtables, lifetime, threading.
4. Data pipeline: token data, language data, lexicon/LTS, prosody, unit selection,
   waveform assembly, output format negotiation.
5. Data-format notes for the voice/language containers, with byte-level evidence.
6. Reimplementation specification: required components, invariants, unknowns.
7. Explicit feasibility assessment and residual unknowns.

## Acceptance criteria

- Every path/hash/CLSID/address claim is reproducible from the extracted image or the
  cited Microsoft documentation.
- Decompiled excerpts are quoted with image base and address.
- Unresolved areas are labeled `[UNKNOWN]` rather than guessed.
- No audio is generated from Anna's voice data.
