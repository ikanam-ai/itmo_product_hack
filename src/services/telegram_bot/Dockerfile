FROM python:3.12-bullseye

WORKDIR /app

COPY requirements.txt /tmp
RUN python3 -m pip install -r /tmp/requirements.txt

COPY bot.py /app

CMD ["python3", "-u", "bot.py"]