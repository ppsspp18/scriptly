import pandas as pd
import json
import re

CSV_FILE = "Shakespeare_data.csv"

df = pd.read_csv(CSV_FILE)

plays = []
characters = []
scenes = []
speeches = []

play_map = {}
character_map = {}
scene_map = {}

play_counter = 1
character_counter = 1
scene_counter = 1
speech_counter = 1

def parse_act_scene_line(value):
    """
    Converts:
    1.1.33 -> (1, 1, 33)
    """
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
    
    # Create Play
    if play_name not in play_map:
        play_id = play_counter
        play_counter += 1
        
        play_map[play_name] = play_id
        
        plays.append({
            "_id": play_id,
            "name": play_name
        })
    
    play_id = play_map[play_name]
    
    # Character Name
    player = ""
    
    if not pd.isna(row["Player"]):
        player = str(row["Player"]).strip()
    
    # Dialogue Text
    text = str(row["PlayerLine"]).strip()
    
    # Parse Act.Scene.Line
    act, scene, line = parse_act_scene_line(
        row["ActSceneLine"]
    )
    
    # Stage Directions
    if not player:
        current_speech = None
        
        if act is not None and scene is not None:
            scene_key = (play_id, act, scene)
            
            if scene_key not in scene_map:
                scene_id = scene_counter
                scene_counter += 1
                
                scene_map[scene_key] = scene_id
                
                scenes.append({
                    "_id": scene_id,
                    "play_id": play_id,
                    "act": act,
                    "scene": scene
                })
        
        continue
    
    # Create Character
    character_key = (play_id, player)
    
    if character_key not in character_map:
        character_id = character_counter
        character_counter += 1
        
        character_map[character_key] = character_id
        
        characters.append({
            "_id": character_id,
            "play_id": play_id,
            "name": player
        })
    
    character_id = character_map[character_key]
    
    # Skip rows without Act.Scene.Line
    if act is None:
        continue
    
    # Create Scene
    scene_key = (play_id, act, scene)
    
    if scene_key not in scene_map:
        scene_id = scene_counter
        scene_counter += 1
        
        scene_map[scene_key] = scene_id
        
        scenes.append({
            "_id": scene_id,
            "play_id": play_id,
            "act": act,
            "scene": scene
        })
    
    scene_id = scene_map[scene_key]
    
    # Determine if a new speech should start
    start_new_speech = False
    
    if current_speech is None:
        start_new_speech = True
    elif current_speech["character_id"] != character_id:
        start_new_speech = True
    elif current_speech["scene_id"] != scene_id:
        start_new_speech = True
    
    # Create New Speech
    if start_new_speech:
        current_speech = {
            "_id": speech_counter,
            "play_id": play_id,
            "character_id": character_id,
            "scene_id": scene_id,
            "act": act,
            "scene": scene,
            "start_line": line,
            "end_line": line,
            "text_lines": [text]
        }
        
        speeches.append(current_speech)
        
        speech_counter += 1
    # Extend Existing Speech
    else:
        current_speech["end_line"] = line
        current_speech["text_lines"].append(text)

# Convert speech blocks into final structure
final_speeches = []

for speech in speeches:
    final_speeches.append({
        "_id": speech["_id"],
        "play_id": speech["play_id"],
        "character_id": speech["character_id"],
        "scene_id": speech["scene_id"],
        "act": speech["act"],
        "scene": speech["scene"],
        "start_line": speech["start_line"],
        "end_line": speech["end_line"],
        "text": "\n".join(speech["text_lines"])
    })

# Save JSON Files
with open("plays.json", "w", encoding="utf-8") as f:
    json.dump(
        plays,
        f,
        indent=2,
        ensure_ascii=False
    )

with open("characters.json", "w", encoding="utf-8") as f:
    json.dump(
        characters,
        f,
        indent=2,
        ensure_ascii=False
    )

with open("scenes.json", "w", encoding="utf-8") as f:
    json.dump(
        scenes,
        f,
        indent=2,
        ensure_ascii=False
    )

with open("speeches.json", "w", encoding="utf-8") as f:
    json.dump(
        final_speeches,
        f,
        indent=2,
        ensure_ascii=False
    )

print(f"Plays      : {len(plays)}")
print(f"Characters : {len(characters)}")
print(f"Scenes     : {len(scenes)}")
print(f"Speeches   : {len(final_speeches)}")