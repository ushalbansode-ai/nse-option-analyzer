import requests
import pandas as pd
import numpy as np
from datetime import datetime
import time as time_module
import json
import os

print("🚀 ADVANCED NSE OPTION SIGNALS - COMPLETE ANALYSIS")

class AdvancedOptionSignalGenerator:
    def __init__(self):
        self.symbols = [
            "NIFTY", "BANKNIFTY",
            "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK",
            "KOTAKBANK", "HDFC", "BHARTIARTL", "ITC", "SBIN"
        ]

    # ------------------ FETCH OPTION CHAIN ------------------
    def fetch_option_chain(self, symbol):
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
                print(f"❌ Failed to fetch {symbol}: Status {response.status_code}")
                return None

        except Exception as e:
            print(f"❌ Error: {symbol} => {e}")
            return None

    # ------------------ ANALYZE ATM ±5 ------------------
    def analyze_atm_strikes(self, data, symbol):
        if not data or 'records' not in data:
            return None

        records = data['records']
        current_price = records['underlyingValue']
        expiry = records['expiryDates'][0]

        option_data = [
            item for item in records['data']
            if item.get('expiryDate') == expiry
        ]

        if not option_data:
            return None

        strikes = sorted([item['strikePrice'] for item in option_data])
        atm = min(strikes, key=lambda x: abs(x - current_price))

        atm_index = strikes.index(atm)
        start = max(0, atm_index - 5)
        end = min(len(strikes), atm_index + 6)

        selected_strikes = strikes[start:end]

        filtered = [
            row for row in option_data if row["strikePrice"] in selected_strikes
        ]

        return {
            "symbol": symbol,
            "current_price": current_price,
            "atm_strike": atm,
            "expiry": expiry,
            "strikes_analyzed": selected_strikes,
            "data": filtered,
            "all_data": option_data
        }

    # ------------------ PCR ------------------
    def calculate_pcr(self, data):
        ce_oi = pe_oi = ce_vol = pe_vol = 0

        for row in data:
            if "CE" in row:
                ce_oi += row["CE"].get("openInterest", 0)
                ce_vol += row["CE"].get("totalTradedVolume", 0)
            if "PE" in row:
                pe_oi += row["PE"].get("openInterest", 0)
                pe_vol += row["PE"].get("totalTradedVolume", 0)

        pcr_oi = pe_oi / ce_oi if ce_oi > 0 else 0
        pcr_vol = pe_vol / ce_vol if ce_vol > 0 else 0

        return round(pcr_oi, 2), round(pcr_vol, 2)
            # ------------------ STRIKE-WISE ANALYSIS ------------------
    def analyze_strike_strength(self, strike_rows):
        result = []

        for row in strike_rows:
            strike = row["strikePrice"]

            ce = row.get("CE", {})
            pe = row.get("PE", {})

            ce_oi = ce.get("openInterest", 0)
            pe_oi = pe.get("openInterest", 0)
            ce_chg = ce.get("changeinOpenInterest", 0)
            pe_chg = pe.get("changeinOpenInterest", 0)
            ce_vol = ce.get("totalTradedVolume", 0)
            pe_vol = pe.get("totalTradedVolume", 0)

            result.append({
                "strike": strike,

                "ce_oi": ce_oi,
                "pe_oi": pe_oi,

                "ce_chg": ce_chg,
                "pe_chg": pe_chg,

                "ce_vol": ce_vol,
                "pe_vol": pe_vol,

                "ce_strength": ce_oi + ce_chg + ce_vol,
                "pe_strength": pe_oi + pe_chg + pe_vol
            })

        return result
            # ------------------ SIGNAL ENGINE ------------------
    def generate_signal_from_analysis(self, analysis_data,
                                      pcr_thresholds=(1.5, 1.2),
                                      oi_ratio_thresholds=(1.3, 0.7)):
        """
        Generate a BUY/SELL/STRONG signal from analysis_data (ATM ±5).
        - pcr_thresholds: (strong, weak) e.g. (1.5, 1.2)
        - oi_ratio_thresholds: (bull_strong, bear_strong) e.g. (1.3, 0.7)
        Returns: dict with detailed signal or None
        """
        if not analysis_data:
            return None

        # compute PCR and OI summary
        pcr_oi, pcr_vol = self.calculate_pcr(analysis_data.get('all_data', []))

        # compute OI sums in ATM window
        total_ce_oi = sum(int(r.get('CE', {}).get('openInterest', 0) or 0)
                          for r in analysis_data.get('data', []))
        total_pe_oi = sum(int(r.get('PE', {}).get('openInterest', 0) or 0)
                          for r in analysis_data.get('data', []))

        oi_ratio = (total_pe_oi / total_ce_oi) if total_ce_oi > 0 else 0.0

        # scoring counters
        bullish_points = 0
        bearish_points = 0

        # PCR interpretation (higher PCR -> relatively more put interest)
        strong_pcr, weak_pcr = pcr_thresholds
        if pcr_oi >= strong_pcr:
            bullish_points += 2
        elif pcr_oi >= weak_pcr:
            bullish_points += 1

        if pcr_oi <= (1.0 / strong_pcr):  # e.g. very low PCR -> bearish
            bearish_points += 2
        elif pcr_oi <= (1.0 / weak_pcr):
            bearish_points += 1

        # OI ratio interpretation (pe_oi / ce_oi)
        bull_oi_thr, bear_oi_thr = oi_ratio_thresholds
        if oi_ratio >= bull_oi_thr:
            bullish_points += 1
        elif oi_ratio <= bear_oi_thr:
            bearish_points += 1

        # Final decision mapping
        signal_label = None
        option_side = None
        chosen_strike = None
        reason = []

        # Decide signal strength
        if bullish_points >= 3:
            signal_label = "STRONG BUY"
            option_side = "CE"
            reason.append(f"PCR={pcr_oi} (bullish), OI_ratio={oi_ratio:.2f}")
        elif bullish_points >= 2:
            signal_label = "BUY"
            option_side = "CE"
            reason.append(f"PCR={pcr_oi} (mild bullish), OI_ratio={oi_ratio:.2f}")
        elif bearish_points >= 3:
            signal_label = "STRONG SELL"
            option_side = "PE"
            reason.append(f"PCR={pcr_oi} (bearish), OI_ratio={oi_ratio:.2f}")
        elif bearish_points >= 2:
            signal_label = "SELL"
            option_side = "PE"
            reason.append(f"PCR={pcr_oi} (mild bearish), OI_ratio={oi_ratio:.2f}")
        else:
            # No clear directional signal
            return None

        # If we reached here, select optimal strike on chosen side
        chosen_strike = self.select_optimal_strike(analysis_data, option_side)
        if not chosen_strike:
            # fallback: if no candidate on preferred side, try opposite side once
            alt_side = "PE" if option_side == "CE" else "CE"
            chosen_strike = self.select_optimal_strike(analysis_data, alt_side)
            if chosen_strike:
                reason.append(f"Fallback to {alt_side} due to liquidity")
                option_side = alt_side
            else:
                # cannot choose any strike => abort
                return None

        # Build result
        result = {
            "symbol": analysis_data.get("symbol"),
            "signal": signal_label,
            "option_type": option_side,
            "strike_price": chosen_strike.get("strike"),
            "atm_strike": analysis_data.get("atm_strike"),
            "distance_from_atm": chosen_strike.get("distance_from_atm"),
            "option_ltp": chosen_strike.get("ltp"),
            "option_change": chosen_strike.get("change"),
            "oi": chosen_strike.get("oi"),
            "coi": chosen_strike.get("coi"),
            "volume": chosen_strike.get("volume"),
            "iv": chosen_strike.get("iv"),
            "delta": chosen_strike.get("delta"),
            "gamma": chosen_strike.get("gamma"),
            "pcr_oi": pcr_oi,
            "pcr_volume": pcr_vol,
            "oi_ratio": round(oi_ratio, 2),
            "strike_score": chosen_strike.get("score"),
            "selection_reason": chosen_strike.get("selection_reason"),
            "signal_reason": "; ".join(reason),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        return result
            # ------------------ MAIN EXECUTION ENGINE ------------------
    def run_all(self):
        all_signals = []
        dashboard_data = []
        detailed_rows = []

        for symbol in self.symbols:
            print(f"Processing {symbol}...")

            # 1️⃣ Fetch chain
            chain = self.fetch_option_chain(symbol)
            if not chain or "records" not in chain:
                continue

            # 2️⃣ ATM ± window analysis
            analysis = self.analyze_atm_strikes(chain)
            if not analysis:
                continue

            # 3️⃣ Generate signal (from Part-3)
            signal = self.generate_signal_from_analysis(analysis)
            if signal:
                all_signals.append(signal)

            # 4️⃣ Add to dashboard view
            dashboard_data.append({
                "symbol": symbol,
                "underlying": analysis.get("underlying"),
                "atm_strike": analysis.get("atm_strike"),
                "signal": signal.get("signal") if signal else "NO TRADE",
                "option_type": signal.get("option_type") if signal else "-",
                "strike_price": signal.get("strike_price") if signal else "-",
                "pcr_oi": signal.get("pcr_oi") if signal else "-",
                "oi_ratio": signal.get("oi_ratio") if signal else "-",
                "timestamp": signal.get("timestamp") if signal else "-"
            })

            # 5️⃣ Prepare detailed strike-level rows
            for row in analysis["strike_analysis"]:
                detailed_rows.append({
                    "symbol": symbol,
                    "strike": row["strike"],
                    "ce_oi": row["ce_oi"],
                    "pe_oi": row["pe_oi"],
                    "ce_chg": row["ce_chg"],
                    "pe_chg": row["pe_chg"],
                    "ce_vol": row["ce_vol"],
                    "pe_vol": row["pe_vol"],
                    "ce_strength": row["ce_strength"],
                    "pe_strength": row["pe_strength"]
                })

        # ------------------ EXPORT SIGNAL CSV ------------------
        self.save_csv("option_signals.csv", all_signals)

        # ------------------ EXPORT DETAILED STRIKE CSV ------------------
        self.save_csv("detailed_option_data.csv", detailed_rows)

        # ------------------ EXPORT DASHBOARD JSON ------------------
        self.save_json("docs/dashboard.json", dashboard_data)

        print("✅ All processing completed.")
        print(f"Generated {len(all_signals)} trade signals.")

        return {
            "signals": all_signals,
            "dashboard": dashboard_data,
            "detailed": detailed_rows
        }
            # ------------------ FILE WRITING UTILITIES ------------------
    def save_csv(self, filename, rows):
        """
        Save any list of dict rows into a CSV file.
        Automatically creates header from keys.
        """
        if not rows:
            print(f"⚠️ CSV skipped (no rows): {filename}")
            return

        import csv

        try:
            with open(filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

            print(f"📄 CSV saved: {filename} ({len(rows)} rows)")

        except Exception as e:
            print(f"❌ Error writing CSV {filename}: {e}")

    def save_json(self, filename, data):
        """
        Save data (list or dict) into JSON.
        Creates directories if needed.
        """
        import json
        import os

        try:
            # ensure directory exists
            os.makedirs(os.path.dirname(filename), exist_ok=True)

            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            print(f"🟢 JSON saved: {filename}")

        except Exception as e:
            print(f"❌ Error writing JSON {filename}: {e}")
            # ------------------ PART 6 : MAIN RUNNER ------------------

def main():
    print("\n🔵 Starting NSE Option Dashboard Builder...")

    try:
        engine = OptionDashboard()

        # 1. Fetch latest NSE data
        print("🔹 Fetching option chain...")
        engine.fetch_data()

        # 2. Process & filter
        print("🔹 Processing data...")
        engine.process_option_data()

        # 3. Generate BUY signals
        print("🔹 Generating signals...")
        signals = engine.generate_signals()

        # 4. Save dashboard JSON for GitHub Pages
        print("🔹 Saving dashboard data...")
        engine.save_json("docs/dashboard.json", signals)

        print("\n✅ Completed successfully.")
        print("📁 Output generated:")
        print("   • docs/dashboard.json (LIVE dashboard data)")
        print("   • option_signals.csv")
        print("   • detailed_option_data.csv\n")

    except Exception as e:
        print("\n❌ Error:", e)


if __name__ == "__main__":
    main()
    
