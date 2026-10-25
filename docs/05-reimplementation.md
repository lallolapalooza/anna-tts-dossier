# 5. Reimplementation specification

This is the handoff contract for an agent or engineer rebuilding the **architecture**
of Anna. It does not authorize or describe voice cloning; no Anna samples were
rendered.

## 5.1 Components

| Component | Responsibility | Evidence |
|---|---|---|
| Host | SAPI `SpVoice` + `ISpTTSEngineSite`; token enumeration; audio output | Microsoft SAPI 5.3 docs, `sapi.dll` |
| Engine | `TTSEngine` COM object; token init; voice load; render thread; output format | `docs/03-engine.md`, `out/decomp/engine64` |
| Frontend | text normalization, lexicon/LTS, phonemes, prosody, unit selection | `docs/03-engine.md`, `out/decomp/frontend64` |
| Decoder | `DecObj`; CSD/IDX parse; WMSpeech DMO bridge | `docs/04-formats.md`, `out/decomp/decwrp32` |
| LTS | `ILTS` letter-to-sound rules | `out/decomp/common64` |
| Data | `.IDX`, `.CSD`, `.WIH`, `.UDT`, `.LTS`, `.APL`, `.UNT`, `.CRT`, `.TTS` | `docs/04-formats.md` |

## 5.2 Required COM surface

```c
interface ISpTTSEngine : IUnknown {
  HRESULT Speak(DWORD flags, REFGUID fmt, const WAVEFORMATEX *wf,
                const SPVTEXTFRAG *frags, ISpTTSEngineSite *site);
  HRESULT GetOutputFormat(REFGUID target, const WAVEFORMATEX *wf,
                          GUID *outFmt, WAVEFORMATEX **outWf);
};

interface ISpObjectWithToken : IUnknown {
  HRESULT SetObjectToken(ISpObjectToken *token);
  HRESULT GetObjectToken(ISpObjectToken **token);
};

interface ITTSFrontend : IUnknown {
  HRESULT Initialize(ISpObjectToken *token);
  HRESULT PrepareSpeech(SPVTEXTFRAG *frags, DWORD flags,
                        ISpTTSEngineSite *site);
  HRESULT FinishSpeech();
  HRESULT GetNextUnitSpecList(tagUnitSpec **list, LONG *count,
                              tagSPEECH_STATE *state, LONG *skip);
  HRESULT Normalize(LPWSTR word, LPWSTR left, LPWSTR right, USHORT lang,
                    SPNORMALIZATIONLIST *out);
  HRESULT GetPronunciations(LPWSTR word, LPWSTR left, LPWSTR right,
                            USHORT lang, SPWORDPRONUNCIATIONLIST *out);
};
```

## 5.3 Engine behavior

```
SetObjectToken(token):
    frontendClsid = token.getString("Frontend")
    frontend = CoCreateInstance(frontendClsid, IID_ITTSFrontend)
    frontend.Initialize(token)
    voice = loadVoice(token.getString("VoicePath"),
                      token.getString("VoiceName"))
    rate = clamp(token.getDWORD("DefaultRate"), -20, 20)
    tempo.setFactor(pow(3.0, rate / 10.0))
    outputFormat = voice.sampleRate == 16000 ? 0x12 : ...
```

```
Speak(flags, fmt, wf, frags, site):
    if fmt not in {SPDFID_WaveFormatEx, SPDFID_Text}: return E_INVALIDARG
    this.site = site
    frontend.PrepareSpeech(frags, flags, site)
    renderLoop()                  // fills double buffers, signals worker
    frontend.FinishSpeech()
```

The worker:

```
while not abort:
    wait(workEvent)
    renderUnits(currentList)
    set(idleEvent)
```

`renderUnits`:

```
for each unit:
    if unit.type == 0:
        emit zero PCM of unit.sampleCount
    else:
        raw = decoder.read(unit.index, unit.length)   // 16-bit PCM
        xor(raw, 32-byte mask)
        append(raw)
        if join flags: overlapAdd(raw, window)
    post events 5/6/7/8 with stream offsets
```

## 5.4 Frontend behavior

```
Initialize(token):
    path = token.getString("VoicePath") + "\" + token.getString("VoiceName")
    context = cache.getOrLoad(path)
    data = context.load(dataFiles)          // .APL/.UNT/.CRT/.UDT/.LTS
    return

PrepareSpeech(frags, flags, site):
    parser.reset()
    this.site = site
    reset prosody/event state

GetNextUnitSpecList(outList, outCount, outState, skip):
    parser.skip(skip)
    specs = parser.nextBatch()              // 0x70-byte tagUnitSpec
    for each spec: attach events (word/phoneme/sentence/viseme)
    *outList = specs; *outCount = n; *outState = done ? 1 : 0
```

Parser batch (`FUN_7ff360bcdec`):

