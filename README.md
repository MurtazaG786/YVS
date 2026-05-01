
# 🎬 YouTube Video Summarizer with AI - Enhanced Version

An intelligent YouTube video summarizer that uses Google's Gemini AI to transform video transcripts into crystal-clear, actionable notes. Now with **caching** and **no-transcript support**!

## ✨ New Features (Upgrades)

### 1. 📦 **Smart Caching System**
- **Automatic Storage**: Summaries are automatically saved to `video_summaries_cache.json`
- **Instant Retrieval**: Same video requested? Get cached summary in milliseconds
- **Timestamp Tracking**: Know when each summary was created
- **Cache Management**: View all cached videos in the sidebar or clear cache with one click

**How it works:**
```python
# First request: generates & caches
summary, is_cached, title = get_video_summary(url)  # is_cached = False

# Second request: retrieves from cache
summary, is_cached, title = get_video_summary(url)  # is_cached = True ✨

# Force new generation
summary, is_cached, title = get_video_summary(url, force_refresh=True)
```

### 2. ❓ **Can LLMs See Videos? - Answer**
**SHORT ANSWER: No, not as video files**

#### Why transcript-based is BETTER:
- ✅ **Most Accurate**: Captures creator's exact words
- ✅ **Fastest**: No frame processing needed
- ✅ **Cheapest**: Minimal API costs (text << video frames)
- ✅ **Best Context**: Transcript has all meaningful audio content

#### What LLMs CAN process:
| Format | Speed | Cost | Quality |
|--------|-------|------|---------|
| **Transcript (TEXT)** | ⚡ Fast | 💰 Cheap | ⭐⭐⭐⭐⭐ Best |
| Video Frames (IMAGES) | 🐌 Slow | 💸 Expensive | ⭐⭐⭐ Medium |
| Audio (SPEECH→TEXT) | ⏱️ Medium | 💸 Expensive | ⭐⭐⭐⭐ Good |

**Our approach**: Transcript → Summary (Optimal!)

### 3. 🎤 **No-Transcript Fallback (Audio Extraction)**
For videos without available transcripts, the system automatically:
1. **Downloads** the audio using `yt-dlp`
2. **Extracts** video metadata using `yt-dlp`
3. **Transcribes** using Gemini's audio capabilities
4. **Summarizes** the extracted transcript

**Automatic fallback:**
```python
try:
    # Try official YouTube transcript
    transcript = generate_transcript(youtube_url)
except:
    # Fallback to audio extraction
    transcript = extract_audio_and_transcribe(youtube_url)
```

## 📦 Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Requirements include:
# - youtube_transcript_api    (Get video transcripts)
# - streamlit                 (Web UI)
# - google_genai              (Gemini API access)
# - python-dotenv             (Environment variables)
# - yt-dlp                    (Download video metadata & audio)
```

## 🔐 Setup

1. **Get Google API Key**:
   - Go to [Google AI Studio](https://aistudio.google.com/app/apikeys)
   - Create new API key for Gemini

2. **Create `.env` file**:
```env
GOOGLE_API_KEY=your_api_key_here
```

## 🚀 Usage

### Option 1: Web UI (Recommended)
```bash
streamlit run streamlit_app.py
```

### Option 2: Python Script
```python
from app import get_video_summary

url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
summary, is_cached, title = get_video_summary(url)

print(f"Title: {title}")
print(f"From Cache: {is_cached}")
print(f"Summary:\n{summary}")
```

## 📁 Project Structure

```
├── app.py                        # Core logic & functions
├── streamlit_app.py             # Web UI
├── video_summaries_cache.json   # Auto-generated cache
├── requirements.txt             # Dependencies
├── .env                         # API keys (create this)
└── README.md                    # This file
```

## 🎯 Key Functions

### `get_video_summary(url, force_refresh=False)`
Main function to get summary with caching

**Returns:** `(summary_text, is_cached, title)`

```python
summary, is_cached, title = get_video_summary(url)
```

### `generate_transcript(youtube_url)`
Get transcript from YouTube API

```python
transcript = generate_transcript(url)
```

### `extract_audio_and_transcribe(youtube_url)`
Fallback for videos without transcripts

```python
transcript = extract_audio_and_transcribe(url)
```

### Cache Functions
```python
# Load cache
cache = load_cache()

