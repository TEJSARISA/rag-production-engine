import hmac
from fastapi import Header, HTTPException
from app.core.config import settings

def verify_api_key(x_api_key: str = Header(...)):
    if not hmac.compare_digest(x_api_key, settings.API_KEY):
        raise HTTPException(status_code=403, detail="Invalid API key")
    return True
