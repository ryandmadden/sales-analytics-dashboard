"""
KPI Calculator Module
Calculates key performance indicators and metrics
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
from datetime import datetime


class KPICalculator:
    """Calculates KPIs and conversion metrics"""
    
    def __init__(self, column_mapping: Dict[str, str]):
        """
        Initialize KPI calculator
        
        Args:
            column_mapping: Dictionary mapping config keys to column names
        """
        self.column_mapping = column_mapping
    
    def calculate_totals(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate total metrics
        
        Args:
            df: DataFrame with individual's data
            
        Returns:
            Dict: Total metrics
        """
        totals = {
            'doors_knocked': df[self.column_mapping['doors_knocked']].sum(),
            'homeowners_talked': df[self.column_mapping['homeowners_talked']].sum(),
            'qualified_leads': df[self.column_mapping['qualified_leads']].sum(),
            'appointments_set': df[self.column_mapping['appointments_set']].sum()
        }
        
        return totals
    
    def calculate_conversion_rates(self, totals: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate conversion rates between stages
        
        Args:
            totals: Dictionary of total metrics
            
        Returns:
            Dict: Conversion rates (as percentages)
        """
        rates = {}
        
        # Talk rate: homeowners talked / doors knocked
        if totals['doors_knocked'] > 0:
            rates['talk_rate'] = (
                totals['homeowners_talked'] / totals['doors_knocked'] * 100
            )
        else:
            rates['talk_rate'] = 0.0
        
        # Qualification rate: qualified leads / homeowners talked
        if totals['homeowners_talked'] > 0:
            rates['qualification_rate'] = (
                totals['qualified_leads'] / totals['homeowners_talked'] * 100
            )
        else:
            rates['qualification_rate'] = 0.0
        
        # Appointment rate: appointments / qualified leads
        if totals['qualified_leads'] > 0:
            rates['appointment_rate'] = (
                totals['appointments_set'] / totals['qualified_leads'] * 100
            )
        else:
            rates['appointment_rate'] = 0.0
        
        # Overall conversion: appointments / doors knocked
        if totals['doors_knocked'] > 0:
            rates['overall_conversion'] = (
                totals['appointments_set'] / totals['doors_knocked'] * 100
            )
        else:
            rates['overall_conversion'] = 0.0
        
        return rates
    
    def calculate_daily_trends(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate daily aggregated metrics
        
        Args:
            df: DataFrame with individual's data
            
        Returns:
            pd.DataFrame: Daily aggregated metrics
        """
        timestamp_col = self.column_mapping['timestamp']
        
        # Create date column (without time)
        df_copy = df.copy()
        df_copy['date'] = df_copy[timestamp_col].dt.date
        
        # Aggregate by date
        daily_agg = df_copy.groupby('date').agg({
            self.column_mapping['doors_knocked']: 'sum',
            self.column_mapping['homeowners_talked']: 'sum',
            self.column_mapping['qualified_leads']: 'sum',
            self.column_mapping['appointments_set']: 'sum'
        }).reset_index()
        
        # Sort by date
        daily_agg = daily_agg.sort_values('date')
        
        return daily_agg
    
    def calculate_weekly_trends(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate weekly aggregated metrics
        
        Args:
            df: DataFrame with individual's data
            
        Returns:
            pd.DataFrame: Weekly aggregated metrics
        """
        timestamp_col = self.column_mapping['timestamp']
        
        # Create week column
        df_copy = df.copy()
        df_copy['week'] = df_copy[timestamp_col].dt.to_period('W')
        
        # Aggregate by week
        weekly_agg = df_copy.groupby('week').agg({
            self.column_mapping['doors_knocked']: 'sum',
            self.column_mapping['homeowners_talked']: 'sum',
            self.column_mapping['qualified_leads']: 'sum',
            self.column_mapping['appointments_set']: 'sum'
        }).reset_index()
        
        # Convert week period to string for display
        weekly_agg['week'] = weekly_agg['week'].astype(str)
        
        return weekly_agg
    
    def calculate_team_comparison(
        self,
        individual_totals: Dict[str, float],
        team_df: pd.DataFrame
    ) -> Dict[str, Dict[str, float]]:
        """
        Compare individual performance to team averages
        
        Args:
            individual_totals: Individual's total metrics
            team_df: DataFrame with all team members' aggregated data
            
        Returns:
            Dict: Comparison metrics
        """
        # Calculate team averages
        team_averages = {
            'doors_knocked': team_df[self.column_mapping['doors_knocked']].mean(),
            'homeowners_talked': team_df[self.column_mapping['homeowners_talked']].mean(),
            'qualified_leads': team_df[self.column_mapping['qualified_leads']].mean(),
            'appointments_set': team_df[self.column_mapping['appointments_set']].mean()
        }
        
        # Calculate differences
        comparison = {}
        for metric in individual_totals.keys():
            individual_val = individual_totals[metric]
            team_avg = team_averages[metric]
            
            if team_avg > 0:
                percent_diff = ((individual_val - team_avg) / team_avg) * 100
            else:
                percent_diff = 0.0
            
            comparison[metric] = {
                'individual': individual_val,
                'team_average': team_avg,
                'percent_difference': percent_diff
            }
        
        return comparison
    
    def get_summary_stats(self, df: pd.DataFrame) -> Dict:
        """
        Get summary statistics for the data
        
        Args:
            df: DataFrame with data
            
        Returns:
            Dict: Summary statistics
        """
        timestamp_col = self.column_mapping['timestamp']
        
        stats = {
            'total_entries': len(df),
            'date_range': {
                'start': df[timestamp_col].min().strftime('%Y-%m-%d'),
                'end': df[timestamp_col].max().strftime('%Y-%m-%d')
            },
            'days_active': df[timestamp_col].dt.date.nunique()
        }
        
        return stats

