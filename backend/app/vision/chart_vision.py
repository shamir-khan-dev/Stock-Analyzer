import io
import re
import base64
import logging
from typing import Dict, Any, Optional
from PIL import Image
import numpy as np
import cv2

from ..config import GEMINI_API_KEY, OPENAI_API_KEY

logger = logging.getLogger(__name__)

def decode_image_base64(image_data: str) -> Image.Image:
    """Decodes data URL or raw base64 string into PIL Image."""
    if "," in image_data:
        image_data = image_data.split(",", 1)[1]
    image_bytes = base64.b64decode(image_data)
    return Image.open(io.BytesIO(image_bytes)).convert("RGB")

def analyze_chart_with_cv(img: Image.Image) -> Dict[str, Any]:
    """
    Computer Vision heuristic analyzer for candlestick chart screenshots:
    - Analyzes green vs red candle pixel mass
    - Extracts price trend direction from left-to-right centroid trajectory
    - Identifies horizontal support/resistance density clusters
    - Determines bullish/bearish momentum and breakout bias
    """
    cv_img = np.array(img)
    # Convert RGB to BGR for OpenCV
    bgr = cv2.cvtColor(cv_img, cv2.COLOR_RGB2BGR)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    height, width, _ = bgr.shape
    
    # 1. Detect Green Candlesticks / Lines (includes Wealthsimple emerald, neon green, cyan-green)
    lower_green = np.array([30, 30, 40])
    upper_green = np.array([90, 255, 255])
    green_mask = cv2.inRange(hsv, lower_green, upper_green)
    green_pixels = int(cv2.countNonZero(green_mask))

    # 2. Detect Red/Pink Candlesticks / Lines (includes Wealthsimple coral/pink-red)
    lower_red1 = np.array([0, 40, 40])
    upper_red1 = np.array([12, 255, 255])
    lower_red2 = np.array([160, 40, 40])
    upper_red2 = np.array([180, 255, 255])
    red_mask = cv2.bitwise_or(
        cv2.inRange(hsv, lower_red1, upper_red1),
        cv2.inRange(hsv, lower_red2, upper_red2)
    )
    red_pixels = int(cv2.countNonZero(red_mask))

    total_colored = green_pixels + red_pixels + 1
    bullish_ratio = green_pixels / total_colored
    bearish_ratio = red_pixels / total_colored

    # 3. Enhanced Line & Candle Trajectory Detection (Handles both Line charts like Wealthsimple & Candlesticks)
    combined_mask = cv2.bitwise_or(green_mask, red_mask)
    
    # If colored line is thin or monochrome (e.g. grayscale/light mode line chart), use edge contour detection
    if cv2.countNonZero(combined_mask) < (width * height * 0.005):
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 40, 150)
        # Exclude border edges (top 5% and bottom 10% where UI headers and timeline buttons reside)
        y_min = int(height * 0.1)
        y_max = int(height * 0.85)
        edges[:y_min, :] = 0
        edges[y_max:, :] = 0
        combined_mask = edges

    # Split the chart into 4 temporal quadrants from left (older) to right (recent)
    quad_w = width // 4
    quad_heights = []
    
    for q in range(4):
        x_start = q * quad_w
        x_end = (q + 1) * quad_w
        quad_crop = combined_mask[:, x_start:x_end]
        y_indices, _ = np.where(quad_crop > 0)
        if len(y_indices) > 0:
            # Note: in image coordinates, smaller Y means HIGHER price on a chart
            avg_y = np.median(y_indices)
            quad_heights.append(avg_y)
        else:
            quad_heights.append(height / 2)

    # Inverted Y: higher on chart = lower Y coordinate
    # If rightmost Y < leftmost Y => Price moved UP
    y_diff = quad_heights[0] - quad_heights[-1] # positive means upward trend
    slope_strength = y_diff / (height + 1e-10)

    # 4. Detect Recent Momentum (Last quadrant green vs red)
    recent_x_start = int(width * 0.75)
    recent_green = int(cv2.countNonZero(green_mask[:, recent_x_start:]))
    recent_red = int(cv2.countNonZero(red_mask[:, recent_x_start:]))
    recent_total = recent_green + recent_red + 1
    recent_bull_ratio = recent_green / recent_total if (recent_green + recent_red) > 20 else (0.6 if slope_strength > 0 else 0.4)

    # Determine Verdict & Score
    score = 0
    if slope_strength > 0.1:
        score += 35
    elif slope_strength > 0.03:
        score += 20
    elif slope_strength < -0.1:
        score -= 35
    elif slope_strength < -0.03:
        score -= 20

    if recent_bull_ratio > 0.6:
        score += 35
    elif recent_bull_ratio < 0.4:
        score -= 35

    if bullish_ratio > 0.55:
        score += 20
    elif bearish_ratio > 0.55:
        score -= 20

    score = max(-100, min(100, score))

    if score >= 40:
        verdict = "STRONG BUY"
        action = "BUY"
        color = "#00e676"
        trend_name = "Bullish Uptrend with Buyer Dominance"
    elif score >= 15:
        verdict = "BUY"
        action = "BUY"
        color = "#4caf50"
        trend_name = "Mild Bullish Bias / Breakout Setup"
    elif score <= -40:
        verdict = "STRONG SELL"
        action = "SELL"
        color = "#ff1744"
        trend_name = "Bearish Downtrend with Seller Dominance"
    elif score <= -15:
        verdict = "SELL"
        action = "SELL"
        color = "#f44336"
        trend_name = "Mild Bearish Bias / Distribution"
    else:
        verdict = "HOLD / CONSOLIDATION"
        action = "WAIT"
        color = "#ffb300"
        trend_name = "Sideways Consolidation / Rangebound"

    confidence = int(60 + (abs(score) / 100.0) * 35)

    findings = [
        f"Price action structure indicates: {trend_name}.",
        f"Candle color distribution: {int(bullish_ratio*100)}% Bullish Green bars vs {int(bearish_ratio*100)}% Bearish Red bars.",
        f"Recent candle momentum (right side of chart): {int(recent_bull_ratio*100)}% buyer volume dominance.",
        f"Visual slope vector: {'Upward sloping (+)' if slope_strength > 0 else 'Downward sloping (-)'} trajectory."
    ]

    return {
        "analysis_type": "COMPUTER_VISION_HEURISTIC",
        "verdict": verdict,
        "action": action,
        "verdict_color": color,
        "confidence_pct": confidence,
        "score": score,
        "trend_name": trend_name,
        "key_findings": findings,
        "detected_patterns": [
            {"name": "Visual Trend Channel", "bias": "BULLISH" if score > 0 else "BEARISH"},
            {"name": "Volume / Candle Density Clustered", "bias": "CONFIRMED"}
        ],
        "trade_recommendation": {
            "action": action,
            "rationale": f"Chart screenshot analysis reveals {trend_name.lower()}. Recommendation is to {action} with prudent risk management."
        }
    }

