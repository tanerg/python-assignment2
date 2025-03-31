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

    # Save to disk
    save_path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(save_path, driver="GeoJSON")
    print(f"Saved municipality data to {save_path}")

    return gdf
