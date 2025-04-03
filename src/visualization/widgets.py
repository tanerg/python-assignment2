import ipywidgets as widgets

def create_year_dropdown(df):
    return widgets.Dropdown(
        options=['All'] + sorted(df['Year'].unique().tolist()),
        description='Year:',
        value='All'
    )

def create_province_dropdown(df):
    return widgets.Dropdown(
        options=['Netherlands', 'All Provinces'] + sorted(df['Province'].dropna().unique().tolist()),
        description='Province:',
        value='Netherlands'
    )

def create_municipality_dropdown():
    return widgets.Dropdown(
        options=['All'],
        description='Municipality:',
        value='All',
        disabled=True
    )

def create_metric_checkboxes():
    cases_checkbox = widgets.Checkbox(value=True, description='Cases', indent=False)
    deaths_checkbox = widgets.Checkbox(value=True, description='Deaths', indent=False)
    hospital_checkbox = widgets.Checkbox(value=True, description='Hospital Admissions', indent=False)
    return cases_checkbox, deaths_checkbox, hospital_checkbox

def create_aggregation_radio():
    return widgets.RadioButtons(
        options=['Year', 'Municipalities', 'Months'],
        description='Aggregate by:',
        value='Year'
    )
