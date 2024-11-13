import os
import instaloader
from concurrent.futures import ThreadPoolExecutor
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
import google_auth_oauthlib.flow

# Authenticate to Google API (YouTube)
CLIENT_SECRETS_FILE = "client_secrets.json"
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

# Initialize Instaloader
loader = instaloader.Instaloader()

# Login to Instagram
username = "link_pl.us"
password = "Shubhamjha@2005"
loader.login(username, password)

# Target Instagram profile
profile_name = "the.poetrygram"
output_directory = f"{profile_name}_downloads"
os.makedirs(output_directory, exist_ok=True)

# Authenticate YouTube
def authenticate_youtube():
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, SCOPES
    )
    credentials = flow.run_local_server(port=8090)
    youtube = build(API_SERVICE_NAME, API_VERSION, credentials=credentials)
    return youtube

youtube = authenticate_youtube()

# Upload video function
def upload_video(youtube, video_file, title, description):
    try:
        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": ["Shorts"],
                },
                "status": {
                    "privacyStatus": "public",
                },
            },
            media_body=MediaFileUpload(video_file, chunksize=-1, resumable=True),
        )
        response = request.execute()
        print(f"Video uploaded successfully: {response['id']}")
        return response['id']
    except HttpError as e:
        print(f"Error uploading video: {e}")
        return None

# Delete video function
def delete_video(video_file):
    if os.path.exists(video_file):
        os.remove(video_file)
        print(f"Deleted video file: {video_file}")
    else:
        print(f"Video file not found: {video_file}")

# Process single video: Upload + Delete
def process_video(youtube, video_file, title, description):
    video_id = upload_video(youtube, video_file, title, description)
    if video_id:
        delete_video(video_file)

# Generate title and description (dummy logic here, you can replace it with your logic)
def generate_title_description(caption_text):
    title = "Sample Title"
    description = f"Description based on caption: {caption_text}"
    return title, description

# Main function to download, upload, and delete files in parallel
def main():
    # Fetch posts
    profile = instaloader.Profile.from_username(loader.context, profile_name)
    posts = profile.get_posts()

    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        for post in posts:
            if post.is_video:
                # Download video
                loader.download_post(post, target=output_directory)
                video_filename = f"{post.date_utc.strftime('%Y-%m-%d_%H-%M-%S')}.mp4"
                video_file_path = os.path.join(output_directory, video_filename)
                
                # Generate title and description
                caption = post.caption or "No caption available."
                title, description = generate_title_description(caption)

                # Submit tasks to executor
                futures.append(
                    executor.submit(process_video, youtube, video_file_path, title, description)
                )

        # Wait for all futures to complete
        for future in futures:
            future.result()

if __name__ == "__main__":
    main()
