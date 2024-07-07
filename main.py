from configparser import ConfigParser
import google.generativeai as genai
import streamlit as st
import textwrap
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound
import re

def to_markdown(text):
    text = text.replace("•", "  *")
    indented_text = textwrap.indent(text, "\n ", predicate=lambda _: True)
    return indented_text

config = ConfigParser()
config.read("credentials.ini")
api_key = config["API_KEY"]["google_api_key"]

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
        st.error(f"Error fetching transcript: {str(e)}")
        return None

# Function to generate summary from provided text
def generate_summary(text):
    try:
        prompt = f"Describe the text considering as it a video in english: {text}"
        response = model_gemini_pro.generate_content(prompt, safety_settings=safety_settings)
        return response.text  # Access the 'text' attribute of the response object
    except Exception as e:
        st.error(f"Error generating summary: {str(e)}")
        return None

def main():
    st.title("YouTube Video Summary Generator")
    youtube_link = st.text_input("Enter the YouTube link you want to summarize")
    generate_button = st.button("Generate Summary")

    if generate_button and youtube_link:
        st.info("Fetching transcript... Please wait.")
        video_text = fetch_youtube_transcript(youtube_link)
        if video_text:
            st.info("Generating summary... Please wait.")
            summary = generate_summary(video_text)
            if summary:
                st.success(summary)
            else:
                st.error("Failed to generate summary.")
        else:
            st.error("Failed to fetch transcript.")

if __name__ == "__main__":
    main()
