# Використовуємо офіційний образ Python
FROM python:3.9.18

# Перейти у робочий каталог /app
WORKDIR /personal_helper

# Скопіювати файли проекту до контейнера
COPY . /personal_helper/

# Встановити залежності зі файла pyproject.toml
RUN pip install poetry && poetry config virtualenvs.create false && poetry install

# Запустити додаток
CMD ["python", "main.py"]