# Save cache
save_cache(cache)

# Get cached summary
cached_summary = get_cached_summary(video_id)

# Store new summary
store_summary(video_id, summary, title)
```

## 📊 Cache Structure

Each cached summary looks like:
```json
{
  "a1b2c3d4e5f6g7h8": {
    "video_id": "dQw4w9WgXcQ",
    "title": "Never Gonna Give You Up",
    "summary": "...",
    "timestamp": "2024-04-30T10:30:45.123456"
  }
}
```

## 🎬 Supported URL Formats

All these work:
- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://www.youtube.com/watch?v=VIDEO_ID&t=120s`
- `https://youtu.be/VIDEO_ID`
- `https://www.youtube.com/shorts/VIDEO_ID`
- `https://m.youtube.com/watch?v=VIDEO_ID`

## ⚙️ Advanced: Customization

### Modify Summary Prompt
Edit the `prompt` variable in `app.py` to change the summary format:

```python
prompt = """Your custom instructions here:
...
"""
```

### Change AI Model
```python
# Default: gemini-2.5-flash
response = client.models.generate_content(
    model="gemini-2.0-flash",  # Change here
    contents=prompt + transcript
)
```

## 🔍 Troubleshooting

### ❌ "Invalid YouTube URL"
- Copy full URL from browser address bar
- Ensure it starts with `https://`

### ❌ "No transcript available" Error
- Video might not have transcripts
- **This is now automatically handled!** System extracts audio instead
- Requires FFmpeg for audio processing

### ❌ API Key Error
- Check `.env` file exists
- Verify `GOOGLE_API_KEY=` is set correctly
- Get new key from [Google AI Studio](https://aistudio.google.com/app/apikeys)

### ❌ Rate Limiting
- Cache is your friend! Uses instant retrieval for repeated videos
- Wait a few minutes between new video requests if hitting limits

## 📈 Performance Notes

| Scenario | Speed | Notes |
|----------|-------|-------|
| **Cached Video** | ⚡⚡⚡ <1s | Instant retrieval |
| **New Video (with transcript)** | ⚡⚡ 5-15s | API calls + generation |
| **New Video (no transcript)** | 🐌 1-3 min | Audio download + extraction |

## 🎓 Summary Format

The AI generates summaries with this structure:

1. **TITLE** - Better title than original
2. **TLDR** - 5-7 bullet points
3. **CORE IDEAS** - Logical sections with explanations
4. **KEY FRAMEWORKS** - Step-by-step methods
5. **IMPORTANT INSIGHTS** - Powerful ideas
6. **MEMORY HOOKS** - Memorable lines
7. **PRACTICAL TAKEAWAYS** - Actionable items

## 📝 Example Summary

```
### How to Build Habits

TLDR
• Habits are formed through consistent repetition
• Environment design is more important than willpower
• Start with tiny habits that take <2 minutes
• Track visibly to build momentum

CORE IDEAS

The 1% Rule
Small improvements compound over time...

...
```

## 🛠️ Future Enhancements

Potential upgrades:
- [ ] Multiple language support
- [ ] Summary export as PDF/Markdown
- [ ] Summarize entire playlists
- [ ] Custom summary length (short/medium/detailed)
- [ ] API endpoint for integration
- [ ] Local summary database (SQLite)

## 📄 License

Free to use and modify!

## 🤝 Contributing

Found a bug or have ideas? Feel free to improve!

---

**Enjoy crystal-clear video summaries! 🎬✨**
