import time
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware

from pipeline import pipeline, load_api_key

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
    return response

# Load our API key securely on the server side
API_KEY = load_api_key()

@app.get('/')
def root():
    return {"instruction": "Open this link: http://127.0.0.1:8000/docs#/",
             "status": "Running"}

@app.get('/api/matches/{platform}/{player_name}/{player_tag}')
def get_matches(
    player_name: str, 
    player_tag: str, 
    platform: str, 
    save: bool = Query(False),
    count: int = Query(20, ge=1, le=100), # Query parameter for count with validation
):
    if not API_KEY:
        raise HTTPException(status_code=500, detail="API Key not configured on the server")
        
    result = pipeline(
        api_key=API_KEY, 
        player_name=player_name, 
        player_tag=player_tag, 
        platform=platform, 
        save = save,
        count=count
    )
    
    if result is None:
        raise HTTPException(
            status_code=404, 
            detail="Could not fetch matches. [404]"
        )
        
    return result



