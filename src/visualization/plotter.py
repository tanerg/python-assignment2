import plotly.express as px
from config.constants import COLOR_MAPPING
import pandas as pd
from plotly.subplots import make_subplots
import ipywidgets as widgets
from IPython.display import display
import os
from data.loader import load_cleaned_data
from data.preprocessing import filter_by_criteria
from visualization.widgets import (
    create_year_dropdown, create_province_dropdown,
    create_municipality_dropdown, create_metric_checkboxes,
    create_aggregation_radio
)
from config.constants import MONTH_MAPPING

def generate_bar_chart(df_grouped, x_axis, metrics, title):
    """
    Creates a bar chart showing COVID data metrics side by side.

    This chart allows you to compare different COVID metrics (like cases, deaths,
    and hospital admissions) next to each other for different regions, time periods,
    or other categories.

    Parameters:
    -----------
    df_grouped : pd.DataFrame
        The organized COVID data with combined totals
    x_axis : str
        What to show on the bottom axis (like 'Year', 'Month', 'Province')
    metrics : list
        Which COVID metrics to show (like cases, deaths, hospitalizations)
    title : str
        The title to display on the chart

    Returns:
    --------
    A chart object that can be displayed in the dashboard
    """
    # Make the technical variable names friendlier for users
    metric_labels = {
        'Total_reported': 'Cases',
        'Deceased': 'Deaths',
        'Hospital_admission': 'Hospital Admissions'
    }

    # Create a copy to avoid changing the original data
    df_plot = df_grouped.copy()

    # Define what text appears when hovering over chart elements
    labels = {
        'value': 'Count',
        'variable': 'Metric',
        x_axis: x_axis.replace('_', ' ')  # Remove underscores for better display
    }

    if len(metrics) > 0:
        # Reshape the data for better visualization
        # This is for creating a grouped bar chart
        # where different metrics (cases, deaths, hospitalizations) appear side by side
        id_vars = [col for col in df_plot.columns if col not in metrics]
        df_melted = pd.melt(
            df_plot,
            id_vars=id_vars,
            value_vars=metrics,
            var_name='Metric',
            value_name='Value'
        )

        # Replace technical names with friendly names
        df_melted['Metric'] = df_melted['Metric'].map(metric_labels)

        # Create the actual bar chart with grouped bars
        fig = px.bar(
            df_melted,
            x=x_axis,
            y='Value',
            color='Metric',  # Colors bars by metric type (cases, deaths, etc.)
            title=title,
            labels=labels,
            barmode='group',  # Places bars side by side rather than stacked
            color_discrete_map={metric_labels[metric]: COLOR_MAPPING[metric] for metric in metrics if metric in metric_labels}
        )
    else:
        # Backup option if no metrics were selected
        fig = px.bar(
            df_plot,
            x=x_axis,
            y=metrics,
            title=title,
            labels=labels,
            color_discrete_map={metric: COLOR_MAPPING[metric] for metric in metrics}
        )
        fig.update_layout(barmode='group')

    # Tilt the labels on the bottom axis so they don't overlap
    fig.update_xaxes(type='category', tickangle=-45)
    return fig

