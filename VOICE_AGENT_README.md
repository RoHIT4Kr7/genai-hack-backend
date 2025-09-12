# Voice Agent for Anime Generation

A voice-powered AI assistant that helps users create anime and manga stories through natural conversation using Google Gemini 2.5 Flash Live API.

## Features

- **Real-time Voice Interaction**: Talk naturally with the AI assistant
- **Voice Transcription**: Automatic speech-to-text conversion
- **Text-to-Speech**: AI responses delivered as natural speech
- **Anime/Manga Expertise**: Specialized in anime and manga creation assistance
- **WebSocket Support**: Real-time updates and communication
- **Session Management**: Track and manage multiple voice sessions
- **RESTful API**: Easy integration with existing applications

## Quick Start

### 1. Install Dependencies

```bash
pip install pyaudio google-generativeai
```

### 2. Set Environment Variables

Make sure your `.env` file contains:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Start the Server

```bash
python main.py
```

### 4. Test the Voice Agent

```bash
python test_voice_agent.py
```

## API Endpoints

### Voice Session Management

#### Start Voice Session

```http
POST /api/v1/voice/start-session
Content-Type: application/json

{
    "session_id": "optional_custom_id",
    "user_id": "user123",
    "context": "anime_generation"
}
```

#### Stop Voice Session

```http
POST /api/v1/voice/stop-session?session_id=your_session_id
```

#### Send Text Message

```http
POST /api/v1/voice/send-message
Content-Type: application/json

{
    "session_id": "your_session_id",
    "message": "Help me create an anime character"
}
```

#### Get Session Status

```http
GET /api/v1/voice/session/{session_id}/status
```

#### List All Sessions

```http
GET /api/v1/voice/sessions
```

### Real-time Communication

#### WebSocket Connection

```javascript
const ws = new WebSocket("ws://localhost:8000/api/v1/voice/ws/your_session_id");

ws.onmessage = function (event) {
  const data = JSON.parse(event.data);

  switch (data.type) {
    case "transcription":
      console.log("User said:", data.text);
      break;
    case "ai_response":
      console.log("AI responded:", data.text);
      break;
    case "session_status":
      console.log("Session status:", data.status);
      break;
  }
};
```

### Health Check

```http
GET /api/v1/voice/health
```

## Usage Examples

### Python Client Example

```python
import asyncio
import aiohttp

async def create_anime_character():
    async with aiohttp.ClientSession() as session:
        # Start voice session
        session_data = {
            "user_id": "creator123",
            "context": "anime_generation"
        }

        async with session.post(
            "http://localhost:8000/api/v1/voice/start-session",
            json=session_data
        ) as response:
            result = await response.json()
            session_id = result["session_id"]

        # Send message about character creation
        message_data = {
            "session_id": session_id,
            "message": "I want to create a protagonist for a magical school anime. They should be shy but determined."
        }

        async with session.post(
            "http://localhost:8000/api/v1/voice/send-message",
            json=message_data
        ) as response:
            result = await response.json()
            print("Message sent successfully!")

        # Check for AI response
        await asyncio.sleep(3)

        async with session.get(
            f"http://localhost:8000/api/v1/voice/session/{session_id}/status"
        ) as response:
            status = await response.json()
            if status.get("last_response"):
                print("AI Response:", status["last_response"]["text"])

# Run the example
asyncio.run(create_anime_character())
```

### JavaScript/Frontend Example

```javascript
class VoiceAgentClient {
  constructor(baseUrl = "http://localhost:8000/api/v1") {
    this.baseUrl = baseUrl;
    this.sessionId = null;
    this.websocket = null;
  }

  async startSession(userId = "user123") {
    const response = await fetch(`${this.baseUrl}/voice/start-session`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: userId,
        context: "anime_generation",
      }),
    });

    const data = await response.json();
    this.sessionId = data.session_id;

    // Connect WebSocket for real-time updates
    this.connectWebSocket();

    return data;
  }

  connectWebSocket() {
    this.websocket = new WebSocket(
      `ws://localhost:8000/api/v1/voice/ws/${this.sessionId}`
    );

    this.websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleWebSocketMessage(data);
    };
  }

  handleWebSocketMessage(data) {
    switch (data.type) {
      case "transcription":
        console.log("🎤 User said:", data.text);
        this.onTranscription?.(data.text);
        break;
      case "ai_response":
        console.log("🤖 AI responded:", data.text);
        this.onAIResponse?.(data.text);
        break;
      case "session_status":
        console.log("📊 Session status:", data.status);
        break;
    }
  }

  async sendMessage(message) {
    const response = await fetch(`${this.baseUrl}/voice/send-message`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: this.sessionId,
        message: message,
      }),
    });

    return await response.json();
  }

  async stopSession() {
    const response = await fetch(
      `${this.baseUrl}/voice/stop-session?session_id=${this.sessionId}`,
      { method: "POST" }
    );

    if (this.websocket) {
      this.websocket.close();
    }

    return await response.json();
  }
}

