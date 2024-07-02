import sqlite3
import requests

# Fetch data from the API endpoint
def fetch_api_data():
    url = "https://apfs-cloud.dhs.gov/api/forecast/?_=1718887822326"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
        return []

# Connect to SQLite database
conn = sqlite3.connect('data.db')
c = conn.cursor()

# Create table if not exists
c.execute('''
CREATE TABLE IF NOT EXISTS data (
    id INTEGER PRIMARY KEY,
    organization TEXT,
    small_business_program TEXT,
    dollar_range TEXT,
    contract_vehicle TEXT,
    competitive TEXT,
    award_quarter TEXT,
    estimated_release_date DATE,
    publish_date DATE,
    naics TEXT,
    contract_type TEXT,
    apfs_number TEXT,
    requirements_title TEXT,
    requirement TEXT,
    contract_status TEXT,
    estimated_period_of_performance_start DATE,
    estimated_period_of_performance_end DATE,
    anticipated_award_date DATE,
    place_of_performance_city TEXT,
    place_of_performance_state TEXT,
    requirements_contact_first_name TEXT,
    requirements_contact_last_name TEXT,
    requirements_contact_email TEXT,
    alternate_contact_first_name TEXT,
    alternate_contact_last_name TEXT,
    alternate_contact_phone TEXT,
    alternate_contact_email TEXT,
    fiscal_year INTEGER,
    created_on DATE,
    requirements_office TEXT,
    contracting_office TEXT,
    apfs_coordinator_office TEXT,
    current_state TEXT,
    last_updated_date DATE,
    published_date DATE,
    previous_published_date DATE
)
''')
conn.commit()

# Function to insert data into the database
def insert_data(data):
    for entry in data:
        c.execute('''
        INSERT OR REPLACE INTO data (id, organization, small_business_program, dollar_range, contract_vehicle, competitive, award_quarter, 
        estimated_release_date, publish_date, naics, contract_type, apfs_number, requirements_title, requirement, contract_status, 
        estimated_period_of_performance_start, estimated_period_of_performance_end, anticipated_award_date, place_of_performance_city, 
        place_of_performance_state, requirements_contact_first_name, requirements_contact_last_name, requirements_contact_email, 
        alternate_contact_first_name, alternate_contact_last_name, alternate_contact_phone, alternate_contact_email, fiscal_year, 
        created_on, requirements_office, contracting_office, apfs_coordinator_office, current_state, last_updated_date, published_date, 
        previous_published_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
        (entry.get("id"), entry.get("organization"), entry.get("small_business_program"), entry["dollar_range"]["display_name"], entry.get("contract_vehicle"), 
        entry.get("competitive"), entry.get("award_quarter"), entry.get("estimated_release_date"), entry.get("publish_date"), entry.get("naics"), entry.get("contract_type"), 
        entry.get("apfs_number"), entry.get("requirements_title"), entry.get("requirement"), entry.get("contract_status"), entry.get("estimated_period_of_performance_start"), 
        entry.get("estimated_period_of_performance_end"), entry.get("anticipated_award_date"), entry.get("place_of_performance_city"), entry.get("place_of_performance_state"), 
        entry.get("requirements_contact_first_name"), entry.get("requirements_contact_last_name"), entry.get("requirements_contact_email"), 
        entry.get("alternate_contact_first_name"), entry.get("alternate_contact_last_name"), entry.get("alternate_contact_phone"), entry.get("alternate_contact_email"), 
        entry.get("fiscal_year"), entry.get("created_on"), entry.get("requirements_office"), entry.get("contracting_office"), entry.get("apfs_coordinator_office"), 
        entry.get("current_state"), entry.get("last_updated_date"), entry.get("published_date"), entry.get("previous_published_date")))
    conn.commit()

# Fetch data and insert into database
api_data = fetch_api_data()
if api_data:
    insert_data(api_data)

# Close the database connection
conn.close()
