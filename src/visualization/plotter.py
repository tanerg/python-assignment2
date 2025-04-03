import plotly.express as px
from config.constants import COLOR_MAPPING

def generate_bar_chart(df_grouped, x_axis, metrics, title):
    fig = px.bar(
        df_grouped,
        x=x_axis,
        y=metrics,
        title=title,
        labels={'value': 'Count', 'variable': 'Metric', x_axis: x_axis.replace('_', ' ')},
        color_discrete_map={metric: COLOR_MAPPING[metric] for metric in metrics}
    )
    fig.update_xaxes(type='category', tickangle=-45)
    fig.update_layout(barmode='group')
    return fig