def generate_monthly_chart(df_filtered, metrics, title, month_mapping):
    """
    Creates a special chart showing monthly COVID data with years stacked.

    This chart is designed to show patterns across months and compare years.
    For example, you can see if cases were higher in winter months and
    compare January 2020 vs January 2021.

    Parameters:
    -----------
    df_filtered : pd.DataFrame
        The filtered COVID data
    metrics : list
        Which COVID metrics to show (cases, deaths, hospitalizations)
    title : str
        The title to display on the chart
    month_mapping : dict
        Converts month numbers (1-12) to month names (January-December)

    Returns:
    --------
    A chart object that can be displayed in the dashboard
    """
    # Create a copy to avoid changing the original data
    df_month = df_filtered.copy()

    # Make sure months are stored as numbers (1-12)
    # This is needed for proper sorting (Jan, Feb, Mar instead of alphabetical)
    if not pd.api.types.is_numeric_dtype(df_month['Month']):
        month_to_num = {v: k for k, v in month_mapping.items()}
        df_month['Month'] = df_month['Month'].map(month_to_num)

    # Store the year as text for better display in the chart legend
    df_month['Year_str'] = df_month['Year'].astype(str)

    # Convert month numbers to names for display (1 → January)
    df_month['Month_name'] = df_month['Month'].map(month_mapping)

    # Create friendly names for the COVID metrics
    metrics_list = []
    metric_mapping = {
        'Total_reported': 'Cases',
        'Deceased': 'Deaths',
        'Hospital_admission': 'Hospital Admissions'
    }

    for metric in metrics:
        if metric in metric_mapping:
            metrics_list.append((metric, metric_mapping[metric]))

    # Prepare data points for each month + metric + year combination
    # This creates individual data points that will make up the chart
    plot_data = []
    for month_num in sorted(df_month['Month'].unique()):
        month_name = month_mapping.get(month_num, str(month_num))
        for metric_col, metric_name in metrics_list:
            for year in sorted(df_month['Year'].unique()):
                year_str = str(year)
                # Find matching data and calculate total for this combination
                mask = (df_month['Month'] == month_num) & (df_month['Year'] == year)
                if mask.any():
                    value = df_month.loc[mask, metric_col].sum()
                    plot_data.append({
                        'Month': month_name,
                        'Metric': metric_name,
                        'Year': year_str,
                        'Month_Metric': f"{month_name} - {metric_name}",
                        'Value': value
                    })

    # Handle case when no data is available
    if not plot_data:
        fig = px.bar(
            x=['No Data'],
            y=[0],
            title=f"{title} - No data available"
        )
    else:
        # Create a table from our prepared data points
        plot_df = pd.DataFrame(plot_data)

        # Make sure months display in calendar order (Jan, Feb, Mar, etc.)
        # instead of alphabetical order (Apr, Aug, Dec, etc.)
        month_list = [month_mapping[i] for i in range(1, 13)
                    if month_mapping[i] in plot_df['Month'].unique()]
        plot_df['Month'] = pd.Categorical(
            plot_df['Month'],
            categories=month_list,
            ordered=True
        )

        # Create labels combining month and metric for the x-axis
        # This gives groups like "January - Cases", "January - Deaths", etc.
        month_metrics = []
        for month in month_list:
            for _, metric_name in metrics_list:
                month_metrics.append(f"{month} - {metric_name}")

        plot_df['Month_Metric'] = pd.Categorical(
            plot_df['Month_Metric'],
            categories=month_metrics,
            ordered=True
        )

        # Add display column for metric names
        plot_df['Metric_display'] = plot_df['Metric']

        # Create the stacked bar chart
        # Years are stacked within each month-metric combination
        fig = px.bar(
            plot_df,
            x='Month_Metric',  # X-axis shows month-metric combinations
            y='Value',  # Y-axis shows the count (cases, deaths, etc.)
            color='Year',  # Color/stack by year
            barmode='stack',  # Stack the years on top of each other
            title=title,
            labels={
                'Value': 'Count',
                'Year': 'Year',
                'Month_Metric': ''
            },
            color_discrete_sequence=px.colors.qualitative.Set1
        )

        # Set the chart size
        fig.update_layout(
            height=600,
            width=1200,
            legend_title_text='Year'
        )

        # Make the x-axis labels more readable
        # Show full month names only at the start of each month group
        metric_names = [m[1] for m in metrics_list]
        fig.update_xaxes(
            tickangle=-45,
            tickmode='array',
            tickvals=list(range(len(month_metrics))),
            ticktext=[m.split(' - ')[1] if i % len(metric_names) != 0 else m
                    for i, m in enumerate(month_metrics)]
        )

        # Add vertical divider lines between months to visually separate them
        for i in range(1, len(month_list)):
            line_position = i * len(metric_names) - 0.5
            fig.add_vline(x=line_position, line_width=1, line_color="gray", line_dash="dash")

    return fig

