import re
import json
import logging
import urllib.request
from typing import Dict, Any, List, Optional, Tuple
from ..core.data_fetcher import fetch_history_data, fetch_live_quote
from ..core.quant_engine import analyze_ticker_confluence
from ..config import GEMINI_API_KEY, GEMINI_MODEL, OPENAI_API_KEY

logger = logging.getLogger(__name__)

# Warm, conversational, plain-English trading mentor persona
TRADER_SYSTEM_PROMPT = """
You are TradeBot — a warm, friendly, clear AI trading mentor. You talk just like a knowledgeable, supportive friend having a natural conversation.

YOUR CORE PRINCIPLES:
1. TALK LIKE A HUMAN, NOT A ROBOT. Speak in everyday plain English. Never dump cold raw statistics, complex formula tables, or cryptic quant codes.
2. ALWAYS TRANSLATE JARGON IN PARENTHESES:
   - If you say "Bearish", immediately add: "(meaning the price is trending down / sellers are taking control)".
   - If you say "Bullish", immediately add: "(meaning the price is trending up / buyers are pushing it higher)".
   - If you mention "Stop-Loss", add: "(your safety exit price so you don't lose more money)".
   - If you mention "Take Profit", add: "(the target price to sell and lock in your gains)".
3. DIRECT ANSWERS TO USER'S PERSONAL SITUATION:
   - If the user says they bought shares (e.g. "I bought 18 shares at $1.33, should I sell?"):
     a) Immediately calculate their dollar and percentage profit or loss.
     b) Give a clear, bold recommendation right away: "**My Advice: SELL NOW**" or "**My Advice: HOLD**".
     c) Explain WHY in 2-3 friendly, simple sentences.
     d) Give them an exact step-by-step action plan right now.
4. If they ask a "yes or no" question, start with YES or NO clearly.
5. Keep your tone encouraging, clear, and easy to understand for beginners.
"""

POPULAR_TICKERS = {
    "NVDA", "TSLA", "AAPL", "MSFT", "AMZN", "GOOGL", "GOOG", "META", "AMD", "PLTR",
    "SPY", "QQQ", "BTC", "ETH", "COIN", "MARA", "NFLX", "AVGO", "SMCI", "BABA",
    "ARM", "INTC", "DIS", "BA", "SOFI", "HOOD", "RIVN", "NIO", "DKNG", "UBER",
    "CRWD", "PANW", "SNOW", "MU", "QCOM", "TXN", "PYPL", "SQ", "GME", "AMC",
    "BTC-USD", "ETH-USD", "SOL-USD", "AHMA", "MSTR", "RKLB", "IONQ", "SOUN",
    "BBAI", "LUNR", "JOBY", "ACHR", "RDDT", "APLD"
}


