import re
import openai
import streamlit as st

def format_timestamp_vtt(seconds):
    """
    Formats seconds into WebVTT timestamp: MM:SS.mmm or HH:MM:SS.mmm
    Microsoft Stream requires strict formatting with dots for milliseconds.
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    
    # MS Stream prefers HH:MM:SS.mmm even if hours is 0, or MM:SS.mmm
    # Let's use HH:MM:SS.mmm to be safe and consistent
    return f"{hours:02}:{minutes:02}:{secs:06.3f}"

def parse_timestamp(timestamp_str):
    """
    Parses timestamp string (SRT with comma or VTT with dot) into seconds.
    """
    timestamp_str = timestamp_str.strip().replace(',', '.')
    parts = timestamp_str.split(':')
    
    seconds = 0
    if len(parts) == 3:
        seconds += int(parts[0]) * 3600
        seconds += int(parts[1]) * 60
        seconds += float(parts[2])
    elif len(parts) == 2:
        seconds += int(parts[0]) * 60
        seconds += float(parts[1])
        
    return seconds

def parse_srt(content):
    """
    Parses SRT content into a list of cues.
    """
    cues = []
    # Normalize newlines
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    blocks = content.strip().split('\n\n')
    
    for block in blocks:
        lines = block.split('\n')
        if len(lines) >= 3:
            # Line 0: Index (ignore)
            # Line 1: Timestamp
            times = lines[1].split(' --> ')
            if len(times) == 2:
                start = parse_timestamp(times[0])
                end = parse_timestamp(times[1])
                text = "\n".join(lines[2:])
                cues.append({"start": start, "end": end, "text": text})
                
    return cues

def parse_vtt(content):
    """
    Parses VTT content into a list of cues.
    Very basic parser that ignores headers and styles for now.
    """
    cues = []
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    lines = content.split('\n')
    
    current_cue = None
    
    timestamp_pattern = re.compile(r'(\d{2}:\d{2}:\d{2}[\.,]\d{3}|\d{2}:\d{2}[\.,]\d{3}) --> (\d{2}:\d{2}:\d{2}[\.,]\d{3}|\d{2}:\d{2}[\.,]\d{3})')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if line == "WEBVTT" or line == "":
            i += 1
            continue
            
        match = timestamp_pattern.search(line)
        if match:
            start = parse_timestamp(match.group(1))
            end = parse_timestamp(match.group(2))
            
            # Get text lines until next empty line
            text_lines = []
            i += 1
            while i < len(lines) and lines[i].strip() != "":
                text_lines.append(lines[i].strip())
                i += 1
                
            cues.append({"start": start, "end": end, "text": "\n".join(text_lines)})
        else:
            # Might be an ID or note, skip
            i += 1
            
    return cues

def translate_batched(cues, target_lang="no", batch_size=20):
    """
    Translates cues in batches using OpenAI.
    """
    if "openai" not in st.secrets or "api_key" not in st.secrets["openai"]:
        raise Exception("OpenAI API Key not found in secrets.")
        
    client = openai.OpenAI(api_key=st.secrets["openai"]["api_key"])
    
    translated_cues = []
    
    # Process in batches
    progress_bar = st.progress(0)
    
    total_batches = (len(cues) + batch_size - 1) // batch_size
    
    for idx, i in enumerate(range(0, len(cues), batch_size)):
        batch = cues[i:i+batch_size]
        
        # Update progress
        progress_bar.progress((idx) / total_batches)
        
        # Prepare prompt
        text_chunk = "\n<SEP>\n".join([c["text"] for c in batch])
        
        prompt = f"""
        Translate the following subtitle segments to Norwegian (Bokmål).
        The segments are separated by '<SEP>'.
        Maintain the exact number of segments.
        Do not translate proper names if inappropriate.
        Keep the verification tone neutral and accurate.
        Microsoft Stream requires strict VTT, so ensure no special characters break it.
        Answer ONLY with the translated segments separated by <SEP>.
        
        Input:
        {text_chunk}
        """
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a professional translator for video subtitles."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            translated_text_chunk = response.choices[0].message.content
            translated_segments = translated_text_chunk.split('<SEP>')
            
            # Clean up segments
            translated_segments = [s.strip() for s in translated_segments]
            
            # Verify length
            if len(translated_segments) != len(batch):
                print(f"Warning: Batch returned {len(translated_segments)} segments, expected {len(batch)}")
                # Best effort mapping
                
            for j, cue in enumerate(batch):
                new_cue = cue.copy()
                if j < len(translated_segments):
                    new_cue["text"] = translated_segments[j]
                translated_cues.append(new_cue)
                
        except Exception as e:
            # On error, append original
            print(f"Error translating batch: {e}")
            translated_cues.extend(batch)
            
    progress_bar.progress(1.0)
    return translated_cues

def generate_vtt(cues):
    """
    Generates WebVTT content from cues.
    """
    output = ["WEBVTT", ""]
    
    for cue in cues:
        start_str = format_timestamp_vtt(cue["start"])
        end_str = format_timestamp_vtt(cue["end"])
        
        output.append(f"{start_str} --> {end_str}")
        output.append(cue["text"])
        output.append("") # Empty line after each cue
        
    return "\n".join(output)
