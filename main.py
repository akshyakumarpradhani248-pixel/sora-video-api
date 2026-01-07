import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from urllib.parse import urlparse, urlunparse

# --- Pydantic Models for Request/Response ---
class VideoRequest(BaseModel):
    url: HttpUrl # Use HttpUrl for automatic validation

class VideoResponse(BaseModel):
    source_url: str

# --- FastAPI App Initialization ---
app = FastAPI(
    title="Sora Video Downloader API",
    description="An API to extract the source MP4 link from a Sora video page.",
    version="1.0.0",
)

# --- CORS Configuration ---
# This allows your frontend (running on a different port/domain)
# to communicate with this backend.
origins = [
    "*", # In production, you should restrict this to your actual frontend domain
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- API Endpoints ---
@app.post("/get-video-source", response_model=VideoResponse)
async def get_video_source(request: VideoRequest):
    """
    Accepts a Sora URL, fetches its notification data, and extracts
    the watermark-free source video URL.
    """
    try:
        # 1. Parse the incoming URL to safely construct the API endpoint URL
        parsed_url = urlparse(str(request.url))
        if not parsed_url.netloc.endswith('sora.chatgpt.com'):
             raise HTTPException(
                status_code=400,
                detail="Invalid URL. Please provide a valid sora.chatgpt.com URL."
            )

        base_sora_url = urlunparse((parsed_url.scheme, parsed_url.netloc, '', '', '', ''))
        notif_url = f"{base_sora_url}/backend/notif?limit=10"

        # 2. Make an asynchronous HTTP request to the notification endpoint
        async with httpx.AsyncClient() as client:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            response = await client.get(notif_url, headers=headers, timeout=10.0)
            response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
            data = response.json()

    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502, # Bad Gateway
            detail=f"Failed to fetch data from Sora API: {exc}"
        )
    except httpx.HTTPStatusError as exc:
         raise HTTPException(
            status_code=exc.response.status_code,
            detail=f"Sora API returned an error: {exc.response.text}"
        )


    # 3. Iterate through the notifications to find the source video URL
    for item in data.get("items", []):
        video_info = item.get("video")
        if video_info and "source" in video_info:
            source_url = video_info["source"]
            if source_url:
                return VideoResponse(source_url=source_url)

    # 4. If no source URL is found after checking all items, raise an error
    raise HTTPException(
        status_code=404,
        detail="Source video not found in the recent notifications. The video may be old or the URL is incorrect."
    )

@app.get("/")
def read_root():
    """ A simple health check endpoint. """
    return {"status": "ok", "message": "Sora Video Downloader API is running."}
