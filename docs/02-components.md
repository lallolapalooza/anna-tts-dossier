# 2. Artifact and COM inventory (verified)

Source image and hashes are in `README.md`; all four archive hashes matched. Everything
below was extracted from image index 4 (`Windows 7 ULTIMATE`, build 7601, SP1).

## 2.1 Install layout

```
%CommonProgramFiles%\SpeechEngines\Microsoft\TTS20\
    MSTTSEngine.dll            engine COM server (coclass TTSEngine)
    MSTTSCommon.dll            LTS COM server (coclass LTS)
    MSTTSLoc.dll               localization resources
    en-US\MSTTSFrontendENU.dll frontend COM server (coclass MSTTSFrontendENU)
    en-US\MSTTSLoc.dll.mui
%CommonProgramFiles(x86)%\SpeechEngines\Microsoft\TTS20\
    ...same DLLs plus...
    MSTTSDecWrp.dll            decoder wrapper COM server (coclass DecObj)
    en-US\enu-dsk\M1033DSK.*   Anna voice data (shared by both engines)
```

The 64-bit TTS20 tree has an empty `en-US\enu-dsk` directory; the voice data exists only
in the 32-bit `Common Files (x86)` tree. `[INFERENCE]` The 64-bit engine reads the same
voice data through the token's hard-coded `VoicePath`; the data container is bitness
independent.

## 2.2 Registry registration

Token (identical in `HKLM\SOFTWARE\Microsoft\Speech\Voices\Tokens` and
`HKLM\SOFTWARE\Wow6432Node\Microsoft\Speech\Voices\Tokens`):

```
MS-Anna-1033-20-DSK
  (default)   = "Microsoft Anna - English (United States)"
  Description = "@%CommonProgramFiles%\SpeechEngines\Microsoft\TTS20\MSTTSLoc.dll,-1033"
  CLSID       = {F51C7B23-6566-424C-94CF-2C4F83EE96FF}
  DefaultRate = 2
  Frontend    = {55DFB4F7-4175-4B3B-B247-D9B399ADB119}
  VoiceName   = "M1033DSK"
  VoicePath   = "D:\Program Files (x86)\Common Files\SpeechEngines\Microsoft\TTS20\en-US\enu-dsk"
  Attributes
    Age=Adult, Gender=Female, Language=409, Name=Microsoft Anna,
    Vendor=Microsoft, Version=2.0, AudioFormats=18
  Lex
    CLSID    = {90903716-2F42-11D3-9C26-00C04F8EF87C}   (SpCompressedLexicon)
    DataFile = "<VoicePath>\M1033DSK.TTS"
```

`D:` is the build machine's system drive; the token is a REG_EXPAND_SZ value only for
some fields. In a live install the path resolves to the x86 Common Files tree.

COM registration:

| CLSID | Name | InprocServer32 |
|---|---|---|
| `{F51C7B23-6566-424C-94CF-2C4F83EE96FF}` | MS TTSEngine Class | `%CommonProgramFiles%\SpeechEngines\Microsoft\TTS20\MSTTSEngine.dll` |
| `{55DFB4F7-4175-4B3B-B247-D9B399ADB119}` | MSTTS Frontend Class (ENU) | `%CommonProgramFiles%\SpeechEngines\Microsoft\TTS20\en-US\MSTTSFrontendENU.dll` |
| `{F66A6818-F490-431B-8CA4-4CFDA287327B}` | LTS | `%CommonProgramFiles%\SpeechEngines\Microsoft\TTS20\MSTTSCommon.dll` |
| `{3F6B5E16-092A-41ED-930B-0B4125D91D4E}` | DecObj (AppID/DllSurrogate) | `%CommonProgramFiles(x86)%\SpeechEngines\Microsoft\TTS20\MSTTSDecWrp.dll` (`[INFERENCE]`; only the AppID key is present in the offline hive) |
| `{90903716-2F42-11D3-9C26-00C04F8EF87C}` | SpCompressedLexicon | `%SystemRoot%\System32\Speech\Common\sapi.dll` |

AppIDs seen in the binaries:

- Engine: `{49AB0B7E-8EA7-4842-AD24-B18BEDACA50F}`
- Common: `{901B8A87-AC4B-434C-BD70-2AA5A09CC0D3}`

Type libraries:

