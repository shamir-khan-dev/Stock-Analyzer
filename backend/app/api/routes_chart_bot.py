from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from ..vision.chart_vision import process_chart_image
from ..vision.trade_bot import generate_bot_response

router = APIRouter()

class ChartUploadRequest(BaseModel):
    image: str  # Base64 data URL or raw string
    ticker: Optional[str] = None

class BotChatRequest(BaseModel):
    message: str
    ticker: Optional[str] = None
    chart_context: Optional[Dict[str, Any]] = None

@router.post("/vision/analyze-chart")
async def analyze_chart_endpoint(req: ChartUploadRequest):
    """
    Accepts a pasted chart screenshot in base64, executes computer vision
    pattern detection and produces buy/sell verdict and findings.
    """
    if not req.image or len(req.image) < 50:
        raise HTTPException(status_code=400, detail="Invalid image payload received.")
        
    result = process_chart_image(req.image)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
        
    return result

@router.post("/bot/chat")
@router.post("/vision/chat")
async def bot_chat_endpoint(req: BotChatRequest):
    """
    Interactive TradeBot conversational endpoint.
    Answers technical questions, analyzes tickers, and interprets pasted chart context.
    """
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
        
    response = generate_bot_response(
        user_message=req.message,
        current_ticker=req.ticker,
        chart_context=req.chart_context
    )
    return response
