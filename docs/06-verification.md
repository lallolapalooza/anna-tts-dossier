# 6. Verification log

## 6.1 Source image

```
size 3319496704 expected 3319496704 match True
md5  88bacec0dab38dfdf84218924711ec8c expected 88bacec0dab38dfdf84218924711ec8c
sha1 90c2e7ee664f7cca1e8ae5d912ec805bbae43261 expected 90c2e7ee664f7cca1e8ae5d912ec805bbae43261
```

`7z l` reports `Type = Udf`; `sources\install.wim` is 2,952,976,413 bytes.

WIM metadata (`wimlib-imagex info`): 4 images, LZX, build 7601/SP1. Image 4 is:

```
Name: Windows 7 ULTIMATE
Architecture: x86_64
Edition ID: Ultimate
Major/Minor/Build: 6.1.7601
Service Pack Build: 17514
Service Pack Level: 1
```

All analysis used image 4.

## 6.2 Artifact hashes

`out/artifacts.json` contains full SHA-256 values. Key binaries:

| File | SHA-256 |
|---|---|
| x64 `MSTTSEngine.dll` | `36b15355ecfb20bf2fbad54ef476db9a1031059f85dbd60dbd1c00c4f8fe4ca1` |
| x64 `MSTTSFrontendENU.dll` | `355481797be01c22764074ae4066d079d5d504611bffdc865fc9a2515c86e9e0` |
| x64 `MSTTSCommon.dll` | `c8103a800569db0e900fc91120aa63a1e04a94646bf7efbcfc1a61d8d85f48dc` |
| x86 `MSTTSDecWrp.dll` | `0c316510a86f2988f624093f6223e1ea7981cb9a549695fcff2bdd6c2ebaf489` |
| x64 `sapi.dll` | `e7c5f172bc194548bdb09cb6ba9d570cda559adf9cb634fdc2086884a26ea290` |
| `M1033DSK.CSD` | `5c087dd0761a5e7cb73b363e5953495a69abf87b2fe97d55edc8b1f4b1ad142e` |
| `M1033DSK.IDX` | `ba40b25afe64e9c9e2e75c59dc982bf54a20a2695cf2280db94500776b761102` |

## 6.3 Registry facts

Parsed directly from the image's `Windows/System32/config/SOFTWARE` hive
(`out/win7-software.json`):

```
token: MS-Anna-1033-20-DSK
CLSID: {F51C7B23-6566-424C-94CF-2C4F83EE96FF}
Frontend: {55DFB4F7-4175-4B3B-B247-D9B399ADB119}
VoiceName: M1033DSK
VoicePath: D:\Program Files (x86)\Common Files\SpeechEngines\Microsoft\TTS20\en-US\enu-dsk
Lex\CLSID: {90903716-2F42-11D3-9C26-00C04F8EF87C}
Lex\DataFile: <VoicePath>\M1033DSK.TTS
Attributes\AudioFormats: 18
```

Both `\Microsoft\Speech\Voices\Tokens` and
`\Wow6432Node\Microsoft\Speech\Voices\Tokens` contain the same token.

```
CLSID {F51C7B23-...} InprocServer32 = %CommonProgramFiles%\SpeechEngines\Microsoft\TTS20\MSTTSEngine.dll
CLSID {55DFB4F7-...} InprocServer32 = %CommonProgramFiles%\SpeechEngines\Microsoft\TTS20\en-US\MSTTSFrontendENU.dll
CLSID {3F6B5E16-...} AppID = "MSTTS DecObj Class Surrogate", DllSurrogate present
CLSID {874131CB-4ECC-443B-8948-746B89595D20} = WMSpeech Decoder DMO -> WMSPDMOD.DLL
```

## 6.4 Type libraries

Extracted from the PE `TYPELIB` resources and parsed with `comtypes`
(`scripts/tlb_dump.py`):

| Binary | TypeLib GUID | Types |
|---|---|---|
| `MSTTSEngine.dll` | `{6A379714-E19D-4D0F-AAC6-20D5F143C420}` | `TTSEngine`, `ISpTTSEngine`, `ISpObjectWithToken`, `ITTSSupportDebug`, `ISpEnginePronunciation` |
| `MSTTSFrontendENU.dll` | `{A7201431-623E-44A7-A85C-D13AFC0F6AA6}` | `MSTTSFrontendENU`, `ITTSFrontend`, `tagUnitSpec` |
| `MSTTSCommon.dll` | `{613808A3-159B-4D91-B4F0-A22AEE2D1AAC}` | `LTS`, `ILTS` |
| `MSTTSDecWrp.dll` | `{EDEBC0B7-FA4D-45FB-B750-16C8D2340AE8}` | `DecObj`, `IDecObj` |

Vtable offsets and parameter names in `docs/02-components.md` come from the parsed
type libraries, not from reading assembly by eye.

## 6.5 Ghidra inventories

| Project | Image base | Functions |
|---|---:|---:|
| `AnnaEngine64` | `0x7ff31780000` | 441 |
| `AnnaFrontend64` | `0x7ff360a0000` | 517 |
| `AnnaDecWrp32` | `0x41500000` | 322 |
| `AnnaCommon64` | `0x7ff25bd0000` | 124 |

Decompiled function counts: 409 (engine), 484 (frontend), 297 (decoder),
103 (LTS). All decompiled outputs are retained in `out/decomp/`.

## 6.6 Container validation

`python scripts/parse_voice.py <voice-dir> > out/voice-metadata.json`:

```
header_size 72
block_size 450
format_size 64
WAVEFORMATEX tag=0x000A ch=1 rate=16000 avg=1500 align=450 bits=16 cb=46
block_count 66218
decoded_samples 635637906
decoded_seconds 39727.37
length_min 4800
length_max 18240
csd_size 29798100
expected_csd_size 29798100
size_matches true
```

WIH header: `00000000 03000000 803e0000 02000100` → version 0, selector 3,
16000 Hz, 2 bytes/sample, 1 channel.

UDT header: `55445400` (`UDT\0`), version 1, 260 entries, LCID `0x409`.

## 6.7 Constraint check

- No `.wav`, `.mp3`, or other audio output exists in the workspace.
- No Anna audio was decoded, synthesized, cloned, or compared for parity.
- The dossier documents architecture and container formats only.

## 6.8 Known limits

- Static analysis cannot prove runtime behavior such as exact audio output.
- `.APL`, `.UNT`, `.CRT` record layouts and `.WIH` payload semantics remain open.
- Unit-selection weights and the exact frontend lexicon/rule split are not fully
  labelled.
- The proxy/surrogate registration is inferred from the AppID and the 32-bit-only
  decoder DLL; no live Win7 machine was used.
