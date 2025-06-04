import re
import json
import pandas as pd
import os
import io
from tqdm import tqdm
import logging
import pdfplumber  # More powerful PDF parsing library
import traceback
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mht_cet_parser.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Set to True to enable more detailed debugging
DEBUG = True

class MHTCutoffParser:
    def __init__(self, pdf_path):
        """Initialize the parser with the PDF file path."""
        self.pdf_path = pdf_path
        self.data = []
        self.raw_data = []  # Store raw extracted data for debugging
        
        # Pattern for college information: 4-digit code followed by name
        self.college_pattern = re.compile(r'(\d{4})\s*-\s*(.+?)(?=\n|\r|$)')
        
        # Pattern for course information: 8-9 digit code followed by name
        self.course_pattern = re.compile(r'(\d{8,9})\s*-\s*(.+?)(?=\n|\r|Status:|$)')
        
        # Pattern for status information
        self.status_pattern = re.compile(r'Status:\s*(.+?)(?=\n|\r|Home University|$)')
        
        # Pattern for university information
        self.university_pattern = re.compile(r'Home University\s*:\s*(.+?)(?=\n|\r|$)')
        
        # Categories often look like GOPENS, GSTS, GOBCS, DEFOPENS, etc.
        # More comprehensive pattern to capture various category formats
        self.category_pattern = re.compile(r'^([A-Z][A-Z0-9]+[A-Z0-9]*H?S?)$')
        
        # Pattern to extract rank (a number by itself on a line)
        self.rank_pattern = re.compile(r'^(\d{1,6})$')
        
        # Pattern to extract percentage (in parentheses)
        self.percentage_pattern = re.compile(r'^\((\d+\.\d+)\)$')
        
        # Special handling for known colleges
        self.special_colleges = {
            "3014": "Sardar Patel College of Engineering, Andheri",
            "3215": "Bhartiya Vidya Bhavan's Sardar Patel Institute of Technology, Andheri, Mumbai"
        }
        
        # Store current parsing state
        self.current_college = None
        self.current_course = None
        self.current_status = None
        self.current_university = None
        self.current_seat_type = None
        
        # Debug flag
        self.debug = DEBUG
        
    def extract_text_from_pdf(self):
        """Extract text from all pages of the PDF using pdfplumber."""
        logger.info(f"Starting text extraction from {self.pdf_path}")
        
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                num_pages = len(pdf.pages)
                logger.info(f"PDF has {num_pages} pages")
                
                all_text = []
                all_tables = []
                
                for i in tqdm(range(num_pages), desc="Extracting text from PDF"):
                    try:
                        page = pdf.pages[i]
                        
                        # Extract text
                        text = page.extract_text()
                        all_text.append(text)
                        
                        # Also extract tables for more structured data
                        tables = page.extract_tables()
                        if tables:
                            all_tables.append((i+1, tables))
                            
                        # Debug: Save first few pages as images for visual inspection
                        if self.debug and i < 10:
                            img = page.to_image()
                            img.save(f"debug_page_{i+1}.png")
                            
                    except Exception as e:
                        logger.error(f"Error extracting text from page {i+1}: {str(e)}")
                        if self.debug:
                            logger.error(traceback.format_exc())
                
                # Store tables for later processing
                self.extracted_tables = all_tables
                
                return all_text
        except Exception as e:
            logger.error(f"Error opening PDF: {str(e)}")
            if self.debug:
                logger.error(traceback.format_exc())
            return []
    
    def parse_college_info(self, text):
        """Extract college code and name from text."""
        match = self.college_pattern.search(text)
        if match:
            code = match.group(1).strip()
            name = match.group(2).strip()
            
            # Apply special handling for known colleges
            if code in self.special_colleges:
                name = self.special_colleges[code]
                logger.info(f"Applied special handling for college: {code} - {name}")
                
            return code, name
        return None, None
    
    def parse_course_info(self, text):
        """Extract course code and name from text."""
        match = self.course_pattern.search(text)
        if match:
            code = match.group(1).strip()
            name = match.group(2).strip()
            
            # Clean up course name
            name = name.replace('\n', ' ').replace('\r', ' ').strip()
            
            return code, name
        return None, None
    
    def parse_status_and_university(self, text):
        """Extract college status and university from text."""
        status_match = self.status_pattern.search(text)
        status = status_match.group(1).strip() if status_match else "Unknown"
        
        university_match = self.university_pattern.search(text)
        university = university_match.group(1).strip() if university_match else ""
        
        return status, university
    
    def determine_seat_type(self, text):
        """Determine the seat type from text."""
        if "Home University Seats" in text:
            return "Home University"
        elif "Other Than Home University Seats" in text:
            return "Other University"
        else:
            return "State Level"
    
    def is_category(self, text):
        """Check if the given text is a category code."""
        return self.category_pattern.match(text) is not None
    
    def is_rank(self, text):
        """Check if the given text is a rank number."""
        return self.rank_pattern.match(text) is not None
    
    def is_percentage(self, text):
        """Check if the given text is a percentage value."""
        return self.percentage_pattern.match(text) is not None
    
    def extract_category_rank_percentage(self, lines):
        """
        Extract categories, ranks, and percentages from a list of lines.
        Returns a dict mapping categories to (rank, percentage) tuples.
        """
        cutoffs = {}
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
                
            # Check if this line contains a category
            if self.is_category(line):
                category = line
                
                # Look ahead for rank and percentage
                if i + 2 < len(lines):
                    rank_line = lines[i+1].strip()
                    percentage_line = lines[i+2].strip()
                    
                    rank_match = self.rank_pattern.match(rank_line)
                    percentage_match = self.percentage_pattern.match(percentage_line)
                    
                    if rank_match and percentage_match:
                        rank = int(rank_match.group(1))
                        percentage = float(percentage_match.group(1))
                        
                        cutoffs[category] = {
                            "rank": rank,
                            "percentage": percentage
                        }
                        
                        logger.debug(f"Found cutoff: {category} - Rank: {rank}, Percentage: {percentage}")
                        i += 3  # Skip the next two lines (rank and percentage)
                        continue
            
            i += 1
            
        return cutoffs

    def parse_pdf(self):
        """Parse the entire PDF and extract structured data."""
        logger.info("Starting PDF parsing")
        
        # Extract text from PDF
        pages_text = self.extract_text_from_pdf()
        if not pages_text:
            logger.error("Failed to extract text from PDF")
            return
        
        # Initialize variables to track current state
        current_college_code = None
        current_college_name = None
        current_course_code = None
        current_course_name = None
        current_status = None
        current_university = None
        current_seat_type = "State Level"  # Default seat type
        
        # Process pages sequentially as the information may span multiple pages
        for i, text in tqdm(enumerate(pages_text), desc="Parsing pages", total=len(pages_text)):
            if self.debug and i < 20:
                logger.info(f"Processing page {i+1}, content sample: {text[:100]}...")
                
            lines = text.split('\n')
            j = 0
            
            while j < len(lines):
                line = lines[j].strip()
                
                # Skip header lines and empty lines
                if not line or "Government of Maharashtra" in line or "State Common Entrance Test Cell" in line:
                    j += 1
                    continue
                
                # Try to match college pattern
                college_match = self.college_pattern.search(line)
                if college_match:
                    current_college_code = college_match.group(1)
                    current_college_name = college_match.group(2).strip()
                    
                    # Apply special handling for known colleges
                    if current_college_code in self.special_colleges:
                        current_college_name = self.special_colleges[current_college_code]
                    
                    logger.info(f"Found college: {current_college_code} - {current_college_name} on page {i+1}")
                    j += 1
                    continue
                
                # Try to match course pattern
                course_match = self.course_pattern.search(line)
                if course_match and current_college_code:
                    current_course_code = course_match.group(1)
                    current_course_name = course_match.group(2).strip()
                    logger.info(f"Found course: {current_course_code} - {current_course_name} on page {i+1}")
                    
                    # Look for status in the next few lines
                    for k in range(j+1, min(j+5, len(lines))):
                        status_match = self.status_pattern.search(lines[k])
                        if status_match:
                            current_status = status_match.group(1).strip()
                            logger.debug(f"Found status: {current_status}")
                            break
                    
                    # Look for university in the next few lines
                    for k in range(j+1, min(j+5, len(lines))):
                        univ_match = self.university_pattern.search(lines[k])
                        if univ_match:
                            current_university = univ_match.group(1).strip()
                            logger.debug(f"Found university: {current_university}")
                            break
                    
                    # Determine seat type
                    current_seat_type = self.determine_seat_type(text)
                    
                    # After finding a course, look for category and cutoff data in the next 30-50 lines
                    next_lines = lines[j+1:min(j+50, len(lines))]
                    cutoffs = self.extract_category_rank_percentage(next_lines)
                    
                    if cutoffs:
                        for category, cutoff_data in cutoffs.items():
                            entry = {
                                "college_code": current_college_code,
                                "college_name": current_college_name,
                                "course_code": current_course_code,
                                "course_name": current_course_name,
                                "status": current_status or "Unknown",
                                "university": current_university or "",
                                "seat_type": current_seat_type,
                                "category": category,
                                "rank": cutoff_data["rank"],
                                "percentage": cutoff_data["percentage"],
                                "page": i+1
                            }
                            
                            self.data.append(entry)
                            logger.debug(f"Added cutoff: {category} - Rank: {cutoff_data['rank']}, Percentage: {cutoff_data['percentage']}")
                    
                    j += 1
                    continue
                
                # Direct detection of categories and cutoffs (alternative approach)
                if current_college_code and current_course_code:
                    # Try to identify if the current line is a category
                    if self.is_category(line):
                        category = line
                        
                        # Check if the next lines contain rank and percentage
                        if j+2 < len(lines):
                            rank_line = lines[j+1].strip()
                            percentage_line = lines[j+2].strip()
                            
                            # Check if we have a valid rank and percentage
                            if self.is_rank(rank_line) and self.is_percentage(percentage_line):
                                rank = int(self.rank_pattern.match(rank_line).group(1))
                                percentage = float(self.percentage_pattern.match(percentage_line).group(1))
                                
                                # Create entry
                                entry = {
                                    "college_code": current_college_code,
                                    "college_name": current_college_name,
                                    "course_code": current_course_code,
                                    "course_name": current_course_name,
                                    "status": current_status or "Unknown",
                                    "university": current_university or "",
                                    "seat_type": current_seat_type,
                                    "category": category,
                                    "rank": rank,
                                    "percentage": percentage,
                                    "page": i+1
                                }
                                
                                self.data.append(entry)
                                logger.debug(f"Added cutoff directly: {category} - Rank: {rank}, Percentage: {percentage}")
                                
                                # Skip the processed lines
                                j += 3
                                continue
                
                # Move to next line
                j += 1
        
        # Check if we found special colleges
        special_colleges_found = set()
        for item in self.data:
            if item['college_code'] in self.special_colleges:
                special_colleges_found.add(item['college_code'])
        
        for code in self.special_colleges:
            if code in special_colleges_found:
                logger.info(f"Successfully extracted data for special college: {code} - {self.special_colleges[code]}")
            else:
                logger.warning(f"No data found for special college: {code} - {self.special_colleges[code]}")
        
        logger.info(f"Parsing complete. Extracted {len(self.data)} entries.")
    
    def save_to_json(self, output_path="mht_cet_cutoffs.json"):
        """Save the parsed data to a JSON file."""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(self.data)} records to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving to JSON: {str(e)}")
            return False
    
    def save_to_csv(self, output_path="mht_cet_cutoffs.csv"):
        """Save the parsed data to a CSV file."""
        try:
            # The data is already in a flattened format, ready for CSV
            df = pd.DataFrame(self.data)
            df.to_csv(output_path, index=False, encoding='utf-8')
            logger.info(f"Saved {len(self.data)} records to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving to CSV: {str(e)}")
            return False

def main():
    pdf_path = "2022ENGG_CAP3_CutOff.pdf"
    
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        return
    
    parser = MHTCutoffParser(pdf_path)
    parser.parse_pdf()
    
    # Output basic statistics
    logger.info(f"Extracted {len(parser.data)} cutoff entries")
    
    if len(parser.data) > 0:
        # Get unique colleges and courses
        colleges = set([(item['college_code'], item['college_name']) for item in parser.data])
        courses = set([(item['course_code'], item['course_name']) for item in parser.data])
        categories = set([item['category'] for item in parser.data])
        
        logger.info(f"Found {len(colleges)} unique colleges")
        logger.info(f"Found {len(courses)} unique courses")
        logger.info(f"Found {len(categories)} unique categories")
        
        # Save in both formats
        parser.save_to_json()
        parser.save_to_csv()
        
        # Output a sample of the data
        logger.info("Sample of extracted data:")
        for i, entry in enumerate(parser.data[:3]):
            logger.info(f"Sample {i+1}: {entry}")
    else:
        logger.error("No data was extracted from the PDF. Check patterns and parsing logic.")
    
    logger.info("Processing complete")

if __name__ == "__main__":
    main()

