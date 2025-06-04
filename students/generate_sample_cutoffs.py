import pandas as pd
import numpy as np

# Create a sample dataset for the Streamlit app
def generate_sample_cutoffs():
    # Define sample values for each field
    colleges = [
        ('1002', 'Government College of Engineering, Amravati'),
        ('1012', 'Government College of Engineering, Yavatmal'),
        ('2008', 'Government College of Engineering, Aurangabad'),
        ('3012', 'Veermata Jijabai Technological Institute(VJTI), Mumbai'),
        ('4025', 'Government College of Engineering, Nagpur'),
        ('5004', 'Government College of Engineering, Jalgaon'),
        ('6006', 'COEP Technological University'),
        ('6207', 'Dr. D. Y. Patil Institute of Technology, Pimpri, Pune')
    ]
    
    courses = [
        ('100219110', 'Civil Engineering'),
        ('421019210', 'Computer Science and Engineering'),
        ('461019610', 'Information Technology'),
        ('931019310', 'Electrical Engineering'), 
        ('721017210', 'Electronics and Telecommunication Engg'),
        ('121011210', 'Mechanical Engineering'),
        ('951019510', 'Artificial Intelligence and Data Science'),
        ('071010710', 'Chemical Engineering')
    ]
    
    categories = ['GOPENS', 'GOBCS', 'GNT1S', 'LOPENH', 'DEFOPENS', 'TFWS', 'PWDOPENS', 'ORPHAN']
    
    statuses = ['Government', 'Government Autonomous', 'Private', 'University Department', 'Government Aided']
    
    seat_types = ['State Level', 'Home University', 'Other University']
    
    # Create empty list to store data
    data = []
    
    # Generate sample data
    for college_code, college_name in colleges:
        for course_code, course_name in courses:
            for category in categories:
                # Generate realistic rank and percentage values
                # Top government colleges have lower ranks (better)
                college_factor = 1.0
                if 'Government' in college_name:
                    if 'VJTI' in college_name or 'COEP' in college_name:
                        college_factor = 0.5  # Top colleges
                    else:
                        college_factor = 0.8  # Other government colleges
                
                # Certain courses are more competitive
                course_factor = 1.0
                if 'Computer' in course_name or 'Information Technology' in course_name:
                    course_factor = 0.7  # Most competitive
                elif 'Electronics' in course_name or 'Electrical' in course_name:
                    course_factor = 0.85
                    
                # Different categories have different cutoffs
                category_factor = 1.0
                if category == 'GOPENS':
                    category_factor = 0.6  # Most competitive
                elif category == 'GOBCS':
                    category_factor = 0.8
                elif category == 'TFWS':
                    category_factor = 0.7
                
                # Calculate rank and percentage
                base_rank = int(np.random.randint(5000, 100000) * college_factor * course_factor * category_factor)
                # Higher rank (worse) corresponds to lower percentage
                percentage = 100 - (base_rank / 100000 * 30)  # Range approx 70-95%
                
                # Select random status and seat type
                if 'Government' in college_name:
                    status = np.random.choice([s for s in statuses if 'Government' in s])
                else:
                    status = np.random.choice(statuses)
                
                seat_type = np.random.choice(seat_types)
                
                # Add to data
                data.append({
                    'college_code': college_code,
                    'college_name': college_name,
                    'course_code': course_code,
                    'course_name': course_name,
                    'category': category,
                    'rank': base_rank,
                    'percentage': round(percentage, 2),
                    'status': status,
                    'university': '',  # Leave empty for simplicity
                    'seat_type': seat_type
                })
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Save to CSV
    df.to_csv('mht_cet_cutoffs.csv', index=False)
    
    print(f"Generated {len(df)} sample cutoff records")
    print(f"Sample data saved to mht_cet_cutoffs.csv")
    
    return df

if __name__ == "__main__":
    generate_sample_cutoffs()

