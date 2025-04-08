import plotly.express as px
from config.constants import COLOR_MAPPING
import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go

def generate_bar_chart(df_grouped, x_axis, metrics, title):
    # Create nice metric names dictionary
    metric_labels = {
        'Total_reported': 'Cases',
        'Deceased': 'Deaths',
        'Hospital_admission': 'Hospital Admissions'
    }

    # If we're directly using metrics as columns (side-by-side bars),
    # we need to rename them in the dataframe before plotting
    df_plot = df_grouped.copy()

    # Extend the labels with metric names for hover text
    labels = {
        'value': 'Count',
        'variable': 'Metric',
        x_axis: x_axis.replace('_', ' ')
    }

    # Convert the dataframe to have properly named columns for the legend
    if len(metrics) > 0:
        # Melt the data to use the nicer metric names in the legend
        id_vars = [col for col in df_plot.columns if col not in metrics]
        df_melted = pd.melt(
            df_plot,
            id_vars=id_vars,
            value_vars=metrics,
            var_name='Metric',
            value_name='Value'
        )

        # Map the metric names to nice display values
        df_melted['Metric'] = df_melted['Metric'].map(metric_labels)

        # Create the plot with the melted data
        fig = px.bar(
            df_melted,
            x=x_axis,
            y='Value',
            color='Metric',  # Use the nice metric names for the legend
            title=title,
            labels=labels,
            barmode='group',
            color_discrete_map={metric_labels[metric]: COLOR_MAPPING[metric] for metric in metrics if metric in metric_labels}
        )
    else:
        # Fallback to original approach if no metrics
        fig = px.bar(
            df_plot,
            x=x_axis,
            y=metrics,
            title=title,
            labels=labels,
            color_discrete_map={metric: COLOR_MAPPING[metric] for metric in metrics}
        )
        fig.update_layout(barmode='group')

    fig.update_xaxes(type='category', tickangle=-45)
    return fig

def generate_monthly_chart(df_filtered, metrics, title, month_mapping):
    """
    Generate a stacked bar chart for monthly data with years stacked within each metric.

    Parameters:
    -----------
    df_filtered : pd.DataFrame
        Filtered dataframe with Month and Year columns
    metrics : list
        List of metric columns to include (e.g., ['Total_reported', 'Deceased'])
    title : str
        Chart title
    month_mapping : dict
        Dictionary mapping numeric months to month names

    Returns:
    --------
    plotly.graph_objects.Figure
        Plotly figure with the chart
    """
    # Make a fresh copy of filtered data
    df_month = df_filtered.copy()

    # Ensure Month is numeric
    if not pd.api.types.is_numeric_dtype(df_month['Month']):
        # If already converted to string/categorical, convert back
        month_to_num = {v: k for k, v in month_mapping.items()}
        df_month['Month'] = df_month['Month'].map(month_to_num)

    # Add Year as string for better display
    df_month['Year_str'] = df_month['Year'].astype(str)

    # Get the month name for better display
    df_month['Month_name'] = df_month['Month'].map(month_mapping)

    # Prepare data for visualization - melt metrics into rows
    metrics_list = []
    metric_mapping = {
        'Total_reported': 'Cases',
        'Deceased': 'Deaths',
        'Hospital_admission': 'Hospital Admissions'
    }

    for metric in metrics:
        if metric in metric_mapping:
            metrics_list.append((metric, metric_mapping[metric]))

    # Create a dataframe for plotting
    plot_data = []

    # For each month, metric, and year, collect the data
    for month_num in sorted(df_month['Month'].unique()):
        month_name = month_mapping.get(month_num, str(month_num))
        for metric_col, metric_name in metrics_list:
            for year in sorted(df_month['Year'].unique()):
                year_str = str(year)
                # Get the value for this combination
                mask = (df_month['Month'] == month_num) & (df_month['Year'] == year)
                if mask.any():
                    value = df_month.loc[mask, metric_col].sum()
                    # Add to plot data
                    plot_data.append({
                        'Month': month_name,
                        'Metric': metric_name,
                        'Year': year_str,
                        'Month_Metric': f"{month_name} - {metric_name}",
                        'Value': value
                    })

    # Convert to DataFrame
    if not plot_data:
        # No data - create empty chart
        fig = px.bar(
            x=['No Data'],
            y=[0],
            title=f"{title} - No data available"
        )
    else:
        # Create DataFrame and set column types
        plot_df = pd.DataFrame(plot_data)

        # Create categorical types for proper ordering
        month_list = [month_mapping[i] for i in range(1, 13)
                    if month_mapping[i] in plot_df['Month'].unique()]
        plot_df['Month'] = pd.Categorical(
            plot_df['Month'],
            categories=month_list,
            ordered=True
        )

        # Generate all Month-Metric combinations
        month_metrics = []
        for month in month_list:
            for _, metric_name in metrics_list:
                month_metrics.append(f"{month} - {metric_name}")

        plot_df['Month_Metric'] = pd.Categorical(
            plot_df['Month_Metric'],
            categories=month_metrics,
            ordered=True
        )

        # Create the chart
        plot_df['Metric_display'] = plot_df['Metric']

        fig = px.bar(
            plot_df,
            x='Month_Metric',
            y='Value',
            color='Year',
            barmode='stack',
            title=title,
            labels={
                'Value': 'Count',
                'Year': 'Year',
                'Month_Metric': ''
            },
            color_discrete_sequence=px.colors.qualitative.Set1
        )

        # Improve layout
        fig.update_layout(
            height=600,
            width=1200,
            legend_title_text='Year'
        )

        # Improve x-axis labels
        metric_names = [m[1] for m in metrics_list]
        fig.update_xaxes(
            tickangle=-45,
            tickmode='array',
            tickvals=list(range(len(month_metrics))),
            ticktext=[m.split(' - ')[1] if i % len(metric_names) != 0 else m
                    for i, m in enumerate(month_metrics)]
        )

        # Add vertical separators between months
        for i in range(1, len(month_list)):
            line_position = i * len(metric_names) - 0.5
            fig.add_vline(x=line_position, line_width=1, line_color="gray", line_dash="dash")

    return fig