def generate_municipality_chart(df_filtered, metrics, title):
    """
    Creates a chart comparing COVID data across different municipalities.

    This chart shows COVID metrics for each municipality, with years stacked
    to show the total and the contribution from each year.

    Parameters:
    -----------
    df_filtered : pd.DataFrame
        Filtered COVID data for the selected province
    metrics : list
        Which COVID metrics to display (cases, deaths, hospitalizations)
    title : str
        The title to display on the chart

    Returns:
    --------
    A chart object that can be displayed in the dashboard
    """
    # Convert Year to text for better display in the legend
    df_filtered['Year_str'] = df_filtered['Year'].astype(str)
    df_muni = df_filtered.copy()

    # Group and sum the data by municipality and year
    # This combines all the individual data points into totals
    df_grouped = df_muni.groupby(['Municipality_name', 'Year_str'], observed=True).agg({
        'Total_reported': 'sum',
        'Deceased': 'sum',
        'Hospital_admission': 'sum'
    }).reset_index()

    # Make sure years appear in order from oldest to newest
    year_order = sorted(df_grouped['Year_str'].unique(), key=int)
    df_grouped['Year_str'] = pd.Categorical(
        df_grouped['Year_str'],
        categories=year_order,
        ordered=True
    )

    # Reshape the data for visualization
    # This creates individual rows for each municipality-metric-year combination
    df_melted = pd.melt(
        df_grouped,
        id_vars=['Municipality_name', 'Year_str'],
        value_vars=metrics,
        var_name='Metric',
        value_name='Count'
    )

    # Use friendly names for metrics
    metric_mapping = {
        'Total_reported': 'Cases',
        'Deceased': 'Deaths',
        'Hospital_admission': 'Hospital Admissions'
    }
    df_melted['Metric'] = df_melted['Metric'].map(metric_mapping)

    # Sort municipalities by total case count (highest first)
    # This helps to see the most affected areas more easily
    municipality_totals = df_grouped.groupby('Municipality_name', observed=True).agg({
        'Total_reported': 'sum'
    }).sort_values('Total_reported', ascending=False)

    all_municipalities = municipality_totals.index.tolist()

    # Get the friendly metric names
    metrics_list = [metric_mapping.get(m) for m in metrics if m in metric_mapping]

    # Create labels for the x-axis combining municipality and metric
    df_melted['Muni_Metric'] = df_melted['Municipality_name'] + ' - ' + df_melted['Metric']

    # Create all possible municipality-metric combinations
    # This ensures consistent ordering on the chart
    muni_metrics = []
    for muni in all_municipalities:
        for metric in metrics_list:
            muni_metrics.append(f"{muni} - {metric}")

    # Create an ordered category to ensure proper x-axis sorting
    df_melted['Muni_Metric'] = pd.Categorical(
        df_melted['Muni_Metric'],
        categories=muni_metrics,
        ordered=True
    )

    # Sort the data to match our desired order
    df_melted = df_melted.sort_values(['Muni_Metric', 'Year_str'])

    # Create the actual chart
    fig = px.bar(
        df_melted,
        x='Muni_Metric',  # X-axis shows municipality-metric combinations
        y='Count',  # Y-axis shows the count (cases, deaths, etc.)
        color='Year_str',  # Color/stack by year
        barmode='stack',  # Stack the years on top of each other
        title=title,
        labels={
            'Count': 'Count',
            'Year_str': 'Year',
            'Muni_Metric': ''
        },
        color_discrete_sequence=px.colors.qualitative.Set1,
        category_orders={'Year_str': year_order}
    )

    # Set the chart size
    # Width is larger to accommodate many municipalities
    fig.update_layout(
        height=600,
        width=1800,
        legend_title_text='Year',
        xaxis_title="Municipality - Metric"
    )

    # Make the x-axis labels more readable
    # Show municipality names only at the start of each municipality group
    if muni_metrics:
        ticktext = []
        for i, m in enumerate(muni_metrics):
            if i % len(metrics_list) == 0:
                ticktext.append(m.split(' - ')[0])  # Municipality name
            else:
                ticktext.append(m.split(' - ')[1])  # Just the metric name

        fig.update_xaxes(
            tickangle=-65,  # Tilt labels to avoid overlap
            tickmode='array',
            tickvals=list(range(len(muni_metrics))),
            ticktext=ticktext
        )

    # Add vertical divider lines between municipalities to visually separate them
    if len(all_municipalities) > 1:
        for i in range(1, len(all_municipalities)):
            line_position = i * len(metrics_list) - 0.5
            fig.add_vline(x=line_position, line_width=1, line_color="gray", line_dash="dash")

    return fig