def check_terminology_or_concept(message: str) -> Optional[str]:
    """
    Detects if the user is asking about confusing trading terminology
    and returns a warm, simple, plain-English explanation.
    """
    msg = message.lower().strip()

    # 1. Bearish / Berish
    if re.search(r'\b(what\s*(is|does)\s*)?(bearish|berish)(\s*mean)?\b', msg) and not re.search(r'\b(is\s+\w+\s+(bearish|berish))\b', msg):
        return (
            "🐻 **What Does \"Bearish\" Mean?**\n\n"
            "In plain English: **Bearish means the price is expected to GO DOWN (drop / fall).**\n\n"
            "**Easy trick to remember it:**\n"
            "Think of a bear attacking by swiping its claws **DOWNWARD** 🐾⬇️.\n\n"
            "**What you should do when a stock is Bearish:**\n"
            "• **If you own shares**: It's a clear warning. You should consider **selling now or setting a strict Stop-Loss** to prevent losing more cash.\n"
            "• **If you want to buy**: Do **NOT** buy yet! Wait until the price stops falling and finds a bottom."
        )

    # 2. Bullish
    if re.search(r'\b(what\s*(is|does)\s*)?bullish(\s*mean)?\b', msg) and not re.search(r'\b(is\s+\w+\s+bullish)\b', msg):
        return (
            "🐂 **What Does \"Bullish\" Mean?**\n\n"
            "In plain English: **Bullish means the price is expected to GO UP (rise / rally).**\n\n"
            "**Easy trick to remember it:**\n"
            "Think of a bull charging by thrusting its horns **UPWARD** 🐂⬆️.\n\n"
            "**What you should do when a stock is Bullish:**\n"
            "• Buyers are eager and momentum is positive.\n"
            "• It is generally a good time to **buy or hold** your position to ride the wave up."
        )

    # 3. Stop-Loss
    if re.search(r'\b(what\s*(is|does)\s*)?(stop[\s\-]?loss|cut\s*loss)(\s*mean)?\b', msg):
        return (
            "🛑 **What is a \"Stop-Loss\"?**\n\n"
            "Think of a Stop-Loss as your **emergency seatbelt / safety net**.\n\n"
            "It is a pre-set price where you agree to sell your shares if the trade goes wrong, so a small loss doesn't turn into a huge disaster.\n\n"
            "**Example:** If you buy a stock at $100 and set your Stop-Loss at $95:\n"
            "If the price drops to $95, you automatically sell. You only lose $5 instead of watching it drop to $50!"
        )

    # 4. Take-Profit
    if re.search(r'\b(what\s*(is|does)\s*)?(take[\s\-]?profit|profit\s*target)(\s*mean)?\b', msg):
        return (
            "🎯 **What is \"Take Profit\"?**\n\n"
            "Take Profit is your **money goal price**.\n\n"
            "When the stock goes up and hits this target, you sell to **lock in your real cash profit** before the price drops back down.\n\n"
            "We show two levels:\n"
            "• **Take Profit 1**: Sell 50% of your shares here to bank guaranteed cash.\n"
            "• **Take Profit 2**: Hold the rest for a bigger 'runner' gain if the rally keeps going."
        )

    # 5. Confluence
    if re.search(r'\b(what\s*(is|does)\s*)?confluence(\s*score)?(\s*mean)?\b', msg):
        return (
            "🧠 **What is \"Confluence\"?**\n\n"
            "In plain English: Confluence is an **agreement score** between multiple independent indicators.\n\n"
            "Instead of trusting just one signal, our system checks 5 different things (Trend, Momentum, Volume, Volatility, and Sentiment).\n\n"
            "• **Positive score (+50 to +100)**: All indicators agree the stock is heading UP (Bullish).\n"
            "• **Negative score (-50 to -100)**: All indicators agree the stock is heading DOWN (Bearish)."
        )

    # 6. General confusing terminology / help
    if any(phrase in msg for phrase in ["confusing", "confisyig", "terminology", "plain english", "explain terms", "cheat sheet", "what do the words mean", "explain words"]):
        return (
            "💡 **Here is Your Quick Plain-English Trading Cheat Sheet:**\n\n"
            "• 🐻 **Bearish**: Price is falling (Bear claws swipe DOWN ⬇️). Be cautious or sell.\n"
            "• 🐂 **Bullish**: Price is rising (Bull horns thrust UP ⬆️). Good time to buy or hold.\n"
            "• 🎯 **Entry Price**: The recommended price to buy the stock.\n"
            "• 🛑 **Stop-Loss**: Your safety seatbelt — sell here to avoid losing more money.\n"
            "• 💰 **Take Profit**: Your goal price — sell here to pocket your profits.\n"
            "• 🧠 **Confluence Score**: How many indicators agree (+ is bullish, - is bearish).\n"
            "• ⚡ **RSI**: Speedometer — below 30 is a cheap bargain, above 70 is overheated.\n\n"
            "Feel free to ask me about any stock or question in plain English!"
        )

    return None


def extract_ticker_from_message(message: str) -> Optional[str]:
    """Finds referenced ticker symbols in message accurately."""
    # 1. Check for explicit cashtag like $NVDA, $TSLA
    cashtags = re.findall(r'\$([A-Za-z]{1,5})\b', message)
    if cashtags:
        return cashtags[0].upper()

    words = re.findall(r'\b[A-Za-z0-9\-]{2,7}\b', message.upper())

    # 2. Check for popular known tickers first
    for w in words:
        if w in POPULAR_TICKERS:
            return w

    return None


