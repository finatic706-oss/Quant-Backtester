import pandas as pd
import numpy as np

def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_metrics(trades, years):
    if not trades:
        return {
            "total_return": 0,
            "cagr": 0,
            "win_rate": 0,
            "max_drawdown": 0,
            "total_trades": 0,
            "avg_profit_per_trade": 0,
            "trade_log": [],
            "chart_data": []
        }
    
    df_trades = pd.DataFrame(trades)
    winning_trades = df_trades[df_trades['pnl_pct'] > 0]
    win_rate = (len(winning_trades) / len(df_trades)) * 100 if len(df_trades) > 0 else 0
    
    cumulative_returns = (1 + df_trades['pnl_pct']).cumprod()
    total_return_decimal = cumulative_returns.iloc[-1] - 1 if not cumulative_returns.empty else 0
    total_return = total_return_decimal * 100
    
    # CAGR Calculation: (Final Value / Initial Value) ^ (1/Years) - 1
    # Note: Initial Value is implicitly 1. Final Value is cumulative_returns.iloc[-1]
    final_multiplier = cumulative_returns.iloc[-1] if not cumulative_returns.empty else 1
    cagr = ((final_multiplier ** (1 / years)) - 1) * 100 if final_multiplier > 0 and years > 0 else 0
    
    peak = cumulative_returns.cummax()
    drawdown = (cumulative_returns - peak) / peak
    max_drawdown = drawdown.min() * 100 if not drawdown.empty else 0

    chart_data = []
    for idx, row in df_trades.iterrows():
        cum_val = (cumulative_returns.iloc[idx] - 1) * 100 
        chart_data.append({
            "x": row['exit_date'],
            "y": round(cum_val, 2)
        })
    
    return {
        "total_return": round(total_return, 2),
        "cagr": round(cagr, 2),
        "win_rate": round(win_rate, 2),
        "max_drawdown": round(max_drawdown, 2),
        "total_trades": len(trades),
        "avg_profit_per_trade": round(df_trades['pnl_pct'].mean() * 100, 2) if len(df_trades) > 0 else 0,
        "trade_log": trades,
        "chart_data": chart_data
    }

def run_buy_and_hold(df):
    """ Benchmark: Buy on day 1, hold until last day """
    df = df.copy()
    years = len(df) / 252
    
    if len(df) < 2:
        return calculate_metrics([], years)
        
    entry_price = round(df['Close'].iloc[0], 2)
    entry_date = df.index[0].strftime('%Y-%m-%d')
    exit_price = round(df['Close'].iloc[-1], 2)
    exit_date = df.index[-1].strftime('%Y-%m-%d')
    pnl_pct = (exit_price - entry_price) / entry_price
    
    trades = [{
        'entry_date': entry_date, 
        'entry_price': entry_price, 
        'exit_date': exit_date, 
        'exit_price': exit_price, 
        'pnl_pct': pnl_pct
    }]
    
    return calculate_metrics(trades, years)

def run_momentum_strategy(df):
    df = df.copy()
    years = len(df) / 252
    df['SMA_200'] = df['Close'].rolling(window=200).mean()
    df['High_20'] = df['High'].rolling(window=20).max().shift(1)
    df['Low_20'] = df['Low'].rolling(window=20).min().shift(1)
    
    trades = []
    in_position = False
    entry_price = 0
    entry_date = None
    
    for i in range(200, len(df)):
        if not in_position:
            if df['Close'].iloc[i] > df['SMA_200'].iloc[i] and df['High'].iloc[i] > df['High_20'].iloc[i]:
                entry_price = round(df['Close'].iloc[i], 2)
                entry_date = df.index[i].strftime('%Y-%m-%d')
                in_position = True
        else:
            if df['Low'].iloc[i] < df['Low_20'].iloc[i]:
                exit_price = round(df['Low_20'].iloc[i], 2)
                exit_date = df.index[i].strftime('%Y-%m-%d')
                pnl_pct = (exit_price - entry_price) / entry_price
                trades.append({
                    'entry_date': entry_date, 'entry_price': entry_price, 
                    'exit_date': exit_date, 'exit_price': exit_price, 'pnl_pct': pnl_pct
                })
                in_position = False
                
    # Close open position at end of backtest
    if in_position:
        exit_price = round(df['Close'].iloc[-1], 2)
        exit_date = df.index[-1].strftime('%Y-%m-%d')
        pnl_pct = (exit_price - entry_price) / entry_price
        trades.append({
            'entry_date': entry_date, 'entry_price': entry_price, 
            'exit_date': exit_date, 'exit_price': exit_price, 'pnl_pct': pnl_pct
        })
                
    return calculate_metrics(trades, years)

