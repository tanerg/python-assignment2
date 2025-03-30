import pandas as pd


def combine_cases_and_hospital_data(
    df_cases: pd.DataFrame, df_hospital: pd.DataFrame
) -> pd.DataFrame:
    """
    Combine cleaned COVID case and hospital admission data, keeping only records
    where both datasets have data for the same municipality and date.

    Parameters
    ----------
    df_cases : pd.DataFrame
        Cleaned case data with columns:
        ['Date', 'Municipality_code', 'Municipality_name', 'Province', 'Total_reported', 'Deceased', 'Year', 'Month']

    df_hospital : pd.DataFrame
        Cleaned hospital data with columns:
        ['Date', 'Municipality_code', 'Municipality_name', 'Hospital_admission', 'Year', 'Month']

    Returns
    -------
    pd.DataFrame
        Combined dataframe containing only rows where both cases and hospital data are present.
    """
    df_covid = pd.merge(
        df_hospital[
            ["Date", "Municipality_code", "Municipality_name", "Hospital_admission"]
        ],
        df_cases[
            [
                "Date",
                "Municipality_code",
                "Province",
                "Total_reported",
                "Deceased",
                "Year",
                "Month",
            ]
        ],
        how="outer",
        on=["Date", "Municipality_code"],
    )
    df_covid = df_covid.dropna().reset_index(drop=True)

    return df_covid


def add_population_and_calculate_incidence(
    df_covid: pd.DataFrame, df_population: pd.DataFrame
) -> pd.DataFrame:
    """
    Merge combined COVID data with population data and calculate incidence rates.

    This function joins the combined COVID case and hospital data with population statistics
    based on municipality code and year, and calculates incidence rates per 100,000 people.

    Parameters
    ----------
    df_covid : pd.DataFrame
        Combined COVID data with cases and hospital admissions.
        Must contain columns: ['Date', 'Municipality_code', 'Year', 'Total_reported', 'Deceased', 'Hospital_admission']

    df_population : pd.DataFrame
        Cleaned population data with columns: ['Municipality_code', 'Year', 'Population']

    Returns
    -------
    pd.DataFrame
        Merged dataset with additional columns:
        ['Population', 'Incidence_rate_cases', 'Incidence_rate_deaths', 'Incidence_rate_hospital_admission']
    """
    df = pd.merge(df_covid, df_population, on=["Municipality_code", "Year"], how="left")

    # Calculate incidence rates per 100,000
    df["Incidence_rate_cases"] = df["Total_reported"] / df["Population"] * 100_000
    df["Incidence_rate_deaths"] = df["Deceased"] / df["Population"] * 100_000
    df["Incidence_rate_hospital_admission"] = (
        df["Hospital_admission"] / df["Population"] * 100_000
    )

    # Reorder columns
    df = df[
        [
            "Date",
            "Month",
            "Year",
            "Municipality_code",
            "Municipality_name",
            "Province",
            "Population",
            "Hospital_admission",
            "Total_reported",
            "Deceased",
            "Incidence_rate_hospital_admission",
            "Incidence_rate_cases",
            "Incidence_rate_deaths",
        ]
    ]

    return df
