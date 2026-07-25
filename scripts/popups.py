# --- popups.py ---

import cairo
import math
from rendering import draw_scale9
from config import game_config

def draw_newgrounds_popup(cr, win):
    if win.newgrounds_popup_scale <= 0.0:
        return
    cr.save()
    cr.set_source_rgba(0.0, 0.0, 0.0, 0.392 * min(1.0, win.newgrounds_popup_scale))
    cr.rectangle(0, 0, 1280, 720)
    cr.fill()
    cx, cy, scale = 640.0, 360.0, win.newgrounds_popup_scale
    
    cr.save()
    cr.push_group()
    if win.square_surface:
        draw_scale9(cr, win.square_surface, win.square_pb, cx, cy, win.popup_width, win.popup_height)
    if win.bm_font and win.bm_font.surface:
        win.bm_font.draw_text(cr, win.popup_title, cx, cy - 76, 40, align="center")
        
    cr.save()
    cr.select_font_face("Arial", cairo.FontSlant.NORMAL, cairo.FontWeight.NORMAL)
    cr.set_font_size(25)
    cr.set_source_rgb(1.0, 1.0, 1.0)
    ext1 = cr.text_extents(win.popup_body_line1)
    cr.move_to(cx - ext1.width / 2, cy - 18)
    cr.show_text(win.popup_body_line1)
    ext2 = cr.text_extents(win.popup_body_line2)
    cr.move_to(cx - ext2.width / 2, cy + 14)
    cr.show_text(win.popup_body_line2)
    cr.restore()
    
    cancel_w, cancel_h, cancel_bounce = 165, 55, win.popup_cancel_btn.current_scale
    cr.save()
    cr.translate(cx - 70, cy + 65)
    cr.scale(cancel_bounce, cancel_bounce)
    if win.button_surface:
        draw_scale9(cr, win.button_surface, win.button_pb, 0, 0, cancel_w, cancel_h, corner_scale=win.settings_button_corner_scale)
    if win.bm_font and win.bm_font.surface:
        win.bm_font.draw_text(cr, win.popup_cancel_lbl, -2, -3, 38, align="center")
    cr.restore()
    
    open_w, open_h, open_bounce = 125, 55, win.popup_open_btn.current_scale
    cr.save()
    cr.translate(cx + 90, cy + 65)
    cr.scale(open_bounce, open_bounce)
    if win.button_surface:
        draw_scale9(cr, win.button_surface, win.button_pb, 0, 0, open_w, open_h, corner_scale=win.settings_button_corner_scale)
    if win.bm_font and win.bm_font.surface:
        win.bm_font.draw_text(cr, win.popup_open_lbl, -2, -3, 39, align="center")
    cr.restore()
    
    popup_pattern = cr.pop_group()
    cr.save()
    cr.translate(cx, cy)
    cr.scale(scale, scale)
    cr.translate(-cx, -cy)
    cr.set_source(popup_pattern)
    cr.paint()
    cr.restore()
    
    cr.restore()
    cr.restore()

