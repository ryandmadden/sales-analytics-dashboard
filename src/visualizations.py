"""
Visualization Module
Generates charts and graphs for KPI display
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
from pathlib import Path
import os


class ChartGenerator:
    """Generates visualization charts for KPIs"""
    
    def __init__(
        self,
        output_dir: str,
        dpi: int = 300,
        figure_size: Tuple[int, int] = (12, 8),
        colors: Dict[str, str] = None
    ):
        """
        Initialize chart generator
        
        Args:
            output_dir: Directory to save charts
            dpi: Resolution for saved charts
            figure_size: Figure size in inches (width, height)
            colors: Color scheme dictionary
        """
        self.output_dir = output_dir
        self.dpi = dpi
        self.figure_size = figure_size
        
        # Default color scheme
        self.colors = colors or {
            'primary': '#2E86AB',
            'secondary': '#A23B72',
            'success': '#06A77D',
            'warning': '#F18F01',
            'danger': '#C73E1D'
        }
        
        # Set seaborn style
        sns.set_style("whitegrid")
        sns.set_palette("husl")
    
    def _ensure_output_dir(self, person_name: str) -> Path:
        """
        Create output directory for person if it doesn't exist
        
        Args:
            person_name: Name of the lead generator
            
        Returns:
            Path: Path to output directory
        """
        # Create safe filename from person name
        safe_name = "".join(c if c.isalnum() or c in (' ', '_') else '_' 
                           for c in person_name).strip().replace(' ', '_').lower()
        
        # Add timestamp to directory name
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y-%m-%d')
        
        output_path = Path(self.output_dir) / f"{safe_name}_{timestamp}"
        output_path.mkdir(parents=True, exist_ok=True)
        
        return output_path
    
    def generate_kpi_bar_chart(
        self,
        totals: Dict[str, float],
        person_name: str,
        date_range: str
    ) -> str:
        """
        Generate bar chart for 4 main KPIs
        
        Args:
            totals: Dictionary with total metrics
            person_name: Name of lead generator
            date_range: Date range string for title
            
        Returns:
            str: Path to saved chart
        """
        fig, ax = plt.subplots(figsize=self.figure_size)
        
        # Prepare data
        metrics = ['Doors\nKnocked', 'Homeowners\nTalked', 
                   'Qualified\nLeads', 'Appointments\nSet']
        values = [
            totals['doors_knocked'],
            totals['homeowners_talked'],
            totals['qualified_leads'],
            totals['appointments_set']
        ]
        colors_list = [
            self.colors['primary'],
            self.colors['warning'],
            self.colors['success'],
            self.colors['secondary']
        ]
        
        # Create bars
        bars = ax.bar(metrics, values, color=colors_list, alpha=0.8, edgecolor='black', linewidth=1.5)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}',
                   ha='center', va='bottom', fontsize=14, fontweight='bold')
        
        # Styling
        ax.set_title(f'Performance Metrics - {person_name}\n{date_range}', 
                    fontsize=18, fontweight='bold', pad=20)
        ax.set_ylabel('Count', fontsize=14, fontweight='bold')
        ax.set_xlabel('Metrics', fontsize=14, fontweight='bold')
        ax.tick_params(labelsize=12)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        
        # Save
        output_path = self._ensure_output_dir(person_name)
        filepath = output_path / 'kpi_metrics.png'
        plt.savefig(filepath, dpi=self.dpi, bbox_inches='tight')
        plt.close()
        
        return str(filepath)
    
    def generate_conversion_funnel(
        self,
        totals: Dict[str, float],
        rates: Dict[str, float],
        person_name: str,
        date_range: str
    ) -> str:
        """
        Generate funnel chart showing conversion through stages
        
        Args:
            totals: Dictionary with total metrics
            rates: Dictionary with conversion rates
            person_name: Name of lead generator
            date_range: Date range string
            
        Returns:
            str: Path to saved chart
        """
        fig, ax = plt.subplots(figsize=self.figure_size)
        
        # Funnel data
        stages = ['Doors\nKnocked', 'Homeowners\nTalked', 'Qualified\nLeads', 'Appointments\nSet']
        values = [
            totals['doors_knocked'],
            totals['homeowners_talked'],
            totals['qualified_leads'],
            totals['appointments_set']
        ]
        
        # Calculate funnel widths (normalized)
        if values[0] > 0:
            normalized_values = [v / values[0] for v in values]
        else:
            normalized_values = [0, 0, 0, 0]
        
        # Create horizontal funnel
        colors_list = [self.colors['primary'], self.colors['warning'], 
                      self.colors['success'], self.colors['secondary']]
        
        y_positions = list(range(len(stages)))
        
        # Draw funnel bars
        bars = ax.barh(y_positions, normalized_values, color=colors_list, 
                      alpha=0.8, edgecolor='black', linewidth=2)
        
        # Add labels with values and conversion rates
        for i, (bar, value) in enumerate(zip(bars, values)):
            width = bar.get_width()
            # Value label
            ax.text(width + 0.02, bar.get_y() + bar.get_height()/2,
                   f'{int(value)}',
                   ha='left', va='center', fontsize=13, fontweight='bold')
            
            # Conversion rate label (skip first stage)
            if i > 0:
                rate_key = ['talk_rate', 'qualification_rate', 'appointment_rate'][i-1]
                rate_val = rates[rate_key]
                ax.text(width/2, bar.get_y() + bar.get_height()/2,
                       f'{rate_val:.1f}%',
                       ha='center', va='center', fontsize=11, 
                       fontweight='bold', color='white')
        
        # Styling
        ax.set_yticks(y_positions)
        ax.set_yticklabels(stages, fontsize=12)
        ax.set_xlim(0, 1.2)
        ax.set_xlabel('Conversion Progress', fontsize=14, fontweight='bold')
        ax.set_title(f'Sales Funnel - {person_name}\n{date_range}', 
                    fontsize=18, fontweight='bold', pad=20)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.set_xticks([])
        ax.grid(False)
        
        plt.tight_layout()
        
        # Save
        output_path = self._ensure_output_dir(person_name)
        filepath = output_path / 'conversion_funnel.png'
        plt.savefig(filepath, dpi=self.dpi, bbox_inches='tight')
        plt.close()
        
        return str(filepath)
    
    def generate_daily_trends(
        self,
        daily_df: pd.DataFrame,
        column_mapping: Dict[str, str],
        person_name: str,
        date_range: str
    ) -> str:
        """
        Generate line chart showing daily trends
        
        Args:
            daily_df: DataFrame with daily aggregated data
            column_mapping: Column name mapping
            person_name: Name of lead generator
            date_range: Date range string
            
        Returns:
            str: Path to saved chart
        """
        fig, ax = plt.subplots(figsize=self.figure_size)
        
        # Convert date to datetime for plotting
        daily_df = daily_df.copy()
        daily_df['date'] = pd.to_datetime(daily_df['date'])
        
        # Plot lines for each metric
        metrics = [
            ('doors_knocked', 'Doors Knocked', self.colors['primary']),
            ('homeowners_talked', 'Homeowners Talked', self.colors['warning']),
            ('qualified_leads', 'Qualified Leads', self.colors['success']),
            ('appointments_set', 'Appointments Set', self.colors['secondary'])
        ]
        
        for metric_key, label, color in metrics:
            col_name = column_mapping[metric_key]
            ax.plot(daily_df['date'], daily_df[col_name], 
                   marker='o', linewidth=2.5, markersize=6, 
                   label=label, color=color, alpha=0.8)
        
        # Styling
        ax.set_title(f'Daily Performance Trends - {person_name}\n{date_range}', 
                    fontsize=18, fontweight='bold', pad=20)
        ax.set_xlabel('Date', fontsize=14, fontweight='bold')
        ax.set_ylabel('Count', fontsize=14, fontweight='bold')
        ax.legend(loc='best', fontsize=11, framealpha=0.9)
        ax.grid(True, alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        
        # Save
        output_path = self._ensure_output_dir(person_name)
        filepath = output_path / 'daily_trends.png'
        plt.savefig(filepath, dpi=self.dpi, bbox_inches='tight')
        plt.close()
        
        return str(filepath)
    
    def generate_team_comparison(
        self,
        comparison: Dict[str, Dict[str, float]],
        person_name: str,
        date_range: str
    ) -> str:
        """
        Generate comparison chart: individual vs team average
        
        Args:
            comparison: Comparison metrics dictionary
            person_name: Name of lead generator
            date_range: Date range string
            
        Returns:
            str: Path to saved chart
        """
        fig, ax = plt.subplots(figsize=self.figure_size)
        
        # Prepare data
        metrics = ['Doors\nKnocked', 'Homeowners\nTalked', 
                   'Qualified\nLeads', 'Appointments\nSet']
        metric_keys = ['doors_knocked', 'homeowners_talked', 
                      'qualified_leads', 'appointments_set']
        
        individual_values = [comparison[key]['individual'] for key in metric_keys]
        team_values = [comparison[key]['team_average'] for key in metric_keys]
        
        # Set up bar positions
        x = np.arange(len(metrics))
        width = 0.35
        
        # Create grouped bars
        bars1 = ax.bar(x - width/2, individual_values, width, 
                      label='You', color=self.colors['primary'], 
                      alpha=0.8, edgecolor='black', linewidth=1.5)
        bars2 = ax.bar(x + width/2, team_values, width, 
                      label='Team Average', color=self.colors['secondary'], 
                      alpha=0.8, edgecolor='black', linewidth=1.5)
        
        # Add value labels
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{int(height)}',
                       ha='center', va='bottom', fontsize=11, fontweight='bold')
        
        # Styling
        ax.set_title(f'Performance vs Team Average - {person_name}\n{date_range}', 
                    fontsize=18, fontweight='bold', pad=20)
        ax.set_ylabel('Count', fontsize=14, fontweight='bold')
        ax.set_xlabel('Metrics', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(metrics, fontsize=12)
        ax.legend(fontsize=12, framealpha=0.9)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        
        # Save
        output_path = self._ensure_output_dir(person_name)
        filepath = output_path / 'team_comparison.png'
        plt.savefig(filepath, dpi=self.dpi, bbox_inches='tight')
        plt.close()
        
        return str(filepath)
    
    def generate_conversion_rates_chart(
        self,
        rates: Dict[str, float],
        person_name: str,
        date_range: str
    ) -> str:
        """
        Generate chart showing conversion rates as percentages
        
        Args:
            rates: Dictionary with conversion rates
            person_name: Name of lead generator
            date_range: Date range string
            
        Returns:
            str: Path to saved chart
        """
        fig, ax = plt.subplots(figsize=self.figure_size)
        
        # Prepare data
        rate_labels = ['Talk\nRate', 'Qualification\nRate', 
                      'Appointment\nRate', 'Overall\nConversion']
        rate_keys = ['talk_rate', 'qualification_rate', 
                    'appointment_rate', 'overall_conversion']
        rate_values = [rates[key] for key in rate_keys]
        
        colors_list = [self.colors['primary'], self.colors['warning'], 
                      self.colors['success'], self.colors['secondary']]
        
        # Create bars
        bars = ax.bar(rate_labels, rate_values, color=colors_list, 
                     alpha=0.8, edgecolor='black', linewidth=1.5)
        
        # Add percentage labels
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}%',
                   ha='center', va='bottom', fontsize=13, fontweight='bold')
        
        # Add reference line at 100%
        ax.axhline(y=100, color='gray', linestyle='--', alpha=0.5, linewidth=1)
        
        # Styling
        ax.set_title(f'Conversion Rates - {person_name}\n{date_range}', 
                    fontsize=18, fontweight='bold', pad=20)
        ax.set_ylabel('Percentage (%)', fontsize=14, fontweight='bold')
        ax.set_xlabel('Conversion Metrics', fontsize=14, fontweight='bold')
        ax.tick_params(labelsize=12)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(axis='y', alpha=0.3)
        ax.set_ylim(0, max(rate_values) * 1.2)
        
        plt.tight_layout()
        
        # Save
        output_path = self._ensure_output_dir(person_name)
        filepath = output_path / 'conversion_rates.png'
        plt.savefig(filepath, dpi=self.dpi, bbox_inches='tight')
        plt.close()
        
        return str(filepath)
    
    def generate_all_charts(
        self,
        person_name: str,
        totals: Dict[str, float],
        rates: Dict[str, float],
        daily_df: pd.DataFrame,
        comparison: Dict[str, Dict[str, float]],
        column_mapping: Dict[str, str],
        date_range: str
    ) -> Dict[str, str]:
        """
        Generate all charts at once
        
        Args:
            person_name: Name of lead generator
            totals: Total metrics
            rates: Conversion rates
            daily_df: Daily aggregated data
            comparison: Team comparison data
            column_mapping: Column name mapping
            date_range: Date range string
            
        Returns:
            Dict: Dictionary mapping chart names to file paths
        """
        chart_paths = {}
        
        print(f"\nGenerating charts for {person_name}...")
        
        chart_paths['kpi_metrics'] = self.generate_kpi_bar_chart(
            totals, person_name, date_range
        )
        print("  KPI metrics chart created")
        
        chart_paths['conversion_funnel'] = self.generate_conversion_funnel(
            totals, rates, person_name, date_range
        )
        print("  Conversion funnel chart created")
        
        chart_paths['daily_trends'] = self.generate_daily_trends(
            daily_df, column_mapping, person_name, date_range
        )
        print("  Daily trends chart created")
        
        chart_paths['team_comparison'] = self.generate_team_comparison(
            comparison, person_name, date_range
        )
        print("  Team comparison chart created")
        
        chart_paths['conversion_rates'] = self.generate_conversion_rates_chart(
            rates, person_name, date_range
        )
        print("  Conversion rates chart created")
        
        return chart_paths

