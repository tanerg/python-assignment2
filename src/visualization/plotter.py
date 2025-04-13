import plotly.express as px
from config.constants import COLOR_MAPPING
import pandas as pd
from plotly.subplots import make_subplots

def generate_bar_chart(df_grouped, x_axis, metrics, title):
    """
    Generate a grouped bar chart showing multiple metrics side by side.

    Parameters:
    -----------
    df_grouped : pd.DataFrame
        Grouped dataframe containing metrics as columns to be visualized
    x_axis : str
        Column name to use for the x-axis categories
    metrics : list
        List of metric columns to include (e.g., ['Total_reported', 'Deceased'])
    title : str
        Chart title

    Returns:
    --------
    plotly.graph_objects.Figure
        Plotly figure with grouped bar chart
    """
    # Dictionary to display friendly metric names
    metric_labels = {
        'Total_reported': 'Cases',
        'Deceased': 'Deaths',
        'Hospital_admission': 'Hospital Admissions'
    }

    df_plot = df_grouped.copy()

    # Labels for tooltip and axis display
    labels = {
        'value': 'Count',
        'variable': 'Metric',
        x_axis: x_axis.replace('_', ' ')
    }

    if len(metrics) > 0:
        # Transform wide data to long format for better Plotly handling
        id_vars = [col for col in df_plot.columns if col not in metrics]
        df_melted = pd.melt(
            df_plot,
            id_vars=id_vars,
            value_vars=metrics,
            var_name='Metric',
            value_name='Value'
        )

        # Use friendly metric names
        df_melted['Metric'] = df_melted['Metric'].map(metric_labels)

        # Create grouped bar chart
        fig = px.bar(
            df_melted,
            x=x_axis,
            y='Value',
            color='Metric',
            title=title,
            labels=labels,
            barmode='group',
            color_discrete_map={metric_labels[metric]: COLOR_MAPPING[metric] for metric in metrics if metric in metric_labels}
        )
    else:
        # Fallback for no metrics selected
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
    df_month = df_filtered.copy()

    # Convert month values to numeric if needed
    if not pd.api.types.is_numeric_dtype(df_month['Month']):
        month_to_num = {v: k for k, v in month_mapping.items()}
        df_month['Month'] = df_month['Month'].map(month_to_num)

    # Convert year to string for better display in legend
    df_month['Year_str'] = df_month['Year'].astype(str)

    # Map numeric months to names for display
    df_month['Month_name'] = df_month['Month'].map(month_mapping)

    # Create friendly metric name mapping
    metrics_list = []
    metric_mapping = {
        'Total_reported': 'Cases',
        'Deceased': 'Deaths',
        'Hospital_admission': 'Hospital Admissions'
    }

    for metric in metrics:
        if metric in metric_mapping:
            metrics_list.append((metric, metric_mapping[metric]))

    # Generate data points for each month-metric-year combination
    plot_data = []
    for month_num in sorted(df_month['Month'].unique()):
        month_name = month_mapping.get(month_num, str(month_num))
        for metric_col, metric_name in metrics_list:
            for year in sorted(df_month['Year'].unique()):
                year_str = str(year)
                # Find values where month and year match
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

    # Handle empty data case
    if not plot_data:
        fig = px.bar(
            x=['No Data'],
            y=[0],
            title=f"{title} - No data available"
        )
    else:
        # Create DataFrame from collected data points
        plot_df = pd.DataFrame(plot_data)

        # Ensure months are in chronological order
        month_list = [month_mapping[i] for i in range(1, 13)
                    if month_mapping[i] in plot_df['Month'].unique()]
        plot_df['Month'] = pd.Categorical(
            plot_df['Month'],
            categories=month_list,
            ordered=True
        )

        # Create all month-metric combinations for proper ordering
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

        # Create stacked bar chart
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

        # Set chart dimensions
        fig.update_layout(
            height=600,
            width=1200,
            legend_title_text='Year'
        )

        # Format x-axis labels to show month names with metrics
        metric_names = [m[1] for m in metrics_list]
        fig.update_xaxes(
            tickangle=-45,
            tickmode='array',
            tickvals=list(range(len(month_metrics))),
            ticktext=[m.split(' - ')[1] if i % len(metric_names) != 0 else m
                    for i, m in enumerate(month_metrics)]
        )

        # Add vertical separators between month groups
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
    # Convert Year to string for legend display
    df_filtered['Year_str'] = df_filtered['Year'].astype(str)
    df_muni = df_filtered.copy()

    # Summarize data by municipality and year
    df_grouped = df_muni.groupby(['Municipality_name', 'Year_str'], observed=True).agg({
        'Total_reported': 'sum',
        'Deceased': 'sum',
        'Hospital_admission': 'sum'
    }).reset_index()

    # Ensure years appear in chronological order
    year_order = sorted(df_grouped['Year_str'].unique(), key=int)
    df_grouped['Year_str'] = pd.Categorical(
        df_grouped['Year_str'],
        categories=year_order,
        ordered=True
    )

    # Transform data to long format for visualizing
    df_melted = pd.melt(
        df_grouped,
        id_vars=['Municipality_name', 'Year_str'],
        value_vars=metrics,
        var_name='Metric',
        value_name='Count'
    )

    # Use friendly metric names
    metric_mapping = {
        'Total_reported': 'Cases',
        'Deceased': 'Deaths',
        'Hospital_admission': 'Hospital Admissions'
    }
    df_melted['Metric'] = df_melted['Metric'].map(metric_mapping)

    # Order municipalities by total case count
    municipality_totals = df_grouped.groupby('Municipality_name', observed=True).agg({
        'Total_reported': 'sum'
    }).sort_values('Total_reported', ascending=False)

    all_municipalities = municipality_totals.index.tolist()

    # Create list of friendly metric names
    metrics_list = [metric_mapping.get(m) for m in metrics if m in metric_mapping]

    # Create combined x-axis labels
    df_melted['Muni_Metric'] = df_melted['Municipality_name'] + ' - ' + df_melted['Metric']

    # Generate all municipality-metric combinations for consistent ordering
    muni_metrics = []
    for muni in all_municipalities:
        for metric in metrics_list:
            muni_metrics.append(f"{muni} - {metric}")

    # Create ordered categorical for proper x-axis sorting
    df_melted['Muni_Metric'] = pd.Categorical(
        df_melted['Muni_Metric'],
        categories=muni_metrics,
        ordered=True
    )

    # Ensure proper data ordering
    df_melted = df_melted.sort_values(['Muni_Metric', 'Year_str'])

    # Create stacked bar chart
    fig = px.bar(
        df_melted,
        x='Muni_Metric',
        y='Count',
        color='Year_str',
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

    # Set chart dimensions
    fig.update_layout(
        height=600,
        width=1800,
        legend_title_text='Year',
        xaxis_title="Municipality - Metric"
    )

    # Format x-axis labels to show municipality name only for first metric
    if muni_metrics:
        ticktext = []
        for i, m in enumerate(muni_metrics):
            if i % len(metrics_list) == 0:
                ticktext.append(m.split(' - ')[0])
            else:
                ticktext.append(m.split(' - ')[1])

        fig.update_xaxes(
            tickangle=-65,
            tickmode='array',
            tickvals=list(range(len(muni_metrics))),
            ticktext=ticktext
        )

    # Add visual separators between municipality groups
    if len(all_municipalities) > 1:
        for i in range(1, len(all_municipalities)):
            line_position = i * len(metrics_list) - 0.5
            fig.add_vline(x=line_position, line_width=1, line_color="gray", line_dash="dash")

    return fig
