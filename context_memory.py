# context_memory.py
import chromadb

class ContextMemory:
    def __init__(self):
        self.client = chromadb.Client()
        self.collection = self.client.create_collection("context")
        
    def remember(self, key, value):
        self.collection.add(ids=[key], documents=[value])
        
    def recall(self, key):
        return self.collection.get(ids=[key])["documents"][0]