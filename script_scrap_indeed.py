import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import csv
import re
import time
import os
import html

CHROMEDRIVER_PATH = r"C:\Users\xelor\Downloads\Chromedriver\chromedriver-win64\chromedriver.exe"
CSV_FILE_PATH = r"C:\Users\xelor\Downloads\MGMT Project\indeed_raw_data3.csv"

def write_to_csv(row_data):
    if len(row_data) == 1 and isinstance(row_data[0], tuple):
        row_data = row_data[0]
    with open(CSV_FILE_PATH, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(row_data)

if not os.path.exists(CSV_FILE_PATH) or os.path.getsize(CSV_FILE_PATH) == 0:
    write_to_csv(['Job Title', 'Company Name', 'Location', 'Skills',
                  'Years of Experience', 'Education', 'Job Type', 'Salary'])

def find_skills_in_description(description, skill_set, aws_synonyms):
    found_skills = set()
    description_lower = description.lower()
    
    for skill in skill_set:
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, description_lower):
            found_skills.add(skill)

    for aws_term, aws_skill in aws_synonyms.items():
        pattern = r'\b' + re.escape(aws_term) + r'\b'
        if re.search(pattern, description_lower):
            found_skills.add(aws_skill)

    return list(found_skills)

def find_years_of_experience(description):
    patterns = [
        r'(\d+)\s*-\s*(\d+)\s*years',
        r'(\d+)\s*\+\s*years',
        r'(\d+)\s*years',
        r'(\d+)\s*to\s*(\d+)\s*years',
        r'at least\s*(\d+)\s*years',
        r'minimum of\s*(\d+)\s*years',
        r'(\d+)\s*years experience minimum',
        r'a minimum of\s*(\d+)\s*years',
        r'min\.?\s*(\d+)\s*years',
        r'min\s*(\d+)\s*yrs',
        r'(\d+)\s*yrs\s*min\.?',
        r'(\d+)\+?\s*yrs',
        r'(\d+)\s*y\+\s*experience',
        r'more than\s*(\d+)\s*years',
        r'over\s*(\d+)\s*years',
        r'from\s*(\d+)\s*years',
        r'starting at\s*(\d+)\s*years',
        r'(\d+)\s*or more years',
        r'(\d+)\s*years or greater',
        r'at least\s*(\d+)\s*professional',
        r'(\d+)\s*years of relevant experience minimum',
        r"(\d+)\+ yrs",
        r"<(\d+) years",
        r"(\d+)-(\d+)y",
        r">=(\d+) years",
        r"(\d+) years\+",
        r"Min. (\d+) years",
        r"(\d+)\+ years preferred",
        r"Up to (\d+) years",
        r"At least (\d+) yr",
        r"Over (\d+) years required"
    ]

    max_years = 0
    for pattern in patterns:
        matches = re.findall(pattern, description.lower())
        for match in matches:
            if isinstance(match, tuple):
                years = max(int(y) for y in match if y.isdigit())
            else:
                years = int(match)
            max_years = max(max_years, years)

    return max_years if max_years != 0 else "Not specified"

