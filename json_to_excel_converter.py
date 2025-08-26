import json
import pandas as pd
import os
import argparse
from datetime import datetime

class JSONToExcelConverter:
    def __init__(self, input_path=None, output_path=None):
        self.input_path = input_path
        self.output_path = output_path
        
        # Hardcoded paths
        self.jsonFolderPath = r"C:\Users\phili\OneDrive\Skrivebord\Coding Projects\Projects\Website_scrapers\scraped data"
        self.outputFolderPath = r"C:\Users\phili\OneDrive\Skrivebord\Coding Projects\Projects\Website_scrapers\converted_data"
        
        # Set default folders to hardcoded paths
        self.input_folder = self.jsonFolderPath
        self.output_folder = self.outputFolderPath
        
        # If custom paths provided, use them instead
        if self.input_path:
            if os.path.isabs(self.input_path):
                self.input_folder = os.path.dirname(self.input_path) if os.path.dirname(self.input_path) else "."
            else:
                # If relative path, make it relative to current working directory
                self.input_folder = os.path.dirname(os.path.abspath(self.input_path)) if os.path.dirname(self.input_path) else "."
        
        if self.output_path:
            if os.path.isabs(self.output_path):
                self.output_folder = os.path.dirname(self.output_path) if os.path.dirname(self.output_path) else "."
            else:
                # If relative path, make it relative to current working directory
                self.output_folder = os.path.dirname(os.path.abspath(self.output_path)) if os.path.dirname(self.output_path) else "."
        
        self.ensure_output_folder()
    
    def ensure_output_folder(self):
        """Create the output folder if it doesn't exist"""
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
            print(f"Created output folder: {self.output_folder}")
    
    def find_latest_json_file(self):
        """Find the most recent JSON file in the scraped data folder (fallback)"""
        try:
            # Ensure we're using absolute path
            if not os.path.isabs(self.input_folder):
                self.input_folder = os.path.abspath(self.input_folder)
            
            if not os.path.exists(self.input_folder):
                print(f"❌ Input folder does not exist: {self.input_folder}")
                return None
            
            json_files = [f for f in os.listdir(self.input_folder) if f.endswith('.json') and 'ultimate' in f]
            if not json_files:
                print(f"No ultimate JSON files found in: {self.input_folder}")
                return None
            
            # Sort by modification time and get the latest
            latest_file = max(json_files, key=lambda x: os.path.getmtime(os.path.join(self.input_folder, x)))
            return os.path.join(self.input_folder, latest_file)
        except Exception as e:
            print(f"Error finding JSON file: {e}")
            return None
    
    def get_input_file_path(self):
        """Get the input JSON file path (custom or auto-detected)"""
        if self.input_path:
            if os.path.exists(self.input_path):
                return os.path.abspath(self.input_path)
            else:
                print(f"❌ Custom input file not found: {self.input_path}")
                return None
        
        # Auto-detect if no custom path provided
        print("🔍 No custom input path provided, auto-detecting latest JSON file...")
        print(f"🔍 Looking in: {self.input_folder}")
        return self.find_latest_json_file()
    
    def get_output_file_path(self, file_type="excel"):
        """Get the output file path (custom or auto-generated)"""
        if self.output_path:
            if file_type == "excel":
                # Ensure .xlsx extension
                if not self.output_path.endswith('.xlsx'):
                    self.output_path = self.output_path.replace('.xls', '.xlsx')
                    if not self.output_path.endswith('.xlsx'):
                        self.output_path += '.xlsx'
                return os.path.abspath(self.output_path)
            else:  # CSV
                if not self.output_path.endswith('.csv'):
                    self.output_path = self.output_path.replace('.xlsx', '.csv').replace('.xls', '.csv')
                    if not self.output_path.endswith('.csv'):
                        self.output_path += '.csv'
                return os.path.abspath(self.output_path)
        
        # Auto-generate filename if no custom path provided
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if file_type == "excel":
            filename = f"interreg_projects_formatted_{timestamp}.xlsx"
        else:
            filename = f"interreg_projects_formatted_{timestamp}.csv"
        
        return os.path.join(self.output_folder, filename)
    
    def load_json_data(self, json_file_path):
        """Load and parse the JSON data"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            print(f"Successfully loaded JSON data with {len(data)} records")
            return data
        except Exception as e:
            print(f"Error loading JSON file: {e}")
            return None
    
    def convert_to_dataframe(self, json_data):
        """Convert JSON data to a pandas DataFrame with proper column formatting"""
        try:
            # Create DataFrame
            df = pd.DataFrame(json_data)
            
            # Clean and format column names
            df.columns = [col.replace('_', ' ').title() for col in df.columns]
            
            # Reorder columns in a logical way
            column_order = [
                'Acronym',
                'Call',
                'Priority',
                'Specific Objective',
                'Title',
                'Description',
                'Summary',
                'Lead Partner',
                'Partners',
                'Objectives',
                'Start End',
                'Start Date',
                'End Date',
                'Total Budget',
                'Erdf Funding',
                'Norway Funding',
                'Budget',
                'Project Url',
                'Status',
                'Main Content',
                'Error'
            ]
            
            # Only include columns that exist in the data
            existing_columns = [col for col in column_order if col in df.columns]
            df = df[existing_columns]
            
            print(f"DataFrame created with {len(df)} rows and {len(df.columns)} columns")
            return df
            
        except Exception as e:
            print(f"Error converting to DataFrame: {e}")
            return None
    
    def save_to_excel(self, df, output_filename=None):
        """Save DataFrame to Excel with formatting"""
        try:
            if not output_filename:
                output_filename = self.get_output_file_path("excel")
            
            # Create Excel writer with formatting
            with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Projects', index=False)
                
                # Get the workbook and worksheet
                workbook = writer.book
                worksheet = writer.sheets['Projects']
                
                # Auto-adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    
                    adjusted_width = min(max_length + 2, 50)  # Cap at 50 characters
                    worksheet.column_dimensions[column_letter].width = adjusted_width
                
                # Format header row
                from openpyxl.styles import Font, PatternFill, Alignment
                header_font = Font(bold=True, color="FFFFFF")
                header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
                header_alignment = Alignment(horizontal="center", vertical="center")
                
                for cell in worksheet[1]:
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.alignment = header_alignment
                
                # Freeze the header row
                worksheet.freeze_panes = 'A2'
            
            print(f"Excel file saved successfully: {output_filename}")
            return output_filename
            
        except Exception as e:
            print(f"Error saving to Excel: {e}")
            return None
    
    def save_to_csv(self, df, output_filename=None):
        """Save DataFrame to CSV as backup"""
        try:
            if not output_filename:
                output_filename = self.get_output_file_path("csv")
            
            df.to_csv(output_filename, index=False, encoding='utf-8')
            
            print(f"CSV file saved successfully: {output_filename}")
            return output_filename
            
        except Exception as e:
            print(f"Error saving to CSV: {e}")
            return None
    
    def display_data_preview(self, df):
        """Display a preview of the data"""
        print(f"\n{'='*80}")
        print("DATA PREVIEW")
        print(f"{'='*80}")
        print(f"Shape: {df.shape[0]} rows × {df.shape[1]} columns")
        print(f"Columns: {', '.join(df.columns)}")
        print(f"\nFirst 3 rows:")
        print(df.head(3).to_string())
        print(f"\n{'='*80}")
    
    def run_conversion(self):
        """Run the complete conversion process"""
        print("🚀 Starting JSON to Excel Conversion...")
        
        # Show input/output paths
        if self.input_path:
            print(f"📁 Custom input file: {self.input_path}")
        else:
            print(f"📁 Input folder: {self.input_folder}")
        
        if self.output_path:
            print(f"📂 Custom output file: {self.output_path}")
        else:
            print(f"📂 Output folder: {self.output_folder}")
        
        print("-" * 60)
        
        # Get input file path
        json_file_path = self.get_input_file_path()
        if not json_file_path:
            print("❌ No JSON file found. Please provide a custom path or ensure the scraper has run first.")
            return
        
        print(f"📄 Using JSON file: {json_file_path}")
        
        # Load JSON data
        json_data = self.load_json_data(json_file_path)
        if not json_data:
            print("❌ Failed to load JSON data.")
            return
        
        # Convert to DataFrame
        df = self.convert_to_dataframe(json_data)
        if df is None:
            print("❌ Failed to convert to DataFrame.")
            return
        
        # Display preview
        self.display_data_preview(df)
        
        # Save to Excel
        excel_file = self.save_to_excel(df)
        if not excel_file:
            print("❌ Failed to save Excel file.")
            return
        
        # Save to CSV as backup
        csv_file = self.save_to_csv(df)
        
        print(f"\n🎉 CONVERSION COMPLETED SUCCESSFULLY!")
        print(f"📊 Excel file: {os.path.basename(excel_file)}")
        print(f"📄 CSV file: {os.path.basename(csv_file)}")
        print(f"📂 Location: {os.path.dirname(excel_file)}")
        print(f"📈 Total projects: {len(df)}")
        print(f"🔤 Total columns: {len(df.columns)}")
        
        return {
            'excel': excel_file,
            'csv': csv_file,
            'dataframe': df
        }

def main():
    """Main function to run the converter with command-line arguments"""
    parser = argparse.ArgumentParser(
        description='Convert Interreg North Sea JSON data to formatted Excel file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-detect latest JSON and create Excel in default location
  python json_to_excel_converter.py
  
  # Use custom JSON file with auto-generated Excel name
  python json_to_excel_converter.py -i "path/to/your/data.json"
  
  # Specify both input and output paths
  python json_to_excel_converter.py -i "data.json" -o "my_projects.xlsx"
  
  # Use custom output folder with auto-generated filename
  python json_to_excel_converter.py -i "data.json" -o "output_folder/"
        """
    )
    
    parser.add_argument(
        '-i', '--input', 
        help='Path to input JSON file (optional: auto-detects if not provided)'
    )
    
    parser.add_argument(
        '-o', '--output', 
        help='Path to output Excel file (optional: auto-generates if not provided)'
    )
    
    args = parser.parse_args()
    
    # Create converter with custom paths if provided
    converter = JSONToExcelConverter(
        input_path=args.input,
        output_path=args.output
    )
    
    try:
        results = converter.run_conversion()
        if results:
            print(f"\n✅ Conversion completed successfully!")
            print(f"🎯 Your formatted Excel file is ready!")
        else:
            print("❌ Conversion failed. Please check the output above for details.")
    
    except KeyboardInterrupt:
        print("\n⏹️ Conversion interrupted by user.")
    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    main()
