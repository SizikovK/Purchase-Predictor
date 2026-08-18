import json
from decimal import Decimal
from pathlib import Path


def calculate_result(file_path: Path) -> tuple[Decimal, Decimal, int]:
    income = Decimal("0")
    expenses = Decimal("0")
    transaction_count: int = 0

    with file_path.open("r", encoding="utf-8") as file:
        document = json.load(file)

    pages = document["pages"]
    for transactions in pages.values():
        for transaction in transactions:
            operation_amount = Decimal(transaction["operation_amount"])
            if operation_amount > 0:
                income += operation_amount
            elif operation_amount < 0:
                expenses += abs(operation_amount)
            transaction_count += 1

    return income, expenses, transaction_count