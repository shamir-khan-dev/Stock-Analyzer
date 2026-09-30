import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .config import FRONTEND_DIR
from .api.routes_analysis import router as analysis_router
from .api.routes_chart_bot import router as chart_bot_router
from .api.routes_backtest import router as backtest_router
from .api.routes_market import router as market_router
from .api.routes_paper import router as paper_router
from .api.routes_signals import router as signals_router

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("AlphaPulse")

app = FastAPI(
    title="AlphaPulse - Institutional Stock & Crypto Analyzer",
    description="Quantitative trading analysis, confluence scoring, ATR risk management, and chart vision bot.",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes under /api
app.include_router(analysis_router, prefix="/api", tags=["Analysis"])
app.include_router(chart_bot_router, prefix="/api", tags=["Vision & Bot"])
app.include_router(backtest_router, prefix="/api", tags=["Backtesting"])
app.include_router(market_router, prefix="/api", tags=["Market"])
app.include_router(paper_router, prefix="/api", tags=["Paper Trading"])
app.include_router(signals_router, prefix="/api", tags=["Signal Tracker"])

# Mount frontend static directory if exists
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.get("/")
async def serve_index():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "AlphaPulse API is running. Open frontend/index.html to view the terminal."}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "AlphaPulse Quant Engine"}
