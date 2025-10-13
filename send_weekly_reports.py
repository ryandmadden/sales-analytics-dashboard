"""
Send Monthly Reports
Automatically generates and emails performance reports to all team members
"""

import sys
import yaml
from pathlib import Path
from datetime import datetime
import subprocess

from src.data_ingestion import GoogleSheetsIngestion
from src.data_processing import DataProcessor
from src.kpi_calculator import KPICalculator
from src.visualizations import ChartGenerator
from src.email_sender import EmailSender


def load_config(config_path: str = "config.yaml") -> dict:
    """Load configuration from YAML file"""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print(f"Error: Configuration file not found at {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing configuration file: {e}")
        sys.exit(1)


def load_team_roster(roster_path: str = "team_roster.yaml") -> list:
    """Load team roster from YAML file"""
    try:
        with open(roster_path, 'r') as f:
            roster = yaml.safe_load(f)
        return roster.get('team_members', [])
    except FileNotFoundError:
        print(f"Error: Team roster file not found at {roster_path}")
        print("Please create team_roster.yaml with your team members")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing team roster file: {e}")
        sys.exit(1)


def generate_report_for_person(
    name: str,
    processor: DataProcessor,
    calculator: KPICalculator,
    chart_generator: ChartGenerator,
    filtered_data,
    column_mapping: dict
):
    """
    Generate charts and calculate KPIs for a specific person
    
    Returns:
        tuple: (chart_paths, totals, rates, summary_stats, date_range_str) or None if error
    """
    try:
        # Filter for specific person
        person_data = processor.filter_by_person(filtered_data, name)
        team_data = processor.get_team_data(filtered_data)
        
        # Calculate KPIs
        totals = calculator.calculate_totals(person_data)
        rates = calculator.calculate_conversion_rates(totals)
        daily_trends = calculator.calculate_daily_trends(person_data)
        comparison = calculator.calculate_team_comparison(totals, team_data)
        summary_stats = calculator.get_summary_stats(person_data)
        
        # Format date range
        date_range_str = f"{summary_stats['date_range']['start']} to {summary_stats['date_range']['end']}"
        
        # Generate visualizations
        chart_paths = chart_generator.generate_all_charts(
            person_name=name,
            totals=totals,
            rates=rates,
            daily_df=daily_trends,
            comparison=comparison,
            column_mapping=column_mapping,
            date_range=date_range_str
        )
        
        return chart_paths, totals, rates, summary_stats, date_range_str
        
    except ValueError as e:
            print(f"  Warning: Skipping {name}: {str(e)}")
            return None
    except Exception as e:
            print(f"  Error processing {name}: {str(e)}")
            return None


def main():
    """Main execution function"""
    
    print("=" * 70)
    print("📧 MONTHLY SALES REPORTS - AUTOMATED EMAIL SENDER")
    print("=" * 70)
    print()
    
    print("Loading configuration...")
    config = load_config()
    
    email_config = config.get('email', {})
    if not email_config.get('enabled', False):
        print("Error: Email sending is disabled in config.yaml")
        print("Set 'email: enabled: true' to send emails")
        sys.exit(1)
    
    print("Configuration loaded")
    
    print("Loading team roster...")
    team_members = load_team_roster()
    print(f"Found {len(team_members)} team members")
    print()
    
    sheet_id = config['google_sheets']['sheet_id']
    worksheet_name = config['google_sheets'].get('worksheet_name', 'Form Responses 1')
    credentials_path = config['google_sheets']['credentials_path']
    column_mapping = config['data']['columns']
    days_to_include = config['data'].get('days_to_include', 30)
    
    viz_config = config.get('visualizations', {})
    output_dir = viz_config.get('output_dir', 'output/charts')
    dpi = viz_config.get('dpi', 300)
    figure_size = tuple(viz_config.get('figure_size', [12, 8]))
    colors = viz_config.get('colors', {})
    
    if sheet_id == "YOUR_SHEET_ID_HERE":
        print("Error: Please update config.yaml with your Google Sheet ID")
        sys.exit(1)
    
    try:
        print("Initializing email sender...")
        email_sender = EmailSender(email_config)
        
        if not email_sender.test_connection():
            print("Email connection test failed. Please check your SMTP settings.")
            sys.exit(1)
        print()
        
        print("Fetching data from Google Sheets...")
        ingestion = GoogleSheetsIngestion(credentials_path)
        ingestion.authenticate()
        raw_data = ingestion.fetch_data(sheet_id, worksheet_name)
        print(f"Fetched {len(raw_data)} rows of data")
        print()
        
        print("Processing data...")
        processor = DataProcessor(column_mapping)
        clean_data = processor.clean_data(raw_data)
        filtered_data = processor.filter_by_date_range(clean_data, days_to_include)
        
        validation = processor.validate_data_quality(filtered_data)
        if validation['warnings']:
            print("Data quality warnings:")
            for warning in validation['warnings']:
                print(f"  - {warning}")
        print("Data processed")
        print()
        
        calculator = KPICalculator(column_mapping)
        chart_generator = ChartGenerator(output_dir, dpi, figure_size, colors)
        
        # Process each team member
        print("=" * 70)
        print("GENERATING AND SENDING REPORTS")
        print("=" * 70)
        print()
        
        successful_sends = 0
        failed_sends = 0
        skipped = 0
        
        for member in team_members:
            name = member['name']
            email = member['email']
            
            print(f"Processing: {name} ({email})")
            
            result = generate_report_for_person(
                name, processor, calculator, chart_generator,
                filtered_data, column_mapping
            )
            
            if result is None:
                skipped += 1
                continue
            
            chart_paths, totals, rates, summary_stats, date_range_str = result
            
            print(f"  Sending email...")
            success = email_sender.send_report(
                to_email=email,
                person_name=name,
                chart_paths=chart_paths,
                totals=totals,
                rates=rates,
                date_range=date_range_str
            )
            
            if success:
                print(f"  Email sent successfully to {email}")
                successful_sends += 1
            else:
                failed_sends += 1
            
            print()
        
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Successfully sent: {successful_sends}")
        if failed_sends > 0:
            print(f"Failed to send: {failed_sends}")
        if skipped > 0:
            print(f"Skipped (no data): {skipped}")
        print()
        print("Monthly reports complete!")
        
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

