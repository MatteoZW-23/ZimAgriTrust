from statistics import mean


HISTORICAL_PRICE_DATA = {
    "maize": [12, 13, 13.5, 14.2, 14.8, 15.3],
    "beans": [20, 19.8, 19.2, 18.7, 18.5, 18.1],
    "groundnuts": [25, 25.5, 26.2, 26.8, 27.1, 27.6],
}


def predict_price_trend(crop: str) -> dict[str, float | str]:
    series = HISTORICAL_PRICE_DATA.get(crop.lower(), [10, 10.1, 10.3, 10.2, 10.4, 10.5])
    trend = "UP" if series[-1] >= series[0] else "DOWN"
    recommendation = "Strong Market Opportunity" if trend == "UP" else "Monitor for Price Rebound"
    return {
        "crop": crop,
        "predicted_price": round(mean(series[-3:]), 2),
        "trend": trend,
        "recommendation": recommendation,
    }
