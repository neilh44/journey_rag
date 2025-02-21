from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from api_client import APIClient
import re
from logger import setup_logger
import traceback
import json

# Set up loggers
app_logger = setup_logger('app')
api_logger = setup_logger('api', 'api.log')

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/components", StaticFiles(directory="static/components"), name="components")

class SearchQuery(BaseModel):
    query: str

@app.get("/")
async def read_root():
    app_logger.info("Serving index.html")
    return FileResponse("static/index.html")

@app.post("/search")
async def search(query: SearchQuery, request: Request):
    api_client = APIClient()
    
    try:
        # Log incoming request
        app_logger.info(f"Received search query: {query.query}")
        
        # Log request headers for debugging
        headers = dict(request.headers)
        app_logger.debug(f"Request headers: {json.dumps(headers, indent=2)}")

        # Check if the query is about a destination
        if re.search(r"tell me about|what.*about|info.*about|guide.*to", query.query.lower()):
            app_logger.info("Processing destination info query")
            try:
                result = await api_client.get_destination_info(query.query)
                app_logger.info("Successfully retrieved destination info")
                return result
            except Exception as e:
                app_logger.error(f"Error getting destination info: {str(e)}")
                app_logger.error(traceback.format_exc())
                raise HTTPException(status_code=500, detail=str(e))
        
        # Handle flight search
        app_logger.info("Processing flight search query")
        try:
            flight_query = await api_client.format_flight_query(query.query)
            app_logger.debug(f"Formatted flight query: {json.dumps(flight_query, indent=2)}")
            
            result = await api_client.search_flights(flight_query)
            app_logger.info("Successfully retrieved flight results")
            app_logger.debug(f"Flight search result: {json.dumps(result, indent=2)}")
            return result
        except Exception as e:
            app_logger.error(f"Error in flight search: {str(e)}")
            app_logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        app_logger.error(f"Unexpected error in search endpoint: {str(e)}")
        app_logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
