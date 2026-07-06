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
        
    # Auto-append .NS if it's an Indian stock and doesn't have an extension
    if '.' not in ticker:
        ticker += '.NS'
        
    try:
        # Fetch 5 years of historical daily data
        stock_data = yf.download(ticker, period="5y", interval="1d", progress=False)
        
        if stock_data.empty:
            return jsonify({"error": f"No data found for {ticker}. Please check the symbol."}), 404
            
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
