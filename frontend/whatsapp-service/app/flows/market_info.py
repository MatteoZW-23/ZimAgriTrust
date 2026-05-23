"""Market information flows – prices, forecast, trending, weather, news."""
from __future__ import annotations

import logging
from typing import Optional

from app.whatsapp_bridge import WhatsAppBridgeClient

logger = logging.getLogger(__name__)


class MarketInfoFlowHandler:
    """Handles prices, forecast, trending, weather, and news commands."""

    def __init__(self, bridge: WhatsAppBridgeClient):
        self._bridge = bridge

    # ── Prices ─────────────────────────────────────────────────────────────

    async def handle_prices(self, phone: str, body: str) -> str:
        try:
            data   = await self._bridge.get("/public/prices/current")
            prices = data.get("prices", [])
            if not prices:
                return "📊 No price data available right now. Please try later."

            lines = ["📊 *Today's Crop Prices (USD)*\n"]
            for item in prices[:10]:
                crop  = item.get("crop", "Unknown")
                price = item.get("price_usd", 0)
                unit  = item.get("unit", "per kg")
                trend = item.get("change_pct", 0)
                arrow = "▲" if trend > 0 else ("▼" if trend < 0 else "–")
                lines.append(f"🌾 *{crop}*: ${price:.4f}/{unit}  {arrow} {abs(trend):.1f}%")

            lines.append(f"\n{data.get('updated_at', '')}")
            lines.append("Reply *forecast* for 7-day predictions")
            return "\n".join(lines)
        except Exception as exc:
            logger.warning("prices fetch failed for %s: %s", phone, exc)
            return "❌ Could not fetch prices. Please try again shortly."

    # ── Forecast ───────────────────────────────────────────────────────────

    async def handle_forecast(self, phone: str, body: str) -> str:
        try:
            data      = await self._bridge.get("/public/prices/current")
            prices    = data.get("prices", [])
            if not prices:
                return "📈 No forecast data available. Please try later."

            lines = ["📈 *7-Day Price Outlook*\n", "Based on current market trends:\n"]
            for item in prices[:6]:
                crop  = item.get("crop", "Unknown")
                price = item.get("price_usd", 0)
                trend = item.get("change_pct", 0)
                arrow = "▲" if trend > 0 else ("▼" if trend < 0 else "–")
                week_pred = price * (1 + trend / 100 * 7) if trend else price
                lines.append(
                    f"*{crop}*: ${price:.4f} → ~${week_pred:.4f}  {arrow} {abs(trend):.1f}%/day"
                )

            lines.append("\nPowered by ZimAgriTrust AI • Reply *menu* to go back")
            return "\n".join(lines)
        except Exception as exc:
            logger.warning("forecast failed for %s: %s", phone, exc)
            return "❌ Could not fetch forecast. Please try again."

    # ── Trending ───────────────────────────────────────────────────────────

    async def handle_trending(self, phone: str) -> str:
        try:
            data  = await self._bridge.get("/public/prices/trending")
            items = data.get("trending", [])
            if not items:
                return "🔥 No trending data available right now."

            lines = ["🔥 *Trending Crops This Week*\n"]
            for i, item in enumerate(items[:6], 1):
                crop     = item.get("crop", "Unknown")
                emoji    = item.get("emoji", "🌱")
                offers   = item.get("offers", 0)
                listings = item.get("listings", 0)
                label    = item.get("label", "Active")
                lines.append(f"{i}. {emoji} *{crop}* — {offers} offers, {listings} listings  {label}")

            lines.append("\nReply *prices* for full price list • *menu* to go back")
            return "\n".join(lines)
        except Exception as exc:
            logger.warning("trending failed for %s: %s", phone, exc)
            return "❌ Could not fetch trending data. Please try again."

    # ── Weather ────────────────────────────────────────────────────────────

    async def handle_weather(self, phone: str, body: str) -> str:
        try:
            data      = await self._bridge.get("/public/weather")
            forecasts = data.get("forecasts", [])

            if not forecasts:
                return (
                    "🌤 *Zimbabwe Weather*\n\n"
                    "Weather data is currently unavailable.\n"
                    "Set OPENWEATHER_API_KEY to enable live weather.\n\n"
                    "Reply *menu* to go back"
                )

            lines = ["🌤 *Zimbabwe Weather – Major Farming Regions*\n"]
            for region in forecasts[:5]:
                city      = region.get("city", "Unknown")
                temp      = region.get("temp_c", 0)
                condition = region.get("condition", "")
                humidity  = region.get("humidity", 0)
                rain      = region.get("rain_mm", 0)
                icon      = region.get("icon", "🌡️")
                advice    = region.get("advice", "")
                lines.append(
                    f"{icon} *{city}*: {temp}°C, {condition}\n"
                    f"   Humidity {humidity}%  Rain {rain}mm  — _{advice}_"
                )

            lines.append(f"\n{data.get('updated_at', '')}")
            lines.append("Reply *menu* to go back")
            return "\n".join(lines)
        except Exception as exc:
            logger.warning("weather failed for %s: %s", phone, exc)
            return "❌ Could not fetch weather data. Please try again."

    # ── News ───────────────────────────────────────────────────────────────

    async def handle_news(self, phone: str) -> str:
        try:
            data    = await self._bridge.get("/public/news")
            articles = data.get("articles", [])
            if not articles:
                return "📰 No news available right now. Please check back later."

            lines = ["📰 *Agricultural News*\n"]
            for i, article in enumerate(articles[:5], 1):
                title   = article.get("title", "Untitled")
                source  = article.get("source", article.get("feed", ""))
                summary = article.get("summary", article.get("description", ""))
                lines.append(f"{i}. *{title}*")
                if source:
                    lines.append(f"   _{source}_")
                if summary:
                    lines.append(f"   {summary[:80]}{'…' if len(summary) > 80 else ''}")
                lines.append("")

            lines.append(f"{data.get('updated_at', '')}")
            lines.append("Reply *menu* to go back")
            return "\n".join(lines)
        except Exception as exc:
            logger.warning("news failed for %s: %s", phone, exc)
            return "❌ Could not fetch news. Please try again."
