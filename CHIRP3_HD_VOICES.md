# Chirp 3 HD Voice Configuration

## ✅ **Corrected Voice Names**

The service now uses the proper Chirp 3 HD voice naming convention:

### **Female Voices:**

- **13-17 years**: `en-US-Chirp3-HD-Kore`
- **18-25 years**: `en-US-Chirp3-HD-Erinome`
- **26-35 years**: `en-US-Chirp3-HD-Callirrhoe`

### **Male Voices:**

- **13-17 years**: `en-US-Chirp3-HD-Puck`
- **18-25 years**: `en-US-Chirp3-HD-Achird`
- **26-35 years**: `en-US-Chirp3-HD-Alnilam`

### **Fallback Voice:**

- Default fallback: `en-US-Chirp3-HD-Kore`

## 🔧 **Technical Notes:**

1. **Correct Naming Convention**: `en-US-Chirp3-HD-[VoiceName]` (not `en-US-Journey-[VoiceName]`)
2. **No SSML Support**: Chirp 3 HD voices don't support SSML, but support pace control options
3. **Supported Controls**:
   - `speaking_rate`: Controls speech pace
   - `pitch`: Controls voice pitch
   - `volume_gain_db`: Controls volume level
   - `effects_profile_id`: Audio effects profiles

## 📋 **Configuration Example:**

```python
voice = texttospeech.VoiceSelectionParams(
    language_code="en-US",
    name="en-US-Chirp3-HD-Kore",
)

audio_config = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.MP3,
    speaking_rate=0.9,
    pitch=0.0,
    volume_gain_db=2.0,
    sample_rate_hertz=24000,
    effects_profile_id=["small-bluetooth-speaker-class-device"]
)
```

This matches the Google Cloud TTS documentation and ensures proper Chirp 3 HD voice functionality.