1. `reset()`
2. `scanAndNormalize()` — `FUN_7ff360bc420`
3. `resolveLexicon()` — `FUN_7ff360bd094`
4. `applyRules()` — `FUN_7ff360bd26c`
5. `prepareCandidates()` — `FUN_7ff360b96bc`
6. `selectUnits()` — `FUN_7ff360b9bd8`
7. `emitSpecs()` — `FUN_7ff360bd8f8`

## 5.5 Structures

```c
/* 12-byte voice info produced by the WIH loader */
typedef struct {
    uint8_t  format;        // 3
    uint8_t  pad[3];
    uint32_t sampleRate;    // 16000
    uint16_t bytesPerSample;// 2
    uint16_t channels;      // 1
    uint8_t  valid;         // 0
} AnnaVoiceInfo;

/* 32-byte engine render unit (internal, reconstructed from FUN_98470/FUN_9899c) */
typedef struct {
    uint16_t type;          // 0=silence
    uint16_t phone;
    uint32_t index;
    uint32_t position;
    uint32_t samples;
    uint32_t sourcePos;
    uint32_t field14;
    uint32_t field18;
    uint8_t  joinLeft;
    uint8_t  joinRight;
    uint8_t  pad[2];
} AnnaRenderUnit;

/* Type-library tagUnitSpec (19 fields, order verified) */
struct tagUnitSpec {
    USHORT wLangID;
    SHORT  sUnitIndex;
    CArray bUnitFeatureVector;
    tagSENT_PUNCTUATION_TYPE ePuncType;
    ULONG  lFrontPhoneFlags;
    ULONG  lBackPhoneFlags;
    tagBREAK_LEVEL_TYPE eBreakLevel;
    LONG   lVolume, lRate, lPitch, lVoice;
    LONG   m_CtrlFlags;
    ULONG  m_SrcPosition, m_SrcLen;
    ULONG  m_SentencePosition, m_SentenceLen;
    LONG   lUserBreak;
    LONG   m_nNumOfEvents;
    SPEVENT *m_pEventArray;
};
```

## 5.6 Decoder

```
Initialize(csdPath, idxPath):
    idx = open(idxPath)
    headerSize = u32(idx); blockSize = u16(idx); formatSize = u16(idx)
    format = read(idx, formatSize)          // WAVEFORMATEX + codec data
    count = (fileSize(idx) - headerSize) / 2
    lengths = read u16[count]
    blocks = open(csdPath)
    create WMSpeech DMO {874131CB-...}
    set input type from format
```

```
Read(start, length):
    locate block range by cumulative lengths
    for each block:
        data = read 450 bytes at blockIndex * 450
        data ^= key[i % 129]
        dmo.processInput(data, timestamp = index*10^7/16000)
        pcm += dmo.processOutput()
    return VARIANT(VT_ARRAY|VT_UI2) slice
```

## 5.7 Acceptance checks

| Check | Expected |
|---|---|
| IDX header | `headerSize=72`, `blockSize=450`, `formatSize=64` |
| IDX WAVEFORMATEX | tag 0x0A, 1 ch, 16000 Hz, 16 bit, align 450, avg 1500 |
| block count | 66,218 |
| CSD size | `blockCount * 450` = 29,798,100 |
| decoded lengths | sum 635,637,906 samples |
| WIH header | `format=3`, 16000 Hz, 2 bytes/sample, 1 channel |
| UDT | `UDT\0`, version 1, 260 entries, LCID 0x409 |
| decoder | WMSpeech DMO `{874131CB-...}` available |
| engine format | `GetOutputFormat` returns 16 kHz/16-bit/mono, `AudioFormats=18` |

`scripts/parse_voice.py` passes all container checks on the extracted files.

## 5.8 Feasibility statement

- **Architecture reimplementation:** feasible; interfaces, object layout, data
  paths, decoder identity, XOR transform and join algorithm are documented.
- **Bit-exact Anna voice:** not established and out of scope. The proprietary
  `.CSD` corpus and WMSpeech codec are the blockers; no voice was recreated.
- **Remaining unknowns:** `.APL`/`.UNT`/`.CRT` record semantics, `.WIH` payload
  meaning, unit-selection cost weights, exact `FinishSpeech` behavior.

## 5.9 Evidence map

| Topic | File |
|---|---|
| Provenance + scope | `README.md`, `docs/00-scope.md` |
| SAPI contract | `docs/01-sapi-host.md` |
| Artifacts, registry, COM | `docs/02-components.md`, `out/artifacts.json`, `out/tlb/*.json` |
| Engine/frontend architecture | `docs/03-engine.md`, `out/decomp/engine64/`, `out/decomp/frontend64/` |
| Data formats | `docs/04-formats.md`, `scripts/parse_voice.py` |
| Decoder/LTS | `out/decomp/decwrp32/`, `out/decomp/common64/` |
| Ghidra inventories | `out/ghidra/*.json` |