def run_mean_reversion_strategy(df):
    df = df.copy()
    years = len(df) / 252
    df['RSI'] = calculate_rsi(df)
    
    trades = []
    in_position = False
    entry_price = 0
    entry_date = None
    
    for i in range(15, len(df)):
        if not in_position:
            if df['RSI'].iloc[i] < 30:
                entry_price = round(df['Close'].iloc[i], 2)
                entry_date = df.index[i].strftime('%Y-%m-%d')
                in_position = True
        else:
            if df['Low'].iloc[i] < entry_price * 0.95:
                exit_price = round(entry_price * 0.95, 2)
                exit_date = df.index[i].strftime('%Y-%m-%d')
                pnl_pct = -0.05
                trades.append({
                    'entry_date': entry_date, 'entry_price': entry_price, 
                    'exit_date': exit_date, 'exit_price': exit_price, 'pnl_pct': pnl_pct
                })
                in_position = False
            elif df['RSI'].iloc[i] > 70:
                exit_price = round(df['Close'].iloc[i], 2)
                exit_date = df.index[i].strftime('%Y-%m-%d')
                pnl_pct = (exit_price - entry_price) / entry_price
                trades.append({
                    'entry_date': entry_date, 'entry_price': entry_price, 
                    'exit_date': exit_date, 'exit_price': exit_price, 'pnl_pct': pnl_pct
                })
                in_position = False
                
    if in_position:
        exit_price = round(df['Close'].iloc[-1], 2)
        exit_date = df.index[-1].strftime('%Y-%m-%d')
        pnl_pct = (exit_price - entry_price) / entry_price
        trades.append({
            'entry_date': entry_date, 'entry_price': entry_price, 
            'exit_date': exit_date, 'exit_price': exit_price, 'pnl_pct': pnl_pct
        })
                
    return calculate_metrics(trades, years)

def run_ma_crossover_strategy(df):
    df = df.copy()
    years = len(df) / 252
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['SMA_200'] = df['Close'].rolling(window=200).mean()
    
    trades = []
    in_position = False
    entry_price = 0
    entry_date = None
    
    for i in range(200, len(df)):
        prev_50 = df['SMA_50'].iloc[i-1]
        prev_200 = df['SMA_200'].iloc[i-1]
        curr_50 = df['SMA_50'].iloc[i]
        curr_200 = df['SMA_200'].iloc[i]
        
        if not in_position and prev_50 <= prev_200 and curr_50 > curr_200:
            entry_price = round(df['Close'].iloc[i], 2)
            entry_date = df.index[i].strftime('%Y-%m-%d')
            in_position = True
        
        elif in_position and prev_50 >= prev_200 and curr_50 < curr_200:
            exit_price = round(df['Close'].iloc[i], 2)
            exit_date = df.index[i].strftime('%Y-%m-%d')
            pnl_pct = (exit_price - entry_price) / entry_price
            trades.append({
                'entry_date': entry_date, 'entry_price': entry_price, 
                'exit_date': exit_date, 'exit_price': exit_price, 'pnl_pct': pnl_pct
            })
            in_position = False
            
    if in_position:
        exit_price = round(df['Close'].iloc[-1], 2)
        exit_date = df.index[-1].strftime('%Y-%m-%d')
        pnl_pct = (exit_price - entry_price) / entry_price
        trades.append({
            'entry_date': entry_date, 'entry_price': entry_price, 
            'exit_date': exit_date, 'exit_price': exit_price, 'pnl_pct': pnl_pct
        })
            
    return calculate_metrics(trades, years)

def backtest_all(df):
    df = df.dropna(subset=['Close', 'High', 'Low'])
    return {
        "Buy & Hold": run_buy_and_hold(df),
        "Momentum Breakout": run_momentum_strategy(df),
        "Mean Reversion (RSI)": run_mean_reversion_strategy(df),
        "MA Crossover": run_ma_crossover_strategy(df)
    }
