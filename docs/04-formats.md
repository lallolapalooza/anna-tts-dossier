# 4. Anna data formats and reimplementation reference

This section is byte-level evidence for the Anna voice set. It intentionally stops at
container decoding: no voice audio is recreated.

## 4.1 Voice set

Path (32-bit Common Files; the 64-bit engine uses the same files through the token):

```
%CommonProgramFiles(x86)%\SpeechEngines\Microsoft\TTS20\en-US\enu-dsk\
  M1033DSK.TTS    2,430,393   SAPI compressed lexicon (token Lex\DataFile)
  M1033DSK.CSD   29,798,100   WMSpeech compressed speech blocks
  M1033DSK.IDX      132,508   block table + WAVEFORMATEX
  M1033DSK.WIH    3,597,414   wave inventory (16-byte header + payload)
  M1033DSK.LTS      931,696   letter-to-sound rule table
  M1033DSK.UDT       11,166   unit/phone table ("UDT\0", 260 entries, LCID 0x409)
  M1033DSK.UNT    3,182,160   unit/name table
  M1033DSK.CRT      484,600   context/rule table
  M1033DSK.APL       16,066   application/rule table
```

`parse_voice.py` reproduces the metadata below:

```json
{
  "header_size": 72,
  "block_size": 450,
  "format_size": 64,
  "wave_format": {
    "format_tag": 10,
    "channels": 1,
    "samples_per_sec": 16000,
    "avg_bytes_per_sec": 1500,
    "block_align": 450,
    "bits_per_sample": 16,
    "cb_size": 46
  },
  "block_count": 66218,
  "decoded_samples": 635637906,
  "decoded_seconds": 39727.37,
  "length_min": 4800,
  "length_max": 18240,
  "size_matches": true
}
```

## 4.2 `.IDX` — precise layout

```
offset 0   u32  headerSize              // 72
offset 4   u16  blockSize               // 450
offset 6   u16  formatSize              // 64
offset 8   u8   format[formatSize]      // WAVEFORMATEX + codec data
offset headerSize:
           u16  decodedLength[count]    // count = (fileSize - headerSize) / 2
```

`format[0..17]` is a `WAVEFORMATEX`:

| Field | Value |
|---|---|
| `wFormatTag` | `0x000A` (`WAVE_FORMAT_WMSPEECH`) |
| `nChannels` | 1 |
| `nSamplesPerSec` | 16000 |
| `nAvgBytesPerSec` | 1500 |
| `nBlockAlign` | 450 |
| `wBitsPerSample` | 16 |
| `cbSize` | 46 |

The 46-byte codec data begins:

```
10 00 04 00 00 00 00 00 00 00 00 00 00 00 10 00
00 00 a7 99 1a 00 05 c9 2d 40 14 5a 60 00 ...
```

`[UNKNOWN]` the exact WMSpeech codec-data fields; they are passed to the DMO
unchanged by `MSTTSDecWrp`.

The length table has exactly 66,218 entries. Its sum is 635,637,906 samples
(39,727.37 s at 16 kHz). Values are multiples of 480 (10 ms), consistent with a
codec frame quantum; observed range 4,800..18,240 samples (100–380 ms).

## 4.3 `.CSD` — precise layout

```
block i: bytes [i*450, (i+1)*450)
count  : 66218  (file size / 450)
```

Each 450-byte block is XOR-obfuscated before being fed to the WMSpeech decoder.
The key is the following 128-byte ASCII string; the C code indexes it modulo
`0x81`, so index 128 is the terminating NUL and XORs with 0:

```
wyClImqDdiZXo70AojxIgiuuUyaR2iZ1ibjHbPfShaPJdRcRCa1i9b6ELZEOQRPWSOzA8SwpvfSCJR0XhzeyuNClPut80OJVSyHirCHyVp1egkunuTG2HzOROvXY5ukw
```

Decode block `i`:

```python
block = csd[i*450:(i+1)*450]
clear = bytes(b ^ key[j % 129] for j, b in enumerate(block))
```

`MSTTSDecWrp!FUN_41508303` then:

1. timestamps it as `i * 10_000_000 / 16000` (100 ns units);
2. calls the DMO input method;
3. pulls decoded 16-bit PCM from the DMO output.

The read path fills a `VARIANT` with `vt = 0x2011` (`VT_ARRAY | VT_UI2`) whose
`SAFEARRAY` contains 16-bit PCM; `start`/`length` are sample offsets resolved
through the cumulative `decodedLength` table. The type library names the method
`ReadBSTR`.

## 4.4 Decoder object

`MSTTSDecWrp.dll` (x86) implements:
- coclass `DecObj` `{3F6B5E16-092A-41ED-930B-0B4125D91D4E}`,
- interface `IDecObj` `{EAAB8DA2-1E94-4037-BB4A-39A8B7B00BC8}`,
- `Initialize(csdPath, idxPath)`, `ReadBSTR(start, length)`.

Registration:
- `HKLM\SOFTWARE\Classes\AppID\{3F6B5E16-...}` = `MSTTS DecObj Class Surrogate`,
  `DllSurrogate` present (empty value).
- The 64-bit engine calls it with `CLSCTX_LOCAL_SERVER` and stores the marshaled
  interface in the Global Interface Table; the 32-bit engine uses in-process.

The codec is the system **WMSpeech Decoder DMO**:

| Item | Value |
|---|---|
| CLSID | `{874131CB-4ECC-443B-8948-746B89595D20}` |
| Name | `WMSpeech Decoder DMO` |
| DLL | `%SystemRoot%\System32\WMSPDMOD.DLL` |
| Input | 450-byte WMSpeech blocks, 16 kHz mono |
| Output | 16-bit PCM |