def draw_settings_popup_custom(cr, win):
    if win.settings_popup_p <= 0.0:
        return
        
    if win.settings_popup_state in ("opening", "open"):
        eased_p = 1.0 - (1.0 - win.settings_popup_p) ** 2  
    else:
        eased_p = win.settings_popup_p ** 2  
        
    y_offset = (eased_p - 1.0) * 650.0  

    cr.save()
    cr.set_source_rgba(0.0, 0.0, 0.0, (180.0 / 255.0) * eased_p)
    cr.rectangle(0, 0, 1280, 720)
    cr.fill()

    cr.save()
    cr.translate(0, y_offset)

    if win.chain_surface:
        # Left Chain
        cr.save()
        cr.translate(win.settings_chain_l_x, win.settings_chain_l_y)
        ch_w_orig = win.chain_pb.get_width()
        ch_h_orig = win.chain_pb.get_height()
        cr.scale(win.settings_chain_l_w / ch_w_orig, win.settings_chain_l_h / ch_h_orig)
        cr.set_source_surface(win.chain_surface, -ch_w_orig/2, -ch_h_orig/2)
        cr.paint()
        cr.restore()

        # Right Chain
        cr.save()
        cr.translate(win.settings_chain_r_x, win.settings_chain_r_y)
        ch_w_orig = win.chain_pb.get_width()
        ch_h_orig = win.chain_pb.get_height()
        cr.scale(win.settings_chain_r_w / ch_w_orig, win.settings_chain_r_h / ch_h_orig)
        cr.set_source_surface(win.chain_surface, -ch_w_orig/2, -ch_h_orig/2)
        cr.paint()
        cr.restore()

    # Dark background plate
    cr.save()
    cr.set_source_rgba(0.0, 0.0, 0.0, (180.0 / 255.0))
    cr.rectangle(
        win.settings_table_bg_x - win.settings_table_bg_w / 2.0,
        win.settings_table_bg_y - win.settings_table_bg_h / 2.0,
        win.settings_table_bg_w,
        win.settings_table_bg_h
    )
    cr.fill()
    cr.restore()

    # Borders
    if win.table_side_surface:
        sw, sh = win.table_side_pb.get_width(), win.table_side_pb.get_height()
        cr.save()
        cr.translate(win.settings_table_left_x, win.settings_table_left_y)
        cr.scale(win.settings_table_left_w / sw, win.settings_table_left_h / sh)
        cr.set_source_surface(win.table_side_surface, -sw/2, -sh/2)
        cr.paint()
        cr.restore()

    if win.table_side_surface:
        sw, sh = win.table_side_pb.get_width(), win.table_side_pb.get_height()
        cr.save()
        cr.translate(win.settings_table_right_x, win.settings_table_right_y)
        cr.scale(-win.settings_table_right_w / sw, win.settings_table_right_h / sh)
        cr.set_source_surface(win.table_side_surface, -sw/2, -sh/2)
        cr.paint()
        cr.restore()

    if win.table_top_surface:
        tw, th = win.table_top_pb.get_width(), win.table_top_pb.get_height()
        cr.save()
        cr.translate(win.settings_table_top_x, win.settings_table_top_y)
        cr.scale(win.settings_table_top_w / tw, win.settings_table_top_h / th)
        cr.set_source_surface(win.table_top_surface, -tw/2, -th/2)
        cr.paint()
        cr.restore()

    if win.table_bottom_surface:
        bw, bh = win.table_bottom_pb.get_width(), win.table_bottom_pb.get_height()
        cr.save()
        cr.translate(win.settings_table_bottom_x, win.settings_table_bottom_y)
        cr.scale(win.settings_table_bottom_w / bw, win.settings_table_bottom_h / bh)
        cr.set_source_surface(win.table_bottom_surface, -bw/2, -bh/2)
        cr.paint()
        cr.restore()

    # Settings Title (bigFont, configurable coords/size)
    if win.big_font and win.big_font.surface:
        win.big_font.draw_text(cr, "Settings", win.settings_title_x, win.settings_title_y, win.settings_title_size, align="center")
    else:
        cr.save()
        cr.select_font_face("Sans", cairo.FontSlant.NORMAL, cairo.FontWeight.BOLD)
        cr.set_font_size(win.settings_title_size)
        cr.set_source_rgb(1.0, 1.0, 1.0)
        ext = cr.text_extents("Settings")
        cr.move_to(win.settings_title_x - ext.width / 2, win.settings_title_y + ext.height / 2)
        cr.show_text("Settings")
        cr.restore()

    def draw_popup_btn(name, bx, by, bw, bh, active, text, text_size, bounce_scale, text_ox, text_oy):
        cr.save()
        cr.translate(bx, by)
        cr.scale(bounce_scale, bounce_scale)
        if not active:
            cr.push_group()
        
        # Draw background plate
        if win.button_surface:
            draw_scale9(cr, win.button_surface, win.button_pb, 0, 0, bw, bh, corner_scale=win.settings_button_corner_scale)
        
        # Use estimated margins to restrict the text bounding width
        if bw > 250:
            estimated_margin = 24.0  # Safe side-margin for wide buttons
        else:
            estimated_margin = 18.0  # Safe side-margin for narrow buttons
            
        max_text_width = bw - (estimated_margin * 2.0)
        
        if win.bm_font and win.bm_font.surface:
            current_scale = text_size / win.bm_font.line_height
            rendered_width = win.bm_font.get_text_width(text, current_scale)
            
            # Constrain text scale down if it exceeds the maximum safe width
            if rendered_width > max_text_width and rendered_width > 0:
                text_size = text_size * (max_text_width / rendered_width)
                
            win.bm_font.draw_text(cr, text, text_ox, text_oy, text_size, align="center")
        else:
            cr.save()
            cr.select_font_face("Sans", cairo.FontSlant.NORMAL, cairo.FontWeight.BOLD)
            cr.set_font_size(text_size * 0.8)
            cr.set_source_rgb(1.0, 1.0, 1.0)
            ext = cr.text_extents(text)
            
            # Constrain fallback font text if it exceeds bounds
            if ext.width > max_text_width and ext.width > 0:
                text_size = text_size * (max_text_width / ext.width)
                cr.set_font_size(text_size * 0.8)
                ext = cr.text_extents(text)
                
            cr.move_to(-ext.width / 2 + text_ox, ext.height / 2 + text_oy)
            cr.show_text(text)
            cr.restore()

        if not active:
            cr.pop_group_to_source()
            cr.paint_with_alpha(0.5)
        cr.restore()

    # Buttons using customizable font sizes and custom text offsets (Graphics set to True)
    draw_popup_btn("Account", win.settings_account_x, win.settings_account_y, win.settings_account_w, win.settings_account_h, False, "Account", win.settings_account_font_size, win.settings_btn_account.current_scale, win.settings_account_text_offset_x, win.settings_account_text_offset_y)
    draw_popup_btn("How To Play", win.settings_how_to_play_x, win.settings_how_to_play_y, win.settings_how_to_play_w, win.settings_how_to_play_h, True, "How To Play", win.settings_how_to_play_font_size, win.settings_btn_how_to_play.current_scale, win.settings_how_to_play_text_offset_x, win.settings_how_to_play_text_offset_y)
    draw_popup_btn("Options", win.settings_options_x, win.settings_options_y, win.settings_options_w, win.settings_options_h, True, "Options", win.settings_options_font_size, win.settings_btn_options.current_scale, win.settings_options_text_offset_x, win.settings_options_text_offset_y)
    draw_popup_btn("Graphics", win.settings_graphics_x, win.settings_graphics_y, win.settings_graphics_w, win.settings_graphics_h, True, "Graphics", win.settings_graphics_font_size, win.settings_btn_graphics.current_scale, win.settings_graphics_text_offset_x, win.settings_graphics_text_offset_y)
    draw_popup_btn("Rate", win.settings_rate_x, win.settings_rate_y, win.settings_rate_w, win.settings_rate_h, False, "Rate", win.settings_rate_font_size, win.settings_btn_rate.current_scale, win.settings_rate_text_offset_x, win.settings_rate_text_offset_y)
    draw_popup_btn("Songs", win.settings_songs_x, win.settings_songs_y, win.settings_songs_w, win.settings_songs_h, False, "Songs", win.settings_songs_font_size, win.settings_btn_songs.current_scale, win.settings_songs_text_offset_x, win.settings_songs_text_offset_y)
    draw_popup_btn("Help", win.settings_help_x, win.settings_help_y, win.settings_help_w, win.settings_help_h, False, "Help", win.settings_help_font_size, win.settings_btn_help.current_scale, win.settings_help_text_offset_x, win.settings_help_text_offset_y)

    # Close button
    if win.settings_close_surface:
        cr.save()
        cr.translate(win.settings_close_x, win.settings_close_y)
        cs_w_orig = win.settings_close_pb.get_width()
        is_prescaled = cs_w_orig <= 80.0
        
        scale_val = win.settings_btn_close.current_scale * 0.563
        if is_prescaled:
            scale_val *= 2.0 
            
        cr.scale(scale_val, scale_val)
        cs_h_orig = win.settings_close_pb.get_height()
        cr.set_source_surface(win.settings_close_surface, -cs_w_orig/2.0, -cs_h_orig/2.0)
        cr.paint()
        cr.restore()

    cr.restore()
    cr.restore()

