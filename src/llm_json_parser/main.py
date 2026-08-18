import argparse
import asyncio
import logging
from logging import INFO
from pathlib import Path

from ..core.config import get_settings
from .calculate_result import calculate_result
from .pipeline import DocumentParsingPipeline

logging.basicConfig(level=INFO)

def analyze_document(path: Path) -> None:
    income, expenses = calculate_result(path)
    logging.info(
        "Итого: Пополнения: %s ₽, Расходы: %s ₽",
        income,
        expenses,
    )

async def run(input_path: Path, output_path: Path) -> None:
    parser = DocumentParsingPipeline(get_settings())
    data = await parser.page_by_page_parsing(input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        data.model_dump_json(indent=2),
        encoding="utf-8",
    )
    logging.info(
        "Результат сохранён в %s: обработано страниц — %d, ошибок — %d",
        output_path,
        len(data.pages),
        len(data.errors),
    )


def main() -> None:
    argument_parser = argparse.ArgumentParser(
        description="Преобразование справки Т-Банка в структурированный JSON"
    )
    argument_parser.add_argument(
        "input",
        nargs="?",
        type=Path,
        default=Path("data/справка.pdf"),
    )
    argument_parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/parsed_output.json"),
    )
    argument_parser.add_argument(
        "--analyze",
        action="store_true",
        help="Проанализировать готовый JSON вместо обработки PDF",
    )

    args = argument_parser.parse_args()

    if not args.analyze:
        asyncio.run(run(args.input, args.output))
    else:
        analyze_document(args.input)

if __name__ == "__main__":
    main()
