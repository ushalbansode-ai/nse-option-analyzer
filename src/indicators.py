"""
Custom Indicators Module
Advanced indicators for option chain analysis
"""

import pandas as pd
import numpy as np
from typing import Dict
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import AnalysisConfig


class OptionIndicators:
    """
    Custom indicators for option chain analysis
    """
    
    @staticmethod
    def calculate_iv_skew(df: pd.DataFrame, spot_price: float) -> Dict:
        """Calculate IV Skew - UNDERRATED indicator"""
        atm_idx = (df['strike'] - spot_price).abs().idxmin()
        atm_strike = df.loc[atm_idx, 'strike']
        
        atm_ce_iv = df.loc[atm_idx, 'CE_IV']
        atm_pe_iv = df.loc[atm_idx, 'PE_IV']
        atm_iv = (atm_ce_iv + atm_pe_iv) / 2
        
        otm_calls = df[df['strike'] > atm_strike].head(5)
        avg_otm_call_iv = otm_calls['CE_IV'].mean()
        
        otm_puts = df[df['strike'] < atm_strike].tail(5)
        avg_otm_put_iv = otm_puts['PE_IV'].mean()
        
        put_skew = ((avg_otm_put_iv - atm_iv) / atm_iv * 100) if atm_iv > 0 else 0
        call_skew = ((avg_otm_call_iv - atm_iv) / atm_iv * 100) if atm_iv > 0 else 0
        
        return {
            'atm_strike': atm_strike,
            'atm_iv': round(atm_iv, 2),
            'put_skew': round(put_skew, 2),
            'call_skew': round(call_skew, 2),
            'skew_direction': 'PUT' if put_skew > call_skew else 'CALL',
            'interpretation': 'Fear' if put_skew > 10 else 'Greed' if call_skew > 10 else 'Neutral'
        }
    
    @staticmethod
    def analyze_liquidity(df: pd.DataFrame) -> Dict:
        """Analyze liquidity using bid-ask spreads"""
        df['CE_spread_pct'] = ((df['CE_ask'] - df['CE_bid']) / df['CE_LTP'] * 100).replace([np.inf, -np.inf], 0)
        df['PE_spread_pct'] = ((df['PE_ask'] - df['PE_bid']) / df['PE_LTP'] * 100).replace([np.inf, -np.inf], 0)
        
        liquid_ce = df[(df['CE_spread_pct'] < AnalysisConfig.MAX_SPREAD_PCT) & 
                       (df['CE_volume'] > AnalysisConfig.MIN_VOLUME)]
        liquid_pe = df[(df['PE_spread_pct'] < AnalysisConfig.MAX_SPREAD_PCT) & 
                       (df['PE_volume'] > AnalysisConfig.MIN_VOLUME)]
        
        avg_ce_spread = df['CE_spread_pct'].mean()
        avg_pe_spread = df['PE_spread_pct'].mean()
        
        return {
            'liquid_ce_strikes': len(liquid_ce),
            'liquid_pe_strikes': len(liquid_pe),
            'avg_ce_spread': round(avg_ce_spread, 2),
            'avg_pe_spread': round(avg_pe_spread, 2),
            'recommendation': 'Good' if len(liquid_ce) > AnalysisConfig.MIN_LIQUID_STRIKES else 'Poor'
        }
    
    @staticmethod
    def calculate_volume_oi_ratio(df: pd.DataFrame) -> Dict:
        """Volume/OI Ratio - Shows fresh activity"""
        df['CE_vol_oi_ratio'] = (df['CE_volume'] / df['CE_OI']).replace([np.inf, -np.inf], 0)
        df['PE_vol_oi_ratio'] = (df['PE_volume'] / df['PE_OI']).replace([np.inf, -np.inf], 0)
        
        high_activity_ce = df[df['CE_vol_oi_ratio'] > AnalysisConfig.HIGH_ACTIVITY_RATIO].nlargest(5, 'CE_volume')
        high_activity_pe = df[df['PE_vol_oi_ratio'] > AnalysisConfig.HIGH_ACTIVITY_RATIO].nlargest(5, 'PE_volume')
        
        return {
            'high_activity_ce_strikes': high_activity_ce['strike'].tolist(),
            'high_activity_pe_strikes': high_activity_pe['strike'].tolist(),
            'avg_ce_ratio': round(df['CE_vol_oi_ratio'].mean(), 3),
            'avg_pe_ratio': round(df['PE_vol_oi_ratio'].mean(), 3),
            'interpretation': 'High momentum' if df['CE_vol_oi_ratio'].mean() > AnalysisConfig.MODERATE_ACTIVITY_RATIO else 'Consolidation'
        }
    
    @staticmethod
    def find_support_resistance(df: pd.DataFrame) -> Dict:
        """Find support/resistance based on OI concentration"""
        df['total_OI'] = df['CE_OI'] + df['PE_OI']
        
        resistance = df.nlargest(3, 'CE_OI')['strike'].tolist()
        support = df.nlargest(3, 'PE_OI')['strike'].tolist()
        
        return {
            'resistance_levels': resistance,
            'support_levels': support,
            'max_oi_strike': int(df.nlargest(1, 'total_OI').iloc[0]['strike'])
        }


if __name__ == "__main__":
    print("Indicators module loaded successfully")
