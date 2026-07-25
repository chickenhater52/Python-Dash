import math
import cairo
from config import LEVELS

def draw_rounded_rect(cr, x, y, w, h, r):
    cr.new_sub_path()
    cr.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    cr.arc(x + w - r, y + r, r, 1.5 * math.pi, 2 * math.pi)
    cr.arc(x + w - r, y + h - r, r, 0, 0.5 * math.pi)
    cr.arc(x + r, y + h - r, r, 0.5 * math.pi, math.pi)
    cr.close_path()

def draw_scale9(cr, surface, pixbuf, cx, cy, w, h, corner_scale=1.0):
    if not surface or not pixbuf:
        return
    sw = pixbuf.get_width()
    sh = pixbuf.get_height()
    
    if sw > 150:
        cw = min(32.0, sw / 3.0) * corner_scale
        ch = min(32.0, sh / 3.0) * corner_scale
    else:
        cw = min(14.0, sw / 3.0) * corner_scale
        ch = min(14.0, sh / 3.0) * corner_scale
    
    x0 = int(round(cx - w / 2.0))
    x1 = int(round(cx - w / 2.0 + cw))
    x2 = int(round(cx + w / 2.0 - cw))
    x3 = int(round(cx + w / 2.0))
    
    y0 = int(round(cy - h / 2.0))
    y1 = int(round(cy - h / 2.0 + ch))
    y2 = int(round(cy + h / 2.0 - ch))
    y3 = int(round(cy + h / 2.0))
    
    dx = [x0, x1, x2, x3]
    dy = [y0, y1, y2, y3]
    
    sx = [0.0, cw / corner_scale, sw - cw / corner_scale, sw]
    sy = [0.0, ch / corner_scale, sh - ch / corner_scale, sh]
    
    for i in range(3):
        for j in range(3):
            s_x0, s_x1 = sx[i], sx[i+1]
            s_y0, s_y1 = sy[j], sy[j+1]
            s_w, s_h = s_x1 - s_x0, s_y1 - s_y0
            
            d_x0 = dx[i]
            d_x1 = dx[i+1]
            d_y0 = dy[j]
            d_y1 = dy[j+1]
            
            d_w = d_x1 - d_x0
            d_y_h = d_y1 - d_y0
            
            if s_w <= 0 or s_h <= 0 or d_w <= 0 or d_y_h <= 0:
                continue
            
            draw_w = d_w
            draw_h = d_y_h
            if i < 2:
                draw_w += 1
            if j < 2:
                draw_h += 1
                
            cr.save()
            cr.rectangle(d_x0, d_y0, draw_w, draw_h)
            cr.clip()
            
            scale_x = draw_w / s_w
            scale_y = draw_h / s_h
            
            cr.translate(d_x0, d_y0)
            cr.scale(scale_x, scale_y)
            cr.set_source_surface(surface, -s_x0, -s_y0)
            cr.get_source().set_filter(cairo.Filter.BILINEAR)
            cr.paint()
            cr.restore()

def draw_procedural_diff_icon(cr, cx, cy, level_index):
    lvl_data, val = LEVELS[level_index], LEVELS[level_index]["Val"]
    colors = {
        1: ((0/255, 102/255, 255/255), (102/255, 204/255, 255/255)), 
        2: ((0/255, 153/255, 0/255), (102/255, 255/255, 102/255)),
        3: ((204/255, 153/255, 0/255), (255/255, 255/255, 102/255)), 
        4: ((153/255, 0/255, 153/255), (255/255, 153/255, 255/255)),
        5: ((204/255, 0/255, 0/255), (255/255, 102/255, 102/255)), 
        6: ((102/255, 0/255, 204/255), (178/255, 102/255, 255/255))
    }
    dark, light = colors.get(val, colors[2])
    cr.save()
    cr.translate(cx, cy)
    cr.arc(0, 4, 30, 0, 2 * math.pi)
    cr.set_source_rgba(0, 0, 0, 0.4)
    cr.fill()
    cr.arc(0, 0, 30, 0, 2 * math.pi)
    cr.set_source_rgb(0, 0, 0)
    cr.fill()
    cr.arc(0, 0, 26, 0, 2 * math.pi)
    cr.set_source_rgb(*light)
    cr.fill()
    cr.arc(0, 0, 26, 0, 2 * math.pi)
    cr.clip()
    cr.arc(-5, -5, 26, 0, 2 * math.pi)
    cr.set_source_rgb(*dark)
    cr.fill()
    cr.reset_clip()
    cr.set_source_rgb(0, 0, 0)
    cr.arc(-10, -5, 5, 0, 2 * math.pi)
    cr.arc(10, -5, 5, 0, 2 * math.pi)
    cr.fill()
    cr.set_source_rgb(1, 1, 1)
    cr.arc(-11, -6, 2, 0, 2 * math.pi)
    cr.arc(9, -6, 2, 0, 2 * math.pi)
    cr.fill()
    cr.set_source_rgb(0, 0, 0)
    cr.set_line_width(4)
    cr.set_line_cap(cairo.LineCap.ROUND)
    if val <= 2:
        cr.arc(0, 4, 10, 0, math.pi)
        cr.stroke()
    elif val == 3:
        cr.move_to(-12, 10)
        cr.line_to(12, 10)
        cr.stroke()
    else:
        cr.arc(0, 16, 10, math.pi, 2 * math.pi)
        cr.stroke()
    cr.restore()

