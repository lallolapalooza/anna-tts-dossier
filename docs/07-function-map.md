# 7. Function map

Addresses are Ghidra virtual addresses; image bases are in
`docs/06-verification.md`. Names are exported names where available, otherwise
`FUN_<address>`. Roles are evidence-backed unless marked `[INFERENCE]`.

## 7.1 MSTTSEngine.dll (x64, base 0x7ff31780000)

| Address | Function | Role |
|---:|---|---|
| `0x7ff317915cc` | `DllGetClassObject` | class-table lookup for `TTSEngine` |
| `0x7ff317916ec` | `DllRegisterServer` | register CLSID/AppID/type library |
| `0x7ff317a1ae4` | `FUN_` | initialize class table (`&PTR_PTR_...`) |
| `0x7ff3179028c` | `FUN_` | create class factory (0x48 bytes) |
| `0x7ff31790470` | `FUN_` | create engine object, non-aggregated (0x110) |
| `0x7ff317905d8` | `FUN_` | create engine object, aggregated (0x128) |
| `0x7ff3179284c` | `FUN_` | `ISpObjectWithToken::SetObjectToken` |
| `0x7ff3179322c` | `FUN_` | token init: frontend, voice, rate, format |
| `0x7ff3179289c` | `FUN_` | `ISpTTSEngine::Speak` |
| `0x7ff317929dc` | `FUN_` | `ISpTTSEngine::GetOutputFormat` |
| `0x7ff31797484` | `FUN_` | load voice: WIH header + caches |
| `0x7ff3179a3b4` | `FUN_` | select WVE/CSD/WIH container |
| `0x7ff3179a958` | `FUN_` | `.CSD` init: create `DecObj` |
| `0x7ff3179ab04` | `FUN_` | `.CSD` read through decoder |
| `0x7ff3179acb4` | `FUN_` | `.WIH` open |
| `0x7ff3179ad48` | `FUN_` | `.WIH` read at `offset+0x10` |
| `0x7ff3179a6c8` | `FUN_` | `.WVE` open |
| `0x7ff31799958` | `FUN_` | load `.APL`, `.UNT`, `.CRT` |
| `0x7ff31798254` | `FUN_` | create renderer + cosine join window |
| `0x7ff31792a58` | `FUN_` | render loop / double buffering |
| `0x7ff31793064` | `FUN_` | fetch unit specs, build 0x20-byte units |
| `0x7ff317938a0` | `FUN_` | render a batch of units |
| `0x7ff3179899c` | `FUN_` | per-unit silence/decode/XOR/join |
| `0x7ff31798f54` | `FUN_` | apply overlap-add window |
| `0x7ff31790bfc` | `FUN_` | emit word/phoneme/sentence/viseme events |
| `0x7ff31792668` | `FUN_` | create render thread and events |
| `0x7ff31792ee4` | `FUN_` | render worker thread |
| `0x7ff31794364` | `FUN_` | build `WAVEFORMATEX` from format ID |
| `0x7ff317947dc` | `FUN_` | allocate prosody/PSOLA buffers |
| `0x7ff317948ec` | `FUN_` | set sample rate/period sizes |
| `0x7ff31794894` | `FUN_` | set rate factor |

## 7.2 MSTTSFrontendENU.dll (x64, base 0x7ff360a0000)

`ITTSFrontend` subobject is at object `+0x18`, vtable `0x7ff360a6540`.

| Address | Function | Role |
|---:|---|---|
| `0x7ff360c58ac` | `DllGetClassObject` | frontend class factory |
| `0x7ff360b8e48` | `FUN_` | `Initialize(ISpObjectToken*)` |
| `0x7ff360b92a0` | `FUN_` | `PrepareSpeech` |
| `0x7ff360b9304` | stub | `FinishSpeech` (`cmp [rcx+0x108],rax; sete al`) |
| `0x7ff360b9318` | `FUN_` | `GetNextUnitSpecList` |
| `0x7ff360bed4c` | `FUN_` | `Normalize` |
| `0x7ff360bed88` | `FUN_` | `GetPronunciations` |
| `0x7ff360bcdec` | `FUN_` | parser batch orchestrator |
| `0x7ff360bc420` | `FUN_` | scan/normalize text, build 0x6a0 word records |
| `0x7ff360bd094` | `FUN_` | lexicon/pronunciation stage `[INFERENCE]` |
| `0x7ff360bd26c` | `FUN_` | rule/pronunciation stage `[INFERENCE]` |
| `0x7ff360b96bc` | `FUN_` | candidate preparation |
| `0x7ff360b9bd8` | `FUN_` | unit selection from 0x50-byte records |
| `0x7ff360bd8f8` | `FUN_` | emit 0x70-byte `tagUnitSpec` |
| `0x7ff360be260` | `FUN_` | attach events to a unit |
| `0x7ff360be618` | `FUN_` | normalization core |
| `0x7ff360bef60` | `FUN_` | copy/attach spec fields |
| `0x7ff360c032c` | `FUN_` | voice-context cache |
| `0x7ff360c054c` | `FUN_` | load frontend data (0x200 object) |
| `0x7ff360cd6cc` | `FUN_` | build phoneme tables (177/71/42) |
| `0x7ff360d2898` | `FUN_` | append `.LTS` to voice path |

## 7.3 MSTTSDecWrp.dll (x86, base 0x41500000)

| Address | Function | Role |
|---:|---|---|
| `0x4150586a` | `DllGetClassObject` | `DecObj` factory |
| `0x4150877e` | `FUN_` | `IDecObj::Initialize(csd, idx)` |
| `0x41508303` | `FUN_` | read/XOR/timestamp one 450-byte block |
| `0x41508407` | `FUN_` | locate and copy decoded PCM for a sample range |
| `0x41506f07` | `FUN_` | build `SAFEARRAY` PCM result (`vt=0x2011`) |
| `0x41508cd8` | `FUN_` | create/setup WMSpeech DMO |
| `0x41508c90` | `FUN_` | validate WMSpeech output format |

## 7.4 MSTTSCommon.dll (x64, base 0x7ff25bd0000)

| Address | Function | Role |
|---:|---|---|
| `0x7ff25bd4660` | `DllGetClassObject` | `LTS` factory |
| `0x7ff25bd581c` | `FUN_` | parse `.LTS` sections/tables |
| `0x7ff25bd4b20` | `FUN_` | ATL COM registration helper |

## 7.5 Key data addresses (engine)

| Address | Bytes | Role |
|---:|---|---|
| `0x7ff317a64d8` | 32 | PCM XOR mask used in `FUN_9899c` |
| `0x7ff3178bf10` | 36 | sample-rate table for output formats |
| `0x7ff3178bfc8` | 32 | secondary rate table |
| `0x7ff3178bea0` | 16 | `IID_IUnknown` |
| `0x7ff3178bf00` | 16 | `IID_ITTSFrontend` |
| `0x7ff317a6360` | 16 | `CLSID_DecObj` |
| `0x7ff3178c1f0` | 16 | `IID_IDecObj` |

## 7.6 Key data addresses (frontend)

| Address | Role |
|---:|---|
| `0x7ff360e73f8` | null/empty spec sentinel table |
| `0x7ff360e7598` | special spec-list marker (`[INFERENCE]` bookmark/silence) |
| `0x7ff360ede18` | phoneme table 1 (177 entries) |
| `0x7ff360f1b48` | phoneme table 2 (71 entries) |
| `0x7ff360f3408` | phoneme table 3 (42 entries) |
