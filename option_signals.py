import requests
import pandas as pd
import numpy as np
from datetime import datetime, time
import time as time_module
import json
import os

print("🛰️ ADVANCED NSE OPTION SIGNALS - COMPLETE ANALYSIS")

class AdvancedOptionSignalGenerator:
    def __init__(self):
        self.symbols = [
            "NIFTY", "BANKNIFTY",
            "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK",
            "KOTAKBANK", "HDFC", "BHARTIARTL", "ITC", "SBIN"
        ]

    def fetch_option_chain(self, symbol):
        """Fetch option chain from NSE"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
            }

            session = requests.Session()
            session.get("https://www.nseindia.com", headers=headers, timeout=10)

            if symbol in ['NIFTY', 'BANKNIFTY']:
                url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
            else:
                url = f"https://www.nseindia.com/api/option-chain-equities?symbol={symbol}"

            response = session.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Failed {symbol}: {response.status_code}")
                return None

        except Exception as e:
            print(f"❌ Error fetching {symbol}: {e}")
            return None
                def analyze_atm_strikes(self, data, symbol):
        if not data or 'records' not in data:
            return None

        records = data['records']
        current_price = records['underlyingValue']
        expiry_dates = records['expiryDates']
        current_expiry = expiry_dates[0]

        option_data = [
            item for item in data['records']['data']
            if item.get('expiryDate') == current_expiry
        ]

        if not option_data:
            return None

        strikes = [item['strikePrice'] for item in option_data]
        atm_strike = min(strikes, key=lambda x: abs(x - current_price))

        all_strikes = sorted(strikes)
        atm_index = all_strikes.index(atm_strike)

        start = max(0, atm_index - 5)
        end = min(len(all_strikes), atm_index + 6)

        relevant_strikes = all_strikes[start:end]

        relevant_data = [
            item for item in option_data
            if item['strikePrice'] in relevant_strikes
        ]

        return {
            "symbol": symbol,
            "current_price": current_price,
            "atm_strike": atm_strike,
            "expiry": current_expiry,
            "strikes_analyzed": relevant_strikes,
            "data": relevant_data,
            "all_data": option_data
        }

    def calculate_pcr(self, data):
        total_ce_oi = total_pe_oi = 0
        total_ce_vol = total_pe_vol = 0

        for row in data:
            if 'CE' in row:
                ce = row['CE']
                total_ce_oi += ce.get('openInterest', 0)
                total_ce_vol += ce.get('totalTradedVolume', 0)

            if 'PE' in row:
                pe = row['PE']
                total_pe_oi += pe.get('openInterest', 0)
                total_pe_vol += pe.get('totalTradedVolume', 0)

        pcr_oi = total_pe_oi / total_ce_oi if total_ce_oi else 0
        pcr_vol = total_pe_vol / total_ce_vol if total_ce_vol else 0

        return round(pcr_oi, 2), round(pcr_vol, 2)
            def select_optimal_strike(self, analysis_data, option_type):
        """Select optimal strike from ATM ±5 with multi-parameter scoring"""
        if not analysis_data:
            return None

        current_price = analysis_data['current_price']
        atm_strike = analysis_data['atm_strike']
        relevant_data = analysis_data['data']
        strikes_list = analysis_data['strikes_analyzed']

        candidate_strikes = []

        for item in relevant_data:
            strike = item['strikePrice']

            # Calculate index distance from ATM in the reduced strike list
            try:
                strike_index = strikes_list.index(strike)
                atm_index = strikes_list.index(atm_strike)
            except ValueError:
                continue
            distance_from_atm = abs(strike_index - atm_index)

            if option_type == 'CE':
                if 'CE' in item and strike >= current_price:  # OTM or ATM CE
                    ce_data = item['CE']
                    candidate_strikes.append({
                        'strike': strike,
                        'distance_from_atm': distance_from_atm,
                        'is_atm': strike == atm_strike,
                        'is_near_atm': distance_from_atm <= 1,
                        'oi': ce_data.get('openInterest', 0),
                        'coi': ce_data.get('changeinOpenInterest', 0),
                        'volume': ce_data.get('totalTradedVolume', 0),
                        'iv': ce_data.get('impliedVolatility', 0),
                        'delta': ce_data.get('delta', 0),
                        'gamma': ce_data.get('gamma', 0),
                        'ltp': ce_data.get('lastPrice', 0),
                        'change': ce_data.get('change', 0),
                        'change_percentage': ce_data.get('pChange', 0)
                    })
            else:  # PE
                if 'PE' in item and strike <= current_price:  # OTM or ATM PE
                    pe_data = item['PE']
                    candidate_strikes.append({
                        'strike': strike,
                        'distance_from_atm': distance_from_atm,
                        'is_atm': strike == atm_strike,
                        'is_near_atm': distance_from_atm <= 1,
                        'oi': pe_data.get('openInterest', 0),
                        'coi': pe_data.get('changeinOpenInterest', 0),
                        'volume': pe_data.get('totalTradedVolume', 0),
                        'iv': pe_data.get('impliedVolatility', 0),
                        'delta': pe_data.get('delta', 0),
                        'gamma': pe_data.get('gamma', 0),
                        'ltp': pe_data.get('lastPrice', 0),
                        'change': pe_data.get('change', 0),
                        'change_percentage': pe_data.get('pChange', 0)
                    })

        if not candidate_strikes:
            return None

        # Multi-parameter scoring
        for candidate in candidate_strikes:
            score = 0.0

            # Priority 1: Proximity to ATM (weighted strongly)
            if candidate['is_atm']:
                score += 60.0
            elif candidate['is_near_atm']:
                score += 50.0
            else:
                score += max(0.0, 40.0 - (candidate['distance_from_atm'] * 5.0))

            # Priority 2: OI and COI (weight)
            oi_score = min(candidate['oi'] / 10000.0, 5.0)
            coi_score = (candidate['coi'] / 500.0) if candidate['coi'] else 0.0
            score += (oi_score * 2.0) + (coi_score * 1.0)  # slightly amplify OI

            # Priority 3: Volume confirmation
            volume_score = min(candidate['volume'] / 1000.0, 3.0)
            score += volume_score

            # Priority 4: IV (lower IV slightly preferred for buying)
            iv_val = candidate.get('iv') or 0.0
            iv_score = max(0.0, 5.0 - (float(iv_val) / 5.0))
            score += iv_score

            # Priority 5: Price momentum
            if candidate.get('change_percentage', 0) > 0:
                score += 2.0

            candidate['score'] = round(score, 2)
            candidate['selection_reason'] = self.get_selection_reason(candidate)

        # Select strike with highest score; prefer those with real volume/oi if ties
        candidate_strikes.sort(key=lambda x: (x['score'], x['volume']), reverse=True)
        best_strike = candidate_strikes[0]
        return best_strike

    def get_selection_reason(self, candidate):
        """Generate detailed selection reason"""
        reasons = []
        if candidate.get('is_atm'):
            reasons.append("ATM Strike")
        elif candidate.get('is_near_atm'):
            reasons.append("Near-ATM")
        else:
            reasons.append(f"{candidate.get('distance_from_atm')} steps from ATM")

        coi = candidate.get('coi', 0)
        if coi > 0:
            reasons.append("Fresh Long Buildup")
        elif coi < 0:
            reasons.append("Long Unwinding")

        if candidate.get('volume', 0) > 1000:
            reasons.append("High Volume")

        iv = candidate.get('iv') or 0
        if iv and iv < 20:
            reasons.append("Low IV")

        return " | ".join(reasons)
            def generate_advanced_signal(self, analysis_data):
        """Generate signals using multiple parameters"""
        if not analysis_data:
            return None

        symbol = analysis_data['symbol']
        current_price = analysis_data['current_price']
        atm_strike = analysis_data['atm_strike']

        # Calculate PCR
        pcr_oi, pcr_volume = self.calculate_pcr(analysis_data['all_data'])

        # OI buildup summary in ATM window
        total_ce_oi = sum(item['CE']['openInterest'] for item in analysis_data['data'] if 'CE' in item)
        total_pe_oi = sum(item['PE']['openInterest'] for item in analysis_data['data'] if 'PE' in item)
        oi_ratio = (total_pe_oi / total_ce_oi) if total_ce_oi else 0.0

        signal = "HOLD"
        option_type = None
        strike_data = None
        reason = ""

        bullish_conditions = 0
        bearish_conditions = 0

        # PCR conditions (interpreting higher PCR as more put interest)
        if pcr_oi > 1.5:
            bullish_conditions += 2
        elif pcr_oi > 1.2:
            bullish_conditions += 1

        if pcr_oi < 0.6:
            bearish_conditions += 2
        elif pcr_oi < 0.8:
            bearish_conditions += 1

        # OI ratio conditions
        if oi_ratio > 1.3:
            bullish_conditions += 1
        elif oi_ratio < 0.7:
            bearish_conditions += 1

        # Final decision
        if bullish_conditions >= 3:
            signal = "STRONG BUY"
            option_type = "CE"
            strike_data = self.select_optimal_strike(analysis_data, 'CE')
            reason = f"Strong Bullish: PCR({pcr_oi}), OI_Ratio({oi_ratio:.2f})"
        elif bullish_conditions >= 2:
            signal = "BUY"
            option_type = "CE"
            strike_data = self.select_optimal_strike(analysis_data, 'CE')
            reason = f"Bullish: PCR({pcr_oi}), OI_Ratio({oi_ratio:.2f})"
        elif bearish_conditions >= 3:
            signal = "STRONG SELL"
            option_type = "PE"
            strike_data = self.select_optimal_strike(analysis_data, 'PE')
            reason = f"Strong Bearish: PCR({pcr_oi}), OI_Ratio({oi_ratio:.2f})"
        elif bearish_conditions >= 2:
            signal = "SELL"
            option_type = "PE"
            strike_data = self.select_optimal_strike(analysis_data, 'PE')
            reason = f"Bearish: PCR({pcr_oi}), OI_Ratio({oi_ratio:.2f})"
        else:
            return None  # No clear signal

        if strike_data:
            return {
                'symbol': symbol,
                'signal': signal,
                'option_type': option_type,
                'strike_price': strike_data['strike'],
                'current_price': current_price,
                'atm_strike': atm_strike,
                'distance_from_atm': strike_data['distance_from_atm'],
                'option_ltp': strike_data['ltp'],
                'option_change': strike_data['change'],
                'option_change_percentage': strike_data['change_percentage'],
                'oi': strike_data['oi'],
                'coi': strike_data['coi'],
                'volume': strike_data['volume'],
                'iv': strike_data['iv'],
                'delta': strike_data['delta'],
                'gamma': strike_data['gamma'],
                'pcr_oi': pcr_oi,
                'pcr_volume': pcr_volume,
                'oi_ratio': round(oi_ratio, 2),
                'strike_score': strike_data['score'],
                'selection_reason': strike_data['selection_reason'],
                'signal_reason': reason,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

        return None

    def run_complete_analysis(self):
        """Run complete analysis with all parameters"""
        print("🎯 RUNNING COMPLETE OPTION CHAIN ANALYSIS...")
        print("📊 Parameters: OI, COI, Price, Change, IV, Delta, Gamma, ATM±5")
        print("=" * 80)

        all_signals = []
        market_data = []

        for symbol in self.symbols:
            print(f"🔍 Analyzing {symbol} (ATM ±5 strikes)...")
            data = self.fetch_option_chain(symbol)

            if data:
                analysis_data = self.analyze_atm_strikes(data, symbol)
                if analysis_data:
                    strikes = analysis_data['strikes_analyzed']
                    print(f"   🎯 ATM: {analysis_data['atm_strike']}, Range: {strikes[0]} to {strikes[-1]}")
                    signal = self.generate_advanced_signal(analysis_data)
                    if signal:
                        all_signals.append(signal)
                        print(f"   ✅ {signal['signal']} {signal['option_type']} at {signal['strike_price']}")
                        print(f"   📍 {signal['selection_reason']}")
                        print(f"   💰 LTP: {signal['option_ltp']}, OI: {signal['oi']:,}, COI: {signal['coi']:+,}")
                    # store market overview
                    market_data.append({
                        'symbol': symbol,
                        'current_price': analysis_data['current_price'],
                        'atm_strike': analysis_data['atm_strike'],
                        'strikes_analyzed': len(strikes),
                        # pcr values saved in signal when exists
                        'pcr_oi': signal['pcr_oi'] if signal else 0,
                        'pcr_volume': signal['pcr_volume'] if signal else 0,
                        'oi_ratio': signal['oi_ratio'] if signal else 0,
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                else:
                    print(f"   ❌ No analysis data for {symbol}")
            else:
                print(f"   ❌ Failed to fetch data for {symbol}")

            print("-" * 50)
            time_module.sleep(1)

        print(f"📊 Analysis Complete: {len(all_signals)} signals generated")
        return all_signals, market_data
        def generate_advanced_dashboard(signals, market_data, out_path="index.html"):
    """Generate comprehensive trading dashboard HTML and save to out_path"""
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Advanced NSE Option Signals - Complete Analysis</title>
    <meta http-equiv="refresh" content="300">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; }}
        .signal-card {{ background: white; padding: 12px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.08); }}
        .strong-buy {{ border-left: 5px solid #28a745; }}
        .buy {{ border-left: 5px solid #17a2b8; }}
        table {{ width: 100%; border-collapse: collapse; background: white; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f8f9fa; }}
        .param-badge {{ background: #e9ecef; padding: 4px 8px; border-radius: 10px; font-size: 12px; margin: 2px; }}
        .positive {{ color: #28a745; }}
        .negative {{ color: #dc3545; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Advanced NSE Option Signals</h1>
            <p>Complete Analysis: OI, COI, Price, IV, Delta, Gamma, ATM ±5 Strikes</p>
            <p><strong>Last Updated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
"""

    if signals:
        html += """
        <h2>🛰️ Active Trading Signals</h2>
        <table>
            <thead>
                <tr>
                    <th>Symbol</th><th>Signal</th><th>Option</th><th>Strike</th><th>ATM</th>
                    <th>LTP</th><th>Change</th><th>OI</th><th>COI</th><th>IV</th>
                    <th>Delta</th><th>PCR</th><th>Score</th><th>Reason</th>
                </tr>
            </thead>
            <tbody>
        """
        for s in signals:
            signal_class = "strong-buy" if "STRONG" in s['signal'] else "buy"
            change_class = "positive" if s.get('option_change', 0) > 0 else "negative"
            coi_class = "positive" if s.get('coi', 0) > 0 else "negative"
            html += f"""
                <tr class="{signal_class}">
                    <td><strong>{s['symbol']}</strong></td>
                    <td><strong>{s['signal']}</strong></td>
                    <td>{s['option_type']}</td>
                    <td>{s['strike_price']}</td>
                    <td>{s['atm_strike']}</td>
                    <td>{s['option_ltp']}</td>
                    <td class="{change_class}">{s['option_change']:+.2f}</td>
                    <td>{s['oi']:,}</td>
                    <td class="{coi_class}">{s['coi']:+,}</td>
                    <td>{s['iv']}</td>
                    <td>{s['delta']}</td>
                    <td>{s['pcr_oi']}</td>
                    <td>{s['strike_score']}</td>
                    <td><small>{s['selection_reason']}</small></td>
                </tr>
            """
        html += """
            </tbody>
        </table>
        """
    else:
        html += """
        <div class="signal-card">
            <h3>⏸️ No Strong Signals Detected</h3>
            <p>Market is neutral. Monitoring ATM ±5 strikes...</p>
        </div>
        """

    if market_data:
        html += """
        <h2>📊 Market Overview (ATM ±5 Analysis)</h2>
        <table>
            <thead><tr><th>Symbol</th><th>Current Price</th><th>ATM</th><th>Strikes</th><th>PCR OI</th><th>OI Ratio</th><th>Signal Strength</th></tr></thead>
            <tbody>
        """
        for d in market_data:
            pcr_oi = d.get('pcr_oi', 0)
            if pcr_oi > 1.5:
                strength = "🟢 Very Bullish"
            elif pcr_oi > 1.2:
                strength = "🟡 Bullish"
            elif pcr_oi < 0.6:
                strength = "🔴 Very Bearish"
            elif pcr_oi < 0.8:
                strength = "🟠 Bearish"
            else:
                strength = "⚪ Neutral"
            html += f"""
                <tr>
                    <td>{d['symbol']}</td>
                    <td>{d['current_price']}</td>
                    <td>{d['atm_strike']}</td>
                    <td>{d['strikes_analyzed']} strikes</td>
                    <td>{d.get('pcr_oi',0)}</td>
                    <td>{d.get('oi_ratio',0)}</td>
                    <td>{strength}</td>
                </tr>
            """
        html += "</tbody></table>"

    html += """
        </div>
    </body>
    </html>
    """

    # save to file
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ Advanced dashboard generated: {out_path}")


