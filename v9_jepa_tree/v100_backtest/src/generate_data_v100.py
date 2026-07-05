"""Generate both US (S&P500) and A-share (沪深300) monthly 1-minute data"""
import numpy as np

TRADING_DAYS = ["2026-06-01","06-02","06-03","06-04","06-05",
                "06-08","06-09","06-10","06-11","06-12",
                "06-15","06-16","06-17","06-18",
                "06-22","06-23","06-24","06-25","06-26",
                "06-29","06-30"]

REGIMES = {
    "W1": {"vol": 0.008, "drift": 0.0002}, "W2": {"vol": 0.015, "drift": 0.0},
    "W3": {"vol": 0.010, "drift": 0.0003}, "W4": {"vol": 0.018, "drift": -0.0002},
    "W5": {"vol": 0.007, "drift": 0.0001},
}
WEEK_MAP = {}
for i, d in enumerate(TRADING_DAYS):
    if i < 5: WEEK_MAP[d]="W1"
    elif i < 10: WEEK_MAP[d]="W2"
    elif i < 14: WEEK_MAP[d]="W3"
    elif i < 19: WEEK_MAP[d]="W4"
    else: WEEK_MAP[d]="W5"

MINUTES = {"US": 390, "A": 240}

def _feats(ohlcv):
    close, high, low, vol = ohlcv[:,3], ohlcv[:,1], ohlcv[:,2], ohlcv[:,4]
    n = len(close)
    feat = np.zeros((n, 10))
    for i in range(n):
        ma5 = np.mean(close[max(0,i-4):i+1]); ma20 = np.mean(close[max(0,i-19):i+1])
        feat[i,0] = (close[i]-ma20)/ma20*100 if ma20>0 else 0
        tr = max(high[i]-low[i], abs(high[i]-close[max(0,i-1)]), abs(low[i]-close[max(0,i-1)])) if i>0 else high[i]-low[i]
        feat[i,1] = tr/close[i]*100
        feat[i,2] = (close[i]-close[max(0,i-5)])/close[max(0,i-5)]*100 if i>=5 else 0
        avg_v = np.mean(vol[max(0,i-19):i+1])
        feat[i,3] = vol[i]/max(avg_v,1)
        rets = [close[max(0,i-j)]/close[max(0,i-j-1)]-1 for j in range(min(5,i)) if close[max(0,i-j-1)]>0]
        neg = [r for r in rets if r<0]
        feat[i,4] = abs(np.mean(neg))*100 if neg else 0
        feat[i,5] = np.clip(np.random.randn()*0.3+0.5,0,1)
        feat[i,6] = min(i/(n/4),3)
        feat[i,7] = abs(close[i]-close[i-1])/close[i-1]*100 if i>0 else 0
        ma = np.mean(close[max(0,i-19):i+1]); std = np.std(close[max(0,i-19):i+1]) if i>=20 else 1
        feat[i,8] = (close[i]-ma)/max(std,0.01)
        up = np.mean([max(close[max(0,i-j)]-close[max(0,i-j-1)],0) for j in range(min(14,i))]) if i>=14 else 0.1
        down = np.mean([max(close[max(0,i-j-1)]-close[max(0,i-j)],0) for j in range(min(14,i))]) if i>=14 else 0.1
        feat[i,9] = abs(up-down)/max(up+down,0.01)*100 if (up+down)>0 else 0
    for j in range(10):
        mn, mx = feat[:,j].min(), feat[:,j].max()
        if mx-mn>0: feat[:,j] = (feat[:,j]-mn)/(mx-mn)
    return feat

def _gen_day(n_min, base_p, vol, drift, seed_add=0, use_ashare=False):
    np.random.seed(42 + seed_add)
    prices = np.zeros(n_min); prices[0] = base_p
    vol_pat = vol*(1+0.5*(1-abs(np.linspace(-1,1,n_min))))
    if use_ashare: vol_pat[:60]*=1.8
    else: vol_pat[:30]*=1.4; vol_pat[-20:]*=1.2
    for i in range(1,n_min):
        prices[i] = prices[i-1] + prices[i-1]*drift + prices[i-1]*vol_pat[i]*np.random.randn()
        prices[i] = np.clip(prices[i], prices[i-1]*0.995, prices[i-1]*1.005)
    ohlcv = np.zeros((n_min,5))
    volume = (100+200*(1-abs(np.linspace(-1,1,n_min))**0.7))*1e6
    if use_ashare: volume[:60]*=2.0; volume[-30:]*=0.8
    else: volume[:30]*=1.5; volume[-20:]*=1.3
    for i in range(n_min):
        ohlcv[i,0] = prices[max(0,i-1)]+prices[i]*np.random.randn()*0.0003
        ohlcv[i,1] = prices[i]+abs(np.random.randn())*prices[i]*0.0005
        ohlcv[i,2] = prices[i]-abs(np.random.randn())*prices[i]*0.0005
        ohlcv[i,3] = prices[i]
        ohlcv[i,4] = volume[i]+np.random.randn()*volume[i]*0.1
    return ohlcv, _feats(ohlcv)

def generate_month(market="US", n_min=390, base_price=5300.0):
    all_data = {}
    for i, day in enumerate(TRADING_DAYS):
        reg = REGIMES[WEEK_MAP[day]]
        daily_drift = 0.0003 if market=="US" else -0.0001
        bp = base_price * (1 + daily_drift * i) + np.random.randn()*2
        use_a = (market == "A")
        ohlcv, feats = _gen_day(n_min, bp, reg["vol"], reg["drift"], i, use_a)
        all_data[day] = {"ohlcv": ohlcv, "features": feats, "close": ohlcv[:,3].copy()}
    return all_data
