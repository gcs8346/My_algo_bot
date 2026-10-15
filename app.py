import os
from datetime import datetime, timedelta
import pandas as pd
import upstox_client
from upstox_client.api import HistoryApi, MarketQuoteApi

# Config
inst = "BSE_INDEX|SENSEX"
api_version = "2.0"

def get_live():
    token = os.environ.get("UPSTOX_TOKEN")
    if not token:
        raise Exception("UPSTOX_TOKEN not found in Environment")

    configuration = upstox_client.Configuration()
    configuration.access_token = token
    client = upstox_client.ApiClient(configuration)

    history_api = HistoryApi(client)
    market_api = MarketQuoteApi(client)

    # Date for history
    to_d = datetime.now().date().isoformat()
    from_d = (datetime.now() - timedelta(days=5)).date().isoformat()

    # 1. History - 1minute is allowed
    resp = history_api.get_historical_candle_data1(
        instrument_key=inst,
        interval="1minute",
        to_date=to_d,
        from_date=from_d,
        api_version=api_version
    )

    candles = resp.data.candles
    df = pd.DataFrame(candles, columns=["timestamp", "open", "high", "low", "close", "volume", "oi"])

    # 2. LTP - Naya tarika - symbol use hoga
    ltp_resp = market_api.ltp(symbol=inst, api_version=api_version)
    # Data structure: data -> BSE_INDEX|SENSEX -> last_price
    ltp_data = ltp_resp.data
    # Dict se nikalna
    ltp = float(ltp_data[inst].last_price)

    return df, ltp

# Test ke liye yahi se call hota hai tere dashboard me
# from app.py import get_live