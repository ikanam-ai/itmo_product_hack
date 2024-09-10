#!/bin/sh

# Запуск bl.py в фоновом режиме
python3 /app/bl.py &

# Запуск tg_utils.py в основном потоке
python3 /app/tg_utils.py