import os
import pandas as pd
from googleapiclient.discovery import build
from pytube import YouTube

# YouTube API Key
API_KEY = "AIzaSyD981heQh7GIWLmtVY-At0-jrXmd4aFhu8"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

def fetch_top_videos(genre, max_results=500):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)
    video_ids = []
    next_page_token = None

    while len(video_ids) < max_results:
        request = youtube.search().list(
            q=genre,
            type="video",
            part="id,snippet",
            maxResults=min(50, max_results - len(video_ids)),
            pageToken=next_page_token
        )
        response = request.execute()
        video_ids += [item['id']['videoId'] for item in response.get('items', [])]
        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break

    return video_ids

def fetch_video_details(video_ids):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)
    video_data = []

    for i in range(0, len(video_ids), 50):  # Batch process video IDs
        request = youtube.videos().list(
            id=",".join(video_ids[i:i+50]),
            part="snippet,contentDetails,statistics,recordingDetails,topicDetails"
        )
        response = request.execute()
        for item in response.get('items', []):
            video_data.append({
                "Video URL": f"https://www.youtube.com/watch?v={item['id']}",
                "Title": item['snippet']['title'],
                "Description": item['snippet']['description'],
                "Channel Title": item['snippet']['channelTitle'],
                "Keyword Tags": item['snippet'].get('tags', []),
                "Category": item['snippet']['categoryId'],
                "Topic Details": item.get('topicDetails', {}).get('topicCategories', None),
                "Published At": item['snippet']['publishedAt'],
                "Duration": item['contentDetails']['duration'],
                "View Count": item['statistics'].get('viewCount', 0),
                "Comment Count": item['statistics'].get('commentCount', 0),
                "Captions Available": item['contentDetails'].get('caption', 'false'),
                "Location": item.get('recordingDetails', {}).get('location', None)
            })

    return video_data

def download_captions(video_url):
    try:
        yt = YouTube(video_url)
        en_caption = yt.captions.get_by_language_code('en')
        if en_caption:
            return en_caption.generate_srt_captions()
        return None
    except Exception as e:
        print(f"Error downloading captions for {video_url}: {e}")
        return None

def save_to_csv(data, filename):
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"Data saved to {filename}")

def main():
    genre = input("Enter the genre to search for: ")
    print("Fetching top videos...")
    video_ids = fetch_top_videos(genre)
    print(f"Found {len(video_ids)} videos. Fetching details...")

    video_data = fetch_video_details(video_ids)
    for video in video_data:
        if video["Captions Available"] == "true":
            captions = download_captions(video["Video URL"])
            video["Caption Text"] = captions if captions else "No Captions"
        else:
            video["Caption Text"] = "No Captions"

    filename = f"{genre}_videos.csv"
    save_to_csv(video_data, filename)

if __name__ == "__main__":
    main()
