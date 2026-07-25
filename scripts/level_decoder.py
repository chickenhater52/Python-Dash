# --- level_decoder.py ---
import os
import base64
import zlib
import gzip

LEVELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "levels")

def ensure_levels_directory():
    if not os.path.exists(LEVELS_DIR):
        os.makedirs(LEVELS_DIR)
    
    # Write a default mock level for 'level_1.txt' if missing
    default_path = os.path.join(LEVELS_DIR, "level_1.txt")
    if not os.path.exists(default_path):
        with open(default_path, "w", encoding="utf-8") as f:
            f.write("kS38,1_255_2_255_3_255_6_1000|1_255_2_255_3_255_6_1001;1,1,2,50,3,30;1,1,2,300,3,30;1,8,2,600,3,30;1,35,2,900,3,30")

def list_local_levels():
    ensure_levels_directory()
    return sorted([f for f in os.listdir(LEVELS_DIR) if f.endswith(".txt")])

def safe_float(val, default=0.0):
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

def safe_int(val, default=0):
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default

def decode_payload(payload):
    cleaned = payload.strip().replace('-', '+').replace('_', '/')
    while len(cleaned) % 4 != 0:
        cleaned += '='
    
    # Try raw payload, or prepend standard official gzip headers if missing
    for string_to_try in (cleaned, 'H4sIAAAAAAAAA' + cleaned):
        try:
            raw_bytes = base64.b64decode(string_to_try)
            try:
                # Try GZIP decompression
                decompressed = gzip.decompress(raw_bytes)
                return decompressed.decode('utf-8', errors='ignore')
            except Exception:
                pass
            try:
                # Try Zlib automatic header detection (zlib/gzip)
                decompressed = zlib.decompress(raw_bytes, 15 + 32)
                return decompressed.decode('utf-8', errors='ignore')
            except Exception:
                pass
            try:
                # Try raw Deflate fallback
                decompressed = zlib.decompress(raw_bytes, -15)
                return decompressed.decode('utf-8', errors='ignore')
            except Exception:
                pass
        except Exception:
            continue
            
    return payload

def parse_settings(settings_str):
    parts = settings_str.split(',')
    settings_map = {}
    for i in range(0, len(parts) - 1, 2):
        settings_map[parts[i]] = parts[i+1]
    return settings_map

def parse_level(filename):
    ensure_levels_directory()
    filepath = os.path.join(LEVELS_DIR, filename)
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        if not content.strip():
            return None
        
        decompressed = decode_payload(content)
        parts = decompressed.split(';')
        
        # Parse settings block into a clean key-value dictionary
        settings = parse_settings(parts[0]) if len(parts) > 0 else {}
        
        objects = []
        for obj_str in parts[1:]:
            if not obj_str.strip():
                continue
            obj = parse_object(obj_str)
            if obj:
                objects.append(obj)
        return {"settings": settings, "objects": objects}
    except Exception as e:
        print(f"[Decoder] Error parsing level {filename}: {e}")
        return None

def parse_object(obj_str):
    parts = obj_str.split(',')
    obj_data = {}
    for i in range(0, len(parts) - 1, 2):
        obj_data[parts[i]] = parts[i+1]
    
    obj_id = safe_int(obj_data.get('1', '0'))
    if obj_id == 0:
        return None
    return {
        "id": obj_id,
        "x": safe_float(obj_data.get('2', '0')) * 2.0, # Align coordinate space mapping
        "y": safe_float(obj_data.get('3', '0')) * 2.0,
        "flipX": obj_data.get('4') == '1',
        "flipY": obj_data.get('5') == '1',
        "rot": safe_float(obj_data.get('6', '0')),
        "scale": safe_float(obj_data.get('32', '1.0'), 1.0),
        "gameMode": safe_int(obj_data.get('kA2', '0')),
        "miniMode": safe_int(obj_data.get('kA3', '0')),
        "speed": safe_int(obj_data.get('kA4', '0')),
        "flipGravity": obj_data.get('kA11') == '1'
    }