def extract_user_context(message: str) -> Dict[str, Any]:
    """
    Parse the user's message for personal position details.
    Extracts: bought price, number of shares, and intent (sell/hold/buy).
    """
    ctx: Dict[str, Any] = {}

    # Detect share count: "18 shares", "bought 18"
    share_match = re.search(r'\b(\d+)\s*shares?\b', message, re.IGNORECASE)
    if share_match:
        ctx["shares"] = int(share_match.group(1))

    # Detect price paid: "at $1.32", "at 1.32", "@1.32", "bought at $222", "of 1.33"
    price_match = re.search(
        r'(?:^|(?:bought|purchased|entry|paid)\s+)?(?:at|@|for|of)\s*\$?\s*([\d]+\.[\d]+|[\d]{1,5})\b',
        message, re.IGNORECASE
    )
    if price_match:
        parsed_price = float(price_match.group(1))
        already_captured_shares = ctx.get("shares")
        if already_captured_shares is None or parsed_price != already_captured_shares:
            ctx["purchase_price"] = parsed_price

    # Detect if they're asking about an existing position
    holding_patterns = [
        r'i (bought|own|have|hold|purchased)',
        r'should i (sell|keep|hold|exit)',
        r'when (should|to) (i )?(sell|exit)'
    ]
    ctx["is_holder"] = any(re.search(p, message, re.IGNORECASE) for p in holding_patterns)

    # Detect yes/no or simple question
    simple_patterns = [
        r'yes or no', r'simple (answer)?', r'just (tell|say)',
        r'quickly', r'short answer', r'briefly'
    ]
    ctx["wants_short"] = any(re.search(p, message, re.IGNORECASE) for p in simple_patterns)

    # Detect investment horizon requested
    ctx["wants_day_trade"] = bool(re.search(r'\b(day\s*trade|scalp|1[\s\-]?2\s*days?|today|tomorrow)\b', message, re.IGNORECASE))
    ctx["wants_swing"] = bool(re.search(r'\b(swing|short\s*term|weeks?)\b', message, re.IGNORECASE))
    ctx["wants_long_term"] = bool(re.search(r'\b(long\s*term|months?|years?|invest(ing|ment)?|portfolio|core\s*hold)\b', message, re.IGNORECASE))

    return ctx


def query_gemini_api(prompt: str, image_b64: Optional[str] = None, mime_type: str = "image/png") -> Optional[str]:
    """Direct REST call to Gemini API."""
    if not GEMINI_API_KEY:
        return None

    models_to_try = [
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
    ]
    seen: set = set()
    models = [m for m in models_to_try if not (m in seen or seen.add(m))][:2]

    for model_name in models:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"

            parts: List[Dict[str, Any]] = []
            if image_b64:
                parts.append({"inlineData": {"mimeType": mime_type, "data": image_b64}})
            parts.append({"text": prompt})

            payload = {
                "contents": [{"parts": parts}],
                "generationConfig": {"temperature": 0.4, "maxOutputTokens": 450}
            }

            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=3.5) as response:
                result = json.loads(response.read().decode("utf-8"))
                candidates = result.get("candidates", [])
                if candidates:
                    text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    if text:
                        return text
        except Exception as e:
            logger.warning(f"Gemini call with model {model_name} failed: {e}")
            continue

    return None


