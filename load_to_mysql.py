import pandas as pd
import re
from sqlalchemy import create_engine, text

# --- DATABASE CONFIGURATION ---
DB_USER = "psp"
DB_PASS = "123456"  # Replace with your password
DB_HOST = "localhost"
DB_NAME = "scriptly_db"

engine = create_engine(
    f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"
)

# --- CSV PARSING & DATA EXTRACTION (YOUR EXISTING LOGIC) ---
CSV_FILE = "Shakespeare_data.csv"
df = pd.read_csv(CSV_FILE)

plays, characters, scenes, speeches = [], [], [], []
play_map, character_map, scene_map = {}, {}, {}
play_counter, character_counter, scene_counter, speech_counter = 1, 1, 1, 1


def parse_act_scene_line(value):
    if pd.isna(value):
        return None, None, None
    value = str(value).strip()
    if re.match(r"^\d+\.\d+\.\d+$", value):
        act, scene, line = value.split(".")
        return int(act), int(scene), int(line)
    return None, None, None


current_speech = None

for _, row in df.iterrows():
    play_name = str(row["Play"]).strip()

    if play_name not in play_map:
        play_id = play_counter
        play_counter += 1
        play_map[play_name] = play_id
        plays.append({"id": play_id, "name": play_name})

    play_id = play_map[play_name]
    player = "" if pd.isna(row["Player"]) else str(row["Player"]).strip()
    text_line = str(row["PlayerLine"]).strip()
    act, scene, line = parse_act_scene_line(row["ActSceneLine"])

    if not player:
        current_speech = None
        if act is not None and scene is not None:
            scene_key = (play_id, act, scene)
            if scene_key not in scene_map:
                scene_id = scene_counter
                scene_counter += 1
                scene_map[scene_key] = scene_id
                scenes.append(
                    {
                        "id": scene_id,
                        "play_id": play_id,
                        "act": act,
                        "scene": scene,
                    }
                )
        continue

    character_key = (play_id, player)
    if character_key not in character_map:
        character_id = character_counter
        character_counter += 1
        character_map[character_key] = character_id
        characters.append(
            {"id": character_id, "play_id": play_id, "name": player}
        )

    character_id = character_map[character_key]
    if act is None:
        continue

    scene_key = (play_id, act, scene)
    if scene_key not in scene_map:
        scene_id = scene_counter
        scene_counter += 1
        scene_map[scene_key] = scene_id
        scenes.append(
            {"id": scene_id, "play_id": play_id, "act": act, "scene": scene}
        )

    scene_id = scene_map[scene_key]

    start_new_speech = False
    if current_speech is None:
        start_new_speech = True
    elif current_speech["character_id"] != character_id:
        start_new_speech = True
    elif current_speech["scene_id"] != scene_id:
        start_new_speech = True

    if start_new_speech:
        current_speech = {
            "id": speech_counter,
            "play_id": play_id,
            "character_id": character_id,
            "scene_id": scene_id,
            "act": act,
            "scene": scene,
            "start_line": line,
            "end_line": line,
            "text_lines": [text_line],
        }
        speeches.append(current_speech)
        speech_counter += 1
    else:
        current_speech["end_line"] = line
        current_speech["text_lines"].append(text_line)

final_speeches = []
for speech in speeches:
    final_speeches.append(
        {
            "id": speech["id"],
            "play_id": speech["play_id"],
            "character_id": speech["character_id"],
            "scene_id": speech["scene_id"],
            "act": speech["act"],
            "scene": speech["scene"],
            "start_line": speech["start_line"],
            "end_line": speech["end_line"],
            "text": "\n".join(speech["text_lines"]),
        }
    )

# --- INSERTING INTO MYSQL ---
print("Pushing data to MySQL tables...")

df_plays = pd.DataFrame(plays)
df_characters = pd.DataFrame(characters)
df_scenes = pd.DataFrame(scenes)
df_speeches = pd.DataFrame(final_speeches)

with engine.connect() as conn:
    # 1. Disable foreign key checks for THIS session
    conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
    
    # 2. Explicitly drop all tables to clear out old foreign key constraints
    conn.execute(text("DROP TABLE IF EXISTS speeches;"))
    conn.execute(text("DROP TABLE IF EXISTS scenes;"))
    conn.execute(text("DROP TABLE IF EXISTS characters;"))
    conn.execute(text("DROP TABLE IF EXISTS plays;"))
    
    # 3. Pass the SAME connection 'conn' to pandas
    df_plays.to_sql("plays", conn, if_exists="replace", index=False)
    df_characters.to_sql("characters", conn, if_exists="replace", index=False)
    df_scenes.to_sql("scenes", conn, if_exists="replace", index=False)
    df_speeches.to_sql("speeches", conn, if_exists="replace", index=False)

    print("Data insertion complete. Setting constraints and indexes...")

    # 4. Apply schemas within the same session
    sql_statements = [
        # Explicitly set IDs to NOT NULL before assigning Primary Keys
        "ALTER TABLE plays MODIFY id BIGINT NOT NULL;",
        "ALTER TABLE characters MODIFY id BIGINT NOT NULL;",
        "ALTER TABLE scenes MODIFY id BIGINT NOT NULL;",
        "ALTER TABLE speeches MODIFY id BIGINT NOT NULL;",
        
        # Primary Keys
        "ALTER TABLE plays ADD PRIMARY KEY (id);",
        "ALTER TABLE characters ADD PRIMARY KEY (id);",
        "ALTER TABLE scenes ADD PRIMARY KEY (id);",
        "ALTER TABLE speeches ADD PRIMARY KEY (id);",
        
        # Convert 'name' from TEXT to VARCHAR so it can be indexed
        "ALTER TABLE characters MODIFY COLUMN name VARCHAR(255);",
        
        # Foreign Keys
        "ALTER TABLE characters ADD CONSTRAINT fk_char_play FOREIGN KEY (play_id) REFERENCES plays(id);",
        "ALTER TABLE scenes ADD CONSTRAINT fk_scene_play FOREIGN KEY (play_id) REFERENCES plays(id);",
        "ALTER TABLE speeches ADD CONSTRAINT fk_speech_play FOREIGN KEY (play_id) REFERENCES plays(id);",
        "ALTER TABLE speeches ADD CONSTRAINT fk_speech_char FOREIGN KEY (character_id) REFERENCES characters(id);",
        "ALTER TABLE speeches ADD CONSTRAINT fk_speech_scene FOREIGN KEY (scene_id) REFERENCES scenes(id);",
        
        # Indexes for Fast Queries
        "CREATE INDEX idx_character_name ON characters(name);",
        "CREATE INDEX idx_play_scene ON scenes(play_id, act, scene);",
        "CREATE INDEX idx_speech_lookup ON speeches(play_id, character_id);"
    ]

    for stmt in sql_statements:
        try:
            conn.execute(text(stmt))
        except Exception as e:
            print(f"Skipped statement: {e}")

    # 5. Re-enable foreign key checks and commit the transaction
    conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
    conn.commit()

print("Database schema successfully configured with indexing!")