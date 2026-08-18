#ё
# Purchase Predictor

Конвертер PDF-выписки Т-Банка в структурированный JSON с помощью LLM. Документ обрабатывается постранично, а ответы модели проверяются Pydantic.

## Установка

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r src/requirements.txt
cp .env.example .env
```

Укажите в `.env` модель и адрес LLM. При использовании Ollama сервер должен быть запущен, а выбранная модель — доступна.

## Конвертация PDF

Из корня проекта:

```bash
python3 -m src.llm_json_parser.main data/справка.pdf \
  --output data/parsed_output.json
```

Без аргументов используются эти же пути по умолчанию:

```bash
python3 -m src.llm_json_parser.main
```

Итоговый JSON содержит операции по страницам и поле `errors` со страницами, которые не удалось обработать.

## Подсчёт итогов

```bash
python3 -m src.llm_json_parser.main \
  --analyze data/parsed_output.json
```

Команда выводит общую сумму пополнений и расходов. Денежные значения складываются через `Decimal`, поэтому вычисления выполняются без погрешности `float`.