def create_interactive_covid_chart(data_file):
    """
    Creates an interactive COVID dashboard with controls and charts.

    This function builds the entire chart section of the COVID dashboard,
    including dropdown menus, checkboxes, and the visualization area.
    It allows users to explore COVID data by selecting different regions,
    time periods, and metrics.

    Parameters:
    -----------
    data_file : str
        Path to the CSV file containing COVID data

    Returns:
    --------
    A dashboard component that can be displayed in a tab
    """
    # Load the COVID data from the CSV file
    df_merged = load_cleaned_data(data_file)

    # Create the interactive controls (dropdowns, checkboxes, etc.)
    year_dropdown = create_year_dropdown(df_merged)  # Year selection
    province_dropdown = create_province_dropdown(df_merged)  # Province selection
    municipality_dropdown = create_municipality_dropdown()  # Municipality selection

    # Checkboxes for selecting which metrics to display
    cases_checkbox, deaths_checkbox, hospital_checkbox = create_metric_checkboxes()

    # Radio buttons for how to group the data
    aggregation_radio = create_aggregation_radio()

    # Arrange the controls in a vertical layout with checkboxes in a row
    controls = widgets.VBox([
        year_dropdown,
        widgets.HBox([cases_checkbox, deaths_checkbox, hospital_checkbox]),
        province_dropdown,
        municipality_dropdown,
        aggregation_radio
    ])

    # Create an area to display the charts
    output = widgets.Output()

    # This function updates the municipality dropdown based on the selected province
    def update_municipality_options(*args):
        selected_province = province_dropdown.value
        if selected_province not in ['Netherlands', 'All Provinces']:
            # If a specific province is selected, show its municipalities
            municipalities = ['All'] + sorted(df_merged[df_merged['Province'] == selected_province]['Municipality_name'].unique())
            municipality_dropdown.options = municipalities
            municipality_dropdown.disabled = False
        else:
            # If Netherlands or All Provinces is selected, disable municipalities
            municipality_dropdown.options = ['All']
            municipality_dropdown.value = 'All'
            municipality_dropdown.disabled = True

    # This function updates the available aggregation options based on selections
    def update_aggregation_options(*args):
        if province_dropdown.value in ['Netherlands', 'All Provinces']:
            # For nationwide or all-provinces view, only allow Year and Months views
            aggregation_radio.options = ['Year', 'Months']
            # If Municipalities was previously selected, change it to Year
            if aggregation_radio.value == 'Municipalities':
                aggregation_radio.value = 'Year'
        elif municipality_dropdown.disabled or municipality_dropdown.value == 'All':
            # For province level, allow all aggregation types
            aggregation_radio.options = ['Year', 'Months', 'Municipalities']
        else:
            # For specific municipality, only allow Year and Months
            aggregation_radio.options = ['Year', 'Months']
            if aggregation_radio.value == 'Municipalities':
                aggregation_radio.value = 'Year'

    # This function updates the chart when any control changes
    def update_plot(*args):
        with output:
            # Clear previous chart
            output.clear_output(wait=True)

            # Filter data based on the selected options
            df_filtered = filter_by_criteria(
                df_merged,
                year=year_dropdown.value,
                province=province_dropdown.value if province_dropdown.value not in ['Netherlands', 'All Provinces'] else 'All',
                municipality=municipality_dropdown.value if not municipality_dropdown.disabled else 'All'
            )

            x_axis, title_suffix = None, ""
            selected_province = province_dropdown.value
            selected_year = year_dropdown.value

            # Determine what to show on the x-axis based on selections
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

            # Convert month numbers to names if showing months
            if x_axis == 'Month':
                month_order = list(MONTH_MAPPING.values())
                df_filtered = df_filtered.copy()
                df_filtered['Month'] = df_filtered['Month'].map(MONTH_MAPPING).astype(
                    pd.CategoricalDtype(categories=month_order, ordered=True)
                )

            # Prepare the data for visualization
            df_filtered = df_filtered.reset_index(drop=True)

            # Determine which metrics to show based on checkbox selections
            metrics = []
            if cases_checkbox.value:
                metrics.append('Total_reported')  # Cases
            if deaths_checkbox.value:
                metrics.append('Deceased')  # Deaths
            if hospital_checkbox.value:
                metrics.append('Hospital_admission')  # Hospitalizations

            # If no metrics selected, don't show anything
            if not metrics:
                return

            # Build the chart title based on selections
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

            # Choose the right chart type based on selections
            if selected_year == 'All' and (selected_province == 'Netherlands' or selected_province == 'All Provinces') and aggregation_radio.value == 'Year':
                # Show a simple bar chart with years on x-axis
                df_grouped = df_filtered.groupby('Year', as_index=False, observed=True).agg({
                    'Total_reported': 'sum',
                    'Deceased': 'sum',
                    'Hospital_admission': 'sum'
                })
                fig = generate_bar_chart(df_grouped, 'Year', metrics, title)

            elif selected_year == 'All' and aggregation_radio.value == 'Months':
                # Show the special monthly chart with years stacked
                if selected_province == 'All Provinces':
                    # Combine data for all provinces
                    df_filtered = df_filtered.groupby(['Month', 'Year'], observed=True).agg({
                        'Total_reported': 'sum',
                        'Deceased': 'sum',
                        'Hospital_admission': 'sum'
                    }).reset_index()

                fig = generate_monthly_chart(df_filtered, metrics, title, MONTH_MAPPING)

            elif selected_year == 'All' and aggregation_radio.value == 'Municipalities':
                # Show the municipality comparison chart
                fig = generate_municipality_chart(df_filtered, metrics, title)

            else:
                # Standard bar chart for other cases
                df_grouped = df_filtered.groupby(x_axis, as_index=False, observed=True).agg({
                    'Total_reported': 'sum',
                    'Deceased': 'sum',
                    'Hospital_admission': 'sum'
                })

                fig = generate_bar_chart(df_grouped, x_axis, metrics, title)

            # Display the chart
            fig.show()

    # Connect the controls to their update functions
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

    # Set up the initial state
    update_municipality_options()
    update_aggregation_options()
    update_plot()

    # Return the complete dashboard section
    return widgets.VBox([controls, output])
