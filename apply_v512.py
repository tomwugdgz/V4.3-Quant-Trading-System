#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Apply all v5.12 fixes to patrol.py - comprehensive fix"""
import re

with open('patrol.py', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

changes = []

# Fix 1: get_pip_size function (missing!)
# Add it before pivot_zone_check
pivot_zone_check_def = content.find('def pivot_zone_check(')
if pivot_zone_check_def == -1:
    changes.append('ERROR: pivot_zone_check not found')
else:
    get_pip_func = '''
def get_pip_size(symbol):
    """Get pip size for a symbol"""
    sym_info = mt5.symbol_info(symbol)
    digits = sym_info.digits
    point = sym_info.point
    return point * 10 if digits in [3, 5] else point

'''
    content = content[:pivot_zone_check_def] + get_pip_func + content[pivot_zone_check_def:]
    changes.append('Fix1: Added get_pip_size function')

# Fix 2: Fix ADX H4 RSI rolling -> EWM
old = '''        delta4 = h4df['close'].diff()
        gain4 = delta4.clip(lower=0).rolling(14).mean()
        loss4 = (-delta4.clip(upper=0)).rolling(14).mean()
        rs4 = gain4 / loss4.replace(0, np.nan)
        h4_rsi = (100 - 100 / (1 + rs4)).iloc[-1]'''
new = '''        delta4 = h4df['close'].diff()
        gain4 = delta4.clip(lower=0).ewm(alpha=1.0/14, adjust=False).mean()
        loss4 = (-delta4.clip(upper=0)).ewm(alpha=1.0/14, adjust=False).mean()
        rs4 = gain4 / loss4.replace(0, 1e-10)
        h4_rsi = (100 - 100 / (1 + rs4)).iloc[-1]'''
if old in content:
    content = content.replace(old, new)
    changes.append('Fix2: H4 RSI rolling->EWM')
else:
    changes.append('Fix2: H4 RSI already EWM or pattern not found')

# Fix 3: Fix ADX rolling -> EWM (Wilder smoothing)
old = '''        atr_h1 = tr.rolling(14).mean()
        plus_dm = hi.diff().clip(lower=0)
        minus_dm = (-lo.diff()).clip(upper=0)
        plus_di = 100 * plus_dm.rolling(14).mean() / atr_h1.replace(0, np.nan)
        minus_di = 100 * minus_dm.rolling(14).mean() / atr_h1.replace(0, np.nan)
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, np.nan)
        adx = dx.rolling(14).mean().iloc[-1]'''
new = '''        sym_info = mt5.symbol_info(symbol)
        digits = sym_info.digits
        pip_mult = 0.0001 if digits == 5 else (0.01 if digits == 3 else 0.0001)
        # Normalize to pips
        tr1 = (hi - lo) / pip_mult
        tr2 = abs(hi - cl.shift(1)) / pip_mult
        tr3 = abs(lo - cl.shift(1)) / pip_mult
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        plus_dm = (hi - hi.shift(1)).clip(lower=0) / pip_mult
        minus_dm = (lo.shift(1) - lo).clip(lower=0) / pip_mult
        atr14 = tr.ewm(alpha=1.0/14, adjust=False).mean()
        plus_di = plus_dm.ewm(alpha=1.0/14, adjust=False).mean() / atr14.replace(0, 1e-10) * 100
        minus_di = minus_dm.ewm(alpha=1.0/14, adjust=False).mean() / atr14.replace(0, 1e-10) * 100
        dx = abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, 1e-10) * 100
        adx = dx.ewm(alpha=1.0/14, adjust=False).mean().iloc[-1]'''
if old in content:
    content = content.replace(old, new)
    changes.append('Fix3: ADX rolling->EWM + pip normalization')
else:
    changes.append('Fix3: ADX already EWM or pattern not found')

# Fix 4: Fix current_price bug in calculate_signal_v3
old = 'pivot_zone_check(symbol, current_price, direction'
new = 'pivot_zone_check(symbol, price, direction'
if old in content:
    content = content.replace(old, new)
    changes.append('Fix4: current_price -> price')
else:
    changes.append('Fix4: current_price bug already fixed')

# Fix 5: SuperTrend numpy array bug
old = 'prev_upper = float(final_upper.iloc[i-1])'
new = 'prev_upper = float(final_upper[i-1])'
if old in content:
    content = content.replace(old, new)
    changes.append('Fix5: final_upper.iloc -> final_upper[i]')
else:
    changes.append('Fix5: final_upper.iloc already fixed')

old = 'prev_lower = float(final_lower.iloc[i-1])'
new = 'prev_lower = float(final_lower[i-1])'
if old in content:
    content = content.replace(old, new)
    changes.append('Fix5b: final_lower.iloc -> final_lower[i]')

old = 'fu = float(final_upper.iloc[i])'
new = 'fu = float(final_upper[i])'
if old in content:
    content = content.replace(old, new)
    changes.append('Fix5c: final_upper.iloc[i] -> final_upper[i]')

old = 'fl = float(final_lower.iloc[i])'
new = 'fl = float(final_lower[i])'
if old in content:
    content = content.replace(old, new)
    changes.append('Fix5d: final_lower.iloc[i] -> final_lower[i]')

# Fix 6: get_dynamic_sl_tp pivot_threshold placement bug
old = '''    pivot_threshold = max(sl_pips, 25)
    if sl_pips < pivot_threshold:
        buffer_extra = pivot_threshold - sl_pips
        sl_pips = pivot_threshold
        tp_pips = tp_pips + buffer_extra'''
new = '    # pivot_threshold removed - sl_pips already has minimum 20pip'
if old in content:
    content = content.replace(old, new)
    changes.append('Fix6: Removed pivot_threshold bug in get_dynamic_sl_tp')
else:
    changes.append('Fix6: pivot_threshold bug already fixed or pattern different')

# Fix 7: Version update
content = content.replace("'Patrol Smart v5.11'", "'Patrol Smart v5.12'")
content = content.replace("'v5.11'", "'v5.12'")
changes.append('Fix7: Version v5.11 -> v5.12')

with open('patrol.py', 'w', encoding='utf-8', errors='ignore') as f:
    f.write(content)

print('Changes applied:')
for c in changes:
    print('  ' + c)
print('Done!')