def generate_municipality_chart(df_filtered, metrics, title):
    """
    Generate a chart for municipality data with years stacked within each metric.

    Parameters:
    -----------
    df_filtered : pd.DataFrame
        Filtered dataframe with Municipality_name and Year columns
    metrics : list
        List of metric columns to include (e.g., ['Total_reported', 'Deceased'])
    title : str
        Chart title

    Returns:
    --------
    plotly.graph_objects.Figure
        Plotly figure with the chart
    """
    # First convert Year to string to avoid dtype issues
    df_filtered['Year_str'] = df_filtered['Year'].astype(str)

    # Create a copy to work with
    df_muni = df_filtered.copy()

    # Group by Municipality and Year to get the totals
    df_grouped = df_muni.groupby(['Municipality_name', 'Year_str'], observed=True).agg({
        'Total_reported': 'sum',
        'Deceased': 'sum',
        'Hospital_admission': 'sum'
    }).reset_index()

    # Sort years in correct chronological order (oldest at bottom, newest at top)
    year_order = sorted(df_grouped['Year_str'].unique(), key=int)
    df_grouped['Year_str'] = pd.Categorical(
        df_grouped['Year_str'],
        categories=year_order,
        ordered=True
    )

    # Melt the dataframe to create the correct structure for side-by-side bars with stacked years
    df_melted = pd.melt(
        df_grouped,
        id_vars=['Municipality_name', 'Year_str'],
        value_vars=metrics,
        var_name='Metric',
        value_name='Count'
    )

    # Create nicer names for metrics
    metric_mapping = {
        'Total_reported': 'Cases',
        'Deceased': 'Deaths',
        'Hospital_admission': 'Hospital Admissions'
    }
    df_melted['Metric'] = df_melted['Metric'].map(metric_mapping)

    # Create a combined x-axis label
    df_melted['Muni_Metric'] = df_melted['Municipality_name'] + ' - ' + df_melted['Metric']

    # Create a categorical version for correct ordering - grouped by municipality first
    muni_metrics = []
    # Get ordered list of municipalities and metrics
    # Limit to top 15 municipalities by total cases to avoid overcrowding
    top_municipalities = df_muni.groupby('Municipality_name', observed=True).agg(
        {'Total_reported': 'sum'}
    ).sort_values('Total_reported', ascending=False).head(15).index.tolist()

    # Filter to only include top municipalities
    df_melted = df_melted[df_melted['Municipality_name'].isin(top_municipalities)]

    # Get ordered metrics
    metrics_list = [metric_mapping.get(m) for m in metrics if m in metric_mapping]

    # First group by municipality, then by metric within each municipality
    for muni in top_municipalities:
        for metric in metrics_list:
            muni_metrics.append(f"{muni} - {metric}")

    df_melted['Muni_Metric'] = pd.Categorical(
        df_melted['Muni_Metric'],
        categories=muni_metrics,
        ordered=True
    )

    # Create a single chart with grouped bars by municipality and metric, stacked by year
    fig = px.bar(
        df_melted,
        x='Muni_Metric',
        y='Count',
        color='Year_str',  # Color by year for stacking
        barmode='stack',
        title=title,
        labels={
            'Count': 'Count',
            'Year_str': 'Year',
            'Muni_Metric': ''
        },
        color_discrete_sequence=px.colors.qualitative.Set1,
        category_orders={'Year_str': year_order}
    )

    # Improve layout
    fig.update_layout(
        height=600,
        width=1500,  # Wider to accommodate more municipalities
        legend_title_text='Year',
        xaxis_title="Municipality - Metric"
    )

    # Adjust x-axis for better readability
    fig.update_xaxes(
        tickangle=-45,
        tickmode='array',
        tickvals=list(range(len(muni_metrics))),
        ticktext=[m.split(' - ')[1] if i % len(metrics_list) != 0 else m.split(' - ')[0] for i, m in enumerate(muni_metrics)]
    )

    # Add vertical lines between municipality groups for visual separation
    if len(top_municipalities) > 1:
        for i in range(1, len(top_municipalities)):
            line_position = i * len(metrics_list) - 0.5
            fig.add_vline(x=line_position, line_width=1, line_color="gray", line_dash="dash")

    return fig

