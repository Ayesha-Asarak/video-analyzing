from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound
from googleapiclient.discovery import build
import re
import main
from configparser import ConfigParser
import textwrap
app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

class YouTubeLink(BaseModel):
    youtube_link: str
def to_markdown(text):
    text = text.replace("•", "  *")
    indented_text = textwrap.indent(text, "\n ", predicate=lambda _: True)
    return indented_text

config = ConfigParser()
config.read("credentials.ini")
api_key = config["API_KEY"]["google_api_key"]
youtube_api_key = config["API_KEY"]["youtube_api_key"]

genai.configure(api_key=api_key)

model_gemini_pro = genai.GenerativeModel("gemini-pro")

safety_settings = [
    {
        "category": "HARM_CATEGORY_DANGEROUS",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE",
    },
]
def extract_video_id(youtube_link):
    video_id = None
    patterns = [
        r'(?<=v=)[^&#]+',  # Handles links like https://www.youtube.com/watch?v=VIDEO_ID
        r'(?<=be/)[^&#]+',  # Handles links like https://youtu.be/VIDEO_ID
        r'(?<=embed/)[^&#]+'  # Handles links like https://www.youtube.com/embed/VIDEO_ID
    ]
    for pattern in patterns:
        match = re.search(pattern, youtube_link)
        if match:
            video_id = match.group()
            break
    return video_id

def fetch_youtube_transcript(youtube_link, languages=('en', 'hi')):
    try:
        video_id = extract_video_id(youtube_link)
        if not video_id:
            raise ValueError("Invalid YouTube link format")
        
        # Attempt to fetch transcript in preferred languages
        transcript = None
        for lang in languages:
            try:
                transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])
                break
            except NoTranscriptFound:
                continue
        
        if not transcript:
            raise NoTranscriptFound(f"No transcripts found for video {video_id} in languages {languages}")

        transcript_text = " ".join([item['text'] for item in transcript])
        return transcript_text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching transcript: {str(e)}")

def fetch_video_description(youtube_link):
    try:
        video_id = extract_video_id(youtube_link)
        if not video_id:
            raise ValueError("Invalid YouTube link format")

        youtube = build('youtube', 'v3', developerKey=youtube_api_key)
        request = youtube.videos().list(part="snippet", id=video_id)
        response = request.execute()
        
        if not response["items"]:
            raise ValueError("Video not found")

        description = response["items"][0]["snippet"]["description"]
        return description
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching video description: {str(e)}")

# def generate_summary(text):
def generate_summary(text):
    try:
        prompt = f"Describe the text considering it is a video in English: {text}"
        response = model_gemini_pro.generate_content(prompt, safety_settings=safety_settings)
        return response.text  # Access the 'text' attribute of the response object
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")

@app.post("/generate-summary")
def generate_summary_endpoint(link: YouTubeLink):
    video_text = fetch_youtube_transcript(link.youtube_link)
    if not video_text:
        video_text = fetch_video_description(link.youtube_link)

    if video_text:
        summary = generate_summary(video_text)
        if summary:
            return {"summary": summary}
        else:
            raise HTTPException(status_code=500, detail="Failed to generate summary.")
    else:
        raise HTTPException(status_code=500, detail="Failed to get summary.")