## 4.5 `.WIH` — header and payload

Header (16 bytes, little-endian):

| Offset | Type | Anna value | Meaning |
|---:|---|---:|---|
| 0 | u32 | 0 | version/reserved |
| 4 | u8 | 3 | format selector |
| 5 | u8[3] | 0 | reserved |
| 8 | u32 | 16000 | sample rate |
| 12 | u16 | 2 | bytes per sample |
| 14 | u16 | 1 | channels |

Engine loader `FUN_7ff31797484` reads exactly 16 bytes and keeps
`{format=3, rate=16000, bytesPerSample=2, channels=1}`. The WIH object
(`FUN_7ff3179acb4`, `FUN_7ff3179ad48`) opens the file and reads at
`offset + 0x10`, so the payload begins immediately after the header.

Payload starts at offset 16 with `80 e1 80 e1 63 60 5b 59 5a 55 5c 57 ...`,
which is `int16` data. `[UNKNOWN]` the record semantics; the payload is about 1.8M `u16`
values, far smaller than the decoded PCM and consistent with per-unit boundary
or pitch/energy metadata, not audio.

## 4.6 `.LTS` — rule table

`MSTTSCommon!FUN_7ff25bd581c` reads:

1. `u32 sectionSize` (used to align/pad the following section);
2. `u32 count1`, then `count1 * u32`;
3. `u32 count2`, then `count2` bytes;
4. zero-padding until the `sectionSize` boundary;
5. `u32 count3`, `count3` bytes, then padding;
6. `u32 count4`, `count4 * u32`, then padding;
7. `u32 count5`, `count5 * u32`, then padding;
8. a final `u32 count6` and `count6 * 4` bytes.

Observed pronunciation strings in the file include:

```
aa1 r, aa1 k s, ae n d, ae1 k, ah1 n, ah1 sh, ah1 z, ao ax, ao r, ...
```

`[INFERENCE]` the arrays are a symbol table, a rule/offset table, and a
pronunciation-string pool for the letter-to-sound engine.

## 4.7 `.UDT`

Header:

| Offset | Type | Value |
|---:|---|---:|
| 0 | char[4] | `UDT\0` |
| 4 | u32 | 1 |
| 8 | u32 | 260 |
| 12 | u16 | 0x0409 |

`260` entries; the entry area contains UTF-16 phone strings such as
`aa+l`, `aa+m`, `ae+d`, `ah+ng`. `[INFERENCE]` each entry maps a phone/context
tuple to a unit ID used by the unit selector.

## 4.8 `.TTS`

The token's `Lex` subkey:

```
CLSID    {90903716-2F42-11D3-9C26-00C04F8EF87C}   SpCompressedLexicon
DataFile <VoicePath>\M1033DSK.TTS
```

So `.TTS` is a **SAPI compressed lexicon**, loaded by `sapi.dll`'s
`SpCompressedLexicon`, not by `MSTTSEngine.dll`. Its header begins with two GUIDs
and the LCID:

```
{12B545C3-0030-11D3-9C26-00C04F8EF87C}
{376FE444-3028-11D3-9C26-00C04F8EF87C}
u32 0x00000409
```

`[INFERENCE]` the GUIDs identify the lexicon format/version; the payload is the
lexicon entry table.

## 4.9 `.APL`, `.UNT`, `.CRT`

Observed headers:

| File | First bytes |
|---|---|
| `.APL` | `01 00 00 00 01 00 00 00 00 01 00 00` |
| `.UNT` | `01 00 00 00 00 01 00 00 05 01 00 00` |
| `.CRT` | `48 fd 07 00 00 01 00 00 f8 0d 00 00 f8 0e 00 00` |

Loaded by:
- `.APL` → `MSTTSEngine!FUN_7ff3179d238`
- `.UNT` → `MSTTSEngine!FUN_7ff31799a94`
- `.CRT` → `MSTTSEngine!FUN_7ff31799d78`

`[UNKNOWN]` exact record semantics; they are required for a working voice because
loading fails if any of the three is missing.

## 4.10 Reimplementation checklist

Minimum viable clone (architecture only, no Anna voice):

1. Parse IDX:
   - validate `headerSize`, `blockSize`, `formatSize`;
   - treat `format` as WAVEFORMATEX;
   - read `decodedLength[]`.
2. Parse CSD:
   - fixed 450-byte blocks;
   - XOR with the 129-byte key;
   - feed WMSpeech DMO (`WMSPDMOD.DLL`) or a compatible decoder.
3. Implement `IDecObj` with `Initialize`/`ReadBSTR`, returning 16-bit PCM.
4. Implement the engine renderer:
   - 0x20-byte render units;
   - silence generation;
   - 200-sample cosine overlap-add at joins;
   - event types 5/6/7/8;
   - output `WAVEFORMATEX` 16 kHz, 16-bit, mono.
5. Implement the frontend contract:
   - `Initialize`, `PrepareSpeech`, `FinishSpeech`, `GetNextUnitSpecList`,
     `Normalize`, `GetPronunciations`;
   - emit `tagUnitSpec` (0x70 bytes) and per-unit events.
6. Parse `.UDT`/`.LTS`/`.APL`/`.UNT`/`.CRT` for phone/unit/rule data; without these,
   the frontend cannot select units.

## 4.11 Limits

- No Anna audio was generated, decoded to WAV, or used to train/synthesize a voice.
- The WMSpeech block payload is not re-encoded here; only its container and
  obfuscation are documented.
- Exact unit-selection costs, `.WIH` payload semantics, and `.APL`/`.UNT`/`.CRT`
  record layouts remain open.