def process_salary_field(salary_field):
    salary_annual_pattern = r'\$(\d{1,3}(?:,\d{3})*) - \$(\d{1,3}(?:,\d{3})*) a year'
    salary_annual_simple_pattern = r'\$(\d{1,3}(?:,\d{3})*) a year'
    salary_hourly_pattern = r'\$(\d{1,3}(?:,\d{3})*) per hour'
    salary_hourly_range_pattern = r'\$(\d{1,3}(?:,\d{3})*) - \$(\d{1,3}(?:,\d{3})*) per hour'
    salary_hourly_slash_pattern = r'(\d{1,3}(?:,\d{3})*)\$/hr'
    salary_hourly_an_hour_pattern = r'\$(\d{1,3}(?:,\d{3})*) - \$(\d{1,3}(?:,\d{3})*) an hour'

    salary_annual = re.search(salary_annual_pattern, salary_field, re.IGNORECASE)
    salary_annual_simple = re.search(salary_annual_simple_pattern, salary_field, re.IGNORECASE)
    salary_hourly = re.search(salary_hourly_pattern, salary_field, re.IGNORECASE)
    salary_hourly_range = re.search(salary_hourly_range_pattern, salary_field, re.IGNORECASE)
    salary_hourly_slash = re.search(salary_hourly_slash_pattern, salary_field, re.IGNORECASE)
    salary_hourly_an_hour = re.search(salary_hourly_an_hour_pattern, salary_field, re.IGNORECASE)

    salary = "Not specified"
    job_type = "Not specified"

    if salary_annual:
        salary = "{} - {} a year".format(salary_annual.group(1), salary_annual.group(2))
    elif salary_annual_simple:
        salary = "{} a year".format(salary_annual_simple.group(1))
    elif salary_hourly_range:
        salary = "{} - {} per hour".format(salary_hourly_range.group(1), salary_hourly_range.group(2))
    elif salary_hourly_slash:
        salary = "{} per hour".format(salary_hourly_slash.group(1))
    elif salary_hourly_an_hour:
        salary = "{} - {} an hour".format(salary_hourly_an_hour.group(1), salary_hourly_an_hour.group(2))
    elif salary_hourly:
        salary = "{} per hour".format(salary_hourly.group(1))

    type_pattern = r'(Full-time|Part-time|Internship)'
    type_match = re.search(type_pattern, salary_field, re.IGNORECASE)
    if type_match:
        job_type = type_match.group(1)

    return salary, job_type

