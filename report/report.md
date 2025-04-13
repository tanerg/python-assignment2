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
- Downloaded raw COVID-19 case and hospital admission data (in CSV format) from public health sources.
- Retrieved municipality boundary data from PDOK’s WFS endpoint and saved it as GeoJSON.
- Loaded annual municipality population data from CBS, ensuring it aligns with administrative changes over time.

### 2. Data Cleaning (`dataframe_cleaner.py`)
- **Cases and Deaths**:
  - Parsed and standardized dates, filled missing municipality codes, and renamed columns for clarity.
  - Corrected outdated municipality codes due to mergers. For example, Brielle, Hellevoetsluis, and Westvoorne were merged into *Voorne aan Zee* (GM1992); codes and names were updated accordingly, and overlapping rows were aggregated.
  - Dummy values (e.g., `9999` or `19998`) found in death statistics were replaced with 0 to prevent misleading results.
  - Added `Year` and `Month` columns to support both monthly and yearly aggregations.

- **Hospital Admissions**:
  - Standardized date formats and filtered out incomplete records.
  - Aggregated data by municipality and date, and aligned municipality codes with the cases dataset.
  - Added `Year` and `Month` columns for temporal analysis.

- **Population Data**:
  - Mapped population data to municipalities using standardized codes.
  - Adjusted for municipality mergers using a mapping of outdated to current codes.
  - Special handling was applied for *Haaren*, which was dissolved and split into four existing municipalities. Its population was evenly distributed among **Boxtel**, **Oisterwijk**, **Tilburg**, and **Vught**.

### 3. Data Combination (`dataframe_combiner.py`)
- Combined cleaned cases and hospital datasets based on municipality and date.
- Merged population data to allow calculation of incidence rates (cases, deaths, hospitalizations per 100,000 people).
- Cleaned data was joined with geospatial boundaries to create GeoDataFrames at the municipality, province, and national levels.
- These GeoDataFrames were pre-aggregated and saved in GeoJSON format for both monthly and yearly intervals to support fast, interactive visualization.


### 4. Interactive Visualization Dashboard
Developed using Python libraries:
- **Pandas**: Data handling and analysis.
- **Plotly Express**: Interactive bar charts.
- **ipywidgets**: Interactive controls within Jupyter Notebook.
- **GeoPandas**: Geospatial data manipulation and integration with shapefiles and GeoJSON.
- **Folium**: Interactive choropleth maps and geographical visualizations.
- **Branca**: Custom color maps and legends for Folium.

Dashboard features:

### Interactive Map Functionality

We developed an interactive choropleth map using `folium` and `ipywidgets` that allows users to explore COVID-19 statistics across the Netherlands. The map visualizes the data on three geographical levels — **municipality**, **province**, and **national** — and supports both **monthly** and **yearly** aggregations.

Users can select:
- The **level of aggregation** (Municipality, Province, National),
- The **time granularity** (Monthly or Yearly),
- A **specific date** (automatically adapted to the chosen aggregation level),
- And the **statistic to display**, including:
  - Total reported cases,
  - Deaths,
  - Hospital admissions,
  - And their incidence rates per 100,000 inhabitants.

The visualization is based on pre-aggregated GeoJSON files to ensure performance. This interactive tool enables a clear and intuitive exploration of temporal and regional trends in the pandemic's impact.


## Challenges and Resolutions

## Conclusion
