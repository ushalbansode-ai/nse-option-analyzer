import requests
import pandas as pd
import numpy as np
from datetime import datetime
import time
import os

class OptionChainAnalyzer:
    def __init__(self):
        self.nse_url = "https://www.nseindia.com/api/option-chain"
        self.symbols = [
            "NIFTY", "BANKNIFTY",
            "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", 
            "KOTAKBANK", "HDFC", "BHARTIARTL", "ITC", "SBIN",
            "ASIANPAINT", "MARUTI", "TATAMOTORS", "TATASTEEL",
            "BAJFINANCE", "WIPRO", "HCLTECH", "LT", "AXISBANK"
        ]
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br'
        }
    
    def fetch_option_chain(self, symbol):
        """Fetch live option chain data from NSE"""
        try:
            url_type = 'indices' if symbol in ['NIFTY','BANKNIFTY'] else 'equities'
            url = f"https://www.nseindia.com/api/option-chain-{url_type}?symbol={symbol}"
            
            session = requests.Session()
            # First request to get cookies
            session.get("https://www.nseindia.com/", headers=self.headers, timeout=10)
            time.sleep(1)
            
            response = session.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"HTTP Error {response.status_code} for {symbol}")
                return None
                
        except Exception as e:
            print(f"Error fetching data for {symbol}: {str(e)}")
            return None

class SignalGenerator:
    def __init__(self):
        self.signals = []
    
    def analyze_option_chain(self, data, symbol):
        """Analyze option chain and generate signals"""
        if not data:
            return None
            
        try:
            records = data['records']
            current_price = records['underlyingValue']
            expiry_dates = data['records']['expiryDates']
            
            # Focus on current week expiry
            current_expiry = expiry_dates[0]
            
            # Get filtered data
            filtered_data = data.get('filtered', {}).get('data', [])
            if not filtered_data:
                filtered_data = data.get('data', [])
            
            # Filter for current expiry
            option_data = [item for item in filtered_data if item.get('expiryDate') == current_expiry]
            
            return self.generate_signals(option_data, symbol, current_price, current_expiry)
            
        except Exception as e:
            print(f"Error analyzing {symbol}: {str(e)}")
            return None
    
    def generate_signals(self, option_data, symbol, current_price, expiry):
        """Generate trading signals"""
        signals = []
        
        if not option_data:
            return signals
        
        # Calculate total OI for PCR
        total_ce_oi = 0
        total_pe_oi = 0
        total_ce_volume = 0
        total_pe_volume = 0
        
        for item in option_data:
            if 'CE' in item and item['CE'] is not None:
                total_ce_oi += item['CE'].get('openInterest', 0)
                total_ce_volume += item['CE'].get('totalTradedVolume', 0)
            if 'PE' in item and item['PE'] is not None:
                total_pe_oi += item['PE'].get('openInterest', 0)
                total_pe_volume += item['PE'].get('totalTradedVolume', 0)
        
        # Calculate PCR
        pcr = total_pe_oi / total_ce_oi if total_ce_oi > 0 else 1
        
        print(f"{symbol}: Current Price={current_price}, PCR={pcr:.2f}")
        
        # Generate signals based on PCR
        if pcr > 1.3:
            strike = self.select_strike(option_data, current_price, 'CE')
            if strike:
                signals.append({
                    'symbol': symbol,
                    'type': 'CE',
                    'signal': 'STRONG BUY',
                    'strike': strike,
                    'current_price': round(current_price, 2),
                    'pcr': round(pcr, 2),
                    'expiry': expiry,
                    'reason': f"High PCR ({pcr:.2f}) - Bullish sentiment"
                })
        
        elif pcr > 1.1:
            strike = self.select_strike(option_data, current_price, 'CE')
            if strike:
                signals.append({
                    'symbol': symbol,
                    'type': 'CE',
                    'signal': 'BUY',
                    'strike': strike,
                    'current_price': round(current_price, 2),
                    'pcr': round(pcr, 2),
                    'expiry': expiry,
                    'reason': f"Moderate PCR ({pcr:.2f}) - Slightly bullish"
                })
        
        elif pcr < 0.7:
            strike = self.select_strike(option_data, current_price, 'PE')
            if strike:
                signals.append({
                    'symbol': symbol,
                    'type': 'PE',
                    'signal': 'STRONG BUY',
                    'strike': strike,
                    'current_price': round(current_price, 2),
                    'pcr': round(pcr, 2),
                    'expiry': expiry,
                    'reason': f"Low PCR ({pcr:.2f}) - Bearish sentiment"
                })
        
        elif pcr < 0.9:
            strike = self.select_strike(option_data, current_price, 'PE')
            if strike:
                signals.append({
                    'symbol': symbol,
                    'type': 'PE',
                    'signal': 'BUY',
                    'strike': strike,
                    'current_price': round(current_price, 2),
                    'pcr': round(pcr, 2),
                    'expiry': expiry,
                    'reason': f"Moderate PCR ({pcr:.2f}) - Slightly bearish"
                })
        
        return signals
    
    def select_strike(self, option_data, current_price, option_type):
        """Select optimal strike price"""
        try:
            strikes = []
            for item in option_data:
                strike_price = item.get('strikePrice')
                if strike_price:
                    strikes.append(strike_price)
            
            if not strikes:
                return None
            
            strikes = sorted(strikes)
            
            # For CE, select strike slightly above current price (OTM)
            if option_type == 'CE':
                target_strike = current_price * 1.01  # 1% OTM
                valid_strikes = [s for s in strikes if s > current_price]
                if valid_strikes:
                    return min(valid_strikes, key=lambda x: abs(x - target_strike))
                else:
                    return max(strikes)
            
            # For PE, select strike slightly below current price (OTM)
            else:
                target_strike = current_price * 0.99  # 1% OTM
                valid_strikes = [s for s in strikes if s < current_price]
                if valid_strikes:
                    return max(valid_strikes, key=lambda x: abs(x - target_strike))
                else:
                    return min(strikes)
                    
        except Exception as e:
            print(f"Error selecting strike: {str(e)}")
            return None

