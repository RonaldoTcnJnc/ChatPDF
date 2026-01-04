
import chromadb
import os
import sys

def inspect_db(name, path, f):
    f.write(f"\n--- Inspecting {name} ({path}) ---\n")
    if not os.path.exists(path):
        f.write("❌ Path does not exist.\n")
        return

    try:
        client = chromadb.PersistentClient(path=path)
        collections = client.list_collections()
        
        if not collections:
            f.write("⚠️  No collections found.\n")
            return

        f.write(f"Found {len(collections)} collections:\n")
        for col in collections:
            count = col.count()
            f.write(f"  - Collection: {col.name}\n")
            f.write(f"    - Items: {count}\n")
            try:
                if count > 0:
                    peek = col.get(limit=1, include=["metadatas"])
                    if peek and peek["metadatas"] and len(peek["metadatas"]) > 0:
                        meta = peek["metadatas"][0]
                        source = meta.get("source", "Unknown")
                        f.write(f"    - Source: {source}\n")
            except Exception as e:
                f.write(f"    - Error reading metadata: {e}\n")
            f.write("\n")

    except Exception as e:
        f.write(f"❌ Error inspecting DB: {e}\n")

if __name__ == "__main__":
    with open("db_inspection.txt", "w", encoding="utf-8") as f:
        # Root DB
        inspect_db("ROOT ChromaDB", "../chroma_db", f)
        
        # Backend DB
        inspect_db("BACKEND ChromaDB", "./chroma_db", f)