| Module | TypeLib GUID | Version | Coclasses |
|---|---|---|---|
| MSTTSEngine.dll | `{6A379714-E19D-4D0F-AAC6-20D5F143C420}` | 2.0 | `TTSEngine` |
| MSTTSFrontendENU.dll | `{A7201431-623E-44A7-A85C-D13AFC0F6AA6}` | 2.0 | `MSTTSFrontendENU` |
| MSTTSCommon.dll | `{613808A3-159B-4D91-B4F0-A22AEE2D1AAC}` | 2.0 | `LTS` |
| MSTTSDecWrp.dll | `{EDEBC0B7-FA4D-45FB-B750-16C8D2340AE8}` | 1.0 | `DecObj` |

## 2.3 Binary inventory

Version resources identify these as Microsoft Windows 7 RTM/SP1 components, file
version `2.00.4319.00 (win7_rtm.090713-1255)` unless noted. Authenticode was not
verified.

| Path (under extracted image) | Arch | Size | SHA-256 (first 24) |
|---|---|---|---|
| `Program Files/.../TTS20/MSTTSEngine.dll` | x64 | 181,248 | `36b15355ecfb20bf2fbad54e` |
| `Program Files/.../TTS20/MSTTSCommon.dll` | x64 | 41,472 | `c8103a800569db0e900fc911` |
| `Program Files/.../TTS20/MSTTSLoc.dll` | x64 | 9,728 | `738cde0c163a29393d665267` |
| `Program Files/.../TTS20/en-US/MSTTSFrontendENU.dll` | x64 | 373,760 | `355481797be01c22764074ae` |
| `Program Files (x86)/.../TTS20/MSTTSEngine.dll` | x86 | 150,528 | `12641a4a285fb99f6a016506` |
| `Program Files (x86)/.../TTS20/MSTTSCommon.dll` | x86 | 35,328 | `91eb82539eb153e40d4e33fa` |
| `Program Files (x86)/.../TTS20/MSTTSDecWrp.dll` | x86 | 47,616 | `0c316510a86f2988f624093f` |
| `Program Files (x86)/.../TTS20/MSTTSLoc.dll` | x86 | 8,704 | `825c4cf167308f691d29375f` |
| `Program Files (x86)/.../TTS20/en-US/MSTTSFrontendENU.dll` | x86 | 274,944 | `4dc0c318603eddd69afac477` |
| `Windows/System32/Speech/Common/sapi.dll` | x64 | 1,435,648 | `e7c5f172bc194548bdb09cb6` |
| `Windows/SysWOW64/Speech/Common/sapi.dll` | x86 | 1,202,176 | `8ba490c65cb6978b4aaa8565` |
| `Windows/Speech/Common/sapisvr.exe` | x64 | 44,544 | `938c02c2c682b542788f0d94` |

`sapi.dll` is version `5.3.13120.00 (win7sp1_rtm.101119-1850)`. `sapisvr.exe` is the
speech *recognition* server (its version resource says "Speech Recognition") and is not
used by TTS rendering.

Full hashes are in `out/artifacts.json`.

## 2.4 Voice data (Anna, `VoiceName=M1033DSK`)

| File | Size | SHA-256 (first 24) | Observed header |
|---|---:|---|---|
| `M1033DSK.TTS` | 2,430,393 | `966315647eb946e2d96033bf` | two GUIDs, then LCID 0x409 |
| `M1033DSK.CSD` | 29,798,100 | `5c087dd0761a5e7cb73b363e` | no ASCII/UTF-16 header; high-entropy |
| `M1033DSK.WIH` | 3,597,414 | `6bd0ac584ff4cb72a9d769c3` | `u32 0`, `u32 3`, `u32 16000`, `u32 0x10002`, then `int16` data |
| `M1033DSK.UNT` | 3,182,160 | `b6849d732ca36cc8002de232` | `u32 1`, `u32 0x100`, `u32 0x105`, `u32 0`, `u32 0x514`, `u32 0x26d43` |
| `M1033DSK.LTS` | 931,696 | `9e8da98bd74242298e89e6df` | table of `u32` offsets; UTF-16 phoneme strings |
| `M1033DSK.IDX` | 132,508 | `ba40b25afe64e9c9e2e75c59` | `u32 0x48`, mixed offsets/sizes |
| `M1033DSK.UDT` | 11,166 | `930dc54f61f42fa2bc1ed9a8` | magic `UDT\0`, version 1, LCID 0x409 |
| `M1033DSK.CRT` | 484,600 | `02fc27af09e0d468c92310ad` | `u32 0x7fd48`, `0x100`, `0xdf8`, ... |
| `M1033DSK.APL` | 16,066 | `ca539393e83f9f437ff032de` | `u32 1`, `u32 1`, `u32 0x100`, ... |

