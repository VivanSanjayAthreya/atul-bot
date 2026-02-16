import os
import json
import scrapetube
from youtube_transcript_api import YouTubeTranscriptApi
from pathlib import Path

# --- CONFIGURATION ---
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / 'data'
INPUT_FILE = DATA_DIR / "youtube_links.txt"
OUTPUT_FILE = DATA_DIR / "youtube_dump.json"

def get_transcript_safe(video_id):
    """
    Retrieves transcript text using whatever method is available.
    """
    try:
        if hasattr(YouTubeTranscriptApi, 'list_transcripts'):
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            t = transcript_list.find_transcript(['en', 'ta', 'hi', 'kn', 'te'])
            return t.fetch()

        api = YouTubeTranscriptApi()
        if hasattr(api, 'list'):
            transcript_list = api.list(video_id)
            if hasattr(transcript_list, 'find_transcript'):
                t = transcript_list.find_transcript(['en', 'ta', 'hi', 'kn', 'te'])
                return t.fetch()
        
        if hasattr(api, 'fetch'):
            return api.fetch(video_id, languages=['en', 'ta', 'hi', 'kn', 'te'])

    except Exception:
        return None
    return None

def fetch_youtube_data():
    if not INPUT_FILE.exists():
        print(f"❌ Error: Input file '{INPUT_FILE}' not found.")
        return

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # --- 1. LOAD EXISTING DATA (Optimization) ---
    existing_data = []
    existing_ids = set()
    
    if OUTPUT_FILE.exists():
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                # Create a set of IDs for fast lookup
                for item in existing_data:
                    # Extract ID from source url "https://...v=ID"
                    if 'v=' in item['source']:
                        vid = item['source'].split('v=')[-1]
                        existing_ids.add(vid)
            print(f"📂 Loaded {len(existing_data)} videos from existing JSON.")
        except Exception as e:
            print(f"⚠️ Could not load existing JSON (starting fresh): {e}")

    # --- 2. PARSE INPUT LINKS ---
    entries = []
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # Skip empty lines OR lines starting with # (comments)
            if not line or line.startswith("#"):
                continue
            entries.append(line)

    new_videos_count = 0
    print(f"🎥 Crawler: Processing {len(entries)} playlists/links...")

    for entry in entries:
        video_details = [] 

        try:
            if "list=" in entry:
                playlist_id = entry.split("list=")[-1].split("&")[0]
                print(f"\n   ▶️  Playlist: {playlist_id}")
                videos = scrapetube.get_playlist(playlist_id)
                for v in videos:
                    # Safely get title
                    title = 'Unknown Title'
                    if 'title' in v:
                        if isinstance(v['title'], dict):
                            title = v['title'].get('runs', [{}])[0].get('text', 'Unknown Title')
                        else:
                            title = v['title']
                    video_details.append({'id': v['videoId'], 'title': title})
            else:
                vid = entry.split("v=")[-1].split("&")[0]
                video_details.append({'id': vid, 'title': 'Single Video'})
        except Exception:
            continue

        # --- 3. PROCESS VIDEOS ---
        for video in video_details:
            vid_id = video['id']
            vid_title = video['title']
            
            # --- THE CHECK: SKIP IF EXISTS ---
            if vid_id in existing_ids:
                # print(f"      ⏭️  Skipping (Already in JSON): {vid_id}", end="\r")
                continue

            print(f"      ⬇️  Fetching New: {vid_id}...", end="\r")
            
            raw_transcript = get_transcript_safe(vid_id)
            
            if raw_transcript:
                full_text_parts = []
                for item in raw_transcript:
                    if hasattr(item, 'text'):
                         full_text_parts.append(item.text)
                    elif isinstance(item, dict) and 'text' in item:
                         full_text_parts.append(item['text'])
                
                full_text = " ".join(full_text_parts)
                
                video_entry = {
                    "source": f"https://www.youtube.com/watch?v={vid_id}",
                    "title": vid_title,
                    "content": full_text,
                    "type": "youtube"
                }
                
                # Append to memory lists
                existing_data.append(video_entry)
                existing_ids.add(vid_id)
                new_videos_count += 1
            else:
                pass

    # --- 4. SAVE ONLY IF NEW DATA ---
    if new_videos_count > 0:
        print(f"\n\n💾 Saving {len(existing_data)} videos (Added {new_videos_count} new) to '{OUTPUT_FILE}'...")
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=4)
        print("✅ Done!")
    else:
        print(f"\n✅ No new videos found. JSON is up to date.")

if __name__ == "__main__":
    fetch_youtube_data()