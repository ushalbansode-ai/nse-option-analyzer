from option_chain import option_chain_analyzer
from flask import Flask, jsonify, render_template
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import json

from nse_data import NSEDataFetcher, DataProcessor
from analytics import OptionAnalytics
from config import Config

app = Flask(__name__)
CORS(app)

# Global data storage
market_data = {
    'NIFTY': {'data': None, 'timestamp': None, 'analysis': None, 'signals': None},
    'BANKNIFTY': {'data': None, 'timestamp': None, 'analysis': None, 'signals': None}
}

def fetch_and_process_data():
    """Fetch and process data for all symbols using OptionChain class"""
    print(f"📊 Fetching data at {datetime.now()}")
    
    # Use the OptionChain class to fetch and process data
    results = option_chain_analyzer.fetch_all_chains()
    
    for symbol, analyzed_data in results.items():
        if analyzed_data:
            # Get trading signals for this symbol
            trading_signals = option_chain_analyzer.get_trading_signals(symbol)
            
            market_data[symbol] = {
                'data': analyzed_data,
                'analysis': analyzed_data['analysis'],
                'signals': trading_signals,
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"✅ Updated {symbol} data with {len(analyzed_data['analysis']['strike_data'])} strikes")
            print(f"   📈 Sentiment Score: {analyzed_data['analysis']['sentiment_score']}")
            print(f"   🎯 Signals: {len(trading_signals.get('signals', []))} generated")
        else:
            print(f"❌ No data for {symbol}")

# API Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data/<symbol>')
def get_symbol_data(symbol):
    if symbol in market_data and market_data[symbol]['analysis']:
        response_data = {
            'analysis': market_data[symbol]['analysis'],
            'signals': market_data[symbol]['signals'],
            'timestamp': market_data[symbol]['timestamp']
        }
        return jsonify(response_data)
    return jsonify({'error': 'Data not available'}), 404

@app.route('/api/dashboard')
def get_dashboard():
    dashboard_data = {}
    for symbol in Config.SYMBOLS:
        if market_data[symbol]['analysis']:
            dashboard_data[symbol] = {
                'analysis': market_data[symbol]['analysis'],
                'signals': market_data[symbol]['signals'],
                'timestamp': market_data[symbol]['timestamp']
            }
    return jsonify(dashboard_data)

@app.route('/api/signals/<symbol>')
def get_trading_signals(symbol):
    if symbol in market_data and market_data[symbol]['signals']:
        return jsonify(market_data[symbol]['signals'])
    return jsonify({'error': 'Signals not available'}), 404

@app.route('/api/health')
def health():
    status = {}
    for symbol in Config.SYMBOLS:
        status[symbol] = {
            'last_update': market_data[symbol]['timestamp'],
            'data_available': market_data[symbol]['data'] is not None,
            'signals_available': market_data[symbol]['signals'] is not None
        }
    return jsonify(status)

@app.route('/api/historical/<symbol>')
def get_historical_data(symbol):
    """Get historical data for trend analysis"""
    if hasattr(option_chain_analyzer, 'historical_data') and symbol in option_chain_analyzer.historical_data:
        return jsonify(option_chain_analyzer.historical_data[symbol][-50:])  # Last 50 points
    return jsonify([])

if __name__ == '__main__':
    # Initial data fetch
    print("🚀 Starting Option Chain Analyzer...")
    fetch_and_process_data()
    
    # Setup scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=fetch_and_process_data,
        trigger="interval",
        seconds=Config.REFRESH_INTERVAL,
        id='data_fetcher'
    )
    scheduler.start()
    
    print(f"🔄 Auto-refresh enabled every {Config.REFRESH_INTERVAL} seconds")
    print("🌐 Dashboard available at: http://localhost:5000")
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
    except (KeyboardInterrupt, SystemExit):
        print("\n👋 Shutting down Option Chain Analyzer...")
        scheduler.shutdown()
