
# 🎯 NSE Option Trading Signals

[![GitHub Actions](https://github.com/ushalbansode-ai/nse-option-signals/actions/workflows/update_signals.yml/badge.svg)](https://github.com/ushalbansode-ai/nse-option-signals/actions)
[![Live Signals](https://img.shields.io/badge/Live-Signals-brightgreen)](https://ushalbansode-ai.github.io/nse-option-signals/)
[![Update Frequency](https://img.shields.io/badge/Updates-5--min%20during%20market hours-blue)](https://github.com/ushalbansode-ai/nse-option-signals)

Live option buying signals for **Nifty, Bank Nifty, and 20 most liquid F&O stocks** based on real-time option chain data from NSE.

## 🚀 Live Dashboard

**👉 [View Live Signals Dashboard](https://ushalbansode-ai.github.io/nse-option-signals/)**

*Auto-updates every 5 minutes during market hours (9:15 AM - 3:30 PM IST)*

## 📊 What This System Does

- **📈 Real-time Analysis**: Fetches live option chain data from NSE
- **🎯 Focused Strike Selection**: Analyzes ONLY ATM ±5 strikes for maximum efficiency
- **🤖 Smart Signals**: Generates BUY/STRONG BUY signals based on PCR (Put-Call Ratio)
- **⏱️ Auto Updates**: Runs every 5 minutes during market hours via GitHub Actions
- **📱 Live Dashboard**: Professional web interface with auto-refresh

## 🎯 Signal Generation Logic

### PCR-Based Signals
| PCR OI | PCR Volume | Signal | Action |
|--------|------------|--------|---------|
| > 1.5 | > 1.2 | **STRONG BUY** | Buy Call Options |
| > 1.2 | Any | **BUY** | Buy Call Options |
| < 0.6 | < 0.8 | **STRONG BUY** | Buy Put Options |
| < 0.8 | Any | **BUY** | Buy Put Options |
| 0.8-1.2 | Any | **HOLD** | No Action |

### Strike Selection Priority
1. **ATM Strike** - Maximum Gamma, highest liquidity
2. **Near-ATM** (±1 strike) - Balanced risk-reward
3. **Other ±5 strikes** - With distance-based scoring

## 📁 Project Structure

