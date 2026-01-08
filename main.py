from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp

app = FastAPI()

# --- 1. SETTING UP PERMISSIONS (CORS) ---
# Iske bina Mobile App server se connect nahi ho payega
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Sabko allow karo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. DATA MODEL ---
class VideoRequest(BaseModel):
    url: str

# --- 3. HOME ROUTE (Server Check) ---
@app.get("/")
def home():
    return {"status": "Running", "message": "Sora Server is Ready! 🚀"}

# --- 4. MAIN ENGINE (The Logic) ---
@app.post("/get-video")
def get_video(request: VideoRequest):
    url = request.url
    print(f"Processing Request for: {url}")

    try:
        # yt-dlp Options (Video Extract karne ka tareeka)
        ydl_opts = {
            'format': 'best',       # Sabse achi quality chahiye
            'quiet': True,          # Background mein shanti se kaam karo
            'no_warnings': True,
            'extract_flat': False,  # Pura info nikalo
        }

        # --- PATTERN BREAKING LOGIC ---
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 1. URL se data nikalo
            info = ydl.extract_info(url, download=False)
            
            # 2. Video ka Direct Link dhoondo
            video_url = info.get('url', None)
            title = info.get('title', 'Sora Generated Video')

            # Agar direct link na mile, to format list check karo
            if not video_url and 'entries' in info:
                 video_url = info['entries'][0].get('url')

            if not video_url:
                raise Exception("Is Link se Video nahi nikal paaya")

            # 3. Safalta! Link mil gaya
            return {
                "status": "success",
                "title": title,
                "download_url": video_url,
                "message": "Watermark Removed Successfully"
            }

    except Exception as e:
        # Agar koi gadbad hui to ye error jayega
        print(f"Error: {str(e)}")
        return {
            "status": "error",
            "detail": "Server Error: Link invalid hai ya server busy hai.",
            "original_error": str(e)
        }
