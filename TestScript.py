# In your other_script.py
from json_to_excel_converter import JSONToExcelConverter

# Or specify custom paths
converter = JSONToExcelConverter(
    input_path=r"C:\Users\phili\OneDrive\Skrivebord\Coding Projects\Projects\Website_scrapers\scraped data\interreg_ultimate_20250826_215924.json",
    output_path=r"C:\Users\phili\OneDrive\Skrivebord\Coding Projects\Projects\Website_scrapers\converted_data\testing.xlsx"
)
results = converter.run_conversion()