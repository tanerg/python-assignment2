import pandas as pd


def clean_cases_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and prepare the raw COVID-19 case data.

    This function:
    - Converts the 'Date_of_publication' column to datetime.
    - Drops rows with missing municipality code or name.
    - Renames 'Date_of_publication' to 'Date'.
    - Merges Brielle, Hellevoetsluis, and Westvoorne into Voorne aan Zee.
    - Aggregates duplicate rows caused by merging municipalities.
    - Adds 'Year' and 'Month' columns for temporal grouping.

    Parameters
    ----------
    df : pd.DataFrame
        Raw case data loaded from CSV (combined old and new datasets).

    Returns
    -------
    pd.DataFrame
        Cleaned DataFrame with consistent municipality coding and date-based columns.
    """
    df = df.copy()

    # Convert date and rename
    df["Date_of_publication"] = pd.to_datetime(
        df["Date_of_publication"], errors="coerce"
    )
    df.rename(columns={"Date_of_publication": "Date"}, inplace=True)

    # Drop non-municipal rows
    df = df.dropna(subset=["Municipality_code", "Municipality_name"])

    # Merge Brielle, Hellevoetsluis, and Westvoorne into Voorne aan Zee
    old_codes = ["GM0501", "GM0530", "GM0614"]
    new_code = "GM1992"
    new_name = "Voorne aan Zee"

    df["Municipality_code"] = df["Municipality_code"].replace(old_codes, new_code)
    df["Municipality_name"] = df["Municipality_name"].replace(
        {"Brielle": new_name, "Hellevoetsluis": new_name, "Westvoorne": new_name}
    )

    # Re-aggregate if necessary
    df = df.groupby(
        ["Date", "Municipality_code", "Municipality_name", "Province"], as_index=False
    ).agg({"Total_reported": "sum", "Deceased": "sum"})

    # Add Year and Month columns
    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.to_period("M")

    return df


def clean_hospital_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and prepare the raw hospital admission data.

    This function:
    - Converts the 'Date_of_statistics' column to datetime.
    - Drops rows with missing municipality code or name.
    - Renames 'Date_of_statistics' to 'Date'.
    - Aggregates duplicate rows by municipality and date.
    - Adds 'Year' and 'Month' columns for temporal grouping.

    Parameters
    ----------
    df : pd.DataFrame
        Raw hospital data loaded from CSV (combined old and new datasets).

    Returns
    -------
    pd.DataFrame
        Cleaned and harmonized hospital admission data.
    """
    df = df.copy()

    # Convert date and rename
    df["Date_of_statistics"] = pd.to_datetime(df["Date_of_statistics"], errors="coerce")
    df.rename(columns={"Date_of_statistics": "Date"}, inplace=True)

    # Drop non-municipality rows
    df = df.dropna(subset=["Municipality_code", "Municipality_name"])

    # Aggregate duplicates
    df = df.groupby(
        ["Date", "Municipality_code", "Municipality_name"], as_index=False
    ).agg({"Hospital_admission": "sum"})

    # Add Year and Month
    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.to_period("M")

    return df


