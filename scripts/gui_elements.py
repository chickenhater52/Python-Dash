import time
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib
from config import bounce_out

class VirtualElement:
    def __init__(self, name, base_scale=1.0):
        self.name, self.scale, self.current_scale, self.pressed = name, base_scale, base_scale, False
        self.anim_start_time, self.anim_duration, self.anim_start_val, self.anim_end_val, self.anim_timeout_id = None, 0.0, base_scale, base_scale, None

    def start_tween(self, target_scale, duration_ms, draw_cb):
        self.stop_tween()
        self.anim_start_val, self.anim_end_val, self.anim_duration, self.anim_start_time = self.current_scale, target_scale, duration_ms / 1000.0, time.time()
        self.anim_timeout_id = GLib.timeout_add(16, self.tick_tween, draw_cb)

    def stop_tween(self):
        if self.anim_timeout_id is not None: GLib.source_remove(self.anim_timeout_id); self.anim_timeout_id = None

    def tick_tween(self, draw_cb):
        if self.anim_start_time is None: return False
        t = (time.time() - self.anim_start_time) / self.anim_duration
        if t >= 1.0:
            self.current_scale = self.anim_end_val
            draw_cb(); self.anim_timeout_id = None
            return False
        self.current_scale = self.anim_start_val + (self.anim_end_val - self.anim_start_val) * bounce_out(t)
        draw_cb()
        return True

class ScreenElement(VirtualElement):
    def __init__(self, name, filename, default_x, default_y, default_scale=1.0):
        super().__init__(name, default_scale)
        self.filename, self.x, self.y, self.pixbuf, self.surface, self.missing = filename, default_x, default_y, None, None, False
        self.half_w, self.half_h = 45.0, 45.0