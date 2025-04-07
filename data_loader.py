import requests
from pathlib import Path
import pandas as pd
import geopandas as gpd
from shapely.geometry import shape


def download_data_from_url(url: str, save_path: Path) -> None:
    """
    Download a file from a given URL and save it to a local path.

    Parameters
    ----------
    url : str
        The URL pointing to the CSV file to be downloaded.
    save_path : Path
        The destination file path where the downloaded content will be saved.
        If the parent directory does not exist, it will be created.

    Returns
    -------
    None
        This function performs a download as a side effect and returns nothing.

    Raises
    ------
    requests.HTTPError
        If the request to the URL fails with a bad HTTP response.
    requests.RequestException
        For other errors related to the HTTP request.
    """
    save_path.parent.mkdir(parents=True, exist_ok=True)

    response = requests.get(url)
    response.raise_for_status()

    with open(save_path, "wb") as f:
        f.write(response.content)

    print(f"Downloaded: {url}: {save_path}")


def load_and_concatenate_csv(file1: Path, file2: Path) -> pd.DataFrame:
    """
    Load and concatenate two semicolon-separated CSV files into a single DataFrame.

    Parameters
    ----------
    file1 : Path
        Path to the first CSV file.
    file2 : Path
        Path to the second CSV file.

    Returns
    -------
    pd.DataFrame
        Concatenated raw DataFrame from both files.
    """
    df1 = pd.read_csv(file1, sep=";", low_memory=False)
    df2 = pd.read_csv(file2, sep=";", low_memory=False)
    return pd.concat([df1, df2], ignore_index=True)


def load_population_data(file_path: Path) -> pd.DataFrame:
    """
    Load a CSV file containing population statistics per municipality and year.

    This function loads the raw dataset from CBS or similar sources and performs no
    cleaning, renaming, or filtering of municipality vs province rows. That logic
    should be handled in the cleaning step.

    Parameters
    ----------
    file_path : Path
        Path to the CSV file containing population statistics.

    Returns
    -------
    pd.DataFrame
        A raw DataFrame with the contents of the population dataset as-is.
    """
    return pd.read_csv(file_path, sep=";", low_memory=False)


def load_municipality_geodata(
    save_path: str = "datasets/municipalities_2023.geojson",
    force_download: bool = False,
) -> gpd.GeoDataFrame:
    """
    Fetch or load Dutch municipality boundary data (2023) from PDOK WFS.

    Parameters
    ----------
    save_path : str
        Path to save the GeoJSON file if downloaded. Defaults to datasets/municipalities_2023.geojson.
    force_download : bool
        If True, re-downloads the data even if the file already exists locally.

    Returns
    -------
    geopandas.GeoDataFrame
        Municipality geometries and metadata.
    """
    save_path = Path(save_path)
    if save_path.exists() and not force_download:
        print(f"Loading municipality data from {save_path}")
        return gpd.read_file(save_path)

    # Define WFS endpoint and parameters
    url = "https://service.pdok.nl/cbs/gebiedsindelingen/2023/wfs/v1_0"
    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typename": "gebiedsindelingen:gemeente_gegeneraliseerd",
        "outputFormat": "application/json",
        "srsName": "EPSG:4326",
    }

    print("Downloading municipality data from PDOK...")
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    # Extract geometries and properties
    features = data["features"]
    geoms = [shape(feature["geometry"]) for feature in features]
    props = [feature["properties"] for feature in features]

    gdf = gpd.GeoDataFrame(props, geometry=geoms, crs="EPSG:4326")

    # Rename columns to match other data
    gdf.rename(columns={
        "statcode": "Municipality_code",
        "statnaam": "Municipality_name"
    }, inplace=True)
    gdf.drop(columns=["jrstatcode", "rubriek", "id"], inplace=True)

    # Save to disk
    save_path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(save_path, driver="GeoJSON")
    print(f"Saved municipality data to {save_path}")

    return gdf