def draw_graphics_popup(cr, win):
    if win.graphics_popup_p <= 0.0:
        return
        
    if win.graphics_popup_state in ("opening", "open"):
        eased_p = 1.0 - (1.0 - win.graphics_popup_p) ** 2  
    else:
        eased_p = win.graphics_popup_p ** 2  
        
    y_offset = (eased_p - 1.0) * 650.0  

    cr.save()
    cr.set_source_rgba(0.0, 0.0, 0.0, (180.0 / 255.0) * eased_p)
    cr.rectangle(0, 0, 1280, 720)
    cr.fill()

    cr.save()
    cr.translate(0, y_offset)

    # Dark background plate
    cr.save()
    cr.set_source_rgba(0.0, 0.0, 0.0, (180.0 / 255.0))
    w_plate, h_plate = 500.0, 400.0
    cr.rectangle(640.0 - w_plate / 2.0, 360.0 - h_plate / 2.0, w_plate, h_plate)
    cr.fill()
    cr.restore()

    # Title
    if win.big_font and win.big_font.surface:
        win.big_font.draw_text(cr, "Graphics", 640.0, 200.0, 48.0, align="center")
    else:
        cr.save()
        cr.select_font_face("Sans", cairo.FontSlant.NORMAL, cairo.FontWeight.BOLD)
        cr.set_font_size(48.0)
        cr.set_source_rgb(1.0, 1.0, 1.0)
        ext = cr.text_extents("Graphics")
        cr.move_to(640.0 - ext.width / 2, 200.0 + ext.height / 2)
        cr.show_text("Graphics")
        cr.restore()

    # Draw check buttons for Low, Medium, High, Auto
    options = ["Low", "Medium", "High", "Auto"]
    for idx, opt in enumerate(options):
        y_pos = 260.0 + idx * 60.0
        is_selected = (game_config.graphics_quality == opt)
        
        # Checkbox
        cr.save()
        cr.translate(520.0, y_pos)
        cr.arc(0, 0, 12, 0, 2 * math.pi)
        cr.set_source_rgb(0.1, 0.1, 0.1)
        cr.fill()
        if is_selected:
            cr.arc(0, 0, 8, 0, 2 * math.pi)
            cr.set_source_rgb(0.0, 1.0, 0.0)
            cr.fill()
        cr.restore()
        
        # Text
        cr.save()
        cr.set_source_rgb(1.0, 1.0, 1.0)
        cr.select_font_face("Sans", cairo.FontSlant.NORMAL, cairo.FontWeight.BOLD)
        cr.set_font_size(24.0)
        ext = cr.text_extents(opt)
        cr.move_to(560.0, y_pos + ext.height / 2)
        cr.show_text(opt)
        cr.restore()

    # Close button (Compensated scale, rendered at top-right of panel)
    if win.settings_close_surface:
        cr.save()
        cr.translate(860.0, 190.0)
        scale_val = win.settings_btn_close.current_scale * 0.563
        cs_w_orig = win.settings_close_pb.get_width()
        is_prescaled = cs_w_orig <= 80.0
        if is_prescaled:
            scale_val *= 2.0
        cr.scale(scale_val, scale_val)
        cs_h_orig = win.settings_close_pb.get_height()
        cr.set_source_surface(win.settings_close_surface, -cs_w_orig/2.0, -cs_h_orig/2.0)
        cr.paint()
        cr.restore()

    cr.restore()
    cr.restore()