from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import requests
import uuid
from datetime import datetime
import logging
import os
import hashlib
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Trico Rosmarinus API", version="1.0.0")

# Environment variables (from Docker environment)
WORLDFILIA_API_KEY = os.getenv("WORLDFILIA_API_KEY", "cDLJTb14RzaP7SzsLfdP7Q")
WORLDFILIA_SOURCE_ID = os.getenv("WORLDFILIA_SOURCE_ID", "57308485b8777")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Facebook Conversion API
FB_PIXEL_ID = os.getenv("FB_PIXEL_ID", "2095934291260128")
FB_ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN", "EAAWzrJVNYx0BQr2wVNTXZB7E8YW0Sj2o9opMDcePaBAPkVLncJ55iyZC3Se74me2OGo3DhpGMfUCHHaYzeNefeHTsbsRYcJZBAzbVI6lQUhq9gZC3MuQkpP31NQyAJzKo6vp4tTqhDld9JuVWjsGgIcQcF0CLUZB1p1NquUZBnZCI0Pcl2l5CnDz9ccZAHoDcwZDZD")

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
        logger.info(f"Worldfilia response headers: {response.headers}")
        logger.info(f"Worldfilia response text: {response.text}")
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                logger.info(f"Worldfilia response JSON: {response_data}")
                logger.info("Order successfully sent to Worldfilia")
                return OrderResponse(
                    success=True,
                    order_id=payload["aff_sub1"],
                    message="Order processed successfully"
                )
            except Exception as json_error:
                logger.error(f"JSON decode error: {json_error}")
                logger.error(f"Response content: {response.text[:500]}")  # First 500 chars
                return OrderResponse(
                    success=False,
                    error="Worldfilia response parsing error",
                    message="Order processing failed"
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
            "/api/stats",
            "/api/track/view",
            "/api/track/purchase"
        ]
    }

# Facebook Conversion API Helper
def send_facebook_event(event_name: str, event_data: dict, user_data: dict, request: Request):
    """
    Send event to Facebook Conversion API
    """
    try:
        # Hash user data for privacy (Facebook requirement)
        def hash_data(data):
            if data:
                return hashlib.sha256(data.lower().strip().encode()).hexdigest()
            return None
        
        # Prepare user data with hashing
        hashed_user_data = {}
        
        if user_data.get("email"):
            hashed_user_data["em"] = [hash_data(user_data["email"])]
        if user_data.get("phone"):
            # Remove +39 and spaces, then hash
            phone = user_data["phone"].replace("+39", "").replace(" ", "").replace("-", "")
            hashed_user_data["ph"] = [hash_data(phone)]
        if user_data.get("first_name"):
            hashed_user_data["fn"] = [hash_data(user_data["first_name"])]
        if user_data.get("last_name"):
            hashed_user_data["ln"] = [hash_data(user_data["last_name"])]
        if user_data.get("city"):
            hashed_user_data["ct"] = [hash_data(user_data["city"])]
        if user_data.get("country"):
            hashed_user_data["country"] = [hash_data(user_data["country"])]
        
        # Add client info - use real IP from proxy headers (nginx + Traefik)
        real_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or request.headers.get("X-Real-IP", "") or request.client.host
        hashed_user_data["client_ip_address"] = real_ip
        hashed_user_data["client_user_agent"] = user_data.get("user_agent") or request.headers.get("user-agent", "")
        
        # External ID for deduplication
        if user_data.get("external_id"):
            hashed_user_data["external_id"] = [hash_data(user_data["external_id"])]
        
        # FBC and FBP cookies if available
        if user_data.get("fbc"):
            hashed_user_data["fbc"] = user_data["fbc"]
        if user_data.get("fbp"):
            hashed_user_data["fbp"] = user_data["fbp"]
        
        # Prepare event payload
        event_payload = {
            "event_name": event_name,
            "event_time": int(time.time()),
            "event_source_url": user_data.get("source_url", ""),
            "action_source": "website",
            "user_data": hashed_user_data
        }
        
        # Add custom data if provided
        if event_data:
            event_payload["custom_data"] = event_data
        
        # Add event_id for deduplication
        event_payload["event_id"] = user_data.get("event_id") or str(uuid.uuid4())
        
        # Facebook API endpoint
        fb_url = f"https://graph.facebook.com/v18.0/{FB_PIXEL_ID}/events"
        
        # Prepare request payload
        payload = {
            "data": [event_payload],
            "access_token": FB_ACCESS_TOKEN
        }
        
        # No test event code - production mode
        
        logger.info(f"Sending Facebook event: {event_name}")
        logger.info(f"Facebook payload: {payload}")
        
        # Send to Facebook
        response = requests.post(fb_url, json=payload, timeout=10)
        
        logger.info(f"Facebook response status: {response.status_code}")
        logger.info(f"Facebook response: {response.text}")
        
        if response.status_code == 200:
            return {"success": True, "response": response.json()}
        else:
            return {"success": False, "error": response.text}
            
    except Exception as e:
        logger.error(f"Facebook API error: {str(e)}")
        return {"success": False, "error": str(e)}

