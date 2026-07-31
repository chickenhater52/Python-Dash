import os
import cairo
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GdkPixbuf
from config import pixbuf_to_surface, find_asset_path

class BMFont:
    def __init__(self, fnt_path, png_path):
        self.chars = {}
        self.line_height = 32
        self.base = 26
        self.surface = None
        self.xrender_font_surface = None
        self._text_cache = {}

        resolved_fnt = find_asset_path(fnt_path)
        resolved_png = find_asset_path(png_path)
        if not (os.path.exists(resolved_fnt) and os.path.exists(resolved_png)):
            return
            
        try:
            self.surface = pixbuf_to_surface(GdkPixbuf.Pixbuf.new_from_file(resolved_png))
        except Exception:
            return
            
        try:
            with open(resolved_fnt, 'r', encoding='utf-8') as f:
                for line in f:
                    p = line.strip().split()
                    if not p or p[0] not in ("common", "char"):
                        continue
                    d = {k: v.replace('"', '') for x in p[1:] if '=' in x for k, v in [x.split('=', 1)]}
                    if p[0] == "common":
                        self.line_height = int(d.get("lineHeight", 32))
                        self.base = int(d.get("base", 26))
                    elif p[0] == "char":
                        self.chars[int(d.get("id", 0))] = {
                            k: int(d.get(k, 0)) for k in ["x", "y", "width", "height", "xoffset", "yoffset", "xadvance"]
                        }
        except Exception:
            pass

    def ensure_xrender(self, cr):
        if self.surface and self.xrender_font_surface is None:
            try:
                sw = self.surface.get_width()
                sh = self.surface.get_height()
                target = cr.get_target()
                similar = target.create_similar(cairo.CONTENT_COLOR_ALPHA, sw, sh)
                xcr = cairo.Context(similar)
                xcr.set_source_surface(self.surface, 0, 0)
                xcr.paint()
                self.xrender_font_surface = similar
            except Exception:
                self.xrender_font_surface = self.surface

    def get_text_width(self, text, scale):
        w = 0
        for c in text:
            cid = ord(c)
            char_data = self.chars.get(cid)
            if char_data is None:
                char_data = self.chars.get(ord(c.lower() if c.isupper() else c.upper()), {"xadvance": 15})
            w += char_data["xadvance"]
        return w * scale

    def draw_text(self, cr, text, x, y, size_px, align="center"):
        if not self.surface:
            return
        self.ensure_xrender(cr)
        
        size_px_int = int(round(size_px))
        cache_key = (text, size_px_int, align)
        cached = self._text_cache.get(cache_key)
        
        if cached is None:
            try:
                scale = size_px / self.line_height
                tw = self.get_text_width(text, scale)
                th = self.line_height * scale
                pad = 10
                surf_w = max(1, int(round(tw + pad * 2)))
                surf_h = max(1, int(round(th + pad * 2)))
                
                target = cr.get_target()
                similar = target.create_similar(cairo.CONTENT_COLOR_ALPHA, surf_w, surf_h)
                xcr = cairo.Context(similar)
                
                font_surf = self.xrender_font_surface or self.surface
                xcr.save()
                xcr.scale(scale, scale)
                cx = pad / scale
                for c in text:
                    cid = ord(c)
                    if cid not in self.chars:
                        cid = ord(c.lower() if c.isupper() else c.upper())
                    if cid in self.chars:
                        ch = self.chars[cid]
                        w, h = ch["width"], ch["height"]
                        if w > 0 and h > 0:
                            rx, ry = cx + ch["xoffset"], ch["yoffset"] + (pad / scale)
                            xcr.rectangle(rx, ry, w, h)
                            xcr.set_source_surface(font_surf, rx - ch["x"], ry - ch["y"])
                            xcr.get_source().set_filter(cairo.Filter.BILINEAR)
                            xcr.fill()
                        cx += ch["xadvance"]
                    else:
                        cx += 15
                xcr.restore()
                
                cached = (similar, tw, th, pad)
                self._text_cache[cache_key] = cached
                if len(self._text_cache) > 200:
                    self._text_cache.clear()
                    self._text_cache[cache_key] = cached
            except Exception:
                scale = size_px / self.line_height
                tw = self.get_text_width(text, scale)
                cr.save()
                start_x = x - tw / 2.0 if align == "center" else x - tw if align == "right" else x
                start_y = y - (self.line_height * scale) / 2.0 if align == "center" else y
                cr.translate(start_x, start_y)
                cr.scale(scale, scale)
                cx = 0.0
                font_surf = self.xrender_font_surface or self.surface
                for c in text:
                    cid = ord(c)
                    if cid not in self.chars:
                        cid = ord(c.lower() if c.isupper() else c.upper())
                    if cid in self.chars:
                        ch = self.chars[cid]
                        w, h = ch["width"], ch["height"]
                        if w > 0 and h > 0:
                            rx, ry = cx + ch["xoffset"], ch["yoffset"]
                            cr.rectangle(rx, ry, w, h)
                            cr.set_source_surface(font_surf, rx - ch["x"], ry - ch["y"])
                            cr.get_source().set_filter(cairo.Filter.BILINEAR)
                            cr.fill()
                        cx += ch["xadvance"]
                    else:
                        cx += 15
                cr.restore()
                return

        surf, tw, th, pad = cached
        cr.save()
        start_x = x - tw / 2.0 if align == "center" else x - tw if align == "right" else x
        start_y = y - th / 2.0 if align == "center" else y
        cr.set_source_surface(surf, start_x - pad, start_y - pad)
        cr.paint()
        cr.restore()