def search_csv(df, query: str):
    query = query.lower()
    results = df[df.apply(lambda row: row.astype(str).str.lower().str.contains(query).any(), axis=1)]
    return results.to_dict(orient="records")
