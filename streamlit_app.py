import streamlit as st
from app import get_video_summary, load_cache, get_video_id, extract_key_frames
import pandas as pd
from datetime import datetime
from pathlib import Path

# Page config
st.set_page_config(
    page_title="YouTube Video Summarizer",
    page_icon="📺",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .cache-badge {
        display: inline-block;
        background-color: #90EE90;
        padding: 5px 10px;
        border-radius: 5px;
        font-size: 12px;
        font-weight: bold;
        margin-left: 10px;
    }
    .new-badge {
        display: inline-block;
        background-color: #FFB6C1;
        padding: 5px 10px;
        border-radius: 5px;
        font-size: 12px;
        font-weight: bold;
        margin-left: 10px;
    }
    .transcript-badge {
        display: inline-block;
        background-color: #87CEEB;
        padding: 3px 8px;
        border-radius: 3px;
        font-size: 11px;
        margin-top: 5px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📺 YouTube Video Summarizer with AI")
st.markdown("Transform YouTube videos into crystal-clear, actionable notes using AI")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    force_refresh = st.checkbox("🔄 Force Refresh Summary", 
                                help="Generate new summary even if cached")
    
    include_visuals = st.checkbox("🎨 Include Visual Context", 
                                 help="Extract key frames from video for better AI understanding (slower)")
    
    if include_visuals:
        st.info("📌 Visual context will be extracted and sent to AI for better understanding of video content")
    
    st.markdown("---")
    st.header("📚 Cached Summaries")
    cache = load_cache()
    
    if cache:
        st.write(f"**Total cached summaries:** {len(cache)}")
        
        # Display cache info
        with st.expander("View All Cached Videos"):
            cache_data = []
            for key, value in cache.items():
                cache_data.append({
                    "Title": value.get('title', 'N/A'),
                    "Cached On": value.get('timestamp', 'N/A')[:10],
                    "Video ID": value.get('video_id', 'N/A')
                })
            
            if cache_data:
                df = pd.DataFrame(cache_data)
                st.dataframe(df, use_container_width=True)
        
        if st.button("🗑️ Clear All Cache"):
            import json
            with open("video_summaries_cache.json", 'w') as f:
                json.dump({}, f)
            st.success("Cache cleared!")
            st.rerun()
    else:
        st.info("No cached summaries yet")

# Main content
col1, col2 = st.columns([3, 1])

with col1:
    youtube_url = st.text_input(
        "🔗 Enter YouTube URL",
        placeholder="https://www.youtube.com/watch?v=...",
        help="Paste any YouTube video URL"
    )

with col2:
    st.write("")  # Spacer for alignment
    submit_button = st.button("✨ Summarize", use_container_width=True)

st.markdown("---")

# Process if URL is provided
if submit_button and youtube_url:
    try:
        # Create status container
        status_placeholder = st.empty()
        
        with status_placeholder.container():
            with st.spinner("🔄 Processing your video..."):
                # Show different status based on what's happening
                with st.status("Processing...", expanded=True) as status_container:
                    status_container.write("📍 Analyzing URL...")
                    
                    # Get video summary with visual context if enabled
                    summary, is_cached, title, transcript_source = get_video_summary(
                        youtube_url, 
                        force_refresh=force_refresh,
                        include_visual_context=include_visuals
                    )
                    
                    # Update status based on transcript source
                    if is_cached:
                        status_container.write("✅ Retrieved from cache")
                    elif transcript_source == "audio":
                        status_container.write("🎤 Converting video audio to text...")
                        status_container.write("⏳ Processing audio (1-2 minutes)")
                        status_container.write("✅ Generated transcript from audio")
                    else:  # transcript
                        status_container.write("📝 Found official transcript")
                    
                    if include_visuals:
                        status_container.write("🎨 Extracted key frames for visual context")
                    
                    status_container.write("🤖 Generating your summary...")
                    status_container.write("✅ Summary created successfully!")
        
        # Display results
        st.success("✅ Summary generated successfully!")
        
        # Header with badge indicators
        if is_cached:
            st.markdown(f"### 🎬 {title} <span class='cache-badge'>📦 FROM CACHE</span>", 
                       unsafe_allow_html=True)
            st.info("This summary was retrieved from cache. Use 'Force Refresh' to generate a new one.")
        else:
            badge_text = "✨ NEW"
            if transcript_source == "audio":
                badge_text += " (Audio)"
            elif transcript_source == "transcript":
                badge_text += " (Transcript)"
            
            st.markdown(f"### 🎬 {title} <span class='new-badge'>{badge_text}</span>", 
                       unsafe_allow_html=True)
            st.success("This summary has been saved to cache for future use!")
            
            # Show transcript source info
            if transcript_source == "audio":
                st.markdown("<span class='transcript-badge'>🎤 Generated from video audio</span>", 
                           unsafe_allow_html=True)
            else:
                st.markdown("<span class='transcript-badge'>📝 Generated from official transcript</span>", 
                           unsafe_allow_html=True)
            
            if include_visuals:
                st.markdown("<span class='transcript-badge'>🎨 Enhanced with visual context</span>", 
                           unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Display summary
        st.markdown("#### 📝 Summary")
        st.write(summary)
        
        # Export options
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📋 Copy to Clipboard"):
                st.write(summary)
        
        with col2:
            if st.button("💾 Export as Text"):
                st.download_button(
                    label="Download Summary",
                    data=summary,
                    file_name=f"{title}.txt",
                    mime="text/plain"
                )
        
        with col3:
            if st.button("📥 Export as Markdown"):
                md_content = f"# {title}\n\n{summary}"
                st.download_button(
                    label="Download as Markdown",
                    data=md_content,
                    file_name=f"{title}.md",
                    mime="text/markdown"
                )
    
    except ValueError as e:
        st.error(f"❌ Invalid URL: {str(e)}")
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        st.info("💡 Make sure your GOOGLE_API_KEY is set correctly in your .env file")

elif submit_button and not youtube_url:
    st.warning("⚠️ Please enter a YouTube URL first")

# Tips section
with st.expander("💡 Tips & Features"):
    st.markdown("""
    ### ✨ Features:
    
    1. **📦 Smart Caching**: Summaries are automatically cached. Same video? Get instant results!
    2. **🎯 No Transcript? No Problem**: Automatically extracts audio and converts to text using AI
    3. **🎨 Visual Context**: Extract key frames from videos for better AI understanding
    4. **⚡ Multiple URL Formats**: Works with:
       - `https://www.youtube.com/watch?v=...`
       - `https://youtu.be/...`
       - `https://www.youtube.com/shorts/...`
    
    5. **🔄 Force Refresh**: Generate new summaries anytime
    6. **📥 Export**: Download summaries as text or markdown files
    
    ### 🎨 About Visual Context:
    - Extracts **3 key frames** from the video
    - Sends frames to AI along with transcript
    - **Better understanding** of visual concepts, diagrams, demos
    - **Takes longer** (adds 30-60 seconds)
    - **Worth it for**: Tutorials, presentations, visual content
    - **Skip for**: Podcasts, audio-heavy content
    
    ### 📚 How it works:
    - **If transcript available**: Uses official YouTube transcript (instant & accurate) ✨
    - **If no transcript**: Extracts audio, converts to text, then summarizes 🐌
    
    ### ⚠️ Note on LLM Capabilities:
    - LLMs cannot directly "watch" videos as video files
    - They process text (transcripts), images (frames), or audio
    - **Our hybrid approach is optimal**: Transcripts + optional frames!
    """)
