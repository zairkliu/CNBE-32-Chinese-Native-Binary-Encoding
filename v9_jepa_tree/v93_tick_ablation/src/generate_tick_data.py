"""Generate realistic S&P 500 1-minute OHLCV data for June 1"""
import numpy as np

# Known S&P 500 reference: ~5500-5800 range for 2024-2025
# June 1, 2023: ~4280 close. We"ll use 2024 data: ~5300
BASE_PRICE = 5280.0

# Typical intraday patterns (U-shaped volume, random walk with drift)
MINUTES = 390  # 6.5 hours × 60

def generate_tick_data(seed=42):
    np.random.seed(seed)
    
    # Generate price path (random walk with slight positive drift and intraday U-shape)
    prices = np.zeros(MINUTES)
    prices[0] = BASE_PRICE
    
    # Intraday volatility pattern: higher at open/close, lower at lunch
    vol_pattern = 0.08 + 0.12 * (1 - abs(np.linspace(-1, 1, MINUTES))) 
    # Add spike at open
    vol_pattern[:30] *= 1.5
    vol_pattern[-20:] *= 1.3
    
    # Volume pattern: U-shaped
    volume = (100 + 200 * (1 - abs(np.linspace(-1, 1, MINUTES))**0.7)) * 1000
    volume[:30] *= 1.5
    volume[-20:] *= 1.3
    
    for i in range(1, MINUTES):
        drift = 0.002 * np.random.randn()  # slight random drift
        vol = vol_pattern[i] * np.random.randn()
        prices[i] = prices[i-1] + drift + vol
        prices[i] = max(prices[i], prices[i-1] * 0.995)  # limit drops
        prices[i] = min(prices[i], prices[i-1] * 1.005)  # limit rises
    
    # Convert to OHLCV
    ohlcv = np.zeros((MINUTES, 5))
    for i in range(MINUTES):
        base = prices[i]
        spread = base * np.random.uniform(0.0001, 0.0005)
        ohlcv[i, 0] = prices[max(0, i-1)] + np.random.randn() * 0.3  # Open
        ohlcv[i, 1] = base + abs(np.random.randn()) * 0.5  # High
        ohlcv[i, 2] = base - abs(np.random.randn()) * 0.5  # Low
        ohlcv[i, 3] = base  # Close
        ohlcv[i, 4] = volume[i] + np.random.randn() * volume[i] * 0.1  # Volume
    
    # Compute 10 financial features
    close = ohlcv[:, 3]
    high = ohlcv[:, 1]
    low = ohlcv[:, 2]
    vol = ohlcv[:, 4]
    
    features = np.zeros((MINUTES, 10))
    for i in range(MINUTES):
        # 0: Trend signal (MA5/MA20 deviation)
        ma5 = np.mean(close[max(0, i-4):i+1])
        ma20 = np.mean(close[max(0, i-19):i+1])
        features[i, 0] = (close[i] - ma20) / ma20 * 100 if ma20 > 0 else 0
        
        # 1: Volatility (ATR-like)
        tr = max(high[i] - low[i], abs(high[i] - close[max(0,i-1)]), abs(low[i] - close[max(0,i-1)])) if i > 0 else high[i] - low[i]
        features[i, 1] = tr / close[i] * 100
        
        # 2: Momentum (ROC)
        features[i, 2] = (close[i] - close[max(0, i-5)]) / close[max(0, i-5)] * 100 if i >= 5 else 0
        
        # 3: Volume level
        avg_vol = np.mean(vol[max(0, i-19):i+1])
        features[i, 3] = vol[i] / max(avg_vol, 1)
        
        # 4: Crisis signal (downside volatility)
        returns_5 = [close[max(0,i-j)] / close[max(0,i-j-1)] - 1 for j in range(min(5, i))]
        neg_returns = [r for r in returns_5 if r < 0]
        features[i, 4] = abs(np.mean(neg_returns)) * 100 if neg_returns else 0
        
        # 5: Market width (simulated)
        features[i, 5] = np.clip(np.random.randn() * 0.3 + 0.5, 0, 1)
        
        # 6: Time phase (0=open, 1=morning, 2=afternoon, 3=close)
        features[i, 6] = min(i / (MINUTES / 4), 3)
        
        # 7: Overnight gap (first minute only)
        features[i, 7] = abs(close[i] - BASE_PRICE) / BASE_PRICE * 100 if i == 0 else abs(close[i] - close[i-1]) / close[i-1] * 100
        
        # 8: Bollinger band position
        ma = np.mean(close[max(0, i-19):i+1])
        std = np.std(close[max(0, i-19):i+1]) if i >= 20 else 1
        features[i, 8] = (close[i] - ma) / max(std, 0.01)  # Z-score
        
        # 9: Trend strength (ADX-like)
        up = np.mean([max(close[max(0,i-j)] - close[max(0,i-j-1)], 0) for j in range(min(14, i))]) if i >= 14 else 0.1
        down = np.mean([max(close[max(0,i-j-1)] - close[max(0,i-j)], 0) for j in range(min(14, i))]) if i >= 14 else 0.1
        features[i, 9] = abs(up - down) / max(up + down, 0.01) * 100 if (up + down) > 0 else 0
    
    # Normalize features to comparable ranges
    for j in range(10):
        col = features[:, j]
        mn, mx = col.min(), col.max()
        if mx - mn > 0:
            features[:, j] = (col - mn) / (mx - mn)
    
    print(f"Generated {MINUTES} minutes of tick data for June 1")
    print(f"Price range: ${close.min():.2f} - ${close.max():.2f}")
    return ohlcv, features
