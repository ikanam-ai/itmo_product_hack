FROM python:3.12-bullseye

WORKDIR /app

COPY requirements.txt /tmp
RUN python3 -m pip install -r /tmp/requirements.txt

# Копируем все Python скрипты и скрипт оболочки в контейнер
COPY bl.py tg_utils.py ai_utils.py email_utils.py start.sh /app/

# Указываем скрипт оболочки как команду для запуска
CMD ["/app/start.sh"]
