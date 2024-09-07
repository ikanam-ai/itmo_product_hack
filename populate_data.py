import json
import pymongo

DATA_FILE = "init_data.json"

with open(DATA_FILE, "r") as fd:
    data = json.load(fd)

mongo_addr = data['mongo_ip']
mongo_port = data['mongo_port']
mongo_full_addr = f"mongodb://{mongo_addr}:{mongo_port}/"
print("Connecting to MongoDB " + mongo_full_addr)

mongo_client = pymongo.MongoClient(mongo_full_addr)
db_name = data["db"]

if db_name in mongo_client.list_database_names():
    print("Dropping DB " + db_name)
    mongo_client.drop_database(db_name)

print("Creating DB " + db_name)
db = mongo_client[db_name]

for collection in data["collections"]:
    print(f"Populating {collection['collection_name']} with {len(collection['docs'])} records")
    mongo_collection = db[collection["collection_name"]]
    mongo_collection.insert_many(collection["docs"])

print("Creating .env file")
env_content = [
    ("MONGO_HOST", mongo_addr),
    ("MONGO_PORT", mongo_port),
    ("DB_NAME", db_name)
]

with open(".env", "w") as fd:
    for var in env_content:
        line = var[0] + '="' + str(var[1]) + '"\n'
        fd.write(line)

print("Done")
