# Automated Lead Enrichment Engine (Make.com & Python)

This repository contains the architecture blueprints and data sanitization logic for a localized B2B lead generation engine.

## How It Works
1. **Extraction:** A Python script scrapes geo-located business data from Google Maps.
2. **Ingestion & Routing:** Data is passed via Webhook to Make.com.
3. **Logic Gate:** The pipeline checks if the business lacks a website or has low Google review counts.
4. **Delivery:** High-intent prospects are automatically appended to a Google Sheets CRM.

## Tech Stack
* Make.com (Advanced Routing & Webhooks)
* Python (Data Scraping & JSON Parsing)
