from sqlalchemy.orm import Session
from backend.models.csv_row import CsvRow

def get_unique_providers(db: Session):
    result = db.query(CsvRow.provider).distinct().filter(CsvRow.provider.isnot(None)).all()
    return [r[0] for r in result]
