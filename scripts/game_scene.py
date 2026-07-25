import os
import sys

LOCAL_DIR = os.path.dirname(os.path.abspath(__file__))
if LOCAL_DIR not in sys.path:
    sys.path.insert(0, LOCAL_DIR)

import time
import math
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gdk, GdkPixbuf
import cairo
import level_decoder
import physics
from config import LEVEL_COLORS, find_asset_path, pixbuf_to_surface

OBJECT_DEFAULT_MAP = {
    "1": {"type": "solid", "frame": "square_01_001.png"},
    "2": {"type": "solid", "frame": "square_02_001.png"},
    "3": {"type": "solid", "frame": "square_03_001.png"},
    "4": {"type": "solid", "frame": "square_04_001.png"},
    "5": {"type": "solid", "frame": "square_05_001.png"},
    "6": {"type": "solid", "frame": "square_06_001.png"},
    "7": {"type": "solid", "frame": "square_07_001.png"},
    "8": {"type": "hazard", "frame": "spike_01_001.png"},
    "9": {"type": "hazard", "frame": "spike_02_001.png"},
    "10": {"type": "hazard", "frame": "spike_03_001.png"},
    "11": {"type": "hazard", "frame": "subSpike_01_001.png"},
    "35": {"type": "pad", "frame": "pad_01_001.png"},
    "36": {"type": "pad", "frame": "pad_02_001.png"},
    "67": {"type": "pad", "frame": "pad_03_001.png"},
    "140": {"type": "pad", "frame": "pad_04_001.png"},
    "39": {"type": "ring", "frame": "ring_01_001.png"},
    "84": {"type": "ring", "frame": "ring_02_001.png"},
    "1022": {"type": "ring", "frame": "ring_03_001.png"},
    "12": {"type": "portal", "frame": "portal_01_front_001.png"},
    "13": {"type": "portal", "frame": "portal_02_front_001.png"},
    "47": {"type": "portal", "frame": "portal_03_front_001.png"},
    "111": {"type": "portal", "frame": "portal_04_front_001.png"},
    "660": {"type": "portal", "frame": "portal_05_front_001.png"},
    "45": {"type": "portal", "frame": "portal_08_front_001.png"},
    "46": {"type": "portal", "frame": "portal_09_front_001.png"},
    "99": {"type": "portal", "frame": "portal_10_front_001.png"},
    "101": {"type": "portal", "frame": "portal_11_front_001.png"},
}

