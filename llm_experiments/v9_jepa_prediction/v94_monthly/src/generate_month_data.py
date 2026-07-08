"""Generate S&P 500 1-minute data for all 21 trading days of June 2026"""
import numpy as np

# 21 trading days in June 2026 (excluding 6/19 Juneteenth)
TRADING_DAYS = ["2026-06-01","06-02","06-03","06-04","06-05",
                "06-08","06-09","06-10","06-11","06-12",
                "06-15","06-16","06-17","06-18",
                "06-22","06-23","06-24","06-25","06-26",
                "06-29","06-30"]

# Different volatility regimes per week to test regime invariance
REGIMES = {
    "W1": {"vol": 0.08, "drift": 0.02, "desc": "Low vol, uptrend"},
    "W2": {"vol": 0.15, "drift": 0.00, "desc": "High vol, sideways"},
    "W3": {"vol": 0.10, "drift": 0.03, "desc": "Med vol, strong uptrend"},
    "W4": {"vol": 0.18, "drift": -0.02, "desc": "High vol, downtrend"},
    "W5": {"vol": 0.07, "drift": 0.01, "desc": "Low vol, recovery"},
}

# Assign weeks to days
WEEK_MAP = {}
for i, d in enumerate(TRADING_DAYS):
    if i < 5: WEEK_MAP[d] = "W1"
    elif i < 10: WEEK_MAP[d] = "W2"
    elif i < 14: WEEK_MAP[d] = "W3"
    elif i < 19: WEEK_MAP[d] = "W4"
    else: WEEK_MAP[d] = "W5"

MINUTES = 390

def _compute_features(ohlcv):
    """Compute 10 financial features from OHLCV"""
    close, high, low, vol = ohlcv[:, 3], ohlcv[:, 1], ohlcv[:, 2], ohlcv[:, 4]
    feat = np.zeros((MINUTES, 10))
    for i in range(MINUTES):
        ma5 = np.mean(close[max(0,i-4):i+1])
        ma20 = np.mean(close[max(0,i-19):i+1])
        feat[i,0] = (close[i] - ma20) / ma20 * 100 if ma20 > 0 else 0  # trend
        tr = max(high[i]-low[i], abs(high[i]-close[max(0,i-1)]), abs(low[i]-close[max(0,i-1)])) if i>0 else high[i]-low[i]
        feat[i,1] = tr / close[i] * 100  # volatility
        feat[i,2] = (close[i] - close[max(0,i-5)]) / close[max(0,i-5)] * 100 if i>=5 else 0  # momentum
        avg_vol = np.mean(vol[max(0,i-19):i+1])
        feat[i,3] = vol[i] / max(avg_vol, 1)  # volume level
        neg_ret = [close[max(0,i-j)]/close[max(0,i-j-1)]-1 for j in range(min(5,i)) if close[max(0,i-j-1)]>0]
        neg = [r for r in neg_ret if r<0]
        feat[i,4] = abs(np.mean(neg))*100 if neg else 0  # crisis
        feat[i,5] = np.clip(np.random.randn()*0.3+0.5,0,1)  # width
        feat[i,6] = min(i/(MINUTES/4),3)  # time phase
        feat[i,7] = abs(close[i]-close[i-1])/close[i-1]*100 if i>0 else 0  # gap
        ma = np.mean(close[max(0,i-19):i+1]); std = np.std(close[max(0,i-19):i+1]) if i>=20 else 1
        feat[i,8] = (close[i]-ma)/max(std,0.01)  # bollinger
        up = np.mean([max(close[max(0,i-j)]-close[max(0,i-j-1)],0) for j in range(min(14,i))]) if i>=14 else 0.1
        down = np.mean([max(close[max(0,i-j-1)]-close[max(0,i-j)],0) for j in range(min(14,i))]) if i>=14 else 0.1
        feat[i,9] = abs(up-down)/max(up+down,0.01)*100 if (up+down)>0 else 0  # ADX
    # Normalize each feature to [0,1]
    for j in range(10):
        mn, mx = feat[:,j].min(), feat[:,j].max()
        if mx-mn>0: feat[:,j] = (feat[:,j]-mn)/(mx-mn)
    return feat

def generate_day(day_str, base_price=5300.0, seed=42):
    """Generate one trading day of 1-minute OHLCV data"""
    np.random.seed(seed + hash(day_str) % 10000)
    regime = REGIMES[WEEK_MAP[day_str]]
    vol, drift = regime["vol"], regime["drift"]
    
    prices = np.zeros(MINUTES); prices[0] = base_price
    vol_pat = vol * (1 + 0.5 * (1 - abs(np.linspace(-1,1,MINUTES))))
    vol_pat[:30]*=1.4; vol_pat[-20:]*=1.2
    
    for i in range(1, MINUTES):
        prices[i] = prices[i-1] + drift*np.random.randn() + vol_pat[i]*np.random.randn()
        prices[i] = np.clip(prices[i], prices[i-1]*0.995, prices[i-1]*1.005)
    
    ohlcv = np.zeros((MINUTES, 5))
    volume = (100 + 200*(1-abs(np.linspace(-1,1,MINUTES))**0.7))*1000
    volume[:30]*=1.5; volume[-20:]*=1.3
    for i in range(MINUTES):
        ohlcv[i,0] = prices[max(0,i-1)]+np.random.randn()*0.3
        ohlcv[i,1] = prices[i]+abs(np.random.randn())*0.5
        ohlcv[i,2] = prices[i]-abs(np.random.randn())*0.5
        ohlcv[i,3] = prices[i]
        ohlcv[i,4] = volume[i]+np.random.randn()*volume[i]*0.1
    
    feats = _compute_features(ohlcv)
    return ohlcv, feats

def generate_month():
    """Generate all 21 trading days"""
    all_data = {}
    for day in TRADING_DAYS:
        ohlcv, feats = generate_day(day, seed=42)
        all_data[day] = {"ohlcv": ohlcv, "features": feats, 
                         "regime": REGIMES[WEEK_MAP[day]]["desc"]}
    return all_data

if __name__ == "__main__":
    data = generate_month()
    print(f"Generated {len(data)} trading days")
    for d, v in data.items():
        print(f"  {d}: {v['features'].shape} - {v['regime']}")
