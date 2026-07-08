import numpy as np
import os

"""Generate realistic 2008 financial crisis data (synthetic, numpy-only)"""

KNOWN_POINTS = {
    "2008-08-01": (11326.52, -0.02, 0.8), "2008-08-15": (11659.90, 0.15, 0.9),
    "2008-08-29": (11543.55, -0.41, 0.7), "2008-09-02": (11383.36, -1.04, 1.2),
    "2008-09-03": (11233.03, -1.32, 1.4), "2008-09-04": (11188.23, -0.40, 1.8),
    "2008-09-05": (11220.96, 0.29, 1.5),  "2008-09-08": (11510.74, 2.58, 2.0),
    "2008-09-09": (11230.05, -2.43, 2.2), "2008-09-10": (11149.92, -0.71, 1.9),
    "2008-09-11": (11143.13, -0.06, 1.7), "2008-09-12": (11021.56, -1.09, 1.6),
    "2008-09-15": (10917.51, -0.94, 3.0), "2008-09-16": (11059.02, 1.30, 2.5),
    "2008-09-17": (10609.66, -4.06, 3.5), "2008-09-18": (11019.69, 3.86, 3.0),
    "2008-09-19": (11388.44, 3.35, 2.8), "2008-09-22": (10968.28, -3.69, 2.0),
    "2008-09-29": (10365.45, -5.49, 3.2), "2008-10-01": (10831.07, 0.0, 1.5),
    "2008-10-03": (10325.38, -1.51, 2.0),
}

def generate_dataset():
    """从已知数据点插值生成完整序列（numpy-only, no pandas）"""
    import calendar
    dates_str = sorted(KNOWN_POINTS.keys())
    points = [KNOWN_POINTS[d] for d in dates_str]
    
    rows_close = []; rows_chg = []; rows_vol = []
    prev_close = None
    
    for i in range(len(dates_str) - 1):
        d1, d2 = dates_str[i], dates_str[i+1]
        c1, _, v1 = points[i]; c2, _, v2 = points[i+1]
        
        y1, m1, day1 = int(d1[:4]), int(d1[5:7]), int(d1[8:10])
        y2, m2, day2 = int(d2[:4]), int(d2[5:7]), int(d2[8:10])
        
        from datetime import datetime, timedelta
        dt1 = datetime(y1, m1, day1); dt2 = datetime(y2, m2, day2)
        days = (dt2 - dt1).days
        
        for j in range(days):
            dt = dt1 + timedelta(days=j)
            if dt.weekday() >= 5: continue  # skip weekends
            
            t = j / max(days, 1)
            close = c1 + (c2 - c1) * t + np.random.randn() * 40 * (1 + t)
            vol = v1 + (v2 - v1) * t + np.random.randn() * 0.08
            
            if prev_close is not None:
                chg = (close - prev_close) / prev_close * 100
            else:
                chg = 0
            chg = np.clip(chg, -10, 10)
            
            rows_close.append(close)
            rows_chg.append(chg)
            rows_vol.append(max(0.1, vol))
            prev_close = close
    
    arr = np.column_stack([rows_close, rows_chg, rows_vol])
    n = len(arr)
    
    # Compute additional features
    ma5 = np.zeros(n); ma20 = np.zeros(n); vola = np.zeros(n); mom = np.zeros(n)
    crisis = np.zeros(n, dtype=int); width = np.zeros(n); trend = np.zeros(n)
    
    for i in range(n):
        if i >= 4: ma5[i] = np.mean(arr[max(0,i-4):i+1, 0])
        else: ma5[i] = arr[i, 0]
        if i >= 19: ma20[i] = np.mean(arr[max(0,i-19):i+1, 0])
        else: ma20[i] = ma5[i]
        if i >= 4: vola[i] = np.std(arr[max(0,i-4):i+1, 1]) if np.std(arr[max(0,i-4):i+1, 1]) > 0 else 0.5
        else: vola[i] = 0.5
        if i >= 2: mom[i] = (arr[i, 0] - arr[i-3, 0]) / max(arr[i-3, 0], 1) * 100 if i >= 3 else 0
        crisis[i] = int(arr[i, 1] < -2) + int(arr[i, 2] > 2) + int(vola[i] > 2)
        width[i] = np.clip(np.random.randn() * 0.3 + 0.5, 0, 1)
        if i >= 4:
            s = np.std(arr[max(0,i-4):i+1, 1])
            trend[i] = abs(np.mean(arr[max(0,i-4):i+1, 1])) / max(s, 0.01)
    
    ma_dev = (arr[:, 0] - ma20) / ma20 * 100
    result = np.column_stack([arr[:, 0], arr[:, 1], arr[:, 2], ma_dev, vola, mom, crisis, width, trend])
    
    return result

if __name__ == "__main__":
    data = generate_dataset()
    print(f"Generated {len(data)} rows")
    print(f"Close range: {data[:, 0].min():.2f} - {data[:, 0].max():.2f}")
    print(f"Shape: {data.shape}")
