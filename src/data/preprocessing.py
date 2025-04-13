def filter_by_criteria(df, year='All', province='All', municipality='All'):
    """
    Filter the dataset by year, province, and municipality.

    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe to filter
    year : str or int
        Year to filter by, use 'All' for all years
    province : str
        Province to filter by, use 'All' for all provinces
    municipality : str
        Municipality to filter by, use 'All' for all municipalities

    Returns:
    --------
    pd.DataFrame
        Filtered dataframe
    """
    if year != 'All':
        df = df[df['Year'] == year]
    if province != 'All':
        df = df[df['Province'] == province]
    if municipality != 'All':
        df = df[df['Municipality_name'] == municipality]
    return df
