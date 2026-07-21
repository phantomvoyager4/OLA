import time
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware

from .pipeline import activity_pipeline, pipeline, load_api_key
from .riot_api import RIOT_RATE_LIMITER

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time_ms = (time.perf_counter() - start_time) * 1000
    response.headers["Process-Time-ms"] = f"{process_time_ms:.2f}"

    rate_limit = RIOT_RATE_LIMITER.snapshot()
    response.headers["X-Riot-Rate-Limit-Short"] = (
        f"{rate_limit['short_used']}/{rate_limit['short_limit']}"
    )
    response.headers["X-Riot-Rate-Limit-Long"] = (
        f"{rate_limit['long_used']}/{rate_limit['long_limit']}"
    )
    response.headers["X-Riot-Rate-Limit-Reset"] = (
        f"{rate_limit['long_reset_seconds']:.0f}"
    )

    short_ratio = rate_limit["short_used"] / rate_limit["short_limit"]
    long_ratio = rate_limit["long_used"] / rate_limit["long_limit"]
    if short_ratio >= 0.8 or long_ratio >= 0.75:
        response.headers["X-Riot-Rate-Limit-Warning"] = "approaching"
    return response

# Load our API key securely on the server side
API_KEY = load_api_key()

@app.get('/')
def root():
    return {"instruction": "Open this link: http://127.0.0.1:8000/docs#/",
             "status": "Running"}


@app.get('/api/rate-limit')
def get_rate_limit():
    """Expose limiter state without consuming Riot API quota."""
    return RIOT_RATE_LIMITER.snapshot()

@app.get('/api/matches/{platform}/{player_name}/{player_tag}')
def get_matches(
    player_name: str, 
    player_tag: str, 
    platform: str, 
    save: bool = Query(False),
    count: int = Query(20, ge=1, le=100), # Query parameter for count with validation
    start: int = Query(0, ge=0), # Query parameter for offset
):
    if not API_KEY:
        raise HTTPException(status_code=500, detail="API Key not configured on the server")
        
    result = pipeline(
        api_key=API_KEY, 
        player_name=player_name, 
        player_tag=player_tag, 
        platform=platform, 
        save=save,
        count=count,
        start=start
    )
    
    if result is None:
        raise HTTPException(
            status_code=404, 
            detail="Could not fetch matches. [404]"
        )
        
    return result


@app.get('/api/activity/{platform}/{player_name}/{player_tag}')
def get_activity(
    player_name: str,
    player_tag: str,
    platform: str,
    count: int = Query(40, ge=1, le=80),
    start: int = Query(20, ge=0),
):
    if not API_KEY:
        raise HTTPException(status_code=500, detail="API Key not configured on the server")

    result = activity_pipeline(
        api_key=API_KEY,
        player_name=player_name,
        player_tag=player_tag,
        platform=platform,
        count=count,
        start=start,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Could not fetch player activity")
    return result



