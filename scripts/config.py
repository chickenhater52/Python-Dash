import os
import math
import colorsys
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gdk, GdkPixbuf

class GameConfig:
    def __init__(self):
        self.graphics_quality = "Auto"
        self.mainColor = 0x04FF00
        self.secondaryColor = 0x00FBFF
        self.currentPlayer = "player_01"
        self.currentShip = "ship_01"
        self.currentBall = "player_ball_01"
        self.currentWave = "dart_01"
        self.currentSpider = "spider_01"
        self.currentBird = "bird_01"
        self.currentlevel = [
            "stereo_madness",
            "Stereo Madness",
            "level_1",
            ["RobTop", "Forever Bound"]
        ]
        self.orbClickScale = 2.0
        self.orbClickShrinkTime = 250
        self.orbParticleSize = 3.5

        self.screenWidth = 1138
        self.screenHeight = 640
        self.a = 60
        self.o = 180
        self.centerX = self.screenWidth / 2 - 150
        self.u = 1.0 / 240.0
        
        self.SpeedPortal = {
            "HALF": 9.30222544655,
            "ONE_TIMES": 11.540004,
            "TWO_TIMES": 14.3488938625,
            "THREE_TIMES": 17.3333393414,
            "FOUR_TIMES": 21.3333407279
        }
        self.playerSpeed = self.SpeedPortal["ONE_TIMES"]
        self.d = 0.9
        self.p = 1.916398
        self.f = 600
        self.g = self.a
        self.T = 460
        
        self.fs = 1000
        self.gs = 1001

    def b(self, y):
        return self.T - y

    def l(self, screenWidth):
        self.screenWidth = screenWidth
        self.centerX = screenWidth / 2 - 150

game_config = GameConfig()

LEVEL_COLORS = [
    (1/255, 0, 245/255), (249/255, 2/255, 248/255), (249/255, 2/255, 133/255),
    (250/255, 1/255, 2/255), (250/255, 135/255, 2/255), (252/255, 252/255, 6/255),
    (3/255, 251/255, 3/255), (2/255, 251/255, 251/255), (0, 125/255, 255/255)
]

LEVELS = [
    {"Name": "Stereo Madness", "Diff": "Easy", "Val": 1},
    {"Name": "Back on Track", "Diff": "Easy", "Val": 1},
    {"Name": "Polargeist", "Diff": "Normal", "Val": 2},
    {"Name": "Dry Out", "Diff": "Normal", "Val": 2},
    {"Name": "Base after Base", "Diff": "Hard", "Val": 3},
    {"Name": "Cant Let Go", "Diff": "Hard", "Val": 3},
    {"Name": "Jumper", "Diff": "Harder", "Val": 4},
    {"Name": "Time Machine", "Diff": "Harder", "Val": 4},
    {"Name": "Cycles", "Diff": "Harder", "Val": 4},
    {"Name": "xStep", "Diff": "Insane", "Val": 5},
    {"Name": "Clutterfunk", "Diff": "Insane", "Val": 5},
    {"Name": "Theory of Everything", "Diff": "Insane", "Val": 5},
    {"Name": "Electroman Adventures", "Diff": "Insane", "Val": 5},
    {"Name": "Clubstep", "Diff": "Demon", "Val": 6},
    {"Name": "Electrodynamix", "Diff": "Insane", "Val": 5},
    {"Name": "Hexagon Force", "Diff": "Insane", "Val": 5},
    {"Name": "Blast Processing", "Diff": "Hard", "Val": 3},
    {"Name": "Theory of Everything 2", "Diff": "Demon", "Val": 6},
    {"Name": "Geometrical Dominator", "Diff": "Hard", "Val": 3},
    {"Name": "Deadlocked", "Diff": "Demon", "Val": 6},
    {"Name": "Fingerdash", "Diff": "Insane", "Val": 5},
    {"Name": "Dash", "Diff": "Insane", "Val": 5}
]

ASSETS = []

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)

def find_asset_path(filename):
    quality = game_config.graphics_quality
    if quality == "Auto":
        quality = "High"

    base_name = os.path.basename(filename)
    name_part, ext = os.path.splitext(base_name)
    
    for suffix in ["-uhd", "-hd", "_uhd", "_hd", "uhd", "hd"]:
        if name_part.endswith(suffix):
            name_part = name_part[:-len(suffix)]
            break
            
    fnt_suffix_bases = {
        "game_bg_01_001",
        "groundSquare_01_001",
        "GJ_button_01",
        "GJ_progressBar_001",
        "square01_001",
        "bigFont",
        "goldFont"
    }
    
    if name_part in fnt_suffix_bases:
        if quality == "High":
            target_name = f"{name_part}-uhd{ext}"
        elif quality == "Medium":
            target_name = f"{name_part}-hd{ext}"
        else:
            target_name = f"{name_part}{ext}"
    else:
        target_name = f"{name_part}{ext}"
        
    if quality == "High":
        q_dir = "uhd"
    elif quality == "Medium":
        q_dir = "hd"
    else:
        q_dir = "low"
        
    subfolders = ["ui", "in-game"]
    
    for sub in subfolders:
        folder = f"{q_dir}/{sub}"
        paths_to_check = [
            os.path.abspath(os.path.join(ROOT_DIR, folder, target_name)),
            os.path.abspath(os.path.join(SCRIPT_DIR, folder, target_name)),
            os.path.abspath(os.path.join(folder, target_name))
        ]
        for p in paths_to_check:
            if os.path.exists(p):
                return p
            
    folder = f"{q_dir}/ui"
    return os.path.abspath(os.path.join(ROOT_DIR, folder, target_name))

def load_uhd_pixbuf(path):
    resolved = find_asset_path(path)
    if not os.path.exists(resolved):
        return None, None
    try:
        pb = GdkPixbuf.Pixbuf.new_from_file(resolved)
        
        quality = game_config.graphics_quality
        if quality == "Auto":
            quality = "High"
            
        if quality == "High":
            scale_fac = 0.5
        elif quality == "Medium":
            scale_fac = 1.0
        elif quality == "Low":
            scale_fac = 2.0
        else:
            scale_fac = 0.5

        scaled = pb.scale_simple(int(pb.get_width() * scale_fac), int(pb.get_height() * scale_fac), GdkPixbuf.InterpType.BILINEAR)
        return scaled, Gdk.cairo_surface_create_from_pixbuf(scaled, 1, None)
    except Exception:
        return None, None

def pixbuf_to_surface(pixbuf):
    if pixbuf is None:
        return None
    return Gdk.cairo_surface_create_from_pixbuf(pixbuf, 1, None)

def hsv_to_rgb(h, s, v):
    return colorsys.hsv_to_rgb(h, s, v)

def bounce_out(t):
    if t < 1.0 / 2.75:
        return 7.5625 * t * t
    elif t < 2.0 / 2.75:
        t -= 1.5 / 2.75
        return 7.5625 * t * t + 0.75
    elif t < 2.5 / 2.75:
        t -= 2.25 / 2.75
        return 7.5625 * t * t + 0.9375
    else:
        t -= 2.625 / 2.75
        return 7.5625 * t * t + 0.984375

def elastic_out(t, amplitude=1.0, period=0.3):
    if t == 0:
        return 0.0
    if t == 1:
        return 1.0
    if period == 0:
        period = 0.3
    if amplitude < 1.0:
        amplitude = 1.0
        s = period / 4.0
    else:
        s = period / (2.0 * math.pi) * math.asin(1.0 / amplitude)
    return amplitude * math.pow(2, -10 * t) * math.sin((t - s) * (2.0 * math.pi) / period) + 1.0