The engine binary contains the format strings `%s.WIH`, `%s.APL`, `%s.UNT`, `%s.CRT`,
`%s.WVE`, `%s.CSD`, `%s.IDX`; `.WVE` is referenced by the loader but is not present in
this image. `M1033DSK.TTS` is referenced by the token's `Lex\DataFile`.

## 2.5 COM interfaces (from embedded type libraries)

### Engine: coclass `TTSEngine` `{F51C7B23-...}`

Implements `ISpTTSEngine`, `ISpObjectWithToken`, `ITTSSupportDebug`,
`ISpEnginePronunciation`.

| Vtable | Method | Signature |
|---:|---|---|
| 24 | `Speak` | `HRESULT Speak(ULONG flags, GUID* fmt, WAVEFORMATEX*, SPVTEXTFRAG*, ISpTTSEngineSite*)` |
| 32 | `GetOutputFormat` | `HRESULT GetOutputFormat(GUID*, WAVEFORMATEX*, GUID*, WAVEFORMATEX**)` |
| 24 | `SetObjectToken` | `HRESULT SetObjectToken(ISpObjectToken*)` |
| 32 | `GetObjectToken` | `HRESULT GetObjectToken(ISpObjectToken**)` |
| 24 | `GetSupportedTypes` | `HRESULT GetSupportedTypes(ULONG*)` |
| 32 | `SetDebugger` | `HRESULT SetDebugger(ITTSDebug*)` |
| 24 | `Normalize` | `HRESULT Normalize(LPWSTR word, LPWSTR left, LPWSTR right, USHORT lang, SPNORMALIZATIONLIST*)` |
| 32 | `GetPronunciations` | `HRESULT GetPronunciations(LPWSTR word, LPWSTR left, LPWSTR right, USHORT lang, SPWORDPRONUNCIATIONLIST*)` |

### Frontend: coclass `MSTTSFrontendENU` `{55DFB4F7-...}`

Implements `ITTSFrontend` and `ITTSSupportDebug`.

| Vtable | Method | Signature |
|---:|---|---|
| 24 | `Initialize` | `HRESULT Initialize(ISpObjectToken* token)` |
| 32 | `PrepareSpeech` | `HRESULT PrepareSpeech(SPVTEXTFRAG*, ULONG flags, ISpTTSEngineSite*)` |
| 40 | `FinishSpeech` | `HRESULT FinishSpeech()` |
| 48 | `GetNextUnitSpecList` | `HRESULT GetNextUnitSpecList(tagUnitSpec** list, LONG* count, tagSPEECH_STATE* state, LONG* skipCount)` |
| 56 | `Normalize` | same shape as engine |
| 64 | `GetPronunciations` | same shape as engine |

`tagUnitSpec` (19 fields, TLB order):

```c
struct tagUnitSpec {
    USHORT  wLangID;
    SHORT   sUnitIndex;
    CArray  bUnitFeatureVector;     // byte array
    tagSENT_PUNCTUATION_TYPE ePuncType;
    ULONG   lFrontPhoneFlags;
    ULONG   lBackPhoneFlags;
    tagBREAK_LEVEL_TYPE eBreakLevel;
    LONG    lVolume;
    LONG    lRate;
    LONG    lPitch;
    LONG    lVoice;
    LONG    m_CtrlFlags;
    ULONG   m_SrcPosition;
    ULONG   m_SrcLen;
    ULONG   m_SentencePosition;
    ULONG   m_SentenceLen;
    LONG    lUserBreak;
    LONG    m_nNumOfEvents;
    SPEVENT* m_pEventArray;
};
```

`ITTSDebug` and `tagMSTTS_DEBUG_TYPE` expose an internal debug channel
(`Invoke(type, BSTR*)`), useful for reconstructing pipeline stages.

### LTS: coclass `LTS` `{F66A6818-...}`

`ILTS`: `Initialize(BSTR file, char shallow)`, `Free()`,
`GetPronunciation(BSTR symbol, BSTR* pronunciation)`.

### Decoder: coclass `DecObj` `{3F6B5E16-...}` (x86 only)

`IDecObj` is a dual interface; its custom methods:

| Vtable | Method | Signature |
|---:|---|---|
| 56 | `Initialize` | `HRESULT Initialize(BSTR file, BSTR waveInventoryIdxFile)` |
| 64 | `ReadBSTR` | `HRESULT ReadBSTR(long start, long length)` → BSTR |

The type library names the second parameter `pwszWaveInventoryIdxFile`, tying the
decoder to the `.WIH` wave-inventory index.
