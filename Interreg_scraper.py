import requests
from bs4 import BeautifulSoup
import csv
import json
from datetime import datetime
import time
import logging
import os
import re

class InterregScraper:
    def __init__(self):
        self.base_url = "https://www.interregnorthsea.eu/project-data"
        self.project_base_url = "https://www.interregnorthsea.eu"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Create scraped_data folder
        self.output_folder = "scraped data"
        self.ensure_output_folder()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(self.output_folder, f'interreg_scraper_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.log')),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def ensure_output_folder(self):
        """Create the output folder if it doesn't exist"""
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
            self.logger.info(f"Created output folder: {self.output_folder}")
    
    def scrape_project_data(self):
        """Scrape all project data from the Interreg North Sea project data page"""
        try:
            self.logger.info(f"Starting to scrape data from: {self.base_url}")
            
            # Make request to the page
            response = self.session.get(self.base_url)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the project data table
            table = soup.find('table')
            if not table:
                self.logger.error("No table found on the page")
                return []
            
            # Extract all rows from the table
            rows = table.find_all('tr')[1:]  # Skip header row
            
            projects = []
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 4:  # Ensure we have enough cells
                    project_data = {
                        'call': cells[0].get_text(strip=True) if len(cells) > 0 else '',
                        'priority': cells[1].get_text(strip=True) if len(cells) > 1 else '',
                        'specific_objective': cells[2].get_text(strip=True) if len(cells) > 2 else '',
                        'acronym': cells[3].get_text(strip=True) if len(cells) > 3 else '',
                        'summary': cells[4].get_text(strip=True) if len(cells) > 4 else '',
                        'lead_partner': cells[5].get_text(strip=True) if len(cells) > 5 else '',
                        'start_end': cells[6].get_text(strip=True) if len(cells) > 6 else '',
                        'total_budget': cells[7].get_text(strip=True) if len(cells) > 7 else '',
                        'erdf_funding': cells[8].get_text(strip=True) if len(cells) > 8 else '',
                        'norway_funding': cells[9].get_text(strip=True) if len(cells) > 9 else ''
                    }
                    projects.append(project_data)
            
            self.logger.info(f"Successfully scraped {len(projects)} projects")
            return projects
            
        except requests.RequestException as e:
            self.logger.error(f"Request failed: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Scraping failed: {e}")
            return []
    
    def scrape_project_details(self, acronym):
        """Scrape detailed information from a specific project's about-us page"""
        try:
            # Clean the acronym for URL (remove special characters, convert to lowercase)
            clean_acronym = re.sub(r'[^a-zA-Z0-9]', '', acronym).lower()
            project_url = f"{self.project_base_url}/{clean_acronym}/about-us"
            
            self.logger.info(f"Scraping project details from: {project_url}")
            
            # Make request to the project page
            response = self.session.get(project_url)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract project details
            project_details = {
                'acronym': acronym,
                'url': project_url,
                'title': '',
                'description': '',
                'objectives': '',
                'partners': '',
                'start_date': '',
                'end_date': '',
                'budget': '',
                'main_content': ''
            }
            
            # Try to extract title
            title_tag = soup.find('h1') or soup.find('title')
            if title_tag:
                project_details['title'] = title_tag.get_text(strip=True)
            
            # Try to extract main content
            main_content = soup.find('main') or soup.find('div', class_='main-content') or soup.find('div', class_='content')
            if main_content:
                project_details['main_content'] = main_content.get_text(strip=True)
            
            # Look for specific sections
            sections = soup.find_all(['h2', 'h3', 'p'])
            for section in sections:
                text = section.get_text(strip=True)
                if 'objective' in text.lower() or 'goal' in text.lower():
                    project_details['objectives'] = text
                elif 'partner' in text.lower():
                    project_details['partners'] = text
                elif 'start' in text.lower() and 'date' in text.lower():
                    project_details['start_date'] = text
                elif 'budget' in text.lower() or 'funding' in text.lower():
                    project_details['budget'] = text
            
            # Extract description from meta tags or first paragraph
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                project_details['description'] = meta_desc.get('content', '')
            else:
                first_p = soup.find('p')
                if first_p:
                    project_details['description'] = first_p.get_text(strip=True)
            
            self.logger.info(f"Successfully scraped details for project: {acronym}")
            return project_details
            
        except requests.RequestException as e:
            self.logger.error(f"Request failed for project {acronym}: {e}")
            return {'acronym': acronym, 'error': f'Request failed: {e}'}
        except Exception as e:
            self.logger.error(f"Scraping failed for project {acronym}: {e}")
            return {'acronym': acronym, 'error': f'Scraping failed: {e}'}
    
    def scrape_all_project_details(self, projects, delay=1):
        """Scrape detailed information for all projects with a delay to be respectful"""
        self.logger.info("Starting to scrape detailed information for all projects...")
        
        all_project_details = []
        total_projects = len(projects)
        
        for i, project in enumerate(projects, 1):
            acronym = project['acronym']
            if acronym:
                self.logger.info(f"Scraping project {i}/{total_projects}: {acronym}")
                
                # Scrape project details
                project_detail = self.scrape_project_details(acronym)
                all_project_details.append(project_detail)
                
                # Add delay between requests to be respectful to the server
                if i < total_projects:
                    time.sleep(delay)
        
        self.logger.info(f"Completed scraping details for {len(all_project_details)} projects")
        return all_project_details
    
    def extract_acronyms_only(self, projects):
        """Extract only the acronyms from the project data"""
        acronyms = []
        for project in projects:
            if project['acronym']:
                acronyms.append({
                    'acronym': project['acronym'],
                    'call': project['call'],
                    'priority': project['priority']
                })
        return acronyms
    
    def save_to_csv(self, data, filename=None):
        """Save data to CSV file in the scraped_data folder"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"interreg_projects_{timestamp}.csv"
        
        # Ensure filename is saved in the scraped_data folder
        filepath = os.path.join(self.output_folder, filename)
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                if data and len(data) > 0:
                    fieldnames = data[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(data)
            
            self.logger.info(f"Data saved to {filepath}")
            return filepath
        except Exception as e:
            self.logger.error(f"Failed to save CSV: {e}")
            return None
    
    def save_to_json(self, data, filename=None):
        """Save data to JSON file in the scraped_data folder"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"interreg_projects_{timestamp}.json"
        
        # Ensure filename is saved in the scraped_data folder
        filepath = os.path.join(self.output_folder, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as jsonfile:
                json.dump(data, jsonfile, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Data saved to {filepath}")
            return filepath
        except Exception as e:
            self.logger.error(f"Failed to save JSON: {e}")
            return None
    
    def print_acronyms(self, acronyms):
        """Print all acronyms in a formatted way"""
        print(f"\n{'='*60}")
        print(f"INTERREG NORTH SEA PROJECT ACRONYMS")
        print(f"{'='*60}")
        print(f"Total projects found: {len(acronyms)}")
        print(f"{'='*60}")
        
        for i, project in enumerate(acronyms, 1):
            print(f"{i:3d}. {project['acronym']:<20} | Call: {project['call']:<15} | Priority: {project['priority']}")
        
        print(f"{'='*60}")
    
    def run_full_scrape(self):
        """Run the complete scraping process"""
        print("Starting Interreg North Sea Project Scraper...")
        print(f"Target URL: {self.base_url}")
        print(f"Output folder: {self.output_folder}")
        print("-" * 60)
        
        # Scrape all project data
        projects = self.scrape_project_data()
        
        if not projects:
            print("No projects found. Please check the website or try again later.")
            return
        
        # Extract acronyms only
        acronyms = self.extract_acronyms_only(projects)
        
        # Display results
        self.print_acronyms(acronyms)
        
        # Save data to files
        csv_file = self.save_to_csv(projects)
        json_file = self.save_to_json(projects)
        
        # Save acronyms only
        acronyms_csv = self.save_to_csv(acronyms, f"interreg_acronyms_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        acronyms_json = self.save_to_json(acronyms, f"interreg_acronyms_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        print(f"\nData saved to folder: {self.output_folder}")
        print(f"  - Full project data: {os.path.basename(csv_file)}")
        print(f"  - Full project data: {os.path.basename(json_file)}")
        print(f"  - Acronyms only: {os.path.basename(acronyms_csv)}")
        print(f"  - Acronyms only: {os.path.basename(acronyms_json)}")
        
        return {
            'projects': projects,
            'acronyms': acronyms,
            'files': {
                'csv': csv_file,
                'json': json_file,
                'acronyms_csv': acronyms_csv,
                'acronyms_json': acronyms_json
            }
        }
    
    def run_detailed_scrape(self, delay=1):
        """Run the complete scraping process including detailed project information"""
        print("Starting Interreg North Sea Project Scraper with Detailed Information...")
        print(f"Target URL: {self.base_url}")
        print(f"Output folder: {self.output_folder}")
        print("-" * 60)
        
        # First scrape the main project data
        projects = self.scrape_project_data()
        
        if not projects:
            print("No projects found. Please check the website or try again later.")
            return
        
        # Extract acronyms only
        acronyms = self.extract_acronyms_only(projects)
        
        # Display results
        self.print_acronyms(acronyms)
        
        # Save basic data to files
        csv_file = self.save_to_csv(projects)
        json_file = self.save_to_json(projects)
        acronyms_csv = self.save_to_csv(acronyms, f"interreg_acronyms_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        acronyms_json = self.save_to_json(acronyms, f"interreg_acronyms_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        print(f"\nBasic data saved to folder: {self.output_folder}")
        print(f"  - Full project data: {os.path.basename(csv_file)}")
        print(f"  - Full project data: {os.path.basename(json_file)}")
        print(f"  - Acronyms only: {os.path.basename(acronyms_csv)}")
        print(f"  - Acronyms only: {os.path.basename(acronyms_json)}")
        
        # Now scrape detailed information for each project
        print(f"\nStarting detailed project information scraping...")
        print(f"This may take a while as we scrape {len(projects)} individual project pages...")
        
        project_details = self.scrape_all_project_details(projects, delay)
        
        # Save detailed project information
        details_csv = self.save_to_csv(project_details, f"interreg_project_details_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        details_json = self.save_to_json(project_details, f"interreg_project_details_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        print(f"\nDetailed project information saved:")
        print(f"  - Project details: {os.path.basename(details_csv)}")
        print(f"  - Project details: {os.path.basename(details_json)}")
        
        return {
            'projects': projects,
            'acronyms': acronyms,
            'project_details': project_details,
            'files': {
                'csv': csv_file,
                'json': json_file,
                'acronyms_csv': acronyms_csv,
                'acronyms_json': acronyms_json,
                'details_csv': details_csv,
                'details_json': details_json
            }
        }

def main():
    """Main function to run the scraper"""
    scraper = InterregScraper()
    
    try:
        print("Choose scraping mode:")
        print("1. Basic scraping (project list and acronyms only)")
        print("2. Detailed scraping (includes individual project pages)")
        
        choice = input("Enter your choice (1 or 2): ").strip()
        
        if choice == "2":
            results = scraper.run_detailed_scrape()
        else:
            results = scraper.run_full_scrape()
        
        if results:
            print(f"\nScraping completed successfully!")
            print(f"Total projects scraped: {len(results['projects'])}")
            print(f"Total acronyms extracted: {len(results['acronyms'])}")
            if 'project_details' in results:
                print(f"Total detailed project pages scraped: {len(results['project_details'])}")
            print(f"All files saved in: {scraper.output_folder}")
        else:
            print("Scraping failed. Check the logs for details.")
    
    except KeyboardInterrupt:
        print("\nScraping interrupted by user.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
