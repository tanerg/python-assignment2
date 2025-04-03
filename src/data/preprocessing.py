def filter_by_criteria(df, year='All', province='All', municipality='All'):
    if year != 'All':
        df = df[df['Year'] == year]
    if province != 'All':
        df = df[df['Province'] == province]
    if municipality != 'All':
        df = df[df['Municipality_name'] == municipality]
    return df