class GameScene:
    def __init__(self, parent_window, level_filename):
        try:
            self.win = parent_window
            self.level_filename = level_filename
            self.level_data = level_decoder.parse_level(level_filename)
            self.state = physics.PlayerState()
            self.camera_x = 0.0
            self.camera_y = 0.0
            self.speed = 11.540004
            self.attempts = 1
            self.is_active = True
            self.death_timer = 0.0

            settings = self.level_data.get("settings") if self.level_data else None
            if isinstance(settings, dict):
                self.state.game_mode = level_decoder.safe_int(settings.get("kA2", "0"))
                self.state.is_mini = (settings.get("kA3") == "1")
                self.state.gravity_flipped = (settings.get("kA11") == "1")
                
                speed_key = level_decoder.safe_int(settings.get("kA4", "0"))
                if speed_key == 0:
                    self.speed = 11.540004
                elif speed_key == 1:
                    self.speed = 9.30222544655
                elif speed_key == 2:
                    self.speed = 14.3488938625
                elif speed_key == 3:
                    self.speed = 17.3333393414
                elif speed_key == 4:
                    self.speed = 21.3333407279
            else:
                self.state.game_mode = 0
                self.state.is_mini = False
                self.state.gravity_flipped = False
                self.speed = 11.540004

            if self.level_data and "objects" in self.level_data:
                physics.precompute_objects(self.level_data["objects"])

            self.assets = {}

        except Exception:
            self.is_active = False
            parent_window.active_game_scene = None
            parent_window.level_select_active = True

    def _load_scene_asset(self, filename):
        if filename in self.assets:
            return self.assets[filename]
        resolved = find_asset_path(filename)
        if os.path.exists(resolved):
            try:
                pb = GdkPixbuf.Pixbuf.new_from_file(resolved)
                
                pb_w = pb.get_width()
                if pb_w > 90:
                    scale_fac = 0.5
                elif pb_w > 45:
                    scale_fac = 1.0
                else:
                    scale_fac = 2.0
                    
                w = int(pb.get_width() * scale_fac)
                h = int(pb.get_height() * scale_fac)
                w = max(1, w)
                h = max(1, h)
                
                scaled = pb.scale_simple(w, h, GdkPixbuf.InterpType.BILINEAR)
                asset_data = (scaled, pixbuf_to_surface(scaled), w, h)
                self.assets[filename] = asset_data
                return asset_data
            except Exception:
                pass
        return None

    def handle_button_press(self):
        if self.is_active:
            self.state.up_key_down = True
            self.state.up_key_pressed = True

    def handle_button_release(self):
        if self.is_active:
            self.state.up_key_down = False
            self.state.up_key_pressed = False

    def handle_key_press(self, keyval):
        if not self.is_active:
            return
        keyname = Gdk.keyval_name(keyval)
        if keyname in ("space", "Up", "w", "W"):
            self.state.up_key_down = True
            self.state.up_key_pressed = True

    def handle_key_release(self, keyval):
        if not self.is_active:
            return
        keyname = Gdk.keyval_name(keyval)
        if keyname in ("space", "Up", "w", "W"):
            self.state.up_key_down = False
            self.state.up_key_pressed = False

    def update_ship_rotation(self, quantized_delta):
        if quantized_delta <= 0:
            return
        dy = -(self.state.y - self.state.last_y_frame)
        dx = quantized_delta * 10.3860036
        if dx * dx + dy * dy >= quantized_delta * 0.6:
            target_angle = math.atan2(dy, dx)
            t = 0.15 * quantized_delta
            self.state.rotation = physics.slerp_2d(self.state.rotation, target_angle, t)

    def update_camera_y(self, ticks_delta):
        if ticks_delta <= 0:
            return
        o = 180.0
        target_y = self.state.y
        high_margin = 140.0
        low_margin = 80.0
        
        current_cam_y = self.camera_y
        target_cam_y = current_cam_y
        camera_center_y = current_cam_y - o + 320.0
        
        if self.state.gravity_flipped:
            if target_y > camera_center_y + low_margin:
                target_cam_y = target_y - 320.0 - low_margin + o
            elif target_y < camera_center_y - high_margin:
                target_cam_y = target_y - 320.0 + high_margin + o
        else:
            if target_y > camera_center_y + high_margin:
                target_cam_y = target_y - 320.0 - high_margin + o
            elif target_y < camera_center_y - low_margin:
                target_cam_y = target_y - 320.0 + low_margin + o
                
        if target_cam_y < 0:
            target_cam_y = 0.0
            
        self.camera_y += (target_cam_y - self.camera_y) / (10.0 / ticks_delta)
        if self.camera_y < 0:
            self.camera_y = 0.0

    def update(self, dt_ms):
        if not self.is_active:
            return
        try:
            if self.state.is_dead:
                self.death_timer += dt_ms / 1000.0
                if self.death_timer >= 0.5:
                    self.death_timer = 0.0
                    self.attempts += 1
                    self.state.reset()
                    self.camera_y = 0.0
                    settings = self.level_data.get("settings") if self.level_data else None
                    if isinstance(settings, dict):
                        self.state.game_mode = level_decoder.safe_int(settings.get("kA2", "0"))
                        self.state.is_mini = (settings.get("kA3") == "1")
                        self.state.gravity_flipped = (settings.get("kA11") == "1")
                    self.camera_x = 0.0
                return

            self.state.last_y_frame = self.state.y

            ticks, quantized_delta = physics.quantize_delta(dt_ms)
            solids = self.level_data["objects"] if self.level_data else []

            vertical_delta = 0.225
            horizontal_delta = 0.225 * self.speed

            for _ in range(ticks):
                prev_x = self.state.x
                prev_y = self.state.y
                prev_last_y = self.state.last_y

                self.state.last_y = self.state.y
                physics.apply_mode_physics(self.state, vertical_delta, self.speed, solids=solids)
                self.state.y += self.state.y_velocity * vertical_delta
                physics.resolve_collisions(self.state, solids)
                if self.state.is_dead:
                    self.state.x = prev_x
                    self.state.y = prev_y
                    self.state.last_y = prev_last_y
                    break
                self.state.x += horizontal_delta

            if self.state.game_mode == 1 and not self.state.is_dead:
                self.update_ship_rotation(quantized_delta)

            if not self.state.is_dead:
                self.update_camera_y(quantized_delta)

            self.camera_x = self.state.x - 320.0
            if self.camera_x < 0:
                self.camera_x = 0.0
        except Exception:
            self.is_active = False
            self.win.active_game_scene = None
            self.win.level_select_active = True

    def draw_hitboxes(self, cr, ground_y):
        cr.save()
        cr.translate(-self.camera_x, self.camera_y)
        
        player_size = 18.0 if self.state.is_mini else 30.0
        hitbox_size = player_size * 2.0
        
        player_screen_x = self.state.x
        player_screen_y = ground_y - self.state.y
        
        cr.set_source_rgba(1.0, 0.0, 0.0, 0.8)
        cr.set_line_width(2.0)
        cr.rectangle(player_screen_x - player_size, player_screen_y - player_size, hitbox_size, hitbox_size)
        cr.stroke()
        
        cr.set_source_rgba(0.7, 0.0, 0.0, 0.8)
        cr.arc(player_screen_x, player_screen_y, player_size, 0, 2.0 * math.pi)
        cr.stroke()
        
        cr.save()
        cr.translate(player_screen_x, player_screen_y)
        cr.rotate(self.state.rotation)
        cr.rectangle(-player_size, -player_size, hitbox_size, hitbox_size)
        cr.stroke()
        cr.restore()
        
        cr.set_source_rgba(0.0, 0.0, 1.0, 1.0)
        cr.rectangle(player_screen_x - 9.0, player_screen_y - 9.0, 18.0, 18.0)
        cr.stroke()
        
        if self.level_data and "objects" in self.level_data:
            for obj in self.level_data["objects"]:
                obj_def = obj.get('obj_def')
                if not obj_def:
                    continue
                    
                obj_type = obj_def.get("type")
                if obj_type not in ("solid", "hazard", "pad", "slope"):
                    continue

                if obj['x'] - self.camera_x < -100 or obj['x'] - self.camera_x > 1380:
                    continue
                
                if obj_type == "hazard":
                    r_c, g_c, b_c = 1.0, 0.1, 0.1
                elif obj_type == "pad":
                    r_c, g_c, b_c = 1.0, 0.5, 0.0
                else:
                    r_c, g_c, b_c = 0.1, 1.0, 0.1
                
                w = obj['w']
                h = obj['h']
                
                cr.save()
                cr.translate(obj['x'], ground_y - obj['y'])
                cr.rotate(math.radians(obj['rot']))
                cr.set_source_rgba(r_c, g_c, b_c, 0.7)
                cr.rectangle(-w / 2.0, -h / 2.0, w, h)
                cr.stroke()
                cr.restore()
                
        cr.restore()

    def draw(self, cr, width, height):
        if not self.is_active:
            return
        try:
            col = LEVEL_COLORS[self.win.current_level_index % len(LEVEL_COLORS)]
            
            cr.set_source_rgb(col[0] * 0.6, col[1] * 0.6, col[2] * 0.6)
            cr.paint()

            ground_y = 517.5
            cr.rectangle(0, ground_y + self.camera_y, 1280, 720 - ground_y - self.camera_y)
            cr.set_source_rgb(col[0] * 0.35, col[1] * 0.35, col[2] * 0.35)
            cr.fill()

            if self.win.floor_line_surface:
                cr.save()
                cr.translate(640.0, ground_y + self.camera_y)
                scale_x = 1280.0 / self.win.floor_line_w_orig
                cr.scale(scale_x, 1.0)
                cr.set_source_surface(self.win.floor_line_surface, -self.win.floor_line_w_orig / 2.0, -self.win.floor_line_h_orig / 2.0)
                cr.set_operator(cairo.Operator.ADD)
                cr.paint()
                cr.restore()

            cr.save()
            cr.translate(-self.camera_x, self.camera_y)

            if self.level_data and "objects" in self.level_data:
                for obj in self.level_data["objects"]:
                    obj_id_str = str(obj.get('id', '1'))
                    obj_def = obj.get('obj_def')
                    
                    obj_type = None
                    frame_name = None

                    if obj_def:
                        obj_type = obj_def.get("type")
                        frame_name = obj_def.get("frame")

                    if not obj_type or not frame_name:
                        default_info = OBJECT_DEFAULT_MAP.get(obj_id_str, {})
                        if not obj_type:
                            obj_type = default_info.get("type", "solid")
                        if not frame_name:
                            frame_name = default_info.get("frame", "square_01_001.png")

                    if obj['x'] - self.camera_x < -100 or obj['x'] - self.camera_x > 1380:
                        continue

                    cr.save()
                    cr.translate(obj['x'], ground_y - obj['y'])
                    cr.rotate(math.radians(obj.get('rot', 0.0)))

                    obj_scale = obj.get('scale', 1.0)
                    cr.scale(obj_scale, obj_scale)

                    asset = self._load_scene_asset(frame_name) if frame_name else None

                    if asset and asset[1]:
                        cr.set_source_surface(asset[1], -asset[2] / 2.0, -asset[3] / 2.0)
                        cr.paint()
                    else:
                        if obj_type == "hazard":
                            cr.move_to(-25, 25)
                            cr.line_to(0, -25)
                            cr.line_to(25, 25)
                            cr.close_path()
                            cr.set_source_rgb(1.0, 0.1, 0.1)
                            cr.fill_preserve()
                            cr.set_source_rgb(0, 0, 0)
                            cr.set_line_width(3)
                            cr.stroke()
                        elif obj_type == "pad":
                            cr.rectangle(-20, 15, 40, 10)
                            cr.set_source_rgb(1.0, 0.8, 0.0)
                            cr.fill_preserve()
                            cr.set_source_rgb(0, 0, 0)
                            cr.stroke()
                        else:
                            cr.rectangle(-30, -30, 60, 60)
                            cr.set_source_rgb(0.2, 0.2, 0.2)
                            cr.fill_preserve()
                            cr.set_source_rgb(1.0, 1.0, 1.0)
                            cr.set_line_width(2.5)
                            cr.stroke()
                    cr.restore()

            physics.draw_temporary_cube(cr, self.state.x, ground_y - self.state.y, self.state.rotation, self.state.is_mini)

            text = f"Attempt {self.attempts}"
            text_x = 640.0 if self.attempts == 1 else 740.0
            
            if self.win.big_font and self.win.big_font.surface:
                self.win.big_font.draw_text(cr, text, text_x, 150, 65, align="center")
            else:
                cr.save()
                cr.select_font_face("Sans", cairo.FontSlant.NORMAL, cairo.FontWeight.BOLD)
                cr.set_font_size(65)
                cr.set_source_rgb(1, 1, 1)
                ext = cr.text_extents(text)
                cr.move_to(text_x - ext.width / 2, 150)
                cr.show_text(text)
                cr.restore()

            cr.restore()
            
            show_hitboxes = getattr(self.win, "showHitboxes", True)
            if show_hitboxes:
                self.draw_hitboxes(cr, ground_y)
            
        except Exception:
            self.is_active = False
            self.win.active_game_scene = None
            self.win.level_select_active = True