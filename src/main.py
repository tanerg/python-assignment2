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
from visualization.plotter import generate_bar_chart, generate_monthly_chart, generate_municipality_chart, generate_incidence_line_chart
from config.constants import MONTH_MAPPING

def run_dashboard(data_path='../data/data_cleaned.csv'):
    df_merged = load_cleaned_data(data_path)

    year_dropdown = create_year_dropdown(df_merged)
    province_dropdown = create_province_dropdown(df_merged)
    municipality_dropdown = create_municipality_dropdown()
    cases_checkbox, deaths_checkbox, hospital_checkbox = create_metric_checkboxes()
    aggregation_radio = create_aggregation_radio()

    # Add chart type selector for counts vs incidence rates
    chart_type_radio = widgets.RadioButtons(
        options=['Counts', 'Incidence Rates'],
        description='Chart Type:',
        value='Counts'
    )

    # Set behavior based on chart type
    def update_for_chart_type(change):
        # Show/hide aggregation radio based on chart type
        if change['new'] == 'Incidence Rates':
            # Hide aggregation radio when viewing incidence rates
            aggregation_radio.layout.display = 'none'
        else:
            # Show aggregation radio when viewing counts
            aggregation_radio.layout.display = 'block'

            # Update aggregation options based on province/municipality
            update_aggregation_options()

    chart_type_radio.observe(update_for_chart_type, 'value')

    controls = widgets.VBox([
        year_dropdown,
        widgets.HBox([cases_checkbox, deaths_checkbox, hospital_checkbox]),
        province_dropdown,
        municipality_dropdown,
        widgets.HBox([aggregation_radio, chart_type_radio])
    ])

    output = widgets.Output()

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
        # Skip if we're viewing incidence rates (aggregation is hidden)
        if chart_type_radio.value == 'Incidence Rates':
            return

        if province_dropdown.value == 'Netherlands':
            # For Netherlands, only allow Year and Months aggregation
            aggregation_radio.options = ['Year', 'Months']
        elif municipality_dropdown.disabled or municipality_dropdown.value == 'All':
            # Allow all aggregation options for province level
            aggregation_radio.options = ['Year', 'Months', 'Municipalities']
        else:
            # For specific municipalities, only allow Year and Months
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

            # For incidence rates, we don't use aggregation_radio.value
            if chart_type_radio.value == 'Incidence Rates':
                title_suffix = 'Incidence Rates'
            else:
                # Determine x_axis based on aggregation selection and province
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

            # Map numeric months to names with explicit ordering - only needed for Counts with Month x-axis
            if chart_type_radio.value == 'Counts' and x_axis == 'Month':
                month_order = list(MONTH_MAPPING.values())
                df_filtered = df_filtered.copy()
                df_filtered['Month'] = df_filtered['Month'].map(MONTH_MAPPING).astype(
                    pd.CategoricalDtype(categories=month_order, ordered=True)
                )

            # Reset index before grouping to avoid alignment errors
            df_filtered = df_filtered.reset_index(drop=True)

            # Determine metrics based on chart type
            if chart_type_radio.value == 'Counts':
                metrics = []
                if cases_checkbox.value:
                    metrics.append('Total_reported')
                if deaths_checkbox.value:
                    metrics.append('Deceased')
                if hospital_checkbox.value:
                    metrics.append('Hospital_admission')
            else:  # Incidence Rates
                metrics = []
                if cases_checkbox.value:
                    metrics.append('Incidence_rate_cases')
                if deaths_checkbox.value:
                    metrics.append('Incidence_rate_deaths')
                if hospital_checkbox.value:
                    metrics.append('Incidence_rate_hospital_admission')

            if not metrics:
                return

            # Generate appropriate title
            title_parts = ['Covid-19 Overview']

            # Add appropriate province information to title
            if selected_province == 'All Provinces' and chart_type_radio.value == 'Counts' and aggregation_radio.value == 'Months':
                title_parts.append('All Provinces - Aggregated')
            elif selected_province == 'Netherlands':
                title_parts.append('Netherlands')
            else:
                title_parts.append(selected_province)

            # Add municipality if applicable
            if not municipality_dropdown.disabled and municipality_dropdown.value != 'All':
                title_parts.append(municipality_dropdown.value)

            # Add metric type
            title_parts.append(title_suffix)
            title_parts.append(str(selected_year))
            title = ' - '.join(title_parts)

            # Determine which visualization to use based on chart type
            if chart_type_radio.value == 'Incidence Rates':
                # For incidence rates, always use the line chart
                fig = generate_incidence_line_chart(
                    df_filtered,
                    metrics,
                    title,
                    MONTH_MAPPING
                )
            else:
                # Use regular visualizations for counts based on aggregation setting
                # Case 1: 'All' years selected + Netherlands or All Provinces + Year aggregation
                if selected_year == 'All' and (selected_province == 'Netherlands' or selected_province == 'All Provinces') and aggregation_radio.value == 'Year':
                    # Group by Year
                    df_grouped = df_filtered.groupby('Year', as_index=False, observed=True).agg({
                        'Total_reported': 'sum',
                        'Deceased': 'sum',
                        'Hospital_admission': 'sum'
                    })
                    # Generate regular bar chart with Year on x-axis
                    fig = generate_bar_chart(df_grouped, 'Year', metrics, title)

                # Case 2: 'All' years selected + Month aggregation (for any province selection)
                elif selected_year == 'All' and aggregation_radio.value == 'Months':
                    # Handle All Provinces case - combine data before passing to visualization
                    if selected_province == 'All Provinces':
                        df_filtered = df_filtered.groupby(['Month', 'Year'], observed=True).agg({
                            'Total_reported': 'sum',
                            'Deceased': 'sum',
                            'Hospital_admission': 'sum'
                        }).reset_index()

                    # Use the refactored monthly chart generator
                    fig = generate_monthly_chart(df_filtered, metrics, title, MONTH_MAPPING)

                # Case 3: 'All' years selected + Municipalities aggregation
                elif selected_year == 'All' and aggregation_radio.value == 'Municipalities':
                    # Use the refactored municipality chart generator
                    fig = generate_municipality_chart(df_filtered, metrics, title)

                # All other cases
                else:
                    # Group by the determined x_axis
                    df_grouped = df_filtered.groupby(x_axis, as_index=False, observed=True).agg({
                        'Total_reported': 'sum',
                        'Deceased': 'sum',
                        'Hospital_admission': 'sum'
                    })

                    # Generate regular bar chart
                    fig = generate_bar_chart(df_grouped, x_axis, metrics, title)

            fig.show()

    year_dropdown.observe(update_plot, 'value')
    province_dropdown.observe(update_plot, 'value')
    municipality_dropdown.observe(update_plot, 'value')
    aggregation_radio.observe(update_plot, 'value')

    # Make sure all checkbox changes trigger plot updates
    cases_checkbox.observe(update_plot, 'value')
    deaths_checkbox.observe(update_plot, 'value')
    hospital_checkbox.observe(update_plot, 'value')

    # Add observer for the chart type radio
    chart_type_radio.observe(update_plot, 'value')

    province_dropdown.observe(update_municipality_options, 'value')
    province_dropdown.observe(update_aggregation_options, 'value')
    municipality_dropdown.observe(update_aggregation_options, 'value')

    # Make sure chart type changes update aggregation options
    chart_type_radio.observe(update_aggregation_options, 'value')

    update_municipality_options()
    update_aggregation_options()
    update_plot()

    display(controls, output)
