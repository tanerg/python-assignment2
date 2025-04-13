import pandas as pd
from IPython.display import display
import ipywidgets as widgets
import plotly.express as px
from plotly.subplots import make_subplots
import warnings
import sys

# Silence the FutureWarning related to observed parameter in groupby
warnings.filterwarnings('ignore', category=FutureWarning,
                       message='The default of observed=False is deprecated')

from data.loader import load_cleaned_data
from data.preprocessing import filter_by_criteria
from visualization.widgets import (
    create_year_dropdown, create_province_dropdown,
    create_municipality_dropdown, create_metric_checkboxes,
    create_aggregation_radio
)
from visualization.plotter import generate_bar_chart, generate_monthly_chart, generate_municipality_chart
from config.constants import MONTH_MAPPING

def run_dashboard(data_path='../data/data_cleaned.csv'):
    df_merged = load_cleaned_data(data_path)

    year_dropdown = create_year_dropdown(df_merged)
    province_dropdown = create_province_dropdown(df_merged)
    municipality_dropdown = create_municipality_dropdown()
    cases_checkbox, deaths_checkbox, hospital_checkbox = create_metric_checkboxes()
    aggregation_radio = create_aggregation_radio()

    controls = widgets.VBox([
        year_dropdown,
        widgets.HBox([cases_checkbox, deaths_checkbox, hospital_checkbox]),
        province_dropdown,
        municipality_dropdown,
        aggregation_radio
    ])

    output = widgets.Output()
    map_output = widgets.Output()

    # Create tab widget with Chart and Map tabs
    tab = widgets.Tab()
    chart_tab = widgets.VBox([controls, output])
    map_tab = widgets.VBox([map_output])

    tab.children = [chart_tab, map_tab]
    tab.set_title(0, 'Chart')
    tab.set_title(1, 'Map')

    def update_municipality_options(*args):
        selected_province = province_dropdown.value
        if selected_province not in ['Netherlands', 'All Provinces']:
            municipalities = ['All'] + sorted(df_merged[df_merged['Province'] == selected_province]['Municipality_name'].unique())
            municipality_dropdown.options = municipalities
            municipality_dropdown.disabled = False
        else:
            municipality_dropdown.options = ['All']
            municipality_dropdown.value = 'All'
            municipality_dropdown.disabled = True

    def update_aggregation_options(*args):
        if province_dropdown.value == 'Netherlands':
            # Only Year and Months available for Netherlands
            aggregation_radio.options = ['Year', 'Months']
        elif municipality_dropdown.disabled or municipality_dropdown.value == 'All':
            # All options for province level
            aggregation_radio.options = ['Year', 'Months', 'Municipalities']
        else:
            # Year and Months for specific municipalities
            aggregation_radio.options = ['Year', 'Months']
            if aggregation_radio.value == 'Municipalities':
                aggregation_radio.value = 'Year'

    def update_plot(*args):
        with output:
            output.clear_output(wait=True)

            df_filtered = filter_by_criteria(
                df_merged,
                year=year_dropdown.value,
                province=province_dropdown.value if province_dropdown.value not in ['Netherlands', 'All Provinces'] else 'All',
                municipality=municipality_dropdown.value if not municipality_dropdown.disabled else 'All'
            )

            x_axis, title_suffix = None, ""
            selected_province = province_dropdown.value
            selected_year = year_dropdown.value

            # Determine x-axis based on current selections
            if selected_province == 'Netherlands':
                x_axis = 'Month' if aggregation_radio.value == 'Months' else 'Year'
            elif selected_province == 'All Provinces':
                if aggregation_radio.value == 'Municipalities':
                    x_axis = 'Municipality_name'
                elif aggregation_radio.value == 'Months':
                    x_axis = 'Month'
                else:
                    x_axis = 'Province'
            else:
                x_axis = 'Municipality_name' if aggregation_radio.value == 'Municipalities' else 'Month' if aggregation_radio.value == 'Months' else 'Year'

            title_suffix = aggregation_radio.value

            # Convert numeric months to names for better display
            if x_axis == 'Month':
                month_order = list(MONTH_MAPPING.values())
                df_filtered = df_filtered.copy()
                df_filtered['Month'] = df_filtered['Month'].map(MONTH_MAPPING).astype(
                    pd.CategoricalDtype(categories=month_order, ordered=True)
                )

            # Reset index to prevent alignment issues during groupby
            df_filtered = df_filtered.reset_index(drop=True)

            # Collect selected metrics from checkboxes
            metrics = []
            if cases_checkbox.value:
                metrics.append('Total_reported')
            if deaths_checkbox.value:
                metrics.append('Deceased')
            if hospital_checkbox.value:
                metrics.append('Hospital_admission')

            if not metrics:
                return

            # Build chart title from current selections
            title_parts = ['Covid-19 Overview']

            if selected_province == 'All Provinces' and aggregation_radio.value == 'Months':
                title_parts.append('All Provinces - Aggregated')
            elif selected_province == 'Netherlands':
                title_parts.append('Netherlands')
            else:
                title_parts.append(selected_province)

            if not municipality_dropdown.disabled and municipality_dropdown.value != 'All':
                title_parts.append(municipality_dropdown.value)

            title_parts.append(title_suffix)
            title_parts.append(str(selected_year))
            title = ' - '.join(title_parts)

            # Generate the appropriate visualization based on current selections
            if selected_year == 'All' and (selected_province == 'Netherlands' or selected_province == 'All Provinces') and aggregation_radio.value == 'Year':
                # Year aggregation - show years on x-axis
                df_grouped = df_filtered.groupby('Year', as_index=False, observed=True).agg({
                    'Total_reported': 'sum',
                    'Deceased': 'sum',
                    'Hospital_admission': 'sum'
                })
                fig = generate_bar_chart(df_grouped, 'Year', metrics, title)

            elif selected_year == 'All' and aggregation_radio.value == 'Months':
                # Month aggregation - special handling with years stacked within metrics
                if selected_province == 'All Provinces':
                    df_filtered = df_filtered.groupby(['Month', 'Year'], observed=True).agg({
                        'Total_reported': 'sum',
                        'Deceased': 'sum',
                        'Hospital_admission': 'sum'
                    }).reset_index()

                fig = generate_monthly_chart(df_filtered, metrics, title, MONTH_MAPPING)

            elif selected_year == 'All' and aggregation_radio.value == 'Municipalities':
                # Municipality aggregation - special handling for multiple municipalities
                if selected_province not in ['Netherlands', 'All Provinces']:
                    # Data has already been filtered by province in filter_by_criteria
                    pass

                fig = generate_municipality_chart(df_filtered, metrics, title)

            else:
                # Standard bar chart for other cases
                df_grouped = df_filtered.groupby(x_axis, as_index=False, observed=True).agg({
                    'Total_reported': 'sum',
                    'Deceased': 'sum',
                    'Hospital_admission': 'sum'
                })

                fig = generate_bar_chart(df_grouped, x_axis, metrics, title)

            fig.show()

    # Set up widget observers
    year_dropdown.observe(update_plot, 'value')
    province_dropdown.observe(update_plot, 'value')
    municipality_dropdown.observe(update_plot, 'value')
    aggregation_radio.observe(update_plot, 'value')

    cases_checkbox.observe(update_plot, 'value')
    deaths_checkbox.observe(update_plot, 'value')
    hospital_checkbox.observe(update_plot, 'value')

    province_dropdown.observe(update_municipality_options, 'value')
    province_dropdown.observe(update_aggregation_options, 'value')
    municipality_dropdown.observe(update_aggregation_options, 'value')

    # Initialize the UI
    update_municipality_options()
    update_aggregation_options()
    update_plot()

    display(tab)