# Track Request Models
from typing import Optional

class TrackViewRequest(BaseModel):
    source_url: Optional[str] = None
    user_agent: Optional[str] = None
    fbp: Optional[str] = None  # Facebook browser pixel cookie
    fbc: Optional[str] = None  # Facebook click ID cookie
    external_id: Optional[str] = None
    event_id: Optional[str] = None

class TrackPurchaseRequest(BaseModel):
    source_url: Optional[str] = None
    user_agent: Optional[str] = None
    fbp: Optional[str] = None
    fbc: Optional[str] = None
    external_id: Optional[str] = None
    event_id: Optional[str] = None
    value: float = 8.00
    currency: str = "EUR"
    content_name: str = "Trico Rosmarinus 75ml"
    content_ids: Optional[list] = None
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

@app.post("/api/track/view")
async def track_view_content(track_data: TrackViewRequest, request: Request):
    """
    Track ViewContent event for Facebook Conversion API
    """
    logger.info("Tracking ViewContent event")
    
    user_data = {
        "source_url": track_data.source_url or str(request.url),
        "user_agent": track_data.user_agent or request.headers.get("user-agent", ""),
        "client_ip": request.client.host,
        "fbp": track_data.fbp,
        "fbc": track_data.fbc,
        "external_id": track_data.external_id,
        "event_id": track_data.event_id,
        "country": "it"
    }
    
    event_data = {
        "content_name": "Trico Rosmarinus Landing Page",
        "content_category": "Hair Care",
        "content_type": "product",
        "content_ids": ["trico_rosmarinus_75ml"]
    }
    
    result = send_facebook_event("ViewContent", event_data, user_data, request)
    
    return {
        "success": result.get("success", False),
        "event": "ViewContent",
        "message": "Event tracked" if result.get("success") else "Event tracking failed",
        "details": result
    }

@app.post("/api/track/purchase")
async def track_purchase(track_data: TrackPurchaseRequest, request: Request):
    """
    Track Purchase event for Facebook Conversion API
    """
    logger.info("Tracking Purchase event")
    
    # Parse name if provided
    first_name = track_data.first_name
    last_name = track_data.last_name
    
    user_data = {
        "source_url": track_data.source_url or str(request.url),
        "user_agent": track_data.user_agent or request.headers.get("user-agent", ""),
        "client_ip": request.client.host,
        "fbp": track_data.fbp,
        "fbc": track_data.fbc,
        "external_id": track_data.external_id,
        "event_id": track_data.event_id,
        "phone": track_data.phone,
        "first_name": first_name,
        "last_name": last_name,
        "country": "it"
    }
    
    event_data = {
        "content_name": track_data.content_name,
        "content_type": "product",
        "content_ids": track_data.content_ids or ["trico_rosmarinus_75ml"],
        "value": track_data.value,
        "currency": track_data.currency,
        "num_items": 1
    }
    
    result = send_facebook_event("Purchase", event_data, user_data, request)
    
    return {
        "success": result.get("success", False),
        "event": "Purchase",
        "message": "Event tracked" if result.get("success") else "Event tracking failed",
        "details": result
    }

