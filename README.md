# itmo_product_hack: Наполеон IT Sales агент для сервиса "Отзывы" 

Система состоит из следующих серверов:
* MongoDB
* Сервер бизнес логики
* Сервер обработки email
* Сервер ТГ бота

Коммуникация между серверами осуществляется через MongoDB.

Т.к. средств для запуска машины c GPU в Яндекс облаке было недостаточно. LLM запущена на собственном сервере.
Сервер бизнес логики общается с LLM через MongoDB соединение с использованием публичного IP адреса.

# Как запустить систему
Каждый сервер системы запускается в собственном Docker контейере. Управдение контейнерами реализовано через docker-compose.

Для запуска системы перейдите в папку src/services и выполните: ```docker compose -d up```

Для остановки системы: ```docker compose down```

Для первоначального старта системы, в БД необходимо записать информацию об email аккаунте и создать .env файл:
* Запустите контейнеры и убедитесь что Mongo контейнер работает (```docker ps```)
* Отредактируйте src/services/init_data.json
* Из папки src/services запустите ```docker run -it -v ./:/my --network=host mail_worker bash``` Откроется консоль в свежезапущенном контейнере
* ```cd /my && python3 populate_data.py```
* Отключитесь от контейнер Ctrl-d

Для мониторинга системы используются логи в докере: ```docker logs app_logic```