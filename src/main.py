import os
import sys
import warnings

import pandas as pd
from IPython.display import display
import ipywidgets as widgets

from visualization.plotter import create_interactive_covid_chart
from visualization.map import create_interactive_covid_map
from data.data_loader import download_data_from_url, load_and_concatenate_csv, load_population_data, load_municipality_geodata
from data.dataframe_cleaner import clean_cases_df, clean_hospital_df, clean_population_df
from data.dataframe_combiner import combine_cases_and_hospital_data, add_population_and_calculate_incidence

# Silence the FutureWarning related to observed parameter in groupby
warnings.filterwarnings('ignore', category=FutureWarning,
                       message='The default of observed=False is deprecated')

def prepare_data(data_dir='../data'):
    """
    Prepare COVID-19 data by downloading, cleaning, and combining datasets.

    This function:
    1. Downloads COVID data from RIVM sources
    2. Loads and concatenates multiple datasets
    3. Cleans the data
    4. Combines cases, hospital, and population data
    5. Saves the cleaned data to a CSV file

    """
    # URLs for the COVID data
    url_cases_2 = "https://data.rivm.nl/covid-19/COVID-19_aantallen_gemeente_per_dag.csv"
    url_cases_1 = "https://data.rivm.nl/covid-19/COVID-19_aantallen_gemeente_per_dag_tm_03102021.csv"
    url_hosp_2 = "https://data.rivm.nl/covid-19/COVID-19_ziekenhuisopnames.csv"
    url_hosp_1 = "https://data.rivm.nl/data/covid-19/COVID-19_ziekenhuisopnames_tm_03102021.csv"

    # Download data from URLs
    print("Downloading COVID-19 data...")
    download_data_from_url(url_cases_2, os.path.join(data_dir, "cases_2.csv"))
    download_data_from_url(url_cases_1, os.path.join(data_dir, "cases_1.csv"))
    download_data_from_url(url_hosp_2, os.path.join(data_dir, "hosp_2.csv"))
    download_data_from_url(url_hosp_1, os.path.join(data_dir, "hosp_1.csv"))

    # Load the case data
    print("Loading and processing data...")
    file_cases_1 = os.path.join(data_dir, "cases_1.csv")
    file_cases_2 = os.path.join(data_dir, "cases_2.csv")
    df_cases = load_and_concatenate_csv(file_cases_1, file_cases_2)

    # Load the hospital data
    file_hospital_1 = os.path.join(data_dir, "hosp_1.csv")
    file_hospital_2 = os.path.join(data_dir, "hosp_2.csv")
    df_hospital = load_and_concatenate_csv(file_hospital_1, file_hospital_2)

    # Load population data
    file_population = os.path.join(data_dir, "population_data.csv")
    df_population = load_population_data(file_population)

    # Load municipality geodata
    municipalities_gdf = load_municipality_geodata(os.path.join(data_dir, "municipalities_2023.geojson"))

    # Clean the dataframes
    print("Cleaning datasets...")
    df_cases_cleaned = clean_cases_df(df_cases)
    df_hospital_cleaned = clean_hospital_df(df_hospital)
    df_population_cleaned = clean_population_df(df_population)

    # Combine the data
    print("Combining datasets...")
    df_covid = combine_cases_and_hospital_data(df_cases_cleaned, df_hospital_cleaned)
    df = add_population_and_calculate_incidence(df_covid, df_population_cleaned)

    # Save the cleaned data
    output_file = os.path.join(data_dir, 'data_cleaned.csv')
    print(f"Saving cleaned data to {output_file}")
    df.to_csv(output_file, index=False)

    print("Data preparation complete!")
    return df

def run_dashboard(data_dir='../data'):
    # Define file paths
    cleaned_data_file = os.path.join(data_dir, 'data_cleaned.csv')
    geodata_path = os.path.join(data_dir, 'geodata')

    # Create tabs for the dashboard
    tab = widgets.Tab()

    # Create chart and map content by calling the respective functions
    chart_tab_content = create_interactive_covid_chart(cleaned_data_file)
    map_tab_content = create_interactive_covid_map(geodata_path)

    # Set up the tabs with their content
    tab.children = [chart_tab_content, map_tab_content]
    tab.set_title(0, 'Chart')
    tab.set_title(1, 'Map')

    # Display the dashboard
    display(tab)

if __name__ == "__main__":
    # If run as a script, execute the dashboard
    run_dashboard()
