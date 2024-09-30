# Используем официальный образ Python как базовый
FROM python:3.12-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY pyproject.toml poetry.lock /app/

# Устанавливаем Poetry
RUN pip install poetry

# Устанавливаем зависимости
RUN poetry config virtualenvs.create false && poetry install --no-root

# Копируем весь проект
COPY . /app/

# Устанавливаем статические файлы
RUN python manage.py collectstatic --noinput

# Команда для запуска приложения
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
