from fastapi import FastAPI, HTTPException, Query
from pipeline import pipeline, load_api_key

app = FastAPI()

# Load our API key securely on the server side
API_KEY = load_api_key()

@app.get('/')
def root():
    return {"message": "Welcome to the Riot Match API", "status": "Running"}

@app.get('/api/matches/{platform}/{player_name}/{player_tag}')
def get_matches(
    platform: str, 
    player_name: str, 
    player_tag: str, 
    count: int = Query(5, ge=1, le=100) # Query parameter for count with validation
):
    if not API_KEY:
        raise HTTPException(status_code=500, detail="API Key not configured on the server")
        
    result = pipeline(
        api_key=API_KEY, 
        player_name=player_name, 
        player_tag=player_tag, 
        platform=platform, 
        count=count
    )
    
    if result is None:
        raise HTTPException(
            status_code=404, 
            detail="Could not fetch matches."
        )
        
    return result



