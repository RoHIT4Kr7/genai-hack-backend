# 🎌 Manga Mental Wellness Backend

> Transform emotions into optimistic manga stories with AI-powered generation

## 🚀 Quick Start

### **Start Backend (FastAPI)**

```bash
python main.py
```

- Server: http://localhost:8000
- API Docs: http://localhost:8000/docs

### **Start Frontend (Streamlit)**

```bash
python start_frontend.py
```

- Frontend: http://localhost:8501

## 🎯 Features

- **🤖 Mangaka-Sensei AI**: Structured storytelling with ChatVertexAI
- **🎨 Typography Generation**: Dialogue embedded in manga images
- **🗣️ Smart Voice Selection**: Age/gender-appropriate narration
- **🎵 Background Music**: Lyria-002 emotional soundtracks
- **📱 Slideshow Experience**: Synchronized audio-visual manga

## 🎭 Manga Styles

| Mood → Vibe               | Generated Style                           |
| ------------------------- | ----------------------------------------- |
| Stressed → Motivational   | **Demon Slayer** - Dynamic determination  |
| Frustrated → Motivational | **Jujitsu Kaisen** - Intense supernatural |
| Sad → Calm                | **Your Name** - Emotional, soft lighting  |
| Happy → Musical           | **Your Lie in April** - Music performance |

## 🎨 Image Generation Format

```
CHARACTER_SHEET(
  character_name: Maya,
  appearance: 16-year-old girl with determined eyes...,
  clothing: casual hoodie reflecting artistic personality
),

PROP_SHEET(
  item: digital drawing tablet,
  description: tablet representing creative expression
),

STYLE_GUIDE(
  art_style: masterpiece, Demon Slayer by Koyoharu Gotouge,
  details: dynamic ink lines, cross-hatching, high contrast,
  framing: cinematic composition,
  negative_prompt: (color, text, signature, watermark, blurry)
)

DIALOGUE: "I won't give up... this challenge will make me stronger!"
```

## 📁 Project Structure

```
manga-wellness-backend/
├── main.py                 # FastAPI app (run this!)
├── start_frontend.py       # Streamlit launcher
├── routers/
│   └── manga_router.py     # API endpoints
├── services/
│   ├── story_service.py    # Mangaka-Sensei AI
│   ├── image_service.py    # Imagen 4.0 typography
│   ├── audio_service.py    # TTS + Lyria-002
│   └── storage_service.py  # Google Cloud Storage
├── models/
│   └── schemas.py          # Pydantic models
├── config/
│   └── settings.py         # Hardcoded configuration
├── utils/
│   └── helpers.py          # Mangaka-Sensei prompt
└── frontend/
    └── streamlit_app.py    # Simplified UI
```

## 🧪 Testing

```bash
# Test complete pipeline
python utils/test_complete_pipeline.py

# Test typography generation
python utils/test_typography_generation.py

# Test individual services
python utils/test_voice_selection.py
```

## ⚙️ Configuration

All settings are hardcoded in `config/settings.py`:

- **Vertex AI Project**: `hackathon-472205`
- **Imagen Model**: `imagen-4.0-generate-001`
- **GCS Bucket**: `hackathon-asset-genai`
- **Voice Selection**: Age/gender-based

Authentication uses `GOOGLE_APPLICATION_CREDENTIALS` environment variable.

## 🎌 Mental Wellness Focus

- **6-Panel Story Structure**: Introduction → Challenge → Reflection → Discovery → Transformation → Resolution
- **Optimistic Narratives**: All stories end with hope and growth
- **Character Consistency**: Same character across all panels
- **Age-Appropriate Content**: Suitable for youth mental wellness

## 🏗️ Built With

- **FastAPI** - Async web framework
- **ChatVertexAI** - Story generation
- **Imagen 4.0** - Image generation with typography
- **Google Cloud TTS** - Voice personalization
- **Lyria-002** - Background music
- **Streamlit** - Frontend interface
- **Google Cloud Storage** - Asset delivery

---

**Ready for hackathons and mental wellness prototypes!** 🚀