class LiveOptionTradingSystem:
    def __init__(self):
        self.analyzer = OptionChainAnalyzer()
        self.signal_gen = SignalGenerator()
    
    def run_analysis(self):
        """Run analysis for all symbols"""
        all_signals = []
        
        print("Fetching option chain data...")
        
        # Test with fewer symbols first to avoid rate limiting
        test_symbols = self.analyzer.symbols[:3]  # Only first 3 symbols
        
        for symbol in test_symbols:
            print(f"Analyzing {symbol}...")
            
            data = self.analyzer.fetch_option_chain(symbol)
            
            if data:
                signals = self.signal_gen.analyze_option_chain(data, symbol)
                if signals:
                    all_signals.extend(signals)
            else:
                print(f"No data received for {symbol}")
            
            time.sleep(2)  # Rate limiting
        
        return self.format_signals(all_signals)
    
    def format_signals(self, signals):
        """Format signals as DataFrame"""
        if not signals:
            return pd.DataFrame()
        
        df = pd.DataFrame(signals)
        df['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Sort by signal strength
        signal_strength = {'STRONG BUY': 2, 'BUY': 1}
        df['strength_score'] = df['signal'].map(signal_strength)
        df = df.sort_values(['strength_score', 'pcr'], ascending=[False, False])
        
        return df[['symbol', 'signal', 'type', 'strike', 'current_price', 'pcr', 'reason', 'timestamp']]

def main():
    """Main function to run option signals analysis"""
    print("🚀 Starting Live Option Signals Analysis")
    print("=" * 60)
    
    trading_system = LiveOptionTradingSystem()
    
    try:
        signals = trading_system.run_analysis()
        
        print("\n" + "=" * 60)
        print("📊 OPTION BUYING SIGNALS")
        print("=" * 60)
        
        if not signals.empty:
            print(signals.to_string(index=False))
            
            # Save to CSV
            if not os.path.exists('signals'):
                os.makedirs('signals')
            
            csv_filename = f"signals/option_signals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            signals.to_csv(csv_filename, index=False)
            print(f"\n💾 Signals saved to: {csv_filename}")
            
            # Also save a latest.csv for easy access
            signals.to_csv("signals/latest_signals.csv", index=False)
            print("📄 Latest signals saved to: signals/latest_signals.csv")
            
            return 0
        else:
            print("❌ No trading signals generated")
            # Create empty signals directory if doesn't exist
            if not os.path.exists('signals'):
                os.makedirs('signals')
            return 1
            
    except Exception as e:
        print(f"❌ Error in main execution: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
