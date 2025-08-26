import requests
from bs4 import BeautifulSoup
import csv
import json
from datetime import datetime
import time
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
        
        # Hardcoded output folder path
        self.folderPath = r"C:\Users\phili\OneDrive\Skrivebord\Coding Projects\Projects\Website_scrapers\scraped data"
        self.output_folder = self.folderPath
        self.ensure_output_folder()
    
    def ensure_output_folder(self):
        """Create the output folder if it doesn't exist"""
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
            print(f"Created output folder: {self.output_folder}")
    
    def scrape_project_data(self):
        """Scrape all project data from the Interreg North Sea project data page"""
        try:
            print(f"Starting to scrape data from: {self.base_url}")
            
            # Make request to the page
            response = self.session.get(self.base_url)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the project data table
            table = soup.find('table')
            if not table:
                print("No table found on the page")
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
            
            print(f"Successfully scraped {len(projects)} projects")
            return projects
            
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return []
        except Exception as e:
            print(f"Scraping failed: {e}")
            return []
    
    def scrape_project_details(self, acronym):
        """Scrape detailed information from a specific project's about-us page"""
        try:
            # Clean the acronym for URL (remove special characters, convert to lowercase)
            clean_acronym = re.sub(r'[^a-zA-Z0-9]', '', acronym).lower()
            project_url = f"{self.project_base_url}/{clean_acronym}/about-us"
            
            # Make request to the project page
            response = self.session.get(project_url)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract project details
            project_details = {
                'acronym': acronym,
                'url': project_url,
                'status': 'success',
                'title': '',
                'description': '',
                'objectives': '',
                'partners': '',
                'start_date': '',
                'end_date': '',
                'budget': '',
                'main_content': '',
                'error': ''
            }
            
            # Try to extract title
            title_tag = soup.find('h1') or soup.find('title')
            if title_tag:
                project_details['title'] = title_tag.get_text(strip=True)
            
            # Try to extract main content
            main_content = soup.find('main') or soup.find('div', class_='main-content') or soup.find('div', class_='content')
            if main_content:
                project_details['main_content'] = main_content.get_text(strip=True)
            
            # Improved partner extraction - look for partner-related sections
            partners_text = self.extract_partner_information(soup)
            if partners_text:
                project_details['partners'] = partners_text
            
            # Look for specific sections
            sections = soup.find_all(['h2', 'h3', 'p'])
            for section in sections:
                text = section.get_text(strip=True)
                if 'objective' in text.lower() or 'goal' in text.lower():
                    project_details['objectives'] = text
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
            
            return project_details
            
        except requests.RequestException as e:
            return {
                'acronym': acronym,
                'url': f"{self.project_base_url}/{re.sub(r'[^a-zA-Z0-9]', '', acronym).lower()}/about-us",
                'status': 'failed',
                'title': '',
                'description': '',
                'objectives': '',
                'partners': '',
                'start_date': '',
                'end_date': '',
                'budget': '',
                'main_content': '',
                'error': f'Request failed: {e}'
            }
        except Exception as e:
            return {
                'acronym': acronym,
                'url': f"{self.project_base_url}/{re.sub(r'[^a-zA-Z0-9]', '', acronym).lower()}/about-us",
                'status': 'failed',
                'title': '',
                'description': '',
                'objectives': '',
                'partners': '',
                'start_date': '',
                'end_date': '',
                'budget': '',
                'main_content': '',
                'error': f'Scraping failed: {e}'
            }
    
    def extract_partner_information(self, soup):
        """Extract comprehensive partner information from the page"""
        partners_text = ""
        
        # Method 1: Look for partner-related headings and their content
        partner_indicators = ['partner', 'partners', 'consortium', 'collaboration', 'team', 'members']
        
        for indicator in partner_indicators:
            # Look for headings containing partner-related words
            headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            for heading in headings:
                heading_text = heading.get_text(strip=True).lower()
                if indicator in heading_text:
                    # Found a partner-related heading, extract content
                    partner_section = self.extract_section_content(heading)
                    if partner_section:
                        partners_text += f"{heading.get_text(strip=True)}:\n{partner_section}\n\n"
        
        # Method 2: Look for paragraphs containing partner information
        paragraphs = soup.find_all('p')
        partner_paragraphs = []
        
        for p in paragraphs:
            p_text = p.get_text(strip=True).lower()
            if any(indicator in p_text for indicator in partner_indicators):
                # Check if this paragraph has substantial partner content
                if len(p.get_text(strip=True)) > 20:  # Avoid very short mentions
                    partner_paragraphs.append(p.get_text(strip=True))
        
        if partner_paragraphs:
            partners_text += "Partner Information:\n" + "\n".join(partner_paragraphs) + "\n\n"
        
        # Method 3: Look for lists that might contain partner names
        lists = soup.find_all(['ul', 'ol'])
        for lst in lists:
            # Check if list items contain partner-related content
            list_items = lst.find_all('li')
            partner_items = []
            
            for item in list_items:
                item_text = item.get_text(strip=True).lower()
                if any(indicator in item_text for indicator in partner_indicators) or len(item_text) > 10:
                    partner_items.append(item.get_text(strip=True))
            
            if partner_items:
                partners_text += "Partner List:\n" + "\n".join(partner_items) + "\n\n"
        
        # Method 4: Look for specific partner patterns in text
        all_text = soup.get_text()
        partner_patterns = [
            r'partner[s]?[:\s]+([^.\n]+)',
            r'consortium[:\s]+([^.\n]+)',
            r'collaboration[:\s]+([^.\n]+)',
            r'team[:\s]+([^.\n]+)',
            r'member[s]?[:\s]+([^.\n]+)'
        ]
        
        for pattern in partner_patterns:
            matches = re.findall(pattern, all_text, re.IGNORECASE)
            for match in matches:
                if match.strip() and len(match.strip()) > 10:
                    partners_text += f"Found: {match.strip()}\n"
        
        return partners_text.strip() if partners_text else ""
    
    def extract_section_content(self, heading):
        """Extract content that follows a heading until the next heading"""
        content = []
        current = heading.find_next_sibling()
        
        # Collect content until we hit another heading or run out of siblings
        while current and current.name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            if current.name in ['p', 'div', 'span'] and current.get_text(strip=True):
                text = current.get_text(strip=True)
                if len(text) > 10:  # Only include substantial content
                    content.append(text)
            current = current.find_next_sibling()
        
        return "\n".join(content)
    
    def scrape_all_project_details(self, projects, delay=1):
        """Scrape detailed information for all projects with a delay to be respectful"""
        print("Starting to scrape detailed information for all projects...")
        
        all_project_details = []
        total_projects = len(projects)
        
        for i, project in enumerate(projects, 1):
            acronym = project['acronym']
            if acronym:
                print(f"Scraping project {i}/{total_projects}: {acronym}")
                
                # Scrape project details
                project_detail = self.scrape_project_details(acronym)
                all_project_details.append(project_detail)
                
                # Add delay between requests to be respectful to the server
                if i < total_projects:
                    time.sleep(delay)
        
        print(f"Completed scraping details for {len(all_project_details)} projects")
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
    
    def create_ultimate_files(self, projects, project_details):
        """Create both CSV and JSON versions of the ultimate scraped information"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_filename = f"interreg_ultimate_{timestamp}.csv"
            json_filename = f"interreg_ultimate_{timestamp}.json"
            
            csv_filepath = os.path.join(self.output_folder, csv_filename)
            json_filepath = os.path.join(self.output_folder, json_filename)
            
            # Create the ultimate dataset
            ultimate_data = []
            
            for project in projects:
                # Find corresponding detailed information
                project_detail = next((pd for pd in project_details if pd['acronym'] == project['acronym']), None)
                
                if project_detail:
                    # Combine basic and detailed data
                    ultimate_row = {
                        'acronym': project['acronym'],
                        'call': project['call'],
                        'priority': project['priority'],
                        'specific_objective': project['specific_objective'],
                        'summary': project['summary'],
                        'lead_partner': project['lead_partner'],
                        'start_end': project['start_end'],
                        'total_budget': project['total_budget'],
                        'erdf_funding': project['erdf_funding'],
                        'norway_funding': project['norway_funding'],
                        'project_url': project_detail['url'],
                        'status': project_detail['status'],
                        'title': project_detail['title'],
                        'description': project_detail['description'],
                        'objectives': project_detail['objectives'],
                        'partners': project_detail['partners'],
                        'start_date': project_detail['start_date'],
                        'end_date': project_detail['end_date'],
                        'budget': project_detail['budget'],
                        'main_content': project_detail['main_content'],
                        'error': project_detail['error']
                    }
                else:
                    # If no detailed info, just use basic data
                    ultimate_row = {
                        'acronym': project['acronym'],
                        'call': project['call'],
                        'priority': project['priority'],
                        'specific_objective': project['specific_objective'],
                        'summary': project['summary'],
                        'lead_partner': project['lead_partner'],
                        'start_end': project['start_end'],
                        'total_budget': project['total_budget'],
                        'erdf_funding': project['erdf_funding'],
                        'norway_funding': project['norway_funding'],
                        'project_url': '',
                        'status': 'not_scraped',
                        'title': '',
                        'description': '',
                        'objectives': '',
                        'partners': '',
                        'start_date': '',
                        'end_date': '',
                        'budget': '',
                        'main_content': '',
                        'error': 'No detailed information available'
                    }
                
                ultimate_data.append(ultimate_row)
            
            # Save to CSV
            with open(csv_filepath, 'w', newline='', encoding='utf-8') as csvfile:
                if ultimate_data and len(ultimate_data) > 0:
                    fieldnames = ultimate_data[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(ultimate_data)
            
            # Save to JSON
            with open(json_filepath, 'w', encoding='utf-8') as jsonfile:
                json.dump(ultimate_data, jsonfile, indent=2, ensure_ascii=False)
            
            print(f"Ultimate CSV file created: {csv_filepath}")
            print(f"Ultimate JSON file created: {json_filepath}")
            
            return {
                'csv': csv_filepath,
                'json': json_filepath
            }
            
        except Exception as e:
            print(f"Failed to create ultimate files: {e}")
            return None
    
    def run_ultimate_scrape(self, delay=1):
        """Run the complete scraping process and create only the ultimate CSV file"""
        print("Starting Interreg North Sea Project Scraper...")
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
        
        # Now scrape detailed information for each project
        print(f"\nStarting detailed project information scraping...")
        print(f"This may take a while as we scrape {len(projects)} individual project pages...")
        
        project_details = self.scrape_all_project_details(projects, delay)
        
        # Create the ultimate CSV file
        ultimate_files = self.create_ultimate_files(projects, project_details)
        
        if ultimate_files:
            print(f"\n🎉 ULTIMATE FILES CREATED SUCCESSFULLY!")
            print(f"📁 CSV File: {os.path.basename(ultimate_files['csv'])}")
            print(f"📁 JSON File: {os.path.basename(ultimate_files['json'])}")
            print(f"📂 Location: {self.output_folder}")
            print(f"📊 Total projects: {len(projects)}")
            print(f"🔍 Total detailed pages scraped: {len(project_details)}")
        
        return ultimate_files

def main():
    """Main function to run the scraper"""
    scraper = InterregScraper()
    
    try:
        results = scraper.run_ultimate_scrape()
        if results:
            print(f"\n✅ Scraping completed successfully!")
            print(f"🎯 Your ultimate CSV file is ready in: {scraper.output_folder}")
        else:
            print("❌ Scraping failed. Please check the output above for details.")
    
    except KeyboardInterrupt:
        print("\n⏹️ Scraping interrupted by user.")
    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    main()
