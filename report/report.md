# Covid-19 Dashboard Data Preparation and Visualization Report

## Overview
This document outlines the steps taken to prepare, clean, combine, and visualize Covid-19 data. The goal was to create an interactive dashboard that clearly shows trends in cases, hospital admissions, and deaths across the Netherlands at different locations and time periods.


---

## Project Structure Explanation

### **Directory Overview**

```text
src/
├── config/
│   └── constants.py
├── data/
│   ├── loader.py
│   └── preprocessing.py
├── visualization/
│   ├── plotter.py
│   └── widgets.py
├── dashboard.ipynb
└── main.py
```

### **Configuration**

- **`config/constants.py`**
  - Contains constant values and configurations.
  - Example contents:
    - Mapping of month numbers to month names (`MONTH_MAPPING`).
    - Color codes used in visualizations (`COLOR_MAPPING`).

---

### **Data Handling**

- **`data/loader.py`**
  - Responsible for loading and preparing datasets.
  - Typical function:
    - `load_cleaned_data(filepath)`: Loads CSV data and sets correct data types.

- **`data/preprocessing.py`**
  - Contains functions for filtering and processing the data.
  - Typical function:
    - `filter_dataframe(df, year, province, municipality)`: Filters data based on user selections from the widgets.

---

### **Visualization**

- **`visualization/widgets.py`**
  - Defines interactive widgets used in the dashboard.
  - Examples:
    - Dropdowns (Year, Province, Municipality selection)
    - Checkboxes (Cases, Deaths, Hospital Admissions)
    - Radio buttons (Aggregation options: Year, Months, Municipalities)

- **`visualization/plotter.py`**
  - Creates interactive plots using Plotly.
  - Typical function:
    - `generate_bar_chart(...)`: Generates bar charts based on filtered data, applying consistent colors and layout.

---

### **Application Logic**

- **`main.py`**
  - Central Python script integrating all functionalities.
  - Provides the main interactive dashboard logic through a callable function (`run_dashboard()`).
  - Coordinates data loading, preprocessing, widget interactions, and visualizations.

---

### **Interactive Dashboard Notebook**

- **`dashboard.ipynb`**
  - Jupyter notebook serving as the user interface for running and interacting with the dashboard.
  - Calls and orchestrates components from all previously mentioned files.

---

This structured approach clearly organizes the project into logical sections, enhancing readability, maintainability, and extensibility.
"""

# Save this markdown content to a file
markdown_file_path = '/mnt/data/project_structure.md'
with open(markdown_file_path, 'w') as file:
    file.write(markdown_content)

markdown_file_path


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
