import requests
from pathlib import Path
import pandas as pd


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


def load_cases_data(file1: Path, file2: Path) -> pd.DataFrame:
    """
    Load and concatenate two raw CSV files containing COVID-19 reported case data per municipality.

    This function simply loads the files and combines them in order. It does not perform
    any cleaning, date conversion, or column renaming. Use `dataframe_cleaner` for that.

    Parameters
    ----------
    file1 : Path
        Path to the more recent dataset (after October 3, 2021).
    file2 : Path
        Path to the earlier dataset (up to and including October 3, 2021).

    Returns
    -------
    pd.DataFrame
        A raw, concatenated DataFrame with the original column names from the CSV files.
        Cleaning and preprocessing should be done separately.
    """
    df1 = pd.read_csv(file1, sep=';', low_memory=False)
    df2 = pd.read_csv(file2, sep=';', low_memory=False)
    return pd.concat([df1, df2], ignore_index=True)


def load_hospital_data(file1: Path, file2: Path) -> pd.DataFrame:
    """
    Load and concatenate two raw CSV files containing hospital admission data per municipality.

    This function reads both CSV files and returns a single combined DataFrame without
    applying any cleaning or transformations. Column names and data types remain unchanged.

    Parameters
    ----------
    file1 : Path
        Path to the more recent hospital dataset (after October 3, 2021).
    file2 : Path
        Path to the earlier hospital dataset (up to and including October 3, 2021).

    Returns
    -------
    pd.DataFrame
        A raw, concatenated DataFrame containing hospital data as originally stored in the files.
        Cleaning and preprocessing should be handled elsewhere.
    """
    df1 = pd.read_csv(file1, sep=';', low_memory=False)
    df2 = pd.read_csv(file2, sep=';', low_memory=False)
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
    return pd.read_csv(file_path, sep=';', low_memory=False)