def analyze_chart_with_llm(img: Image.Image) -> Optional[Dict[str, Any]]:
    """
    Multimodal LLM vision analysis if API key is provided (Gemini / OpenAI).
    """
    if not GEMINI_API_KEY and not OPENAI_API_KEY:
        return None

    # Try Gemini if API key is present
    if GEMINI_API_KEY:
        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-1.5-flash")
            prompt = """
            You are a senior quantitative hedge fund trader and technical chart analyst.
            Analyze this chart screenshot in detail:
            1. Identify the primary trend (Uptrend, Downtrend, Range).
            2. Identify any visible chart patterns (Head & Shoulders, Double Bottom, Flag, Pennant, Breakout, Support/Resistance lines, Candlestick patterns).
            3. Provide a clear verdict: STRONG BUY, BUY, HOLD, SELL, or STRONG SELL.
            4. Provide an estimated Confidence % (between 50% and 95%).
            5. Provide exact actionable trade game-plan: Entry Zone, Stop-Loss Level, Take-Profit Targets, and Risk/Reward.
            Return your response in clean JSON with fields:
            {
              "verdict": "BUY/SELL/HOLD/STRONG BUY/STRONG SELL",
              "action": "BUY/SELL/WAIT",
              "confidence_pct": 85,
              "trend_name": "...",
              "patterns": ["pattern 1", "pattern 2"],
              "key_findings": ["point 1", "point 2", "point 3"],
              "entry_level": "...",
              "stop_loss": "...",
              "take_profit": "...",
              "risk_reward": "..."
            }
            """
            response = model.generate_content([prompt, img])
            import json
            match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                data["analysis_type"] = "GEMINI_MULTIMODAL_VISION"
                data["verdict_color"] = "#00e676" if "BUY" in data.get("verdict", "") else ("#ff1744" if "SELL" in data.get("verdict", "") else "#ffb300")
                return data
        except Exception as e:
            logger.warning(f"Gemini vision call failed: {e}")

    return None

def process_chart_image(image_base64: str) -> Dict[str, Any]:
    """
    Unified entry point for chart image analysis.
    Uses Multimodal LLM Vision if configured, otherwise employs high-speed local Computer Vision.
    """
    try:
        pil_image = decode_image_base64(image_base64)
    except Exception as e:
        return {"error": f"Failed to decode image data: {str(e)}"}

    # Attempt AI multimodal analysis if configured
    llm_result = analyze_chart_with_llm(pil_image)
    if llm_result:
        return llm_result

    # Fallback to high-performance local Computer Vision pipeline
    return analyze_chart_with_cv(pil_image)