def generate_smart_fallback(
    user_message: str,
    ticker: str,
    verdict: str,
    conf: int,
    entry: float,
    sl: float,
    tp1: float,
    tp2: float,
    reasons: List[str],
    user_ctx: Dict[str, Any],
    multi_horizon: Optional[Dict[str, Any]] = None
) -> str:
    """
    Warm, human, plain-English fallback that answers the user's specific
    question directly instead of dumping an unreadable quant template.
    """
    purchase_price = user_ctx.get("purchase_price")
    shares = user_ctx.get("shares")
    is_holder = user_ctx.get("is_holder", False)
    wants_short = user_ctx.get("wants_short", False)

    # 1. Check if user asked about a specific timeframe/horizon
    if user_ctx.get("wants_day_trade") and multi_horizon and "day_trade" in multi_horizon:
        dt = multi_horizon["day_trade"]
        return (
            f"⚡ **1 – 2 Days Outlook (Day Trade & Scalp) for {ticker}:**\n\n"
            f"• **Signal**: **{dt['verdict']}** ({dt['badge']})\n"
            f"• **Target Entry**: ${dt['entry']:.2f}\n"
            f"• **Quick Profit Target**: ${dt['target']:.2f}\n"
            f"• **Tight Stop-Loss**: ${dt['stop_loss']:.2f}\n\n"
            f"**Action Plan:**\n{dt['summary']}\n\n"
            f"*Strategy Model: {dt['model_name']}*"
        )

    if user_ctx.get("wants_long_term") and multi_horizon and "long_term" in multi_horizon:
        lt = multi_horizon["long_term"]
        return (
            f"🏛️ **Months – Years Outlook (Long-Term Wealth) for {ticker}:**\n\n"
            f"• **Institutional Verdict**: **{lt['verdict']}** ({lt['badge']})\n"
            f"• **DCA Accumulation Range**: {lt['accumulation_zone']}\n"
            f"• **12-Month Bull Target**: ${lt['twelve_month_target']:.2f}\n"
            f"• **Invalidation Floor**: ${lt['invalidation_floor']:.2f}\n"
            f"• **200-Day SMA Trend**: {lt['dist_200_sma_pct']:+.1f}% vs 200-day average\n\n"
            f"**Long-Term Strategy:**\n{lt['summary']}\n\n"
            f"*Wall Street Institutional Model: {lt['model_name']} (AQR & FINRA due diligence)*"
        )

    if user_ctx.get("wants_swing") and multi_horizon and "swing_trade" in multi_horizon:
        sw = multi_horizon["swing_trade"]
        return (
            f"🌊 **Days – Weeks Outlook (Swing Trading) for {ticker}:**\n\n"
            f"• **Signal**: **{sw['verdict']}** ({sw['badge']})\n"
            f"• **Swing Entry**: ${sw['entry']:.2f}\n"
            f"• **Take Profit 1**: ${sw['take_profit_1']:.2f}\n"
            f"• **Take Profit 2 (Runner)**: ${sw['take_profit_2']:.2f}\n"
            f"• **Safety Stop-Loss**: ${sw['stop_loss']:.2f}\n\n"
            f"**Action Plan:**\n{sw['summary']}\n\n"
            f"*Strategy Model: {sw['model_name']} (AQR Trend Following)*"
        )

    is_bullish = verdict in ("BUY", "STRONG BUY", "STRONG_BUY")
    is_bearish = verdict in ("SELL", "STRONG SELL", "STRONG_SELL")

    # If the user owns shares / mentioned purchase price
    if is_holder or purchase_price is not None:
        pnl_lines = []
        if purchase_price and entry:
            pnl_pct = ((entry - purchase_price) / purchase_price) * 100
            dollar_diff = entry - purchase_price
            pnl_lines.append(f"• You bought at **${purchase_price:.2f}** and the stock is currently at **${entry:.2f}**.")
            if shares:
                total_dollar = dollar_diff * shares
                sign = "+" if total_dollar >= 0 else "-"
                pnl_lines.append(f"• On your {shares} shares, you are down {sign}${abs(total_dollar):.2f} ({pnl_pct:+.1f}%).")
            else:
                pnl_lines.append(f"• You are currently {pnl_pct:+.1f}% on this position.")

        pnl_text = "\n".join(pnl_lines)

        if is_bearish:
            holder_cutoff = round(entry * 0.95, 2) if sl >= entry else sl
            return (
                f"👉 **My Advice: SELL NOW.**\n\n"
                f"{pnl_text}\n\n"
                f"**Why?**\n"
                f"The trend is **Bearish** (which means the price is heading downward and likely to fall further). "
                f"Our algorithm has a **{verdict}** signal with {conf}% confidence.\n\n"
                f"Selling now at around **${entry:.2f}** protects your money so you don't take an even bigger loss.\n\n"
                f"**If you decide to hold:** Do not let it drop below **${holder_cutoff:.2f}** (your emergency Stop-Loss cutoff)."
            )
        elif is_bullish:
            return (
                f"👉 **My Advice: HOLD — you are in good shape!**\n\n"
                f"{pnl_text}\n\n"
                f"**Why?**\n"
                f"The trend is **Bullish** (which means buyers are pushing the price higher). "
                f"Our signal is **{verdict}** ({conf}% confidence).\n\n"
                f"**What to do next:**\n"
                f"1. Keep holding for now.\n"
                f"2. Sell half your shares when it reaches **${tp1:.2f}** to lock in profit.\n"
                f"3. Set your safety Stop-Loss at **${sl:.2f}** just in case the market reverses."
            )
        else:
            return (
                f"👉 **My Advice: HOLD and watch closely.**\n\n"
                f"{pnl_text}\n\n"
                f"**Why?**\n"
                f"The stock is moving sideways (Neutral). Neither buyers nor sellers have full control yet.\n\n"
                f"**Safety Rule:** Set a Stop-Loss at **${sl:.2f}**. If it falls below that, sell immediately."
            )

    # General overview question with 3-horizon summary
    direction_desc = "trending DOWN (Bearish — sellers in control)" if is_bearish else (
        "trending UP (Bullish — buyers in control)" if is_bullish else "moving sideways (Neutral)"
    )

    horizon_table = ""
    if multi_horizon:
        dt = multi_horizon.get("day_trade", {})
        sw = multi_horizon.get("swing_trade", {})
        lt = multi_horizon.get("long_term", {})
        horizon_table = (
            f"\n\n**⏱️ Multi-Horizon Investment Breakdown:**\n"
            f"• ⚡ **1-2 Days (Scalp)**: **{dt.get('verdict','--')}** — Target: ${dt.get('target', 0):.2f} (Stop: ${dt.get('stop_loss', 0):.2f})\n"
            f"• 🌊 **Days-Weeks (Swing)**: **{sw.get('verdict','--')}** — Target: ${sw.get('take_profit_1', 0):.2f} (Stop: ${sw.get('stop_loss', 0):.2f})\n"
            f"• 🏛️ **Months-Years (Long Term)**: **{lt.get('verdict','--')}** — 1-Yr Target: ${lt.get('twelve_month_target', 0):.2f} (Floor: ${lt.get('invalidation_floor', 0):.2f})"
        )

    return (
        f"### 📊 Here is the Plain-English Breakdown for {ticker}:\n\n"
        f"• **Current Price**: ${entry:.2f}\n"
        f"• **Overall Verdict**: **{verdict}** ({conf}% confidence)\n"
        f"• **Market Trend**: {direction_desc}.{horizon_table}\n\n"
        f"**Immediate Action:**\n"
        f"• Stop-Loss: ${sl:.2f} (emergency safety net)\n"
        f"• Target: ${tp1:.2f} (first profit-taking level)"
    )


