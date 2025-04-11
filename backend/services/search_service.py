from sqlalchemy.orm import Session
from backend.models.csv_row import CsvRow

def search_csv(db: Session, filters: dict):
    query = db.query(CsvRow)

    for key, value in filters.items():
        if key.endswith("_lt"):
            col = getattr(CsvRow, key[:-3], None)
            if col is not None:
                query = query.filter(col < value)
        elif key.endswith("_gt"):
            col = getattr(CsvRow, key[:-3], None)
            if col is not None:
                query = query.filter(col > value)
        else:
            col = getattr(CsvRow, key, None)
            if col is not None:
                query = query.filter(col == value)

    return [row.__dict__ for row in query.all()]
