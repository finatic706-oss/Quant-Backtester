import requests
import pandas as pd
from flask import Flask, render_template, request, jsonify
import yfinance as yf
from backtester import backtest_all

app = Flask(__name__, template_folder='.', static_folder='.', static_url_path='')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/backtest', methods=['POST'])
def run_backtest():
    data = request.get_json()
    ticker = data.get('ticker', '').upper().strip()
    
    if not ticker:
        return jsonify({"error": "Please provide a valid stock ticker."}), 400
        
    if '.' not in ticker:
        ticker += '.NS'
        
    try:
        # Custom session to bypass Yahoo Finance datacenter blocks
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        })
        
        # Fetch 5 years of historical daily data
        stock_data = yf.download(ticker, period="5y", interval="1d", session=session, progress=False)
        
        if stock_data.empty:
            return jsonify({"error": f"No data found for {ticker}. Please check the symbol or try again later."}), 404
            
        # yfinance returns MultiIndex columns sometimes in newer versions, flatten them
        if isinstance(stock_data.columns, pd.MultiIndex):
            stock_data.columns = stock_data.columns.droplevel(1)
            
        # Run backtests
        results = backtest_all(stock_data)
        
        return jsonify({
            "ticker": ticker,
            "results": results
        })
        
    except Exception as e:
        print(f"Error during backtest: {e}")
        return jsonify({"error": f"Failed to backtest {ticker}. Error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