def find_salary_in_description(description):
    patterns = [
        r"\$(\d{1,3}(?:,\d{3})*) per year",
        r"\$(\d{1,3}(?:,\d{3})*) a year",
        r"\$(\d{1,3}(?:,\d{3})*) annually",
        r"\$(\d{1,3}(?:,\d{3})*) each year",
        r"(\d{1,3}(?:,\d{3})*) USD per year",
        r"(\d{1,3}(?:,\d{3})*) dollars per year",
        
        r"\$(\d{1,3}(?:,\d{3})*) per month",
        r"\$(\d{1,3}(?:,\d{3})*) a month",
        r"\$(\d{1,3}(?:,\d{3})*) monthly",
        r"(\d{1,3}(?:,\d{3})*) USD per month",
        r"(\d{1,3}(?:,\d{3})*) dollars per month",
        
        r"\$(\d{1,3}(?:,\d{3})*) per hour",
        r"\$(\d{1,3}(?:,\d{3})*) an hour",
        r"\$(\d{1,3}(?:,\d{3})*) hourly",
        r"(\d{1,3}(?:,\d{3})*) USD per hour",
        r"(\d{1,3}(?:,\d{3})*) dollars per hour",
        
        r"\$(\d{1,3}(?:,\d{3})*) - \$(\d{1,3}(?:,\d{3})*) per year",
        r"\$(\d{1,3}(?:,\d{3})*) to \$(\d{1,3}(?:,\d{3})*) a year",
        r"\$(\d{1,3}(?:,\d{3})*) - \$(\d{1,3}(?:,\d{3})*) annually",
        r"(\d{1,3}(?:,\d{3})*) - (\d{1,3}(?:,\d{3})*) USD each year",
        r"(\d{1,3}(?:,\d{3})*) to (\d{1,3}(?:,\d{3})*) dollars per year",

        r"\$(\d{1,3}(?:,\d{3})*) - \$(\d{1,3}(?:,\d{3})*) per month",
        r"\$(\d{1,3}(?:,\d{3})*) to \$(\d{1,3}(?:,\d{3})*) a month",
        r"\$(\d{1,3}(?:,\d{3})*) - \$(\d{1,3}(?:,\d{3})*) monthly",
        r"(\d{1,3}(?:,\d{3})*) - (\d{1,3}(?:,\d{3})*) USD per month",
        r"(\d{1,3}(?:,\d{3})*) to (\d{1,3}(?:,\d{3})*) dollars per month",

        r"\$(\d{1,3}(?:,\d{3})*) - \$(\d{1,3}(?:,\d{3})*) per hour",
        r"\$(\d{1,3}(?:,\d{3})*) to \$(\d{1,3}(?:,\d{3})*) an hour",
        r"\$(\d{1,3}(?:,\d{3})*) - \$(\d{1,3}(?:,\d{3})*) hourly",
        r"(\d{1,3}(?:,\d{3})*) - (\d{1,3}(?:,\d{3})*) USD per hour",
        r"(\d{1,3}(?:,\d{3})*) to (\d{1,3}(?:,\d{3})*) dollars per hour"

        r'\$(\d+)(k|K)/year',
        r'\$(\d{1,3}(?:,\d{3})*)/yr',
        r'USD (\d+)(k|K) annually',
        r'(\d+)(K|k) USD a year',
        r'Salary:\s*\$(\d{1,3}(?:,\d{3})*)',
        r'Salary Range:\s*\$(\d{1,3}(?:,\d{3})*) to \$(\d{1,3}(?:,\d{3})*)',
        r'\$(\d+)-(\d+)(K|k) annually',
        r'Annual Pay:\s*\$(\d+)K-\$(\d+)K',
        r'Salary:\s*\$(\d{1,3}(?:,\d{3})*)-\$(\d{1,3}(?:,\d{3})*) per annum',
        r'Pay scale:\s*\$(\d+)(k|K) to \$(\d+)(k|K) per year',
        r'Hourly Wage:\s*\$(\d+)-\$(\d+)',
        r'Monthly Salary:\s*\$(\d{1,3}(?:,\d{3})*) to \$(\d{1,3}(?:,\d{3})*)',
        r'\$(\d+) to \$(\d+) per hour',
        r'\$(\d+)(K|k)-\$(\d+\.?\d*)(K|k) per month',
        r"\$(\d+K)\+",
        r"Up to \$(\d+K)",
        r"From \$(\d+,\d+) to \$(\d+,\d+)",
        r">\$(\d+,\d+) depending on experience",
        r"~\$(\d+K)",
        r"(\d+)-(\d+)k per annum",
        r"\$(\d+)/hr",
        r"\$(\d+) monthly",
        r"Annual: \$(\d+)K",
        r"Hourly Rate: \$(\d+)\+"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            if match.lastindex == 2:
                return "${} - ${} {}".format(match.group(1), match.group(2), pattern.split()[-3])
            return "${} {}".format(match.group(1), pattern.split()[-3])
    return "Not specified"

def find_education_requirements(description):
    education_levels = {
        "Bachelor": ["bachelor's", "bachelors", "bachelor", "undergraduate"],
        "Master": ["master's", "masters", "master"],
        "Doctorate": ["ph.d", "phd", "doctorate", "doctoral"]
    }
    found_levels = set()

    for level, keywords in education_levels.items():
        if any(keyword in description.lower() for keyword in keywords):
            found_levels.add(level)

    return ", ".join(found_levels) if found_levels else "Not Specified"

def clean_salary_data(salary_element, full_description):
    standard_salary_format = r'\$\d{1,3}(?:,\d{3})*(?: - \$\d{1,3}(?:,\d{3})*)? a year'
    salary_match = re.search(standard_salary_format, salary_element)
    if salary_match:
        return salary_match.group(0)
    else:
        alternative_formats = [
            r'\b(\d{1,3}(?:,\d{3})* - \d{1,3}(?:,\d{3})*) (USD|usd|dollars)\b',
            r'\$\d{1,3}(?:,\d{3})*(?: - \$\d{1,3}(?:,\d{3})*)? a year',
            r'\$\d{1,3}(?:,\d{3})*(?: - \$\d{1,3}(?:,\d{3})*)?',
            r'\b(\d{1,3}(?:,\d{3})* - \d{1,3}(?:,\d{3})*)\b'
        ]
        for pattern in alternative_formats:
            salary_match = re.search(pattern, full_description, re.IGNORECASE)
            if salary_match:
                return salary_match.group(0) + ' USD a year'
        return "Not specified"

def clear_salary_data(salary):
    salary = re.sub(r'\s*-\s*(Full[-\s]*time|Part[-\s]*time)$', '', salary, flags=re.IGNORECASE)
    if re.search(r'\$\d+,\d+ - \$\d+,\d+ a year', salary):
        return salary
    else:
        return "Not specified"

def clean_text(text):
    text = html.unescape(text)
    text = text.replace('\n', ' ').replace('\r', '').replace('\t', ' ')
    text = ' '.join(text.split())
    return text

def clean_text_final(text):
    return text.replace('\n', ' ').replace('\r', '').replace(',', ';')


skill_list = [
    "Python", "C#", "C++", "Agile", "SQL", "MySQL", "Perl", "Java", "Git", "JSON",
    "Jira", "Project Management", "Feature Extraction", "MLOps", "AI", "Deep Learning",
    "Hypothesis testing", "Forecasting", "XML", "Machine Learning", "Microsoft SQL Server",
    "SAS", "Cloud Computing", "R", "Go", "Scala", "Data Analytics", "Statistics",
    "Data Mining", "Data Analysis", "Analytics", "Statistical Analysis", "MATLAB",
    "Machine Learning Algorithms", "Natural Language Processing", "Computer Vision",
    "Big Data", "Hadoop", "Spark", "Pig", "Apache Hive", "Graph Databases", "Tableau",
    "Computer Science", "Power BI", "Excel", "Matplotlib", "Seaborn", "Pandas", "NumPy", "SciPy",
    "Scikit-learn", "TensorFlow", "Keras", "PyTorch", "AWS", "Azure", "Google Cloud",
    "Docker", "Kubernetes", "APIs", "REST", "GraphQL", "NoSQL", "MongoDB", "Cassandra", "HBase",
    "Distributed Systems", "Snowflake", "Github", "Kafka", "Data lake", "Encryption",
    "Data Visualization", "Data Engineering", "Predictive Analysis", "Data Warehouse",
    "Software development", "A/B Testing", "Scripting", "Analysis Skills", "Data Analysis Skills",
    "CI/CD", "Cloud Architecture", "SPSS", "Julia", "Data Structures", "GLM", "Redshift",
    "Reinforcement Learning", "Regression Analysis", "Linux", "Unix", "Machine learning frameworks",
    "Project Management", "Product Management", "Marketing", "Banking", "Presentation Skills",
    "Quantitative analysis", "Accounting", "Business Analysis", "Project Leadership", "Sales",
    "Risk Management", "Team Management", "Statistical Software", "Leadership", "Research", "Financial Services"
]

aws_synonyms = {
    "ec2": "AWS",
    "s3": "AWS",
    "amazon web services": "AWS",
    "elastic compute cloud": "AWS",
    "simple storage service": "AWS",
    "rds": "AWS",
    "lambda": "AWS",
    "dynamodb": "AWS",
    "aws lambda": "AWS",
    "amazon rds": "AWS"
}

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.2420.81",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 OPR/109.0.0.0",
]