def main():
    print("=" * 70)
    print("🛰️ ADVANCED NSE OPTION SIGNALS - COMPLETE ANALYSIS (RUN)")
    print("=" * 70)

    generator = AdvancedOptionSignalGenerator()
    signals, market_data = generator.run_complete_analysis()

    # Save CSVs
    if signals:
        df_signals = pd.DataFrame(signals)
        df_signals.to_csv("option_signals.csv", index=False)
        print(f"✅ Detailed signals saved: {len(signals)} signals")
    else:
        empty_df = pd.DataFrame(columns=[
            'symbol', 'signal', 'option_type', 'strike_price', 'current_price',
            'atm_strike', 'distance_from_atm', 'option_ltp', 'option_change',
            'option_change_percentage', 'oi', 'coi', 'volume', 'iv', 'delta',
            'gamma', 'pcr_oi', 'pcr_volume', 'oi_ratio', 'strike_score',
            'selection_reason', 'signal_reason', 'timestamp'
        ])
        empty_df.to_csv("option_signals.csv", index=False)
        print("❔ No strong signals - empty CSV written")

    if market_data:
        df_market = pd.DataFrame(market_data)
        df_market.to_csv("detailed_option_data.csv", index=False)
        print(f"✅ Market data saved: {len(market_data)} symbols")

    # Generate dashboard HTML saved to docs/index.html for GitHub Pages
    # ensure docs folder exists
    os.makedirs("docs", exist_ok=True)
    generate_advanced_dashboard(signals, market_data, out_path="docs/index.html")


if __name__ == "__main__":
    main()
    
