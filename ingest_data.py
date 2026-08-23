import os
import sys
import time
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "backend")))

import spacy
import mysql.connector
import chromadb
from api.embeddings import EmbeddingService

def main():
    try:
        # 1. Initialize services
        nlp = spacy.load("en_core_web_sm")
        embedder = EmbeddingService()

        # 2. Setup ChromaDB
        chroma_client = chromadb.PersistentClient(path="./chroma_db")
        
        # Reset collection if needed
        try:
            chroma_client.delete_collection("shakespeare_speeches")
        except Exception:
            pass  # Collection doesn't exist yet
            
        collection = chroma_client.get_or_create_collection(name="shakespeare_speeches")

        # 3. Connect to MySQL
        db = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "psp"),
            password=os.getenv("DB_PASSWORD", "123456"),
            database=os.getenv("DB_NAME", "scriptly_db")
        )
        cursor = db.cursor(dictionary=True)

        # 4. Fetch speeches with relational metadata
        query = """
            SELECT 
                s.id AS speech_id,
                p.name AS play_name,
                c.name AS character_name,
                sc.act,
                sc.scene,
                s.text AS speech_text
            FROM speeches s
            JOIN plays p ON s.play_id = p.id
            JOIN characters c ON s.character_id = c.id
            JOIN scenes sc ON s.scene_id = sc.id;
        """
        cursor.execute(query)

        batch_size = 256
        total_processed = 0

        while True:
            rows = cursor.fetchmany(batch_size)
            if not rows:
                break
                
            ids = []
            documents = []
            metadatas = []
            
            # Extract texts for batched NLP processing
            texts = [row["speech_text"] for row in rows]
            docs = list(nlp.pipe(texts, batch_size=batch_size))
            
            for row, doc in zip(rows, docs):
                entities = list(set([ent.text for ent in doc.ents if ent.label_ in ["PERSON", "GPE", "ORG"]]))
                
                metadata = {
                    "play_name": str(row["play_name"]),
                    "character_name": str(row["character_name"]),
                    "act": int(row["act"]),
                    "scene": int(row["scene"]),
                    "entities": ", ".join(entities) if entities else "None"
                }
                
                formatted_doc = f"Play: {row['play_name']} | Act: {row['act']} Scene: {row['scene']} | Speaker: {row['character_name']}\nDialogue: {row['speech_text']}"
                
                # Deterministic primary key mapping
                ids.append(f"speech_{row['speech_id']}")
                documents.append(formatted_doc)
                metadatas.append(metadata)

            # Generate embeddings
            embeddings = embedder.embed_texts(documents)

            # Add batch to ChromaDB
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            
            total_processed += len(rows)
            print(f"Ingested {total_processed} speeches into ChromaDB.")

        print("Ingestion complete! Local database created at ./chroma_db/")

    except mysql.connector.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    main()