def clean_population_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and prepare the raw population data for municipalities.

    This function:
    - Filters for municipality-level entries (RegioS starting with 'GM').
    - Renames columns for clarity and consistency.
    - Converts year format to integer.
    - Converts population values to numeric.
    - Merges outdated municipalities into their new equivalents.
    - Handles Haaren (GM0788) by redistributing its population to 4 municipalities
      only in years where Haaren has valid data.
    - Aggregates population by year and municipality.

    Parameters
    ----------
    df : pd.DataFrame
        Raw population dataset downloaded from CBS.

    Returns
    -------
    pd.DataFrame
        Cleaned DataFrame with columns: 'Municipality_code', 'Year', 'Population'.
    """
    df = df.copy()

    # Keep only municipality rows
    df = df[df["RegioS"].str.startswith("GM")]

    # Rename columns
    df = df.rename(
        columns={
            "RegioS": "Municipality_code",
            "Perioden": "Year",
            "TotaleBevolking_1": "Population",
        }
    )

    # Convert columns
    df["Year"] = df["Year"].str.extract(r"(\d{4})").astype(int)
    df["Population"] = pd.to_numeric(df["Population"], errors="coerce")

    # Replace outdated codes
    # Define fused municipality code replacements
    fused_municipality_map = {
        "GM0370": "GM0439",  # Beemster → Purmerend
        "GM0398": "GM1980",  # Heerhugowaard → Dijk en Waard
        "GM0416": "GM1980",  # Langedijk → Dijk en Waard
        "GM0457": "GM0363",  # Weesp → Amsterdam
        "GM0501": "GM1992",  # Brielle → Voorne aan Zee
        "GM0530": "GM1992",  # Hellevoetsluis → Voorne aan Zee
        "GM0614": "GM1992",  # Westvoorne → Voorne aan Zee
        "GM0756": "GM1982",  # Boxmeer → Land van Cuijk
        "GM0786": "GM1982",  # Grave → Land van Cuijk
        "GM0815": "GM1982",  # Mill en Sint Hubert → Land van Cuijk
        "GM0856": "GM1991",  # Uden → Maashorst
        "GM1684": "GM1982",  # Cuijk → Land van Cuijk
        "GM1685": "GM1991",  # Landerd → Maashorst
        "GM1702": "GM1982",  # Sint Anthonis → Land van Cuijk
        "GM0003": "GM1979",  # Appingedam → Eemsdelta
        "GM0010": "GM1979",  # Delfzijl → Eemsdelta
        "GM0024": "GM1979",  # Loppersum → Eemsdelta
    }
    df["Municipality_code"] = df["Municipality_code"].replace(fused_municipality_map)

    # Handle Haaren (GM0788) splitting of population over 4 existing municipalities
    haaren_code = "GM0788"
    receiving_codes = [
        "GM0824",
        "GM0865",
        "GM0757",
        "GM0855",
    ]  # Oisterwijk, Vught, Boxtel, Tilburg

    haaren_valid_rows = df[
        (df["Municipality_code"] == haaren_code) & (df["Population"].notna())
    ]
    haaren_years = haaren_valid_rows["Year"].unique()

    for year in haaren_years:
        haaren_population = haaren_valid_rows[haaren_valid_rows["Year"] == year][
            "Population"
        ].values[0]
        split_population = haaren_population / 4

        for code in receiving_codes:
            mask = (df["Municipality_code"] == code) & (df["Year"] == year)
            if df[mask].empty:
                df = pd.concat(
                    [
                        df,
                        pd.DataFrame(
                            {
                                "Municipality_code": [code],
                                "Year": [year],
                                "Population": [split_population],
                            }
                        ),
                    ],
                    ignore_index=True,
                )
            else:
                df.loc[mask, "Population"] += split_population

    # Drop Haaren from final result
    df = df[df["Municipality_code"] != haaren_code]

    # Final aggregation
    df = df.groupby(["Municipality_code", "Year"], as_index=False).agg(
        {"Population": "sum"}
    )

    return df


def cast_column_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cast standard columns to appropriate types (int, datetime, etc.).

    Parameters
    ----------
    df : pd.DataFrame
        The cleaned but untyped DataFrame.

    Returns
    -------
    pd.DataFrame
        DataFrame with proper column types enforced.
    """
    df = df.copy()

    if "Year" in df.columns:
        df["Year"] = df["Year"].astype(int)

    if "Month" in df.columns and df["Month"].dtype.name != "period[M]":
        df["Month"] = pd.to_datetime(df["Month"]).dt.to_period("M")

    for col in ["Total_reported", "Deceased", "Hospital_admission", "Population"]:
        if col in df.columns:
            df[col] = df[col].fillna(0).astype(int)

    return df
