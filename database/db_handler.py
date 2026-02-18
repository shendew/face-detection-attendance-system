
import pymongo
from pymongo import MongoClient
from config import MONGO_URI, DB_NAME

class DatabaseHandler:
    _instance = None
    _client = None
    _db = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseHandler, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        if self._client is None:
            try:
                self._client = MongoClient(MONGO_URI)
                self._db = self._client[DB_NAME]
                # Send a ping to confirm a successful connection
                self._client.admin.command('ping')
                print("Connected to MongoDB successfully!")
            except Exception as e:
                print(f"Could not connect to MongoDB: {e}")

    def get_collection(self, collection_name):
        return self._db[collection_name]
    
    def insert_document(self, collection_name, data):
        try:
            col = self.get_collection(collection_name)
            result = col.insert_one(data)
            return result.inserted_id
        except Exception as e:
            print(f"Error inserting document: {e}")
            return None

    def find_document(self, collection_name, query):
        col = self.get_collection(collection_name)
        return col.find_one(query)

    def find_all_documents(self, collection_name, query=None):
        col = self.get_collection(collection_name)
        return list(col.find(query if query else {}))

    def update_document(self, collection_name, query, new_values):
        col = self.get_collection(collection_name)
        return col.update_one(query, {"$set": new_values})
    
    def delete_document(self, collection_name, query):
        col = self.get_collection(collection_name)
        result = col.delete_one(query)
        return result.deleted_count > 0

    def delete_many_documents(self, collection_name, query):
        col = self.get_collection(collection_name)
        result = col.delete_many(query)
        return result.deleted_count

    def get_next_id(self, collection_name, id_field, prefix):
        col = self.get_collection(collection_name)
        # Find the last ID that starts with the prefix
        # We use regex to match prefix
        last_doc = col.find_one(
            {id_field: {"$regex": f"^{prefix}"}},
            sort=[(id_field, pymongo.DESCENDING)]
        )
        
        if last_doc and id_field in last_doc:
            last_id = last_doc[id_field]
            try:
                # Extract number part (assuming PREFIX + Digits)
                # e.g. STU001 -> 001
                number_part = last_id.replace(prefix, "")
                next_num = int(number_part) + 1
            except ValueError:
                next_num = 1
        else:
            next_num = 1
            
        return f"{prefix}{next_num:03d}"
