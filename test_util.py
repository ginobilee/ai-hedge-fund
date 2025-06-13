from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

def calculate_start_date(end_date: str, limit: int) -> str:
    dt = datetime.strptime(end_date, "%Y-%m-%d")  # [8,6](@ref)

    years_ago = dt - relativedelta(years=limit)
    result = years_ago.strftime("%Y-%m-%d")
    return result

end_date = calculate_start_date(end_date="2025-04-28", limit=5)
print(end_date)