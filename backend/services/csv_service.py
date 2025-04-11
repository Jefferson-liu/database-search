import pandas as pd
from fastapi import UploadFile

_dataframe = None  # Global for MVP simplicity

async def store_csv(file: UploadFile) -> pd.DataFrame:
    global _dataframe
    contents = await file.read()
    _dataframe = pd.read_csv(pd.compat.StringIO(contents.decode()))
    return _dataframe

def get_dataframe() -> pd.DataFrame | None:
    return _dataframe