def create_municipality_geodata(df: pd.DataFrame, gdf_geo: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Combine municipality-level COVID data with geometry to create a GeoDataFrame for mapping.

    Parameters
    ----------
    df : pd.DataFrame
        Cleaned COVID dataset with daily data and population per municipality.
        Must include: Municipality_code, Municipality_name, Date, Year, Month,
        Total_reported, Deceased, Hospital_admission, Population.
    
    gdf_geo : geopandas.GeoDataFrame
        GeoDataFrame with municipality geometries. Should already include 'Province' and 'Municipality_code'.

    Returns
    -------
    geopandas.GeoDataFrame
        A GeoDataFrame with one row per day per municipality, containing COVID stats,
        incidence rates, and geometries.
    """
    # Copy COVID data
    df_mun = df.copy()

    # Compute incidence rates per 100k
    for kind, col in [("cases", "Total_reported"), ("deaths", "Deceased"), ("hospital", "Hospital_admission")]:
        df_mun[f"Incidence_rate_{kind}"] = df_mun[col] / df_mun["Population"] * 100_000

    # Merge with geodata
    gdf = gdf_geo.merge(df_mun, on="Municipality_code", how="left")

    # Drop duplicate columns
    if "Municipality_name_x" in gdf.columns and "Municipality_name_y" in gdf.columns:
        gdf.drop(columns=["Municipality_name_x"], inplace=True)
        gdf.rename(columns={"Municipality_name_y": "Municipality_name"}, inplace=True)

    return gdf

def create_province_geodata(gdf_mun: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Create a province-level GeoDataFrame by aggregating a municipality-level COVID GeoDataFrame.

    This function:
    - Aggregates COVID statistics and population at the province level
    - Dissolves geometries by province
    - Computes incidence rates per 100,000 inhabitants

    Parameters
    ----------
    gdf_mun : geopandas.GeoDataFrame
        Municipality-level GeoDataFrame with columns: Province, Date, Year, Month,
        Total_reported, Deceased, Hospital_admission, Population, and geometry.

    Returns
    -------
    geopandas.GeoDataFrame
        A GeoDataFrame with aggregated COVID stats and geometries per province per day.
    """
    # Group and aggregate data per province and day
    df_prov = (
        gdf_mun
        .groupby(["Date", "Year", "Month", "Province"], as_index=False)
        .agg({
            "Total_reported": "sum",
            "Deceased": "sum",
            "Hospital_admission": "sum",
            "Population": "sum"
        })
    )

    # Compute incidence rates
    for kind, col in [("cases", "Total_reported"), ("deaths", "Deceased"), ("hospital", "Hospital_admission")]:
        df_prov[f"Incidence_rate_{kind}"] = df_prov[col] / df_prov["Population"] * 100_000

    # Create province geometry by dissolving municipalities
    gdf_prov_shapes = gdf_mun[["Province", "geometry"]].dropna().dissolve(by="Province", as_index=False)

    # Merge geometry with aggregated stats
    gdf_prov = gdf_prov_shapes.merge(df_prov, on="Province", how="left")

    return gdf_prov


def create_national_geodata(gdf_mun: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Create a national-level GeoDataFrame by aggregating municipality-level COVID data.

    This function:
    - Aggregates COVID statistics and population across all municipalities per day
    - Computes incidence rates per 100,000 inhabitants
    - Creates a single national geometry (the union of all municipality shapes)

    Parameters
    ----------
    gdf_mun : geopandas.GeoDataFrame
        Municipality-level GeoDataFrame with columns: Date, Year, Month, Total_reported,
        Deceased, Hospital_admission, Population, and geometry.

    Returns
    -------
    geopandas.GeoDataFrame
        A GeoDataFrame with one row per day containing national totals and a single geometry.
    """
    # Aggregate COVID data across all municipalities per day
    df_nl = (
        gdf_mun
        .groupby(["Date", "Year", "Month"], as_index=False)
        .agg({
            "Total_reported": "sum",
            "Deceased": "sum",
            "Hospital_admission": "sum",
            "Population": "sum"
        })
    )

    # Compute national incidence rates
    for kind, col in [("cases", "Total_reported"), ("deaths", "Deceased"), ("hospital", "Hospital_admission")]:
        df_nl[f"Incidence_rate_{kind}"] = df_nl[col] / df_nl["Population"] * 100_000

    # Create a single geometry (union of all municipality polygons)
    national_shape = gdf_mun.unary_union
    gdf_nl = gpd.GeoDataFrame(df_nl, geometry=[national_shape] * len(df_nl), crs=gdf_mun.crs)

    return gdf_nl

def save_geodataframes(
    gdf_mun: gpd.GeoDataFrame,
    gdf_prov: gpd.GeoDataFrame,
    gdf_nl: gpd.GeoDataFrame,
    output_dir: str = "datasets/geodata"
) -> None:
    """
    Save municipality, province, and national GeoDataFrames to disk as GeoJSON files.

    Parameters
    ----------
    gdf_mun : geopandas.GeoDataFrame
        Municipality-level GeoDataFrame to save.
    
    gdf_prov : geopandas.GeoDataFrame
        Province-level GeoDataFrame to save.
    
    gdf_nl : geopandas.GeoDataFrame
        National-level GeoDataFrame to save.

    output_dir : str, optional
        Folder to save the files to. Default is 'datasets/geodata'.

    Returns
    -------
    None
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    gdf_mun.to_file(output_path / "municipality_data.geojson", driver="GeoJSON")
    gdf_prov.to_file(output_path / "province_data.geojson", driver="GeoJSON")
    gdf_nl.to_file(output_path / "national_data.geojson", driver="GeoJSON")

    print(f"Saved GeoDataFrames to {output_path.resolve()}")