// Usage
const voiceAgent = new VoiceAgentClient();

voiceAgent.onTranscription = (text) => {
  document.getElementById("transcription").textContent = text;
};

voiceAgent.onAIResponse = (text) => {
  document.getElementById("ai-response").textContent = text;
};

// Start session and send a message
voiceAgent.startSession("user123").then(() => {
  voiceAgent.sendMessage("Help me create a magical girl anime character!");
});
```

## Voice Agent Capabilities

The voice agent is specifically designed to help with anime and manga creation:

### Story Development

- Plot brainstorming and structure
- Character development and backstories
- World-building and setting creation
- Theme exploration and messaging

### Character Creation

- Personality traits and motivations
- Visual design suggestions
- Character relationships and dynamics
- Character arcs and development

### Creative Assistance

- Genre-specific tropes and conventions
- Visual storytelling techniques
- Dialogue writing tips
- Pacing and narrative flow

### Technical Guidance

- Panel composition and layout
- Art style recommendations
- Publishing and distribution advice
- Industry insights and trends

## Audio Configuration

- **Input Sample Rate**: 16,000 Hz
- **Output Sample Rate**: 24,000 Hz
- **Channels**: Mono (1 channel)
- **Format**: 16-bit PCM
- **Chunk Size**: 1024 samples
- **Voice**: Zephyr (Google's natural voice)

## Error Handling

The voice agent includes comprehensive error handling:

- **Session Management**: Automatic cleanup of failed sessions
- **Audio Errors**: Graceful handling of microphone/speaker issues
- **Network Issues**: Retry logic for API calls
- **WebSocket Reconnection**: Automatic reconnection on connection loss

## Troubleshooting

### Common Issues

1. **PyAudio Installation Issues**

   ```bash
   # On Windows
   pip install pipwin
   pipwin install pyaudio

   # On macOS
   brew install portaudio
   pip install pyaudio

   # On Linux
   sudo apt-get install portaudio19-dev
   pip install pyaudio
   ```

2. **Microphone Permission**

   - Ensure your application has microphone permissions
   - Check system audio settings
   - Test with `python test_voice_agent.py`

3. **API Key Issues**

   - Verify `GEMINI_API_KEY` is set correctly
   - Check API key permissions and quotas
   - Ensure you're using Google AI Studio (not Vertex AI)

4. **WebSocket Connection Issues**
   - Check firewall settings
   - Verify session exists before connecting
   - Monitor network connectivity

### Debug Mode

Enable debug logging by setting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Integration with Existing Workflow

The voice agent is designed to work alongside your existing anime generation workflow:

1. **Voice Input**: Users describe their anime concept through voice
2. **AI Processing**: Voice agent helps refine and develop the concept
3. **Story Generation**: Refined concept feeds into your manga generation pipeline
4. **Visual Creation**: Generated story creates manga panels as usual
5. **Voice Feedback**: Users can provide feedback and iterations through voice

## Performance Considerations

- **Latency**: ~200-500ms for voice processing
- **Concurrent Sessions**: Supports multiple simultaneous voice sessions
- **Memory Usage**: ~50MB per active session
- **API Limits**: Respects Google Gemini API rate limits
- **Audio Quality**: Optimized for clear speech recognition

## Security

- **API Key Protection**: Environment variable storage
- **Session Isolation**: Each session is isolated and secure
- **Data Privacy**: Voice data is processed in real-time, not stored
- **CORS Configuration**: Proper cross-origin request handling

## Future Enhancements

- **Multi-language Support**: Support for Japanese, Korean, and other languages
- **Voice Cloning**: Custom voice generation for characters
- **Emotion Recognition**: Detect user emotions from voice tone
- **Background Music**: Dynamic background music during conversations
- **Voice Commands**: Specific commands for common anime creation tasks

## Support

For issues or questions:

1. Check the troubleshooting section above
2. Run the test script: `python test_voice_agent.py`
3. Check logs in `logs/manga_wellness.log`
4. Review the client example: `python voice_agent_client_example.py`
