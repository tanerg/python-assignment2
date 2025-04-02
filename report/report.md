# Covid-19 Dashboard Data Preparation and Visualization Report

## Overview
This document outlines the steps taken to prepare, clean, combine, and visualize Covid-19 data. The goal was to create an interactive dashboard that clearly shows trends in cases, hospital admissions, and deaths across the Netherlands at different locations and time periods.

## Data Sources
The data was sourced from official Dutch repositories providing:
- Covid-19 reported cases.
- Hospital admission records.
- Population data.
- Municipality location data.

## Data Preparation Steps

### 1. Data Acquisition (`data_loader.py`)
- Used functions to automatically download raw CSV datasets from public health websites.
- Loaded datasets directly into pandas DataFrames for further processing.
- Collected municipality location data in GeoJSON format from public services.

### 2. Data Cleaning (`dataframe_cleaner.py`)
- **Cases data**:
  - Converted dates, filled missing municipality codes, and renamed columns to make them clearer.
  - Handled merged municipalities (e.g., Brielle, Hellevoetsluis, Westvoorne into Voorne aan Zee).
  - Combined data by date and municipality and added 'Year' and 'Month' columns for easier grouping.
- **Hospital data**:
  - Standardized date fields and removed incomplete records.
  - Summarized hospital admissions by municipality and date.
  - Added 'Year' and 'Month' columns for easier time-based grouping.
- **Population data**:
  - Gathered municipality-level statistics, handled outdated municipality codes, and adjusted populations for merged municipalities.
  - Created a clean dataset suitable for calculating incidence rates.

### 3. Data Combination (`dataframe_combiner.py`)
- Merged cleaned cases and hospital admission datasets using date and municipality codes.
- Included population data to calculate incidence rates for cases, deaths, and hospital admissions per 100,000 residents.

### 4. Interactive Visualization Dashboard
Developed using Python libraries:
- **Pandas**: Data handling and analysis.
- **Plotly Express**: Interactive bar charts.
- **ipywidgets**: Interactive controls within Jupyter Notebook.

Dashboard features:


## Challenges and Resolutions

## Conclusion
