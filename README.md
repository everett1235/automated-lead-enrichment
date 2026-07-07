# Automated Lead Enrichment Engine (Make.com & Python)

This repository contains a custom object-oriented Selenium web scraper and the architecture blueprints for an automated, localized B2B lead generation pipeline.

## How It Works
1. **Targeted Extraction:** An object-oriented `GoogleMapsScraper` script built in Python uses Selenium WebDriver to bypass geolocational bounds, handle dynamic infinite scroll rendering, and extract high-yield business payloads.
2. **Data Sanitization:** The script natively uses Regular Expressions (`re`) and Pandas dataframes to split unstructured string addresses into normalized schema structures (Street, City, State, Zip) and instantly filter out businesses that already own active websites.
3. **Ingestion & Routing:** Cleansed data structures are exported to CSV and structured to pass via webhooks into Make.com.
4. **Logic Gate & Delivery:** The external automation layers cross-reference review gaps to identify high-intent outbound targets and append them to operational dashboards.

## Tech Stack
* **Languages:** Python (Selenium, Pandas, Regex)
* **Automation:** Make.com (Advanced Conditional Routing & Webhooks)
