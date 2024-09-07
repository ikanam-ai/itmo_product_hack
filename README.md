# itmo_product_hack

# How to start
The system is built with Docker and docker-compose. All servers are run in their respective containers.
For now the host network is used for container communication.

To start the system run: ```docker compose -d up```

To stop: ```docker compose down```

To populate data ito the DB:
* Start containers, check if all is running (```docker ps```)
* Modify init_data.json
* From the root folder of the project run ```docker run -it -v ./:/my --network=host mail_worker bash``` you will get a bash console inside the newly run container
* ```cd /my && python3 populate_data.py```
* Exit the container with Ctrl-d