def generate_bot_response(
    user_message: str,
    current_ticker: Optional[str] = None,
    chart_context: Optional[Dict[str, Any]] = None,
    image_b64: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generates intelligent, personalized response from TradeBot AI.
    Reads user context (position size, purchase price) and gives direct, actionable answers.
    """
    # 1. First, check if the user is asking about terminology or educational concepts
    concept_answer = check_terminology_or_concept(user_message)
    if concept_answer:
        return {
            "bot_name": "TradeBot",
            "message": concept_answer,
            "referenced_ticker": current_ticker or "NVDA",
            "provider": "TradeBot Plain-English Guide"
        }

    ticker = extract_ticker_from_message(user_message) or current_ticker or "NVDA"
    ticker = ticker.upper()

    # Parse user's personal context from message
    user_ctx = extract_user_context(user_message)

    # Fetch live market data
    entry = 0.0
    sl = 0.0
    tp1 = 0.0
    tp2 = 0.0
    verdict = "HOLD"
    conf = 70
    score = 50
    reasons: List[str] = []
    rsi = 50.0
    supertrend = "NEUTRAL"

    try:
        hist = fetch_history_data(ticker, period="6mo", interval="1d")
        if hist is not None and not hist.empty:
            analysis = analyze_ticker_confluence(hist, ticker)
            quote = fetch_live_quote(ticker)

            verdict = analysis.get("verdict", "HOLD")
            conf = analysis.get("confidence_pct", 70)
            score = analysis.get("confluence_score", 50)
            setup = analysis.get("trade_setup", {})
            entry = float(setup.get("entry_price") or quote.get("current_price") or 0.0)
            sl = float(setup.get("stop_loss") or 0.0)
            tp1 = float(setup.get("take_profit_1") or 0.0)
            tp2 = float(setup.get("take_profit_2") or 0.0)
            reasons = analysis.get("key_reasons", [])
            rsi = analysis.get("breakdown", {}).get("rsi", 50.0)
            supertrend = analysis.get("breakdown", {}).get("supertrend", "NEUTRAL")
    except Exception as e:
        logger.error(f"Error computing quant metrics for {ticker}: {e}")

    if entry == 0.0:
        try:
            q = fetch_live_quote(ticker)
            entry = float(q.get("current_price", 100.0))
            sl = round(entry * 0.95, 2)
            tp1 = round(entry * 1.06, 2)
            tp2 = round(entry * 1.10, 2)
        except Exception:
            pass

    # Try Gemini with full context
    if GEMINI_API_KEY:
        purchase_price = user_ctx.get("purchase_price")
        shares = user_ctx.get("shares")

        position_context = ""
        if purchase_price and shares:
            pnl_pct = ((entry - purchase_price) / purchase_price) * 100
            dollar_pnl = (entry - purchase_price) * shares
            position_context = f"""
[USER'S PERSONAL POSITION]
- They own {shares} shares of {ticker}
- They bought at: ${purchase_price:.2f}
- Current price: ${entry:.2f}
- Their P&L: {'+'if dollar_pnl>=0 else ''}{dollar_pnl:.2f} ({'+'if pnl_pct>=0 else ''}{pnl_pct:.1f}%)
- IMPORTANT: Address their specific position directly! Give clear sell/hold advice and calculate their exact P&L for them.
"""
        elif purchase_price:
            pnl_pct = ((entry - purchase_price) / purchase_price) * 100
            position_context = f"""
[USER'S POSITION]
- They bought {ticker} at: ${purchase_price:.2f}
- Current price: ${entry:.2f}
- Current P&L: {'+'if pnl_pct>=0 else ''}{pnl_pct:.1f}%
"""

        short_mode = ""
        if user_ctx.get("wants_short"):
            short_mode = "\nCRITICAL: The user asked for a SHORT / DIRECT answer. Give a direct recommendation first, followed by 2-3 friendly lines."

        multi_horizon_data = analysis.get("multi_horizon") if 'analysis' in locals() and analysis else None
        mh_dossier = ""
        if multi_horizon_data:
            dt = multi_horizon_data.get("day_trade", {})
            sw = multi_horizon_data.get("swing_trade", {})
            lt = multi_horizon_data.get("long_term", {})
            mh_dossier = f"""
[WALL STREET MULTI-HORIZON BREAKDOWN]
- 1-2 Day Scalp: {dt.get('verdict')} (Entry: ${dt.get('entry', entry):.2f}, Target: ${dt.get('target', tp1):.2f}, Stop: ${dt.get('stop_loss', sl):.2f}) - {dt.get('summary')}
- Days-Weeks Swing: {sw.get('verdict')} (Entry: ${sw.get('entry', entry):.2f}, TP1: ${sw.get('take_profit_1', tp1):.2f}, Stop: ${sw.get('stop_loss', sl):.2f}) - {sw.get('summary')}
- Months-Years Long-Term: {lt.get('verdict')} (DCA Zone: {lt.get('accumulation_zone', 'N/A')}, 12-Mo Target: ${lt.get('twelve_month_target', tp2):.2f}, Floor: ${lt.get('invalidation_floor', sl):.2f}) - {lt.get('summary')}
"""

        rag_dossier = f"""
[LIVE MARKET DATA FOR {ticker}]
- Live Price: ${entry:,.2f}
- Signal: {verdict} ({conf}% Confidence)
- Confluence Score: {score}/100
- Trend Description: {'Bearish (falling)' if 'SELL' in verdict else ('Bullish (rising)' if 'BUY' in verdict else 'Neutral (sideways)')}
- RSI: {rsi}
- Stop-Loss Level: ${sl:,.2f}
- Take Profit 1: ${tp1:,.2f}
- Take Profit 2: ${tp2:,.2f}
- Key Reasons: {', '.join(reasons[:2]) if reasons else 'Market consolidation'}
{position_context}
{mh_dossier}
"""

        llm_prompt = f"""{TRADER_SYSTEM_PROMPT}
{short_mode}

{rag_dossier}

USER SAYS: "{user_message}"

INSTRUCTIONS:
- Talk like a warm, supportive expert friend.
- If the user asks about their shares/price, calculate their profit/loss and give them a direct recommendation first.
- If the user asks about short term vs long term or 1-2 days, reference the Wall Street multi-horizon breakdown.
- Always translate technical terms in parentheses: "Bearish (meaning price is dropping)", "Bullish (meaning price is rising)".
- Keep it concise, friendly, and easy to read.
"""
        ai_reply = query_gemini_api(llm_prompt, image_b64=image_b64)
        if ai_reply:
            return {
                "bot_name": "TradeBot AI",
                "message": ai_reply,
                "referenced_ticker": ticker,
                "signal_summary": {"verdict": verdict, "confidence": conf, "entry": entry, "stop_loss": sl, "target_1": tp1, "target_2": tp2},
                "provider": "Gemini Flash Intelligence"
            }

    # Smart deterministic fallback (reads user context — never a generic dump)
    multi_horizon_data = analysis.get("multi_horizon") if 'analysis' in locals() else None
    fallback_msg = generate_smart_fallback(
        user_message, ticker, verdict, conf, entry, sl, tp1, tp2, reasons, user_ctx, multi_horizon=multi_horizon_data
    )

    return {
        "bot_name": "TradeBot",
        "message": fallback_msg,
        "referenced_ticker": ticker,
        "signal_summary": {"verdict": verdict, "confidence": conf, "entry": entry, "stop_loss": sl, "target_1": tp1, "target_2": tp2},
        "provider": "TradeBot Engine"
    }
