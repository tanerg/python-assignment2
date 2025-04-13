# Covid-19 Dashboard Data Preparation and Visualization Report

## Overview
For this assignment, we created interactive dashboard for displaying Covid-19 data in Netherlands. Our goal was to show how pandemic affected different regions and time periods. Dashboard allows users to see cases, hospital admissions and deaths with charts and maps.

---

## Project Structure

### **Directory Overview**

```text
/
├── data/                # Data files (raw and processed)
│   ├── cases_1.csv      # Case data (first period)
│   ├── cases_2.csv      # Case data (second period)
│   ├── data_cleaned.csv # Combined and processed data
│   └── geodata/         # Geospatial data for maps
├── src/
│   ├── config/
│   │   └── constants.py # Color mappings, month names
│   ├── data/
│   │   ├── data_loader.py      # Downloads and loads data
│   │   ├── dataframe_cleaner.py # Cleans raw data
│   │   ├── dataframe_combiner.py # Combines datasets
│   │   ├── loader.py          # Loads processed data
│   │   └── preprocessing.py   # Filters data for visualization
│   ├── visualization/
│   │   ├── map.py       # Interactive map visualization
│   │   ├── plotter.py   # Chart visualization functions
│   │   └── widgets.py   # UI controls (dropdowns, etc.)
│   ├── dashboard.ipynb  # Notebook to run the dashboard
│   └── main.py          # Main application with data prep and dashboard
└── requirements.txt     # Python package dependencies
```

## Code Structure Evolution

We started with notebook that had all code in one place, but it was not good for maintenance. Then we changed structure in steps:

1. First, we separated data processing from visualization
2. Then, we made separate chart and map components
3. At last, we moved preparation code from notebook to `prepare_data()` function in main.py

Current structure is better for maintenance. Now we can:
- Run dashboard with existing data
- Update data without changing visualization code
- Add new features to charts or maps separately

## Data Preparation

We used following steps to prepare data:

### 1. Data Acquisition
We download COVID data from RIVM (Dutch National Institute for Public Health):
```python
# Part of prepare_data() function in main.py
url_cases_2 = "https://data.rivm.nl/covid-19/COVID-19_aantallen_gemeente_per_dag.csv"
url_cases_1 = "https://data.rivm.nl/covid-19/COVID-19_aantallen_gemeente_per_dag_tm_03102021.csv"
url_hosp_2 = "https://data.rivm.nl/covid-19/COVID-19_ziekenhuisopnames.csv"
url_hosp_1 = "https://data.rivm.nl/data/covid-19/COVID-19_ziekenhuisopnames_tm_03102021.csv"

download_data_from_url(url_cases_2, data_path / "cases_2.csv")
download_data_from_url(url_cases_1, data_path / "cases_1.csv")
# ... etc
```

### 2. Data Cleaning
This was most difficult part. We had many problems:
- Date formats were different between datasets
- Municipality changed names and borders during pandemic
- Many missing values and wrong codes
- Hospital data had different structure than case data

We had problems with municipality matching. For example, Haaren municipality was removed during pandemic and we needed special solution for this.

### 3. Data Combination
We combined these datasets:
- Case data (infections and deaths)
- Hospital admission data
- Population data (for calculating rates per 100.000)

Big problem was to make correct joins between these different datasets.

## Interactive Dashboard

Dashboard has two tabs:

### Chart Tab
Shows interactive bar charts with options:
- Select years (2020-2023 or All)
- Choose metrics (Cases, Deaths, Hospital Admissions)
- Filter by province and municipality
- Change grouping (Year, Months, Municipalities)

We had problem with month ordering. Default was alphabetical (April, August, etc.) but we need chronological order!

### Map Tab
Shows map with colors to show COVID data:
- Choose level: municipality, province or country
- Change between monthly and yearly data
- Show different metrics (total numbers or rates per 100.000)

Most difficult was to make color scale change correctly when user selects different metrics.

## Challenges and Solutions

Main problems we had:

1. **Data problems**:
   Municipality changes were very difficult. We need to find which municipalities where merged or split.

2. **Visualization problems**:
   - Month order was wrong (alphabetical not chronological)
   - Legend for years was not always in right position
   - When showing many metrics, layout was confusing
   - Too many municipalities make chart unreadable

3. **Code organization**:
   We tried many different ways to organize code before we found good structure.

## Key Learnings

1. **Pandas techniques**:
   - pd.Categorical with ordering is important for correct sorting
   - melt() function is needed for changing data shape for visualization

2. **Visualization techniques**:
   - Same colors for same metrics help user understand
   - Vertical lines between groups make chart easier to read
   - For municipalities, showing only important ones is better than showing all

3. **Code structure**:
   - Separating data code from visualization code is better
   - Using consistent patterns makes maintenance easier
   - Modular design helps when adding new features

## Conclusion

This project taught us much about data problems and visualization in Python. We are satisfied with dashboard that shows COVID patterns in different regions and times.

If we had more time, we would:
- Add analysis of trends to show important changes
- Make map more interactive
- Add more information about population
- Add feature to compare different regions

Overall, assignment gave us good experience with pandas, visualization libraries and Python project structure.
