"""
Data Processing Module
Handles data cleaning, validation, and transformation
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional


class DataProcessor:
    """Processes and cleans sales data"""
    
    def __init__(self, column_mapping: Dict[str, str]):
        """
        Initialize data processor
        
        Args:
            column_mapping: Dictionary mapping config keys to actual column names
        """
        self.column_mapping = column_mapping
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and standardize the DataFrame
        
        Args:
            df: Raw DataFrame from Google Sheets
            
        Returns:
            pd.DataFrame: Cleaned DataFrame
        """
        # Make a copy to avoid modifying original
        df_clean = df.copy()
        
        # Standardize column names (if they exist)
        self._validate_columns(df_clean)
        
        # Parse timestamp column
        timestamp_col = self.column_mapping['timestamp']
        df_clean[timestamp_col] = pd.to_datetime(
            df_clean[timestamp_col],
            errors='coerce'
        )
        
        # Convert numeric columns to appropriate types
        numeric_columns = [
            self.column_mapping['doors_knocked'],
            self.column_mapping['homeowners_talked'],
            self.column_mapping['qualified_leads'],
            self.column_mapping['appointments_set']
        ]
        
        for col in numeric_columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
        
        # Clean name column (strip whitespace, title case)
        name_col = self.column_mapping['name']
        df_clean[name_col] = df_clean[name_col].str.strip().str.title()
        
        # Remove rows with invalid timestamps
        df_clean = df_clean[df_clean[timestamp_col].notna()].copy()
        
        # Fill missing numeric values with 0
        df_clean[numeric_columns] = df_clean[numeric_columns].fillna(0)
        
        # Ensure all numeric values are non-negative
        for col in numeric_columns:
            df_clean[col] = df_clean[col].clip(lower=0)
        
        print(f"Data cleaned: {len(df_clean)} valid rows")
        return df_clean
    
    def _validate_columns(self, df: pd.DataFrame):
        """
        Validate that required columns exist
        
        Args:
            df: DataFrame to validate
            
        Raises:
            ValueError: If required columns are missing
        """
        missing_columns = []
        for key, col_name in self.column_mapping.items():
            if col_name not in df.columns:
                missing_columns.append(col_name)
        
        if missing_columns:
            raise ValueError(
                f"Missing required columns: {', '.join(missing_columns)}\n"
                f"Available columns: {', '.join(df.columns)}\n"
                "Please update your config.yaml with the correct column names."
            )
    
    def filter_by_date_range(
        self,
        df: pd.DataFrame,
        days: int = 30
    ) -> pd.DataFrame:
        """
        Filter data to specified number of days
        
        Args:
            df: Cleaned DataFrame
            days: Number of days to include (0 = all data)
            
        Returns:
            pd.DataFrame: Filtered DataFrame
        """
        if days <= 0:
            print(f"Using all available data: {len(df)} rows")
            return df
        
        timestamp_col = self.column_mapping['timestamp']
        cutoff_date = datetime.now() - timedelta(days=days)
        
        df_filtered = df[df[timestamp_col] >= cutoff_date].copy()
        
        print(f"Filtered to last {days} days: {len(df_filtered)} rows")
        return df_filtered
    
    def filter_by_person(
        self,
        df: pd.DataFrame,
        person_name: str
    ) -> pd.DataFrame:
        """
        Filter data for a specific person
        
        Args:
            df: Cleaned DataFrame
            person_name: Name of the lead generator
            
        Returns:
            pd.DataFrame: Filtered DataFrame for the person
        """
        name_col = self.column_mapping['name']
        
        # Try exact match first
        df_person = df[df[name_col].str.lower() == person_name.lower()].copy()
        
        # If no exact match, try partial match
        if len(df_person) == 0:
            df_person = df[
                df[name_col].str.lower().str.contains(
                    person_name.lower(),
                    na=False
                )
            ].copy()
        
        if len(df_person) == 0:
            available_names = df[name_col].unique()
            raise ValueError(
                f"No data found for '{person_name}'.\n"
                f"Available names: {', '.join(sorted(available_names))}"
            )
        
        print(f"Found {len(df_person)} rows for {person_name}")
        return df_person
    
    def get_team_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Get aggregated team data for comparison
        
        Args:
            df: Cleaned DataFrame
            
        Returns:
            pd.DataFrame: Team aggregated data
        """
        name_col = self.column_mapping['name']
        
        # Aggregate by person
        team_agg = df.groupby(name_col).agg({
            self.column_mapping['doors_knocked']: 'sum',
            self.column_mapping['homeowners_talked']: 'sum',
            self.column_mapping['qualified_leads']: 'sum',
            self.column_mapping['appointments_set']: 'sum'
        }).reset_index()
        
        return team_agg
    
    def validate_data_quality(self, df: pd.DataFrame) -> Dict:
        """
        Validate data quality and return report
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Dict: Validation report with warnings
        """
        warnings = []
        
        # Check for logical inconsistencies
        doors_col = self.column_mapping['doors_knocked']
        talked_col = self.column_mapping['homeowners_talked']
        qualified_col = self.column_mapping['qualified_leads']
        appts_col = self.column_mapping['appointments_set']
        
        # Homeowners talked shouldn't exceed doors knocked
        if (df[talked_col] > df[doors_col]).any():
            warnings.append("Some records have more homeowners talked than doors knocked")
        
        # Qualified leads shouldn't exceed homeowners talked
        if (df[qualified_col] > df[talked_col]).any():
            warnings.append("Some records have more qualified leads than homeowners talked")
        
        # Appointments shouldn't exceed qualified leads
        if (df[appts_col] > df[qualified_col]).any():
            warnings.append("Some records have more appointments than qualified leads")
        
        return {
            'valid': len(warnings) == 0,
            'warnings': warnings,
            'total_rows': len(df)
        }

