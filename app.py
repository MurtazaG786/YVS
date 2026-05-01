import os
from dotenv import load_dotenv
load_dotenv()
import google.genai as genai 
from youtube_transcript_api import YouTubeTranscriptApi 
import json
import hashlib
from pathlib import Path
from datetime import datetime
import yt_dlp
import re
from urllib.parse import urlparse, parse_qs
import subprocess
import time

# Ensure ffmpeg/ffprobe are on PATH (Windows)
FFMPEG_BIN_DIR = "C:/ffmpeg/bin"
os.environ["PATH"] = f"{FFMPEG_BIN_DIR};{os.environ.get('PATH', '')}"

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

def upload_file(path):
    with open(path, "rb") as file_handle:
        return client.files.upload(file=file_handle)

# ==================== CACHE MANAGEMENT ====================
CACHE_FILE = "video_summaries_cache.json"

def load_cache():
    """Load existing summaries from cache"""
    if Path(CACHE_FILE).exists():
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_cache(cache):
    """Save summaries to cache"""
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)

def get_cache_key(video_id):
    """Generate unique cache key for video"""
    return hashlib.md5(video_id.encode()).hexdigest()

def get_cached_summary(video_id):
    """Retrieve cached summary if exists"""
    cache = load_cache()
    cache_key = get_cache_key(video_id)
    if cache_key in cache:
        return cache[cache_key]
    return None

def store_summary(video_id, summary, title):
    """Store new summary in cache"""
    cache = load_cache()
    cache_key = get_cache_key(video_id)
    cache[cache_key] = {
        "video_id": video_id,
        "title": title,
        "summary": summary,
        "timestamp": datetime.now().isoformat()
    }
    save_cache(cache)

# ==================== TRANSCRIPT GENERATION ====================
def generate_transcript(youtube_url):
    try:
        video_id=youtube_url.split("=")[1]
        ytt_api = YouTubeTranscriptApi()
        transcript_data=ytt_api.fetch(video_id)        
        
        transcript=""

        for line in transcript_data:
            transcript+=" "+line.text
        return transcript
    except Exception as e:
        raise e

# ==================== AUDIO EXTRACTION FOR NO-TRANSCRIPT VIDEOS ====================
def extract_audio_and_transcribe(youtube_url):
    """
    Extract audio from YouTube video and convert to text using Whisper
    This is for videos without available transcripts
    """
    try:
        # Download audio from YouTube
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': 'temp_audio',
            'quiet': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            audio_file = f"temp_audio.mp3"
        
        # Transcribe using Gemini's audio capabilities
        audio_file_obj = upload_file(audio_file)
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                "Please transcribe this audio and provide the full text:",
                audio_file_obj
            ]
        )
        
        transcript = response.text
        
        # Cleanup
        if Path(audio_file).exists():
            os.remove(audio_file)
        
        return transcript
        
    except Exception as e:
        raise e

# ==================== VIDEO FRAME EXTRACTION FOR VISUAL CONTEXT ====================
def extract_key_frames(youtube_url, num_frames=3):
    """
    Extract key frames from YouTube video to provide visual context to AI
    
    Args:
        youtube_url: YouTube video URL
        num_frames: Number of frames to extract (default 3)
    
    Returns:
        List of image paths
    """
    try:
        video_id = get_video_id(youtube_url)
        frames_dir = Path(f"video_frames_{video_id}")
        frames_dir.mkdir(exist_ok=True)
        
        # Download video
        ydl_opts = {
            'format': 'best[height<=720]',  # Limit resolution for speed
            'outtmpl': str(frames_dir / 'video.%(ext)s'),
            'quiet': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            video_file = str(frames_dir / f"video.{info['ext']}")
        
        # Extract frames using ffmpeg
        output_pattern = str(frames_dir / f"frame_%02d.jpg")
        
        # Get video duration first
        probe_cmd = [
            'ffprobe', '-v', 'error', 
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1:noescapetext=1',
            video_file
        ]
        
        try:
            duration = float(subprocess.check_output(probe_cmd, text=True).strip())
        except:
            duration = 300  # Default to 5 minutes if ffprobe fails
        
        # Calculate frame intervals
        interval = max(1, duration / (num_frames + 1))
        
        # Extract frames at intervals
        ffmpeg_cmd = [
            'ffmpeg', '-i', video_file,
            '-vf', f'fps=1/{int(interval)}',
            '-vframes', str(num_frames),
            output_pattern,
            '-y'
        ]
        
        subprocess.run(ffmpeg_cmd, capture_output=True, check=False)
        
        # Get extracted frame paths
        frame_paths = sorted(frames_dir.glob("frame_*.jpg"))[:num_frames]
        
        return [str(p) for p in frame_paths]
        
    except Exception as e:
        return []

def response_generation_with_visual_context(transcribe_text, frame_paths=None):
    """
    Generate summary with optional visual context from video frames
    
    Args:
        transcribe_text: Transcript text
        frame_paths: List of image file paths to include as context
    
    Returns:
        Summary text
    """
    enhanced_prompt = prompt + transcribe_text
    
    if frame_paths and len(frame_paths) > 0:
        # Include visual context
        contents = [enhanced_prompt]
        
        # Add images to context
        for frame_path in frame_paths:
            if Path(frame_path).exists():
                try:
                    image_file = upload_file(frame_path)
                    contents.append("Here are key frames from the video for additional context:")
                    contents.append(image_file)
                except Exception as e:
                    print(f"Warning: Could not upload frame {frame_path}: {e}")
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents
        )
    else:
        # Text-only mode
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=enhanced_prompt
        )
    
    return response.text

