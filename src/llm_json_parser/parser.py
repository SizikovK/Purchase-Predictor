import logging
import re
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import AliasChoices, BaseModel, Field, model_validator
from pypdf import PdfReader

from ..core.config import Settings
from .create_llm import create_llm


logger = logging.getLogger(__name__)


def get_system_prompt() -> str:
    return """
Ты извлекаешь банковские операции из текста одной страницы справки Т-Банка.

На странице таблица содержит колонки в таком порядке:
1. дата и время операции;
2. дата и время списания;
3. сумма в валюте операции;
4. сумма операции в валюте карты;
5. описание операции;
6. последние четыре цифры номера карты либо символ «—».

Правила:
- Верни все и только те операции, которые явно присутствуют на странице.
- Одна операция никогда не переходит на другую страницу.
- Описание может занимать одну или несколько строк. Объедини его части пробелами.
- Не объединяй соседние операции, даже если у них одинаковые дата и время.
- Не включай заголовок таблицы, реквизиты банка, номер страницы и итоговые суммы.
- Сохраняй знак суммы: плюс для поступления, минус для расхода.
- Возвращай обе суммы строками: например, "-500.00" или "+4050.00".
- Удаляй символ валюты и пробелы-разделители тысяч из сумм.
- Не придумывай отсутствующие значения.
- Если на странице нет операций, верни пустой список transactions.
- Поле card_number является строкой: четыре цифры либо символ «—».
- Используй ровно следующие имена полей: operation_date, payment_date,
  operation_amount, card_amount, description, card_number.

Пример одного элемента transactions:
{
  "operation_date": "11.08.2026 12:47",
  "payment_date": "11.08.2026 12:47",
  "operation_amount": "-500.00",
  "card_amount": "-500.00",
  "description": "Пополнение брокерского счета",
  "card_number": "4054"
}

Ответ должен строго соответствовать переданной структурированной схеме.
""".strip()


class Transaction(BaseModel):
    operation_date: str = Field(
        description='Дата и время операции в формате "ДД.ММ.ГГГГ ЧЧ:ММ"',
        validation_alias=AliasChoices("operation_date", "operation_datetime"),
    )
    payment_date: str = Field(
        description='Дата и время списания в формате "ДД.ММ.ГГГГ ЧЧ:ММ"',
        validation_alias=AliasChoices("payment_date", "writeoff_datetime"),
    )
    operation_amount: str = Field(
        description='Сумма в валюте операции строкой со знаком, например "-500.00"',
        validation_alias=AliasChoices(
            "operation_amount", "amount_operation_currency"
        ),
    )
    card_amount: str = Field(
        description='Сумма в валюте карты строкой со знаком, например "-500.00"',
        validation_alias=AliasChoices("card_amount", "amount_card_currency"),
    )
    description: str = Field(description="Полное описание операции")
    card_number: str = Field(
        description='Последние четыре цифры карты или символ «—»'
    )


class PageParsingResult(BaseModel):
    transactions: list[Transaction] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def accept_bare_transaction_list(cls, value):
        """Принимает и {"transactions": [...]}, и возвращённый LLM список [...]."""
        if isinstance(value, list):
            return {"transactions": value}
        return value


class DocumentSchema(BaseModel):
    title: str = "Справка о движении средств"
    pages: dict[int, list[Transaction]] = Field(default_factory=dict)
    errors: dict[int, str] = Field(default_factory=dict)


class DocumentParsingPipeline:
    def __init__(self, settings: Settings):
        model = create_llm(
            provider=settings.llm_provider,
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            model=settings.llm_model,
            temperature=settings.llm_temperature,
        )
        self._structured_model = model.with_structured_output(PageParsingResult)

    @staticmethod
    def _extract_pages(path_to_file: str | Path) -> dict[int, str]:
        reader = PdfReader(path_to_file)
        pages = {}
        for index, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            pages[index] = re.sub(r"\s+", " ", text).strip()
        return pages

    async def _call_llm(self, text: str) -> PageParsingResult:
        messages = [
            SystemMessage(content=get_system_prompt()),
            HumanMessage(content=text),
        ]
        return await self._structured_model.ainvoke(messages)

    async def page_by_page_parsing(self, path_to_file: str | Path) -> DocumentSchema:
        pages = self._extract_pages(path_to_file)
        result = DocumentSchema()

        logger.info("Документ поступил в обработку: %d страниц на обработку", len(pages))

        for page_number, page_text in pages.items():
            logger.info("Идет обработка страницы %d", page_number)
            try:
                parsed_page = await self._call_llm(page_text)
            except Exception as error:
                details = str(error).splitlines()[0]
                message = f"{type(error).__name__}: {details}"
                result.errors[page_number] = message
                logger.error(
                    "Страница %d не обработана: %s",
                    page_number,
                    message,
                )
                continue

            result.pages[page_number] = parsed_page.transactions
            logger.info(
                "Страница %d обработана: найдено операций — %d",
                page_number,
                len(parsed_page.transactions),
            )

        return result