def generate_incidence_line_chart(df_filtered, metrics, title, month_mapping):
    """
    Generate a line chart showing incidence rates over time.

    Parameters:
    -----------
    df_filtered : pd.DataFrame
        Filtered dataframe with incidence rate columns
    metrics : list
        List of incidence rate metrics to include
    title : str
        Chart title
    month_mapping : dict
        Dictionary mapping numeric months to month names

    Returns:
    --------
    plotly.graph_objects.Figure
        Line chart showing incidence rates over time
    """
    # Create nice metric names dictionary
    metric_labels = {
        'Incidence_rate_cases': 'Case Rate (per 100k)',
        'Incidence_rate_deaths': 'Death Rate (per 100k)',
        'Incidence_rate_hospital_admission': 'Hospitalization Rate (per 100k)'
    }

    # Ensure we have data to plot
    if df_filtered.empty:
        fig = px.line(
            x=[0], y=[0],
            title=f"{title} - No data available"
        )
        return fig

    # Make a copy to avoid modifying the original
    df_plot = df_filtered.copy()

    # Ensure Year is present as needed for grouping
    if 'Year' not in df_plot.columns and 'Year_str' in df_plot.columns:
        df_plot['Year'] = df_plot['Year_str'].astype(int)

    # Prepare data for time-based visualization
    # If Month column exists, use it for x-axis
    if 'Month' in df_plot.columns:
        # If Month is numeric, map to names
        if pd.api.types.is_numeric_dtype(df_plot['Month']):
            df_plot['Month_name'] = df_plot['Month'].map(month_mapping)
            time_column = 'Month_name'
        # If Month is already a string or object type
        else:
            # If it's a period, convert to string
            if isinstance(df_plot['Month'].iloc[0], pd.Period):
                df_plot['Month_str'] = df_plot['Month'].dt.strftime('%Y-%m')
                time_column = 'Month_str'
            else:
                time_column = 'Month'
    # If no Month column, try to use Date
    elif 'Date' in df_plot.columns:
        time_column = 'Date'
    else:
        # Fallback to Year if no month or date
        time_column = 'Year'

    # Group by time and region (province or municipality) if available
    group_cols = [time_column]

    if 'Province' in df_plot.columns:
        group_cols.append('Province')
        color_column = 'Province'
    elif 'Municipality_name' in df_plot.columns:
        group_cols.append('Municipality_name')
        color_column = 'Municipality_name'
    else:
        color_column = None

    # If using months, ensure proper ordering
    if time_column == 'Month_name' and 'Month' in df_plot.columns:
        # Create a sort key based on numeric month
        df_plot['month_sort'] = df_plot['Month']
        df_plot = df_plot.sort_values(['Year', 'month_sort'])

    # Group and aggregate the data
    if 'Month' in df_plot.columns or 'Date' in df_plot.columns:
        df_grouped = df_plot.groupby(group_cols, observed=True)[metrics].mean().reset_index()
    else:
        df_grouped = df_plot

    # Create the line chart
    fig = px.line(
        df_grouped,
        x=time_column,
        y=metrics,
        color=color_column,
        markers=True,  # Show markers at data points
        title=title,
        labels={m: metric_labels.get(m, m) for m in metrics},
        hover_data={time_column: True, color_column: True if color_column else False}
    )

    # Improve layout
    fig.update_layout(
        height=600,
        width=1200,
        xaxis_title="Time Period",
        yaxis_title="Incidence Rate (per 100,000 population)",
        legend_title=color_column if color_column else "Metric",
        hovermode="x unified"  # Show all points at the same x-value
    )

    # Add range slider for date/time selection
    has_multiple_periods = len(df_grouped[time_column].unique()) > 3
    if has_multiple_periods:
        fig.update_xaxes(rangeslider_visible=True)

    return fig