prompt="""You are an elite knowledge distillation AI.

Your job is to transform the following YouTube video transcript into highly engaging, crystal clear notes that are MORE enjoyable and easier to understand than watching the video.

Rules:
1. Remove filler, repetition, sponsor segments, and off-topic speech.
2. Extract only the most valuable insights, ideas, explanations, frameworks, and examples.
3. Rewrite everything in clear, elegant language.

Structure the output like this:

1. TITLE
Create a better title than the original video if possible.

2. TLDR (5-7 bullets)
Summarize the entire video in the most important takeaways.

3. CORE IDEAS
Break the video into logical sections.
For each section:
- Give a short heading
- Explain the concept clearly
- Add simple examples if needed
- Use analogies where helpful

4. KEY FRAMEWORKS / METHODS
If the video explains a system, method, or strategy:
- Turn it into numbered steps
- Make it actionable

5. IMPORTANT INSIGHTS
Write the most powerful ideas from the video.

6. MEMORY HOOKS
Convert important ideas into short memorable lines.

7. PRACTICAL TAKEAWAYS
Explain what someone should DO after learning this.

Writing Style:
- Clear
- Slightly conversational
- Insightful
- Easy to skim
- More valuable than the original video

Do NOT mention the transcript.
Do NOT include timestamps.
Focus entirely on clarity and learning.
Do not make it a big boring story but summerize it in the very few and required length.create it in only 500 words.

Here is the transcript:"""

def response_generation(transcribe_text):
    response = client.models.generate_content(model="gemini-2.5-flash",contents=prompt+transcribe_text)   
    return response.text

def get_video_summary(youtube_url, force_refresh=False, include_visual_context=False):
    """
    Main function to get video summary with caching
    
    Args:
        youtube_url: YouTube video URL
        force_refresh: If True, ignore cache and generate new summary
        include_visual_context: If True, extract frames and include them for better context
    
    Returns:
        Tuple of (summary_text, is_cached, title, transcript_source)
    """
    video_id = get_video_id(youtube_url)
    
    if not video_id:
        raise ValueError("Invalid YouTube URL")
    
    # Check cache first
    if not force_refresh:
        cached = get_cached_summary(video_id)
        if cached:
            return cached['summary'], True, cached['title'], "cache"
    
    # Get transcript
    transcript_source = ""
    try:
        transcript = generate_transcript(youtube_url)
        transcript_source = "transcript"
    except:
        # If transcript not available, extract from audio
        transcript_source = "audio"
        transcript = extract_audio_and_transcribe(youtube_url)
    
    # Get video title
    try:
        ydl_opts = {'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            title = info.get('title', 'Unknown Title')
    except:
        title = "Unknown Title"
    
    # Extract frames if visual context is requested
    frame_paths = []
    if include_visual_context:
        frame_paths = extract_key_frames(youtube_url, num_frames=3)
    
    # Generate summary
    summary = response_generation_with_visual_context(transcript, frame_paths if frame_paths else None)
    
    # Store in cache
    store_summary(video_id, summary, title)
    
    return summary, False, title, transcript_source

# ==================== VIDEO ID EXTRACTION ====================
def get_video_id(youtube_url: str):
    if not youtube_url:
        return None

    parsed = urlparse(youtube_url)

    # youtube.com URLs
    if parsed.hostname in ("www.youtube.com", "youtube.com", "m.youtube.com"):
        # watch?v=VIDEO_ID
        if parsed.path == "/watch":
            return parse_qs(parsed.query).get("v", [None])[0]

        # /shorts/VIDEO_ID or /embed/VIDEO_ID
        match = re.match(r"/(shorts|embed)/([^/?]+)", parsed.path)
        if match:
            return match.group(2)

    # youtu.be/VIDEO_ID
    if parsed.hostname == "youtu.be":
        return parsed.path.lstrip("/")

    return None
