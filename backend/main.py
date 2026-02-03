from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import uuid
from datetime import datetime
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Trico Rosmarinus API", version="1.0.0")

# Environment variables
WORLDFILIA_API_KEY = os.getenv("WORLDFILIA_API_KEY", "cDLJTb14RzaP7SzsLfdP7Q")
WORLDFILIA_SOURCE_ID = os.getenv("WORLDFILIA_SOURCE_ID", "57308485b8777")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

class OrderRequest(BaseModel):
    name: str
    phone: str
    address: str
    aff_sub1: str = None
    aff_sub2: str = None

class OrderResponse(BaseModel):
    success: bool
    order_id: str = None
    message: str = None
    error: str = None

@app.get("/")
async def root():
    return {
        "status": "ok", 
        "service": "Trico Rosmarinus API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/order", response_model=OrderResponse)
async def create_order(order: OrderRequest):
    """
    Create order and send to Worldfilia API
    """
    try:
        logger.info(f"Received order request: {order.name}")
        
        # Worldfilia API endpoint
        worldfilia_url = "https://network.worldfilia.net/manager/inventory/buy/ntm_tricorosmarinus_1x19.json"
        
        # Prepare payload for Worldfilia
        payload = {
            "source_id": WORLDFILIA_SOURCE_ID,
            "aff_sub1": order.aff_sub1 or str(uuid.uuid4()),
            "aff_sub2": order.aff_sub2 or "tricosolutions",
            "name": order.name.strip(),
            "phone": order.phone.strip(),
            "address": order.address.strip()
        }
        
        logger.info(f"Sending to Worldfilia: {payload}")
        logger.info(f"Environment: {ENVIRONMENT}")
        
        # Make API call to Worldfilia
        response = requests.post(
            f"{worldfilia_url}?api_key={WORLDFILIA_API_KEY}",
            json=payload,
            timeout=30,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "TricoRosmarinus-API/1.0"
            }
        )
        
        logger.info(f"Worldfilia response status: {response.status_code}")
        
        if response.status_code == 200:
            logger.info("Order successfully sent to Worldfilia")
            return OrderResponse(
                success=True,
                order_id=payload["aff_sub1"],
                message="Order processed successfully"
            )
        else:
            logger.error(f"Worldfilia API error: {response.status_code} - {response.text}")
            return OrderResponse(
                success=False,
                error=f"API Error: {response.status_code}",
                message="Order processing failed"
            )
            
    except requests.exceptions.Timeout:
        logger.error("Worldfilia API timeout")
        return OrderResponse(
            success=False,
            error="API timeout",
            message="Order processing timeout - please try again"
        )
    except requests.exceptions.ConnectionError:
        logger.error("Worldfilia API connection error")
        return OrderResponse(
            success=False,
            error="Connection error",
            message="Service temporarily unavailable"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return OrderResponse(
            success=False,
            error=str(e),
            message="Order processing failed"
        )

@app.get("/api/stats")
async def get_stats():
    """
    Simple stats endpoint for monitoring
    """
    return {
        "service": "Trico Rosmarinus API",
        "environment": ENVIRONMENT,
        "uptime": "Running",
        "version": "1.0.0",
        "endpoints": [
            "/api/order",
            "/health",
            "/api/stats"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
