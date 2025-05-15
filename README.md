# Cortex – Just A Rather Very Intelligent System

**Version:** 1.0  
**Authors:** Yasser Bases 2280989 and Seif Alkhalidy 2282975
**Acknowledgements:** Many thanks to Professor Arezoo for this opportunity.

---

## Overview

Cortex is a multimodal, agentic AI assistant speaking in British RP. It integrates a large-language model with a suite of real-time tools:

- **Automation** via webhooks (n8n)  
- **Web Search** (Google Search API)  
- **Voice Interaction** (client-side STT/TTS)  
- **Live Camera Feed** (real-time video frames over WebSockets)  
- **Retrieval-Augmented Generation (RAG)**  
- **Weather Information** (python_weather)  
- **Travel & Maps** (Google Maps API)

---

## Features

### 1. Core LLM Agent  
- British-RP voice and tone  
- Dry-witted, efficient, concise  
- Carefully prompt engineered

### 2. Automation  
- `send_webhook(recipient: string, message: string)`  
  - Triggers an n8n webhook via GET  
  - Automatically invoked when user says “send a message to …”

### 3. Web Search & RAG  
- Synchronous Google search (`googlesearch`)  
- Document retrieval for context-aware generation  
- Configurable index refresh schedules

### 4. Voice Interaction  
- Client-side speech-to-text & text-to-speech  
- Noise-robust handling and real-time transcription

### 5. Live Camera Feed  
- Video frames streamed from client → server over WebSockets  
- Processed by `Cortex.instance` for visual feedback  
- Automatic queue management on feed stop

### 6. Weather 
- Current forecast & multi-day outlook via `python_weather`  

---

## Architecture

\`\`\`plaintext
┌──────────────┐     WebSockets     ┌──────────────┐
│  React UI    │ ────────────────▶ │ Flask Socket │
│ (Widgets +   │                     │ server       │
│  STT/TTS)    │ ◀───────────────   │ (Cortex      │
└──────────────┘     HTTP/Webhook   └──────────────┘
      │                                        │
      │                                        │
      │                                ┌───────▼──────┐
      │                                │  Python      │
      │                                │  Modules:    │
      │                                │  – python_weather  
      │                                │  – googlemaps  
      │                                │  – googlesearch  
      │                                │  – genai (Google Gemini)  
      │                                │  – aiohttp / websockets  
      │                                └──────────────┘
      │
      ▼
┌──────────────┐
│ n8n Webhook  │
└──────────────┘
\`\`\`

---

## Installation

1. **Clone the repo**  
   

2. **Server dependencies**  
   \`\`\`bash
   pip install -r server/requirements.txt
   \`\`\`

3. **Client dependencies**  
   \`\`\`bash
   cd client/Cortex-online
   npm install
   \`\`\`

4. **Environment**  
   Create a \`.env\` in \`server/\` with:  
   \`\`\`ini
   FLASK_SECRET_KEY=your_secret
   REACT_APP_PORT=5173
   GOOGLE_API_KEY=…
   MAPS_API_KEY=…
   ELEVENLABS_API_KEY=…
   \`\`\`

---

## Usage

1. **Start the server**  
   \`\`\`bash
   cd server
   flask run
   \`\`\`

2. **Start the client**  
   \`\`\`bash
   cd client/Cortex-online
   npm start
   \`\`\`

3. **Interact**  
   - Open your browser at \`http://localhost:5173\`  
   - Speak, type, or send images (as “live video feed”)  
   - Invoke “send a message to …” to trigger webhooks

---

## Configuration

- **Weather**: adjust cache duration in \`Cortex_Online.py\`  
- **Video queue**: clear behaviour on \`video_feed_stopped\`  
- **RAG index**: set refresh interval in your retrieval script

---

## Testing & Metrics

- **Latency**: measure end-to-end from capture → response  
- **Webhook delivery**: verify GET responses & retries  
- **RAG accuracy**: track retrieval relevance

---

## Future Work

- **Auxiliary Widgets:** code execution, YouTube, status display, visualiser  
- Add OCR module for real-time text extraction  
- Extend RAG to domain-specific corpora (e.g. medical)  
- Integrate GDPR-compliant user-consent flows

---

## License

MIT License. See [LICENSE](LICENSE) for details.
