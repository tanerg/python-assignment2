import folium
import geopandas as gpd
import ipywidgets as widgets
from IPython.display import display
import branca.colormap as cm
import pandas as pd
from pathlib import Path


def create_interactive_covid_map(data_dir: Path = Path("data/geodata")):
    # Load data
    levels = {
        "Municipality": {
            "monthly": gpd.read_file(data_dir / "agg_mun_monthly.geojson"),
            "yearly": gpd.read_file(data_dir / "agg_mun_yearly.geojson")
        },
        "Province": {
            "monthly": gpd.read_file(data_dir / "agg_prov_monthly.geojson"),
            "yearly": gpd.read_file(data_dir / "agg_prov_yearly.geojson")
        },
        "National": {
            "monthly": gpd.read_file(data_dir / "agg_nl_monthly.geojson"),
            "yearly": gpd.read_file(data_dir / "agg_nl_yearly.geojson")
        }
    }

    # Define widgets
    level_dropdown = widgets.Dropdown(
        options=["Municipality", "Province", "National"],
        value="Municipality",
        description="Level:"
    )

    aggregation_dropdown = widgets.Dropdown(
        options=["monthly", "yearly"],
        value="yearly",
        description="Aggregation:"
    )

    stat_dropdown = widgets.Dropdown(
        options=[
            "Total_reported", "Deceased", "Hospital_admission",
            "Incidence_rate_cases", "Incidence_rate_deaths", "Incidence_rate_hospital"
        ],
        value="Incidence_rate_cases",
        description="Statistic:"
    )

    date_dropdown = widgets.Dropdown(description="Date:")

    # Update dates function
    def update_dates(*args):
        df = levels[level_dropdown.value][aggregation_dropdown.value]
        dates = sorted(df["Date"].dropna().unique())

        if aggregation_dropdown.value == "monthly":
            formatted = [pd.to_datetime(d).strftime("%Y-%m") for d in dates]
        else:
            formatted = [pd.to_datetime(d).strftime("%Y") for d in dates]

        date_dropdown.options = formatted
        date_dropdown.value = formatted[0]

    level_dropdown.observe(update_dates, names="value")
    aggregation_dropdown.observe(update_dates, names="value")
    update_dates()

    # Draw map function
    def draw_map(level, aggregation, stat_col, date_value):
        df = levels[level][aggregation]
        if aggregation == "monthly":
            filtered = df[df["Date"].dt.strftime("%Y-%m") == date_value].copy()
        else:
            filtered = df[df["Date"].dt.strftime("%Y") == date_value].copy()

        # Handle date-like columns
        for col in filtered.columns:
            if pd.api.types.is_datetime64_any_dtype(filtered[col]) or isinstance(filtered[col].dtype, pd.PeriodDtype):
                filtered[col] = filtered[col].astype(str)

        # Define color scale
        min_val = filtered[stat_col].min()
        max_val = filtered[stat_col].max()
        colormap = cm.linear.YlGnBu_09.scale(min_val, max_val)
        colormap.caption = stat_col

        def style_function(feature):
            value = feature["properties"].get(stat_col)
            color = colormap(value) if value is not None else "#cccccc"
            return {
                "fillColor": color,
                "color": "black",
                "weight": 0.5,
                "fillOpacity": 0.7,
            }

        # Define name fields
        name_field = (
            "Municipality_name" if level == "Municipality"
            else "Province" if level == "Province"
            else None
        )
        popup_fields = [name_field] if name_field else []

        # Create tooltip
        filtered["tooltip_text"] = filtered.apply(
            lambda row: (
                f"{row.get(name_field, 'The Netherlands')}<br>{stat_col.replace('_', ' ')}: "
                f"{row[stat_col]:,.2f}" if "Incidence_rate" in stat_col else
                f"{row.get(name_field, 'The Netherlands')}<br>{stat_col.replace('_', ' ')}: {int(row[stat_col]):,}"
            ) if pd.notna(row[stat_col]) else
            f"{row.get(name_field, 'The Netherlands')}: no data",
            axis=1
        )

        # Make map
        m = folium.Map(location=[52.1, 5.1], zoom_start=7, tiles="cartodbpositron")
        folium.GeoJson(
            data=filtered.drop(columns=["Date"], errors="ignore"),
            style_function=style_function,
            highlight_function=lambda x: {"weight": 2, "fillOpacity": 0.9},
            tooltip=folium.GeoJsonTooltip(
                fields=["tooltip_text"],
                aliases=[""],
                labels=False,
                sticky=True
            ),
            popup=folium.GeoJsonPopup(
                fields=popup_fields,
                aliases=["Name:"] if name_field else None,
                labels=True
            )
        ).add_to(m)

        colormap.add_to(m)
        display(m)

    # Start widgets
    display(
        widgets.interactive(
            draw_map,
            level=level_dropdown,
            aggregation=aggregation_dropdown,
            stat_col=stat_dropdown,
            date_value=date_dropdown
        )
    )

