"""
Sales Analytics Dashboard - Main Script
Orchestrates the complete workflow for generating sales analytics
"""

import argparse
import sys
import yaml
from pathlib import Path
from datetime import datetime

from src.data_ingestion import GoogleSheetsIngestion
from src.data_processing import DataProcessor
from src.kpi_calculator import KPICalculator
from src.visualizations import ChartGenerator


def load_config(config_path: str = "config.yaml") -> dict:
    """Load configuration from YAML file"""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print(f"Error: Configuration file not found at {config_path}")
        print("Please create a config.yaml file. See README for instructions.")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing configuration file: {e}")
        sys.exit(1)


def validate_config(config: dict) -> bool:
    """Validate that configuration has required fields"""
    required_fields = [
        ('google_sheets', 'sheet_id'),
        ('google_sheets', 'credentials_path'),
        ('data', 'columns')
    ]
    
    for *path, field in required_fields:
        current = config
        for key in path:
            if key not in current:
                print(f"Error: Missing configuration: {'.'.join(path)}.{field}")
                return False
            current = current[key]
        if field not in current:
            print(f"Error: Missing configuration: {'.'.join(path)}.{field}")
            return False
    
    return True


def format_date_range(start_date: str, end_date: str) -> str:
    """Format date range string for display"""
    return f"{start_date} to {end_date}"


def main():
    """Main execution function"""
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Sales Analytics Dashboard - Generate performance charts for lead generators'
    )
    parser.add_argument(
        '--name',
        type=str,
        required=True,
        help='Name of the lead generator (must match Google Form responses)'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=None,
        help='Number of days to include (overrides config)'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Sales Analytics Dashboard")
    print("=" * 60)
    print()
    
    print("Loading configuration...")
    config = load_config(args.config)
    
    if not validate_config(config):
        sys.exit(1)
    
    print("Configuration loaded successfully")
    print()
    
    sheet_id = config['google_sheets']['sheet_id']
    worksheet_name = config['google_sheets'].get('worksheet_name', 'Form Responses 1')
    credentials_path = config['google_sheets']['credentials_path']
    column_mapping = config['data']['columns']
    days_to_include = args.days if args.days is not None else config['data'].get('days_to_include', 30)
    
    viz_config = config.get('visualizations', {})
    output_dir = viz_config.get('output_dir', 'output/charts')
    dpi = viz_config.get('dpi', 300)
    figure_size = tuple(viz_config.get('figure_size', [12, 8]))
    colors = viz_config.get('colors', {})
    
    if sheet_id == "YOUR_SHEET_ID_HERE":
        print("Error: Please update config.yaml with your Google Sheet ID")
        print("See README.md for setup instructions")
        sys.exit(1)
    
    try:
        print("Step 1: Fetching data from Google Sheets...")
        ingestion = GoogleSheetsIngestion(credentials_path)
        ingestion.authenticate()
        print("Authenticated with Google Sheets API")
        
        raw_data = ingestion.fetch_data(sheet_id, worksheet_name)
        print(f"Fetched {len(raw_data)} rows of data")
        print()
        
        print("Step 2: Processing and cleaning data...")
        processor = DataProcessor(column_mapping)
        clean_data = processor.clean_data(raw_data)
        
        filtered_data = processor.filter_by_date_range(clean_data, days_to_include)
        
        validation = processor.validate_data_quality(filtered_data)
        if validation['warnings']:
            print("Data quality warnings:")
            for warning in validation['warnings']:
                print(f"  - {warning}")
        print("Data processed successfully")
        print()
        
        print(f"Step 3: Filtering data for '{args.name}'...")
        person_data = processor.filter_by_person(filtered_data, args.name)
        team_data = processor.get_team_data(filtered_data)
        print("Data filtered successfully")
        print()
        
        print("Step 4: Calculating KPIs...")
        calculator = KPICalculator(column_mapping)
        
        totals = calculator.calculate_totals(person_data)
        rates = calculator.calculate_conversion_rates(totals)
        daily_trends = calculator.calculate_daily_trends(person_data)
        comparison = calculator.calculate_team_comparison(totals, team_data)
        summary_stats = calculator.get_summary_stats(person_data)
        
        print("KPIs calculated")
        print()
        print("Summary Statistics:")
        print(f"  Total entries: {summary_stats['total_entries']}")
        print(f"  Date range: {summary_stats['date_range']['start']} to {summary_stats['date_range']['end']}")
        print(f"  Days active: {summary_stats['days_active']}")
        print()
        print("Your Totals:")
        print(f"  Doors Knocked: {int(totals['doors_knocked'])}")
        print(f"  Homeowners Talked: {int(totals['homeowners_talked'])}")
        print(f"  Qualified Leads: {int(totals['qualified_leads'])}")
        print(f"  Appointments Set: {int(totals['appointments_set'])}")
        print()
        print("Your Conversion Rates:")
        print(f"  Talk Rate: {rates['talk_rate']:.1f}%")
        print(f"  Qualification Rate: {rates['qualification_rate']:.1f}%")
        print(f"  Appointment Rate: {rates['appointment_rate']:.1f}%")
        print(f"  Overall Conversion: {rates['overall_conversion']:.1f}%")
        print()
        
        print("Step 5: Generating visualizations...")
        chart_generator = ChartGenerator(output_dir, dpi, figure_size, colors)
        
        date_range_str = format_date_range(
            summary_stats['date_range']['start'],
            summary_stats['date_range']['end']
        )
        
        chart_paths = chart_generator.generate_all_charts(
            person_name=args.name,
            totals=totals,
            rates=rates,
            daily_df=daily_trends,
            comparison=comparison,
            column_mapping=column_mapping,
            date_range=date_range_str
        )
        
        print()
        print("=" * 60)
        print("SUCCESS! All charts generated")
        print("=" * 60)
        print()
        print("Charts saved to:")
        for chart_name, chart_path in chart_paths.items():
            print(f"  - {chart_name}: {chart_path}")
        print()
        
    except FileNotFoundError as e:
        print(f"\nError: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"\nError: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
