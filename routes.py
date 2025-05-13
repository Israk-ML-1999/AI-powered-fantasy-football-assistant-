from fastapi import APIRouter, HTTPException, Path, Depends
from typing import Optional
from datetime import datetime, timedelta
import functools

from App.services.nfl_service import nfl_service
from App.models.schemas import ErrorResponse

# Simple in-memory cache for API responses
cache = {}
CACHE_EXPIRY = timedelta(minutes=15)  # Cache expiry time

def with_cache(expiry: Optional[timedelta] = None):
    """
    Decorator to cache API responses
    
    Args:
        expiry: Optional time delta for cache expiry (default: 15 minutes)
    """
    if expiry is None:
        expiry = CACHE_EXPIRY
        
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Create a cache key from function name and arguments
            key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Check if we have a cached response and it's still valid
            if key in cache:
                timestamp, value = cache[key]
                if datetime.now() - timestamp < expiry:
                    return value
            
            # Call the original function if no cache hit
            result = await func(*args, **kwargs)
            
            # Cache the result
            cache[key] = (datetime.now(), result)
            return result
        return wrapper
    return decorator

router = APIRouter(prefix="/nfl", tags=["NFL Data"])

@router.get("/tea





ms", response_model=dict, summary="Get NFL Teams Hierarchy")
@with_cache(timedelta(hours=24))  # Teams don't change often, cache for 24 hours
async def get_teams():
    """
    Retrieve all NFL teams organized by conference and division.
    """
    return await nfl_service.get_teams()

@router.get("/schedule/{year}/{season_type}", response_model=dict, summary="Get NFL Schedule")
@with_cache(timedelta(hours=6))  # Schedules might update during the day
async def get_schedule(
    year: int = Path(..., description="Year of the schedule", example=2023),
    season_type: str = Path(..., description="Type of season (REG, PRE, PST)", example="REG")
):
    """
    Retrieve the NFL schedule for a specific year and season type.
    
    - **year**: Year of the schedule (e.g., 2023)
    - **season_type**: Type of season (REG: Regular Season, PRE: Preseason, PST: Postseason)
    """
    return await nfl_service.get_schedule(year, season_type)

@router.get("/teams/{team_id}", response_model=dict, summary="Get Team Profile")
@with_cache(timedelta(hours=12))  # Team profiles don't change very often
async def get_team_profile(
    team_id: str = Path(..., description="Team ID", example="97354895-8c77-4fd4-a860-32e62ea7382a")
):
    """
    Retrieve detailed information about a specific NFL team.
    
    - **team_id**: The unique identifier for the team
    """
    return await nfl_service.get_team_profile(team_id)

@router.get("/players/{player_id}", response_model=dict, summary="Get Player Profile")
@with_cache(timedelta(hours=6))  # Player profiles might update during the day
async def get_player_profile(
    player_id: str = Path(..., description="Player ID", example="2cae6d5b-b7b5-4a1c-bfd6-cc43dded3037")
):
    """
    Retrieve detailed information about a specific NFL player.
    
    - **player_id**: The unique identifier for the player
    """
    return await nfl_service.get_player_profile(player_id)

@router.get("/games/{game_id}/boxscore", response_model=dict, summary="Get Game Boxscore")
@with_cache(timedelta(minutes=30))  # Game stats might update frequently during games
async def get_game_boxscore(
    game_id: str = Path(..., description="Game ID", example="1f5dca5b-b5c9-4ec9-88c7-937c7f8e5e84")
):
    """
    Retrieve boxscore statistics for a specific NFL game.
    
    - **game_id**: The unique identifier for the game
    """
    return await nfl_service.get_game_boxscore(game_id)

@router.delete("/cache", summary="Clear API Cache")
async def clear_cache():
    """
    Clear the API response cache. This is useful when you want to force fresh data from the NFL API.
    """
    global cache
    cache = {}
    return {"message": "Cache cleared successfully"}
