import scrapetube
from langchain_community.document_loaders import YoutubeLoader

def fetch_playlist_transcripts(playlist_id):
    print(f"\n🎥 [YouTube] Processing Playlist: {playlist_id}...")
    docs = []
    
    try:
        videos = scrapetube.get_playlist(playlist_id)
        for video in videos:
            video_id = video['videoId']
            url = f"https://www.youtube.com/watch?v={video_id}"
            try:
                loader = YoutubeLoader.from_youtube_url(
                    url, add_video_info=True, language=["en", "ta"], translation="en"
                )
                docs.extend(loader.load())
                print(f"   ✅ Fetched: {video_id}")
            except Exception:
                print(f"   ⚠️ No transcript: {video_id}")
    except Exception as e:
        print(f"   ❌ Playlist Error: {e}")
        
    return docs