# Generic event tracking model
class TrackEventRequest(BaseModel):
    event_name: str
    source_url: Optional[str] = None
    user_agent: Optional[str] = None
    fbp: Optional[str] = None
    fbc: Optional[str] = None
    external_id: Optional[str] = None
    event_id: Optional[str] = None

@app.post("/api/track/initiate-checkout")
async def track_initiate_checkout(track_data: TrackViewRequest, request: Request):
    """
    Track InitiateCheckout event - when user starts typing in form
    """
    logger.info("Tracking InitiateCheckout event")
    
    user_data = {
        "source_url": track_data.source_url or str(request.url),
        "user_agent": track_data.user_agent or request.headers.get("user-agent", ""),
        "client_ip": request.client.host,
        "fbp": track_data.fbp,
        "fbc": track_data.fbc,
        "external_id": track_data.external_id,
        "event_id": track_data.event_id,
        "country": "it"
    }
    
    event_data = {
        "content_name": "Trico Rosmarinus 75ml",
        "content_category": "Hair Care",
        "content_type": "product",
        "content_ids": ["trico_rosmarinus_75ml"]
    }
    
    result = send_facebook_event("InitiateCheckout", event_data, user_data, request)
    
    return {
        "success": result.get("success", False),
        "event": "InitiateCheckout",
        "message": "Event tracked" if result.get("success") else "Event tracking failed",
        "details": result
    }

@app.post("/api/track/add-to-cart")
async def track_add_to_cart(track_data: TrackViewRequest, request: Request):
    """
    Track AddToCart event - when user clicks sticky CTA
    """
    logger.info("Tracking AddToCart event")
    
    user_data = {
        "source_url": track_data.source_url or str(request.url),
        "user_agent": track_data.user_agent or request.headers.get("user-agent", ""),
        "client_ip": request.client.host,
        "fbp": track_data.fbp,
        "fbc": track_data.fbc,
        "external_id": track_data.external_id,
        "event_id": track_data.event_id,
        "country": "it"
    }
    
    event_data = {
        "content_name": "Trico Rosmarinus 75ml",
        "content_type": "product",
        "content_ids": ["trico_rosmarinus_75ml"]
    }
    
    result = send_facebook_event("AddToCart", event_data, user_data, request)
    
    return {
        "success": result.get("success", False),
        "event": "AddToCart",
        "message": "Event tracked" if result.get("success") else "Event tracking failed",
        "details": result
    }

@app.post("/api/track/scroll")
async def track_scroll(track_data: TrackViewRequest, request: Request):
    """
    Track custom Scroll/Engaged event - when user scrolls for first time
    """
    logger.info("Tracking Scroll/Engaged event")
    
    user_data = {
        "source_url": track_data.source_url or str(request.url),
        "user_agent": track_data.user_agent or request.headers.get("user-agent", ""),
        "client_ip": request.client.host,
        "fbp": track_data.fbp,
        "fbc": track_data.fbc,
        "external_id": track_data.external_id,
        "event_id": track_data.event_id,
        "country": "it"
    }
    
    event_data = {
        "content_name": "Trico Rosmarinus Landing Page",
        "content_category": "Hair Care"
    }
    
    # Using custom event name for scroll engagement
    result = send_facebook_event("PageEngagement", event_data, user_data, request)
    
    return {
        "success": result.get("success", False),
        "event": "PageEngagement",
        "message": "Event tracked" if result.get("success") else "Event tracking failed",
        "details": result
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
