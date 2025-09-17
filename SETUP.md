# 🚀 Team Setup Guide - Manga Wellness Backend

## 📋 Prerequisites

- Python 3.9+ installed
- Node.js 18+ installed (for frontend)
- Git installed
- Google Cloud account access (shared by team lead)

## 🔐 Credentials Setup

### 1. Get Service Account Key

Since we're using shared Google Cloud resources, you'll need the service account key:

**Option A: Get from Team Lead**

- Ask your team lead for the `servicekey.json` file
- Place it in the root directory: `backned-hck/servicekey.json`

**Option B: Download from Google Cloud Console**

- Go to [Google Cloud Console](https://console.cloud.google.com/)
- Navigate to IAM & Admin > Service Accounts
- Find the service account: `hackathon@hackathon-472205.iam.gserviceaccount.com`
- Create a new key (JSON format)
- Download and rename to `servicekey.json`

### 2. Set Environment Variable

Set the Google Cloud credentials path:

**Windows:**

```bash
set GOOGLE_APPLICATION_CREDENTIALS=D:\calmira\backned-hck\servicekey.json
```

**macOS/Linux:**

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/backned-hck/servicekey.json
```

**Or add to your shell profile (.bashrc, .zshrc, etc.):**

```bash
echo 'export GOOGLE_APPLICATION_CREDENTIALS="/path/to/backned-hck/servicekey.json"' >> ~/.bashrc
source ~/.bashrc
```

## 🛠️ Installation

### Backend Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd backned-hck

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify setup
python -c "import google.cloud.aiplatform; print('✅ Google Cloud setup successful')"
```

### Frontend Setup

```bash
cd ../calmira-mind-haven

# Install dependencies
npm install

# Start development server
npm run dev
```

## 🔄 Development Workflow

### 1. Branch Strategy (Recommended)

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "feat: add your feature description"

# Push to your branch
git push origin feature/your-feature-name

# Create Pull Request on GitHub
```

### 2. Direct Collaboration (Alternative)

```bash
# Clone and work directly on main branch
git clone <your-repo-url>
cd backned-hck

# Make changes and commit
git add .
git commit -m "feat: add your feature description"

# Push directly (if you have write access)
git push origin main
```

## 🚀 Running the Application

### Start Backend

```bash
cd backned-hck
python main.py
```

### Start Frontend

```bash
cd calmira-mind-haven
npm run dev
```

### Test the Application

1. Backend should be running on `http://localhost:8000`
2. Frontend should be running on `http://localhost:5173`
3. Open frontend URL in browser
4. Test story generation functionality

## 📁 Project Structure

```
backned-hck/
├── main.py                 # FastAPI application entry point
├── services/               # Core business logic
│   ├── story_service.py    # Story generation
│   ├── image_service.py    # Image generation
│   ├── audio_service.py    # TTS generation
│   └── panel_processor.py  # Panel processing
├── routers/                # API routes
├── models/                 # Data models
├── utils/                  # Helper functions
└── config/                 # Configuration

calmira-mind-haven/
├── src/
│   ├── components/         # React components
│   ├── pages/             # Page components
│   └── App.tsx            # Main app component
└── package.json
```

## 🔧 Common Issues & Solutions

### 1. Google Cloud Authentication Error

```bash
# Verify credentials are set
echo $GOOGLE_APPLICATION_CREDENTIALS

# Test authentication
python -c "from google.cloud import aiplatform; print('Auth successful')"
```

### 2. Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill process
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows
```

### 3. Python Dependencies Issues

```bash
# Reinstall dependencies
pip uninstall -r requirements.txt -y
pip install -r requirements.txt
```

## 📝 Development Guidelines

### Code Style

- Use meaningful commit messages
- Follow existing code formatting
- Add comments for complex logic
- Test your changes before committing

### Testing

```bash
# Run backend tests
python -m pytest tests/

# Run frontend tests
npm test
```

### API Testing

```bash
# Test story generation endpoint
curl -X POST "http://localhost:8000/generate-story" \
  -H "Content-Type: application/json" \
  -d '{
    "nickname": "TestUser",
    "age": 25,
    "gender": "non-binary",
    "mood": "happy",
    "vibe": "calm",
    "archetype": "artist",
    "dream": "become a painter",
    "hobby": "painting",
    "mangaTitle": "Test Story"
  }'
```

## 🆘 Getting Help

1. Check existing issues on GitHub
2. Ask in team chat/discord
3. Create new issue with detailed description
4. Include error logs and steps to reproduce

## 🔒 Security Notes

- Never commit `servicekey.json` to Git
- Keep credentials secure and don't share publicly
- Use environment variables for sensitive data
- Report any security issues immediately

---

**Happy coding! 🎨✨**
