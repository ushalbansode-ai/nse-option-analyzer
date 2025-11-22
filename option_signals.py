import requests
import pandas as pd
import numpy as np
from datetime import datetime, time
import time as time_module
import json
import os

print("🚀 STARTING OPTION SIGNALS SCRIPT - DEBUG VERSION")

class FocusedOptionSignalGenerator:
    def __init__(self):
        self.symbols = ["NIFTY", "BANKNIFTY"]  # Test with just 2 symbols first
        print(f"✅ Initialized with symbols: {self.symbols}")
        
    def fetch_option_chain(self, symbol):
        """Fetch complete option chain data from NSE"""
        try:
            print(f"🔗 Fetching data for {symbol}...")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            if symbol in ['NIFTY', 'BANKNIFTY']:
                url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
            else:
                url = f"https://www.nseindia.com/api/option-chain-equities?symbol={symbol}"
            
            session = requests.Session()
            session.get("https://www.nseindia.com", headers=headers, timeout=10)
            response = session.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ Successfully fetched {symbol}")
                data = response.json()
                print(f"📊 Records found: {len(data['records']['data'])}")
                return data
            else:
                print(f"❌ Failed to fetch {symbol}: Status {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error fetching {symbol}: {e}")
            return None
    
    def run_analysis(self):
        """Main analysis function"""
        print("🎯 Starting analysis...")
        
        all_signals = []
        detailed_data = []
        
        for symbol in self.symbols:
            print(f"📊 Analyzing {symbol}...")
            
            # Fetch option chain data
            data = self.fetch_option_chain(symbol)
            
            if data and 'records' in data:
                current_price = data['records']['underlyingValue']
                print(f"💰 {symbol} Current Price: {current_price}")
                
                # Create a simple test signal
                test_signal = {
                    'symbol': symbol,
                    'signal': 'BUY',
                    'option_type': 'CE',
                    'strike_price': round(current_price * 1.01, -2),
                    'current_price': current_price,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'reason': 'Test signal - NSE connection working'
                }
                all_signals.append(test_signal)
                
                detailed_data.append({
                    'symbol': symbol,
                    'current_price': current_price,
                    'status': 'Success',
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                print(f"✅ Created test signal for {symbol}")
            else:
                print(f"❌ No data for {symbol}")
            
            time_module.sleep(1)
        
        print(f"📈 Generated {len(all_signals)} signals")
        return all_signals, detailed_data

def main():
    print("🎯 MAIN FUNCTION STARTED")
    
    generator = FocusedOptionSignalGenerator()
    
    # Run analysis
    signals, detailed_data = generator.run_analysis()
    
    # Save signals to CSV
    if signals:
        df_signals = pd.DataFrame(signals)
        df_signals.to_csv("option_signals.csv", index=False)
        print("✅ option_signals.csv created successfully!")
        print(f"📄 File content: {len(df_signals)} rows")
    else:
        print("❌ No signals to save")
        # Create empty file anyway
        pd.DataFrame().to_csv("option_signals.csv", index=False)
        print("✅ Created empty option_signals.csv")
    
    # Save detailed data
    if detailed_data:
        df_detailed = pd.DataFrame(detailed_data)
        df_detailed.to_csv("detailed_option_data.csv", index=False)
        print("✅ detailed_option_data.csv created successfully!")
    else:
        print("❌ No detailed data to save")
        pd.DataFrame().to_csv("detailed_option_data.csv", index=False)
        print("✅ Created empty detailed_option_data.csv")
    
    # Generate HTML report
    try:
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>NSE Option Signals - TEST</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h1>🎯 NSE Option Trading Signals - TEST</h1>
            <p>Last Updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            <p>This is a test file to verify the script is working.</p>
        """
        
        if signals:
            df = pd.DataFrame(signals)
            html_content += df.to_html(index=False)
        else:
            html_content += "<p>No signals generated</p>"
        
        html_content += "</body></html>"
        
        with open("index.html", "w") as f:
            f.write(html_content)
        print("✅ index.html created successfully!")
    except Exception as e:
        print(f"❌ Error creating HTML: {e}")
    
    print("🎯 MAIN FUNCTION COMPLETED")
    return signals, detailed_data

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 SCRIPT EXECUTION STARTED")
    print("=" * 50)
    
    main()
    
    print("=" * 50)
    print("✅ SCRIPT EXECUTION COMPLETED")
    print("=" * 50)
    
    # List files to verify creation
    print("📁 Current directory files:")
    files = os.listdir('.')
    for file in files:
        print(f"   {file}")