options = Options()
options.add_argument(f"user-agent={random.choice(user_agents)}")
options.headless = True
service = Service(executable_path=CHROMEDRIVER_PATH)
driver = webdriver.Chrome(service=service, options=options)

# driver.get("https://www.indeed.com/jobs?q=data+scientist&l=New+York%2C+NY")
driver.get("https://www.indeed.com/q-data-scientist-l-United-States-jobs.html?vjk=4f9abc9f3a2fc313")
time.sleep(random.randint(5, 10))
time.sleep(random.uniform(3, 5))

wait = WebDriverWait(driver, 20)

results = []
max_pages = 350
current_page = 1

while current_page <= max_pages:
    job_cards = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'job_seen_beacon')))
    time.sleep(random.uniform(3, 7))

    for index, card in enumerate(job_cards, start=1):
        try:
            print(f"Processing card {index}")
            job_title = card.find_element(By.CSS_SELECTOR, 'h2.jobTitle').text.strip()
            print(f"Job title found: {job_title} \n")
            time.sleep(random.uniform(3, 5))
            
            company_name = card.find_element(By.CSS_SELECTOR, 'span[data-testid="company-name"]').text.strip()
            print(f"Company name found: {company_name} \n")
            time.sleep(random.uniform(3, 5))

            location = card.find_element(By.CSS_SELECTOR, 'div[data-testid="text-location"]').text.strip()
            print(f"Location found: {location} \n")
            time.sleep(random.uniform(3, 5))

            # summary = card.find_element(By.CSS_SELECTOR, 'ul').text.strip()
            # print(f"Job Summary found: {summary} \n")
            # time.sleep(random.uniform(3, 7))

            card.click()  
            print("Clicked on card \n")
            time.sleep(random.uniform(3, 5))

            try:
                full_job_description_element = WebDriverWait(driver, 20).until(
                    EC.visibility_of_element_located((By.ID, 'jobDescriptionText')))
                full_job_description = clean_text(full_job_description_element.text)
                print("Full job description extracted with success \n")
                time.sleep(random.uniform(3, 5))
            except TimeoutException:
                full_job_description = "Full job description not found"
                print("Full job description not found")

            try:
                print("Waiting for salary and job infos ... \n")
                salary_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, 'salaryInfoAndJobType'))
                )
                salary_text = salary_element.text.strip()
                salary, job_type = process_salary_field(salary_text)

                if salary == "Not specified":
                    print("Salary not found in the initial field, checking full job description... \n")
                    salary = find_salary_in_description(full_job_description)
                
                print(f"Salary info extracted: {salary} \n")
                print(f"Job type found: {job_type} \n")

                time.sleep(random.uniform(3, 5))
            except TimeoutException:
                salary = "Not specified"
                job_type = "Not specified"
                print(f"Salary and Job infos not found for card {index}")

            years_experience_list = find_years_of_experience(full_job_description)
            print(f"Years of experience found: {years_experience_list} \n")
            time.sleep(random.uniform(3, 5))

            education_level = find_education_requirements(full_job_description)
            print(f"Education requirements found: {education_level} \n")
            time.sleep(random.uniform(3, 5))

            found_skills = find_skills_in_description(full_job_description, skill_list, aws_synonyms)
            
            print(f"Skills found: {found_skills} \n")
            time.sleep(random.uniform(3, 5))

            if index == len(job_cards):
                try:
                    next_button = driver.find_element(By.CSS_SELECTOR, 'a[data-testid="pagination-page-next"]')
                    if next_button.get_attribute('aria-label') == 'Next Page':
                        next_button.click()
                        print(f"Passage à la page {current_page + 1}")
                        current_page += 1
                        wait.until(EC.staleness_of(job_cards[0]))
                    else:
                        print("Dernière page atteinte ou bouton 'Suivant' non cliquable.")
                        break
                except NoSuchElementException:
                    print("Bouton 'Suivant' non trouvé, possible fin des résultats.")
                    break
            
            data_to_write = [
                clean_text_final(job_title), clean_text_final(company_name), clean_text_final(location), ', '.join([clean_text_final(skill) for skill in found_skills]),
                str(years_experience_list), clean_text_final(education_level), clean_text_final(job_type), clean_text_final(salary)
            ]

            write_to_csv(data_to_write)

        except Exception as e:
            print(f"Error on card {index}: {e}")
            continue


driver.quit()
print("Scraping terminé et données enregistrées.")
