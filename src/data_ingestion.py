"""
Data Ingestion Module
Handles Google Sheets API authentication and data fetching
"""

import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from typing import Optional


class GoogleSheetsIngestion:
    """Handles data ingestion from Google Sheets"""
    
    def __init__(self, credentials_path: str):
        """
        Initialize Google Sheets connection
        
        Args:
            credentials_path: Path to service account credentials JSON file
        """
        self.credentials_path = credentials_path
        self.client = None
    
    def authenticate(self) -> bool:
        """
        Authenticate with Google Sheets API
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets.readonly',
                'https://www.googleapis.com/auth/drive.readonly'
            ]
            
            credentials = Credentials.from_service_account_file(
                self.credentials_path,
                scopes=scopes
            )
            
            self.client = gspread.authorize(credentials)
            return True
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Credentials file not found at: {self.credentials_path}\n"
                "Please ensure you have created a service account and downloaded the credentials.json file."
            )
        except Exception as e:
            raise Exception(f"Authentication failed: {str(e)}")
    
    def fetch_data(
        self,
        sheet_id: str,
        worksheet_name: str = "Form Responses 1"
    ) -> pd.DataFrame:
        """
        Fetch data from Google Sheet and return as pandas DataFrame
        
        Args:
            sheet_id: Google Sheet ID from the URL
            worksheet_name: Name of the worksheet/tab
            
        Returns:
            pd.DataFrame: Data from the sheet
        """
        if self.client is None:
            raise Exception("Not authenticated. Call authenticate() first.")
        
        try:
            # Open the spreadsheet
            spreadsheet = self.client.open_by_key(sheet_id)
            
            # Get the specific worksheet
            worksheet = spreadsheet.worksheet(worksheet_name)
            
            # Get all values
            data = worksheet.get_all_values()
            
            if not data:
                raise ValueError("No data found in the worksheet")
            
            # Convert to DataFrame (first row as headers)
            df = pd.DataFrame(data[1:], columns=data[0])
            
            print(f"Successfully fetched {len(df)} rows from Google Sheets")
            return df
            
        except gspread.exceptions.SpreadsheetNotFound:
            raise Exception(
                f"Spreadsheet not found with ID: {sheet_id}\n"
                "Please ensure:\n"
                "1. The Sheet ID is correct\n"
                "2. The sheet is shared with your service account email"
            )
        except gspread.exceptions.WorksheetNotFound:
            raise Exception(
                f"Worksheet '{worksheet_name}' not found in spreadsheet.\n"
                "Please check the worksheet name in your config."
            )
        except Exception as e:
            raise Exception(f"Failed to fetch data: {str(e)}")
    
    def fetch_data_with_retry(
        self,
        sheet_id: str,
        worksheet_name: str = "Form Responses 1",
        max_retries: int = 3
    ) -> pd.DataFrame:
        """
        Fetch data with automatic retry on failure
        
        Args:
            sheet_id: Google Sheet ID
            worksheet_name: Name of worksheet
            max_retries: Maximum number of retry attempts
            
        Returns:
            pd.DataFrame: Data from the sheet
        """
        for attempt in range(max_retries):
            try:
                return self.fetch_data(sheet_id, worksheet_name)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                print(f"Attempt {attempt + 1} failed, retrying...")
        
        raise Exception("Failed to fetch data after maximum retries")