def draw_progress_bar_custom(cr, bx, by, bw, bh, label_text, percentage, fill_color, title_ox, title_oy, title_size, pct_ox, pct_oy, pct_size, big_font, progress_bar_surface, progress_bar_pb, progress_bar_w_orig, progress_bar_h_orig):
    cr.save()
    title_x, title_y = bx + title_ox, by + title_oy
    if big_font and big_font.surface: 
        big_font.draw_text(cr, label_text, title_x, title_y, title_size, align="center")
    else:
        cr.save()
        cr.select_font_face("Sans", cairo.FontSlant.NORMAL, cairo.FontWeight.BOLD)
        cr.set_font_size(title_size)
        cr.set_source_rgb(1.0, 1.0, 1.0)
        ext = cr.text_extents(label_text)
        cr.move_to(title_x - ext.width / 2, title_y + ext.height / 2)
        cr.show_text(label_text)
        cr.restore()
        
    if progress_bar_surface and progress_bar_pb:
        orig_w, orig_h = progress_bar_w_orig, progress_bar_h_orig
        cr.save()
        cr.translate(bx, by)
        cr.scale(bw / orig_w, bh / orig_h)
        cr.set_source_rgba(0.0, 0.0, 0.0, 125.0 / 255.0)
        cr.mask_surface(progress_bar_surface, -orig_w / 2.0, -orig_h / 2.0)
        cr.restore()
    else:
        cr.save()
        cr.translate(bx, by + 2)
        cr.rectangle(-bw / 2, -bh / 2, bw, bh)
        cr.set_source_rgba(0, 0, 0, 0.4)
        cr.fill()
        cr.restore()
        
        cr.save()
        cr.translate(bx, by)
        cr.rectangle(-bw / 2, -bh / 2, bw, bh)
        cr.set_source_rgb(0, 0, 0)
        cr.fill()
        cr.restore()
        
    if percentage > 0:
        if progress_bar_surface and progress_bar_pb:
            orig_w, orig_h = progress_bar_w_orig, progress_bar_h_orig
            fill_bw, fill_bh = bw * 0.992, bh * 0.86
            fill_w = fill_bw * (percentage / 100.0)
            
            cr.save()
            draw_rounded_rect(cr, bx - fill_bw / 2.0, by - fill_bh / 2.0, fill_bw, fill_bh, fill_bh / 2.0)
            cr.clip()
            cr.rectangle(bx - fill_bw / 2.0, by - fill_bh / 2.0, fill_w, fill_bh)
            cr.clip()
            cr.translate(bx, by)
            cr.scale(fill_bw / orig_w, fill_bh / orig_h)
            cr.set_source_surface(progress_bar_surface, -orig_w / 2.0, -orig_h / 2.0)
            cr.paint()
            cr.set_operator(cairo.Operator.MULTIPLY)
            cr.set_source_rgb(*fill_color)
            cr.paint()
            cr.restore()
        else:
            padding = 4
            inner_w, inner_h = bw - (padding * 2), bh - (padding * 2)
            fill_width = int(inner_w * (percentage / 100.0))
            if fill_width > 0:
                cr.save()
                cr.translate(bx - bw / 2 + padding, by - bh / 2 + padding)
                cr.rectangle(0, 0, fill_width, inner_h)
                cr.set_source_rgb(*fill_color)
                cr.fill()
                cr.restore()
                
    pct_text, pct_x, pct_y = f"{percentage}%", bx + pct_ox, by + pct_oy
    if big_font and big_font.surface: 
        big_font.draw_text(cr, pct_text, pct_x, pct_y, pct_size, align="center")
    else:
        cr.save()
        cr.select_font_face("Sans", cairo.FontSlant.NORMAL, cairo.FontWeight.BOLD)
        cr.set_font_size(pct_size)
        cr.set_source_rgb(1.0, 1.0, 1.0)
        ext = cr.text_extents(pct_text)
        cr.move_to(pct_x - ext.width / 2, pct_y + ext.height / 2)
        cr.show_text(pct_text)
        cr.restore()
        
    cr.restore()