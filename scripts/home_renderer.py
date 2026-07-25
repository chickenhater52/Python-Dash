import math
import cairo
from config import LEVELS, LEVEL_COLORS, find_asset_path
from rendering import draw_rounded_rect, draw_scale9, draw_procedural_diff_icon, draw_progress_bar_custom
from popups import draw_newgrounds_popup, draw_settings_popup_custom, draw_graphics_popup
from gui_elements import VirtualElement

def calculate_time_text_layout(text, base_size=27.5, base_y=99.5):
    return base_size, base_y

def calculate_music_text_layout(text, base_size=27.5, base_y=99.7):
    L = len(text)
    if L <= 13:
        S = base_size
    elif L <= 16:
        S = base_size - ((base_size - 27.0) / 3.0) * (L - 13)
    else:
        S = max(11.0, 27.0 - ((27.0 - 15.6) / 9.0) * (L - 16))
        
    Y = base_y + 0.504 * (28.1 - S)
    return S, Y

def draw_home_screen(win, cr):
    target_ratio = 16.0 / 9.0
    current_width = win.drawing_area.get_allocated_width()
    current_height = win.drawing_area.get_allocated_height()
    current_ratio = current_width / current_height
    if current_ratio > target_ratio:
        h_box = current_height
        w_box = h_box * target_ratio
        x_offset = (current_width - w_box) / 2.0
        y_offset = 0.0
    else:
        w_box = current_width
        h_box = w_box / target_ratio
        x_offset = 0.0
        y_offset = (current_height - h_box) / 2.0
    scale_factor = w_box / 1280.0 if w_box > 0 else 1.0

    cr.save()
    cr.translate(x_offset, y_offset)
    cr.scale(scale_factor, scale_factor)
    cr.rectangle(0, 0, 1280, 720)
    cr.clip()

    if win.active_game_scene:
        win.active_game_scene.draw(cr, 1280, 720)
        cr.restore()
        
        cr.save()
        cr.select_font_face("Sans", cairo.FontSlant.NORMAL, cairo.FontWeight.BOLD)
        cr.set_font_size(18)
        cr.set_source_rgba(1.0, 1.0, 1.0, 0.8)
        cr.move_to(10, 25)
        cr.show_text(f"FPS: {win.current_fps}")
        cr.restore()

        if win.transition_alpha > 0.0:
            cr.save()
            cr.set_source_rgba(0.0, 0.0, 0.0, win.transition_alpha)
            cr.rectangle(0, 0, current_width, current_height)
            cr.fill()
            cr.restore()
        return

    hue = (win.menu_rainbow_time * 15.0) % 360.0
    r, g, b_val = hsv_to_rgb(hue / 360.0, 0.85, 1.0)
    
    if win.creator_menu_active or win.my_levels_active or win.level_view_active:
        cr.set_source(win.creator_bg_gradient)
        cr.paint()
    elif win.level_select_active:
        grad = win.bg_gradients[win.current_level_index % len(LEVEL_COLORS)]
        cr.set_source(grad)
        cr.paint()
    else:
        cr.save()
        cr.set_source_rgb(r, g, b_val)
        cr.paint()
        if win.bg_surface:
            scroll_x = (win.bg_scroll_x) % win.bg_w
            pattern = cairo.SurfacePattern(win.bg_surface)
            pattern.set_extend(cairo.Extend.REPEAT)
            matrix = cairo.Matrix()
            matrix.translate(scroll_x, win.bg_h - 720 + win.bg_y_offset)
            pattern.set_matrix(matrix)
            cr.set_operator(cairo.Operator.MULTIPLY)
            cr.set_source(pattern)
            cr.rectangle(0, 0, 1280, 720)
            cr.fill()
        cr.restore()

    if not win.creator_menu_active and not win.my_levels_active and not win.level_view_active:
        cr.save()
        ground_y = win.ground_y_level_select if win.level_select_active else win.ground_y
        col = LEVEL_COLORS[win.current_level_index % len(LEVEL_COLORS)] if win.level_select_active else (r, g, b_val)
        if win.ground_surface and win.ground_pb:
            cr.save()
            cr.rectangle(0, ground_y, 1280, 720 - ground_y)
            cr.clip()
            offset_x = win.ground_x_offset if win.level_select_active else win.ground_x_offset - win.ground_scroll_x
            
            cr.set_source_rgb(col[0] * 0.45, col[1] * 0.45, col[2] * 0.45)
            cr.paint()
            
            pattern = cairo.SurfacePattern(win.ground_surface)
            pattern.set_extend(cairo.Extend.REPEAT)
            inv_s = 1.0 / win.ground_tile_scale if win.ground_tile_scale > 0 else 1.0
            matrix = cairo.Matrix(inv_s, 0.0, 0.0, inv_s, -inv_s * offset_x, -inv_s * ground_y)
            pattern.set_matrix(matrix)
            cr.set_operator(cairo.Operator.MULTIPLY)
            cr.set_source(pattern)
            cr.paint()
            cr.restore()

        if win.floor_line_surface:
            cr.save()
            cr.translate(640.0, ground_y)
            scale_x = win.floor_line_width / win.floor_line_w_orig
            cr.scale(scale_x, 1.0)
            cr.set_source_surface(win.floor_line_surface, -win.floor_line_w_orig / 2.0, -win.floor_line_h_orig / 2.0)
            cr.paint()
            cr.restore()
        cr.restore()

    cr.save()
    cr.translate(win.offset_x, win.offset_y)
    cr.scale(win.zoom, win.zoom)
    if win.creator_menu_active:
        for elem in win.creator_elements:
            cr.save()
            cr.translate(elem.x, elem.y)
            cr.scale(elem.current_scale, elem.current_scale)
            if elem.surface:
                cr.set_source_surface(elem.surface, -elem.half_w, -elem.half_h)
                cr.paint()
            cr.restore()
    elif win.my_levels_active:
        draw_my_levels_screen(win, cr)
    elif win.level_view_active:
        draw_level_view_screen(win, cr)
    elif not win.level_select_active:
        for elem in win.elements:
            cr.save()
            cr.translate(elem.x, elem.y)
            cr.scale(elem.current_scale, elem.current_scale)
            if elem.surface:
                cr.set_source_surface(elem.surface, -elem.half_w, -elem.half_h)
                cr.paint()
            cr.restore()
    else:
        cr.save()
        cr.translate(win.spring_x, 0)
        
        cr.save()
        cr.translate(win.card_x, win.card_y)
        cr.scale(win.card_element.current_scale, win.card_element.current_scale)
        draw_rounded_rect(cr, -win.card_w / 2, -win.card_h / 2, win.card_w, win.card_h, 18)
        cr.set_source_rgba(0.0, 0.0, 0.0, 125.0 / 255.0)
        cr.fill()
        cr.restore()

        title_text = LEVELS[win.current_level_index]["Name"]
        title_width = win.big_font.get_text_width(title_text, win.title_size / win.big_font.line_height) if win.big_font and win.big_font.surface else cr.text_extents(title_text).width
        limit_a, scale_a = win.card_w - 200.0, 1.0
        if title_width > limit_a:
            scale_a = limit_a / title_width
        title_x_pos, title_y_pos = win.card_x + win.title_offset_x, win.card_y + win.title_offset_y
        diff_x, diff_y = (title_x_pos - (title_width * scale_a) / 2.0) - win.diff_icon_distance, win.card_y + win.diff_offset_y
        lvl_val = LEVELS[win.current_level_index]["Val"]
        if lvl_val in win.diff_icons:
            _, surf, dw_orig, _ = win.diff_icons[lvl_val]
            cr.save()
            cr.translate(diff_x, diff_y)
            icon_scale = win.diff_size / dw_orig
            cr.scale(icon_scale, icon_scale)
            cr.set_source_surface(surf, -dw_orig / 2.0, -dw_orig / 2.0)
            cr.paint()
            cr.restore()
        if win.big_font and win.big_font.surface:
            win.big_font.draw_text(cr, title_text, title_x_pos, title_y_pos, win.title_size * scale_a, align="center")
        if win.bar_norm_visible:
            best_normal = win.level_best_normal[win.current_level_index]
            draw_progress_bar_custom(cr, win.bar_norm_x, win.bar_norm_y, win.bar_norm_w, win.bar_norm_h, win.bar_norm_title_text, best_normal, (0.0, 1.0, 0.0), win.bar_norm_title_offset_x, win.bar_norm_title_offset_y, win.bar_norm_title_size, win.bar_norm_pct_offset_x, win.bar_norm_pct_offset_y, win.bar_norm_pct_size, win.big_font, win.progress_bar_surface, win.progress_bar_pb, win.progress_bar_w_orig, win.progress_bar_h_orig)
        
        if win.bar_pract_visible:
            best_pract = win.level_best_practice[win.current_level_index]
            draw_progress_bar_custom(cr, win.bar_pract_x, win.bar_pract_y, win.bar_pract_w, win.bar_pract_h, win.bar_pract_title_text, best_pract, (0.0, 1.0, 1.0), win.bar_pract_title_offset_x, win.bar_pract_title_offset_y, win.bar_pract_title_size, win.bar_pract_pct_offset_x, win.bar_pract_pct_offset_y, win.bar_pract_pct_size, win.big_font, win.progress_bar_surface, win.progress_bar_pb, win.progress_bar_w_orig, win.progress_bar_h_orig)
            
        cr.restore()

        cr.save()
        for i in range(len(LEVELS)):
            cx_dot = win.dot_x + (i - len(LEVELS)/2 + 0.5) * win.dot_spacing
            cr.arc(cx_dot, win.dot_y, win.dot_size, 0, 2 * math.pi)
            if i == win.current_level_index:
                cr.set_source_rgba(1.0, 1.0, 1.0, 1.0)
            else:
                cr.set_source_rgba(1.0, 1.0, 1.0, 0.3)
            cr.fill()
        cr.restore()
    cr.restore()

    if win.level_select_active:
        for elem in win.ls_elements:
            cr.save()
            cr.translate(elem.x, elem.y)
            pw = elem.pixbuf.get_width() if elem.pixbuf else 100.0
            ph = elem.pixbuf.get_height() if elem.pixbuf else 100.0
            
            if elem.name == "LS Arrow Left":
                cr.scale(win.nav_arrow_left_w / pw, win.nav_arrow_left_h / ph)
                cr.scale(-elem.current_scale / elem.scale, elem.current_scale / elem.scale)
            elif elem.name == "LS Arrow Right":
                cr.scale(win.nav_arrow_right_w / pw, win.nav_arrow_right_h / ph)
                cr.scale(elem.current_scale / elem.scale, elem.current_scale / elem.scale)
            else:
                cr.scale(elem.current_scale, elem.current_scale)

            if elem.surface:
                cr.set_source_surface(elem.surface, -elem.half_w, -elem.half_h)
                cr.paint()
            cr.restore()
        if win.top_bar_surface and win.top_bar_visible:
            cr.save()
            cr.translate(win.top_bar_x, win.top_bar_y)
            cr.scale(win.top_bar_w / win.top_bar_w_orig, win.top_bar_h / win.top_bar_h_orig)
            cr.set_source_surface(win.top_bar_surface, -win.top_bar_w_orig / 2.0, -win.top_bar_h_orig / 2.0)
            cr.paint()
            cr.restore()
        if win.side_art_surface and win.side_art_visible:
            cr.save()
            cr.translate(win.left_side_art_x, win.left_side_art_y)
            cr.scale(win.left_side_art_w / win.side_art_w_orig, win.left_side_art_h / win.side_art_h_orig)
            cr.set_source_surface(win.side_art_surface, 0, 0)
            cr.paint()
            cr.restore()

            cr.save()
            cr.translate(win.right_side_art_x, win.right_side_art_y)
            cr.scale(-win.right_side_art_w / win.side_art_w_orig, win.right_side_art_h / win.side_art_h_orig)
            cr.set_source_surface(win.side_art_surface, 0, 0)
            cr.paint()
            cr.restore()

    if win.creator_menu_active and win.side_art_surface:
        cr.save()
        cr.translate(win.creator_sideart_tl_x, win.creator_sideart_tl_y)
        cr.rotate(math.radians(win.creator_sideart_tl_rot))
        cr.scale(-1.0 if win.creator_sideart_tl_mirror_x else 1.0, -1.0 if win.creator_sideart_tl_mirror_y else 1.0)
        cr.scale(161.0 / win.side_art_w_orig, 159.0 / win.side_art_h_orig)
        cr.set_source_surface(win.side_art_surface, -win.side_art_w_orig / 2.0, -win.side_art_h_orig / 2.0)
        cr.paint()
        cr.restore()

        if win.settings_close_surface:
            cr.save()
            cr.translate(54.5, 49.5)
            scale_val = win.creator_back_btn.current_scale * 0.563
            cs_w_orig = win.settings_close_pb.get_width()
            is_prescaled = cs_w_orig <= 80.0
            if is_prescaled:
                scale_val *= 2.0
            cr.scale(scale_val, scale_val)
            cs_h_orig = win.settings_close_pb.get_height()
            cr.set_source_surface(win.settings_close_surface, -cs_w_orig / 2.0, -cs_h_orig / 2.0)
            cr.paint()
            cr.restore()

    if win.settings_popup_p > 0.0:
        draw_settings_popup_custom(cr, win)
    if win.graphics_popup_p > 0.0:
        draw_graphics_popup(cr, win)
    if win.newgrounds_popup_scale > 0.0:
        draw_newgrounds_popup(cr, win)
    
    if win.overlay_opacity > 0.0 and win.overlay_element.surface:
        elem = win.overlay_element
        cr.save()
        cr.translate(elem.x, elem.y)
        cr.scale(elem.current_scale, elem.current_scale)
        cr.set_source_surface(elem.surface, -elem.half_w, -elem.half_h)
        cr.paint_with_alpha(win.overlay_opacity)
        cr.restore()

    cr.save()
    cr.select_font_face("Sans", cairo.FontSlant.NORMAL, cairo.FontWeight.BOLD)
    cr.set_font_size(18)
    cr.set_source_rgba(1.0, 1.0, 1.0, 0.8)
    cr.move_to(10, 25)
    cr.show_text(f"FPS: {win.current_fps}")
    cr.restore()

    cr.restore()

    if win.transition_alpha > 0.0:
        cr.save()
        cr.set_source_rgba(0.0, 0.0, 0.0, win.transition_alpha)
        cr.rectangle(0, 0, current_width, current_height)
        cr.fill()
        cr.restore()

def hsv_to_rgb(h, s, v):
    import colorsys
    return colorsys.hsv_to_rgb(h, s, v)

def draw_my_levels_screen(win, cr):
    if win.side_art_surface:
        cr.save()
        cr.translate(win.left_side_art_x, win.left_side_art_y)
        cr.scale(win.left_side_art_w / win.side_art_w_orig, win.left_side_art_h / win.side_art_h_orig)
        cr.set_source_surface(win.side_art_surface, 0, 0)
        cr.paint()
        cr.restore()
        
        cr.save()
        cr.translate(win.right_side_art_x, win.right_side_art_y)
        cr.scale(-win.right_side_art_w / win.side_art_w_orig, win.right_side_art_h / win.side_art_h_orig)
        cr.set_source_surface(win.side_art_surface, 0, 0)
        cr.paint()
        cr.restore()

    left = win.settings_table_bg_x - win.my_levels_row_w / 2.0
    right = win.settings_table_bg_x + win.my_levels_row_w / 2.0
    top = win.settings_table_bg_y - win.settings_table_bg_h / 2.0
    bottom = win.settings_table_bg_y + win.settings_table_bg_h / 2.0
    
    table_w = win.my_levels_row_w
    table_h = win.settings_table_bg_h
    
    cr.save()
    cr.set_source_rgb(194/255.0, 114/255.0, 62/255.0)
    cr.rectangle(left, top, table_w, table_h)
    cr.fill()
    cr.restore()

    cr.save()
    cr.rectangle(left, top, table_w, table_h)
    cr.clip()

    lengths = ["Tiny", "Short", "Medium", "Long", "XL"]

    for i, lvl in enumerate(win.my_levels_list):
        row_y_offset = -1.25 * i
        row_y = top + i * win.my_levels_row_h - win.my_levels_scroll_y + row_y_offset
        
        if row_y + win.my_levels_row_h < top or row_y > bottom:
            continue
        
        cr.save()
        if i % 2 == 0:
            cr.set_source_rgb(161/255.0, 88/255.0, 44/255.0)
        else:
            cr.set_source_rgb(194/255.0, 114/255.0, 62/255.0)
        cr.rectangle(left, row_y, table_w, win.my_levels_row_h)
        cr.fill()
        cr.restore()

        cr.save()
        cr.set_source_rgb(107/255.0, 43/255.0, 1/255.0)
        cr.rectangle(left, row_y + win.my_levels_row_h - win.my_levels_separator_thickness, table_w, win.my_levels_separator_thickness)
        cr.fill()
        cr.restore()

        name_text = lvl.get("levelName", "Unnamed")
        
        default_size = win.level_title_size
        max_title_w = 420.0
        
        if win.big_font and win.big_font.surface:
            scale_init = default_size / win.big_font.line_height
            tw = win.big_font.get_text_width(name_text, scale_init)
            if tw > max_title_w and tw > 0:
                title_size = default_size * (max_title_w / tw)
                if title_size < 44.5:
                    title_size = 44.5
            else:
                title_size = default_size
        else:
            title_size = default_size

        cr.save()
        default_y_calc = 30.3857 - 0.1142857 * default_size
        scaled_math_y = 30.3857 - 0.1142857 * title_size
        title_y_calc = row_y + win.level_title_y + (scaled_math_y - default_y_calc)

        if win.big_font and win.big_font.surface:
            win.big_font.draw_text(cr, name_text, left + win.level_title_x, title_y_calc, title_size, align="left")
        else:
            cr.select_font_face("Sans", cairo.FontSlant.NORMAL, cairo.FontWeight.BOLD)
            cr.set_font_size(title_size)
            cr.set_source_rgb(1.0, 1.0, 1.0)
            cr.move_to(left + win.level_title_x, title_y_calc + 3)
            cr.show_text(name_text)
        cr.restore()

        len_text = win.time_text_override if win.time_text_override else lengths[lvl.get("levelLength", 0)]
        time_font_size, time_y_pos = calculate_time_text_layout(len_text, win.time_text_size, win.time_text_y)

        iw_time_half = (win.time_icon_pb.get_width() if win.time_icon_pb else 50.0) / 2.0
        if win.time_icon_surface and win.time_icon_pb:
            cr.save()
            cr.translate(left + win.time_icon_x, row_y + win.time_icon_y)
            cr.scale(win.time_icon_scale, win.time_icon_scale)
            iw = win.time_icon_pb.get_width()
            ih = win.time_icon_pb.get_height()
            cr.set_source_surface(win.time_icon_surface, -iw/2.0, -ih/2.0)
            cr.paint()
            cr.restore()
        else:
            cr.save()
            cr.translate(left + win.time_icon_x, row_y + win.time_icon_y)
            cr.arc(0, 0, 8, 0, 2 * math.pi)
            cr.set_source_rgb(1, 1, 1)
            cr.set_line_width(2)
            cr.stroke()
            cr.move_to(0, 0)
            cr.line_to(0, -5)
            cr.move_to(0, 0)
            cr.line_to(4, 0)
            cr.stroke()
            cr.restore()

        right_time_icon = left + win.time_icon_x + iw_time_half * win.time_icon_scale
        time_text_start_x = right_time_icon + win.icon_text_gap

        cr.save()
        if win.big_font and win.big_font.surface:
            win.big_font.draw_text(cr, len_text, time_text_start_x, row_y + time_y_pos, time_font_size, align="left")
            w_time_text = win.big_font.get_text_width(len_text, time_font_size / win.big_font.line_height)
        else:
            cr.select_font_face("Sans", cairo.FontSlant.NORMAL, cairo.FontWeight.BOLD)
            cr.set_font_size(time_font_size)
            cr.set_source_rgb(1.0, 1.0, 1.0)
            ext = cr.text_extents(len_text)
            cr.move_to(time_text_start_x, row_y + time_y_pos + ext.height)
            cr.show_text(len_text)
            w_time_text = ext.width
        cr.restore()

        right_time_text = time_text_start_x + w_time_text

        song_text = win.music_text_override if win.music_text_override else lvl.get("song", "Stereo Madness")
        music_font_size, music_y_pos = calculate_music_text_layout(song_text, win.music_text_size, win.music_text_y)

        iw_music_half = (win.music_icon_pb.get_width() if win.music_icon_pb else 50.0) / 2.0
        music_icon_start_x = right_time_text + win.music_icon_gap + iw_music_half * win.music_icon_scale

        if win.music_icon_surface and win.music_icon_pb:
            cr.save()
            cr.translate(music_icon_start_x, row_y + win.music_icon_y)
            cr.scale(win.music_icon_scale, win.music_icon_scale)
            iw = win.music_icon_pb.get_width()
            ih = win.music_icon_pb.get_height()
            cr.set_source_surface(win.music_icon_surface, -iw/2.0, -ih/2.0)
            cr.paint()
            cr.restore()
        else:
            cr.save()
            cr.translate(music_icon_start_x, row_y + win.music_icon_y)
            cr.set_source_rgb(1, 1, 1)
            cr.rectangle(-4, -6, 8, 3)
            cr.fill()
            cr.move_to(2, -6)
            cr.line_to(2, 4)
            cr.arc(0, 4, 3, 0, 2*math.pi)
            cr.fill()
            cr.stroke()
            cr.restore()

        right_music_icon = music_icon_start_x + iw_music_half * win.music_icon_scale
        music_text_start_x = right_music_icon + win.icon_text_gap

        cr.save()
        if win.big_font and win.big_font.surface:
            win.big_font.draw_text(cr, song_text, music_text_start_x, row_y + music_y_pos, music_font_size, align="left")
            w_music_text = win.big_font.get_text_width(song_text, music_font_size / win.big_font.line_height)
        else:
            cr.select_font_face("Sans", cairo.FontSlant.NORMAL, cairo.FontWeight.BOLD)
            cr.set_font_size(music_font_size)
            cr.set_source_rgb(1.0, 1.0, 1.0)
            ext = cr.text_extents(song_text)
            cr.move_to(music_text_start_x, row_y + music_y_pos + ext.height)
            cr.show_text(song_text)
            w_music_text = ext.width
        cr.restore()

        right_music_text = music_text_start_x + w_music_text

        status_text = win.info_text_override if win.info_text_override else lvl.get("status", "Unverified")
        info_font_size, info_y_pos = win.info_text_size, win.info_text_y

        iw_info_half = (win.info_icon_pb.get_width() if win.info_icon_pb else 50.0) / 2.0
        info_icon_start_x = right_music_text + win.info_icon_gap + iw_info_half * win.info_icon_scale

        if win.info_icon_surface and win.info_icon_pb:
            cr.save()
            cr.translate(info_icon_start_x, row_y + win.info_icon_y)
            cr.scale(win.info_icon_scale, win.info_icon_scale)
            iw = win.info_icon_pb.get_width()
            ih = win.info_icon_pb.get_height()
            cr.set_source_surface(win.info_icon_surface, -iw/2.0, -ih/2.0)
            cr.paint()
            cr.restore()
        else:
            cr.save()
            cr.translate(info_icon_start_x, row_y + win.info_icon_y)
            cr.arc(0, 0, 8, 0, 2*math.pi)
            cr.set_source_rgb(1, 1, 1)
            cr.stroke()
            cr.select_font_face("Sans", cairo.FontSlant.NORMAL, cairo.FontWeight.BOLD)
            cr.set_font_size(10)
            cr.move_to(-2, 3)
            cr.show_text("i")
            cr.restore()

        right_info_icon = info_icon_start_x + iw_info_half * win.info_icon_scale
        info_text_start_x = right_info_icon + win.icon_text_gap

        cr.save()
        if win.big_font and win.big_font.surface:
            win.big_font.draw_text(cr, status_text, info_text_start_x, row_y + info_y_pos, info_font_size, align="left")
        else:
            cr.select_font_face("Sans", cairo.FontSlant.NORMAL, cairo.FontWeight.BOLD)
            cr.set_font_size(info_font_size)
            cr.set_source_rgb(1.0, 1.0, 1.0)
            ext = cr.text_extents(status_text)
            cr.move_to(info_text_start_x, row_y + info_y_pos + ext.height)
            cr.show_text(status_text)
        cr.restore()

        view_btn_x = left + win.view_btn_x
        view_btn_y = row_y + win.view_btn_y
        while len(win.my_levels_view_btns) <= i:
            win.my_levels_view_btns.append(VirtualElement("View Button", 1.0))
        
        scale_val = win.my_levels_view_btns[i].current_scale * win.view_btn_scale
        bw = win.view_btn_w
        bh = win.view_btn_h
        
        cr.save()
        cr.translate(view_btn_x, view_btn_y)
        cr.scale(scale_val * 0.75, scale_val * 0.75)
        if win.button_surface:
            draw_scale9(cr, win.button_surface, win.button_pb, 0, 0, bw, bh, corner_scale=win.view_btn_corner_scale)
        else:
            cr.set_source_rgb(0, 0.8, 0)
            draw_rounded_rect(cr, -bw/2.0, -bh/2.0, bw, bh, 10)
            cr.fill()
        
        txt_x = win.view_btn_text_x
        txt_y = win.view_btn_text_y
        txt_size = win.view_btn_font_size

        if win.big_font and win.big_font.surface:
            win.big_font.draw_text(cr, "View", txt_x, txt_y, txt_size, align="center")
        else:
            cr.select_font_face("Sans", cairo.FontSlant.NORMAL, cairo.FontWeight.BOLD)
            cr.set_font_size(txt_size * 0.625)
            cr.set_source_rgb(1.0, 1.0, 1.0)
            ext = cr.text_extents("View")
            cr.move_to(txt_x - ext.width/2.0, txt_y + ext.height/2.0)
            cr.show_text("View")
        cr.restore()

    cr.restore()

    if win.table_side_surface:
        sw, sh_side = win.table_side_pb.get_width(), win.table_side_pb.get_height()
        cr.save()
        cr.translate(win.settings_table_left_x, win.settings_table_left_y)
        cr.scale(win.settings_table_left_w / sw, win.settings_table_left_h / sh_side)
        cr.set_source_surface(win.table_side_surface, -sw/2.0, -sh_side/2.0)
        cr.paint()
        cr.restore()

        cr.save()
        cr.translate(win.settings_table_right_x, win.settings_table_right_y)
        cr.scale(-win.settings_table_right_w / sw, win.settings_table_right_h / sh_side)
        cr.set_source_surface(win.table_side_surface, -sw/2.0, -sh_side/2.0)
        cr.paint()
        cr.restore()

    if win.table_top_surface:
        tw, th_top = win.table_top_pb.get_width(), win.table_top_pb.get_height()
        cr.save()
        cr.translate(win.settings_table_top_x, win.settings_table_top_y)
        cr.scale(win.settings_table_top_w / tw, win.settings_table_top_h / th_top)
        cr.set_source_surface(win.table_top_surface, -tw/2.0, -th_top/2.0)
        cr.paint()
        cr.restore()

    if win.table_bottom_surface:
        bw, bh_bot = win.table_bottom_pb.get_width(), win.table_bottom_pb.get_height()
        cr.save()
        cr.translate(win.settings_table_bottom_x, win.settings_table_bottom_y)
        cr.scale(win.settings_table_bottom_w / bw, win.settings_table_bottom_h / bh_bot)
        cr.set_source_surface(win.table_bottom_surface, -bw/2.0, -bh_bot/2.0)
        cr.paint()
        cr.restore()

    if win.big_font and win.big_font.surface:
        win.big_font.draw_text(cr, "My Levels", win.settings_title_x, win.settings_title_y, win.settings_title_size, align="center")
    else:
        cr.save()
        cr.select_font_face("Sans", cairo.FontSlant.NORMAL, cairo.FontWeight.BOLD)
        cr.set_font_size(win.settings_title_size)
        cr.set_source_rgb(1.0, 1.0, 1.0)
        ext = cr.text_extents("My Levels")
        cr.move_to(win.settings_title_x - ext.width/2.0, win.settings_title_y + ext.height/2.0)
        cr.show_text("My Levels")
        cr.restore()

    if win.arrow_01_surface:
        cr.save()
        cr.translate(win.settings_close_x, win.settings_close_y)
        scale_val = win.my_levels_btn_back.current_scale * 0.563
        cs_w_orig = win.arrow_01_pb.get_width()
        if cs_w_orig <= 80.0:
            scale_val *= 2.0
        cr.scale(scale_val, scale_val)
        cr.set_source_surface(win.arrow_01_surface, -cs_w_orig/2.0, -win.arrow_01_pb.get_height()/2.0)
        cr.paint()
        cr.restore()

    cr.save()
    cr.translate(win.new_btn_x, win.new_btn_y)
    cr.scale(win.my_levels_btn_new.current_scale * win.new_btn_scale, win.my_levels_btn_new.current_scale * win.new_btn_scale)
    if win.new_btn_surface and win.new_btn_pb:
        iw = win.new_btn_pb.get_width()
        ih = win.new_btn_pb.get_height()
        cr.set_source_surface(win.new_btn_surface, -iw/2.0, -ih/2.0)
        cr.paint()
    else:
        cr.arc(0, 0, 32, 0, 2*math.pi)
        cr.set_source_rgb(0, 0.8, 0)
        cr.fill_preserve()
        cr.set_source_rgb(0, 0, 0)
        cr.set_line_width(4)
        cr.stroke()
        cr.set_source_rgb(1, 1, 1)
        cr.set_line_width(6)
        cr.move_to(-16, 0)
        cr.line_to(16, 0)
        cr.move_to(0, -16)
        cr.line_to(0, 16)
        cr.stroke()
    cr.restore()

    cr.save()
    cr.translate(1220.0, 575.0)
    cr.scale(win.my_levels_btn_import.current_scale, win.my_levels_btn_import.current_scale)
    cr.arc(0, 0, 24, 0, 2*math.pi)
    cr.set_source_rgb(0, 0.5, 1.0)
    cr.fill_preserve()
    cr.set_source_rgb(0, 0, 0)
    cr.set_line_width(3)
    cr.stroke()
    cr.set_source_rgb(1, 1, 1)
    cr.set_line_width(4)
    cr.move_to(0, -10)
    cr.line_to(0, 10)
    cr.move_to(-8, 2)
    cr.line_to(0, 10)
    cr.line_to(8, 2)
    cr.stroke()
    cr.restore()

def draw_level_view_screen(win, cr):
    lvl = win.selected_level
    if not lvl:
        return

    if win.side_art_surface:
        cr.save()
        cr.translate(win.left_side_art_x, win.left_side_art_y)
        cr.scale(win.left_side_art_w / win.side_art_w_orig, win.left_side_art_h / win.side_art_h_orig)
        cr.set_source_surface(win.side_art_surface, 0, 0)
        cr.paint()
        cr.restore()
        
        cr.save()
        cr.translate(win.right_side_art_x, win.right_side_art_y)
        cr.scale(-win.right_side_art_w / win.side_art_w_orig, win.right_side_art_h / win.side_art_h_orig)
        cr.set_source_surface(win.side_art_surface, 0, 0)
        cr.paint()
        cr.restore()

    if win.chain_surface:
        cr.save()
        cr.translate(win.settings_chain_l_x, win.settings_chain_l_y)
        ch_w_orig = win.chain_pb.get_width()
        ch_h_orig = win.chain_pb.get_height()
        cr.scale(win.settings_chain_l_w / ch_w_orig, win.settings_chain_l_h / ch_h_orig)
        cr.set_source_surface(win.chain_surface, -ch_w_orig/2, -ch_h_orig/2)
        cr.paint()
        cr.restore()

        cr.save()
        cr.translate(win.settings_chain_r_x, win.settings_chain_r_y)
        ch_w_orig = win.chain_pb.get_width()
        ch_h_orig = win.chain_pb.get_height()
        cr.scale(win.settings_chain_r_w / ch_w_orig, win.settings_chain_r_h / ch_h_orig)
        cr.set_source_surface(win.chain_surface, -ch_w_orig/2, -ch_h_orig/2)
        cr.paint()
        cr.restore()

    cx = win.settings_table_bg_x
    cy = win.settings_table_bg_y
    panel_w = win.settings_table_bg_w
    panel_h = win.settings_table_bg_h

    cr.save()
    cr.set_source_rgba(194/255.0, 114/255.0, 62/255.0, 0.95)
    draw_rounded_rect(cr, cx - panel_w/2.0, cy - panel_h/2.0, panel_w, panel_h, 18)
    cr.fill()
    cr.restore()

    cr.save()
    cr.set_source_rgba(0.0, 0.0, 0.0, 0.3)
    draw_rounded_rect(cr, cx - panel_w/2.0 + 20, cy - panel_h/2.0 + 60, panel_w - 40, 70, 18)
    cr.fill()
    cr.restore()

    name_text = lvl.get("levelName", "Unnamed")
    if win.big_font and win.big_font.surface:
        win.big_font.draw_text(cr, name_text, cx, cy - panel_h/2.0 + 95, 45, align="center")
    else:
        cr.save()
        cr.select_font_face("Sans", cairo.FontSlant.NORMAL, cairo.FontWeight.BOLD)
        cr.set_font_size(36)
        cr.set_source_rgb(1, 1, 1)
        ext = cr.text_extents(name_text)
        cr.move_to(cx - ext.width/2.0, cy - panel_h/2.0 + 102)
        cr.show_text(name_text)
        cr.restore()

    cr.save()
    cr.set_source_rgba(0.0, 0.0, 0.0, 0.3)
    draw_rounded_rect(cr, cx - panel_w/2.0 + 20, cy - panel_h/2.0 + 150, panel_w - 40, 120, 18)
    cr.fill()
    cr.restore()

    desc_text = lvl.get("description", "")
    if not desc_text:
        desc_text = "Description [Optional]"
    
    cr.save()
    cr.select_font_face("Sans", cairo.FontSlant.NORMAL, cairo.FontWeight.NORMAL)
    cr.set_font_size(22)
    cr.set_source_rgb(1, 1, 1)
    ext = cr.text_extents(desc_text)
    cr.move_to(cx - ext.width/2.0, cy - panel_h/2.0 + 215)
    cr.show_text(desc_text)
    cr.restore()

    btn_y = cy + 60.0
    
    def draw_lv_btn(bx, label, scale, btn_type):
        cr.save()
        cr.translate(bx, btn_y)
        
        surface = None
        pb = None
        if btn_type == "edit":
            surface = win.edit_btn_surface
            pb = win.edit_btn_pb
        elif btn_type == "play":
            surface = win.play_btn2_surface
            pb = win.play_btn2_pb
        elif btn_type == "share":
            surface = win.share_btn_surface
            pb = win.share_btn_pb

        if surface and pb:
            cr.scale(scale, -scale)
            cr.rotate(math.radians(90))
            iw = pb.get_width()
            ih = pb.get_height()
            cr.set_source_surface(surface, -iw/2.0, -ih/2.0)
            cr.paint()
        else:
            cr.scale(scale, scale)
            cr.set_source_rgb(0.2, 0.6, 1.0)
            draw_rounded_rect(cr, -60, -35, 120, 70, 12)
            cr.fill_preserve()
            cr.set_source_rgb(0, 0, 0)
            cr.set_line_width(3)
            cr.stroke()
            
            cr.set_source_rgb(1, 1, 1)
            cr.select_font_face("Sans", cairo.FontSlant.NORMAL, cairo.FontWeight.BOLD)
            cr.set_font_size(24)
            ext_lbl = cr.text_extents(label)
            cr.move_to(-ext_lbl.width/2.0, ext_lbl.height/2.0)
            cr.show_text(label)
        cr.restore()

    draw_lv_btn(cx - 220, "Edit", win.level_view_btn_edit.current_scale, "edit")
    draw_lv_btn(cx, "Play", win.level_view_btn_play.current_scale, "play")
    draw_lv_btn(cx + 220, "Share", win.level_view_btn_share.current_scale, "share")

    cr.save()
    cr.translate(1230.0, 48.0)
    scale_del = win.level_view_btn_delete.current_scale
    if win.delete_btn_surface and win.delete_btn_pb:
        cr.scale(0.8 * scale_del, -0.8 * scale_del)
        cr.rotate(math.radians(90))
        iw = win.delete_btn_pb.get_width()
        ih = win.delete_btn_pb.get_height()
        cr.set_source_surface(win.delete_btn_surface, -iw/2.0, -ih/2.0)
        cr.paint()
    else:
        cr.scale(scale_del, scale_del)
        cr.set_source_rgb(0.8, 0.0, 0.0)
        cr.rectangle(-15, -15, 30, 30)
        cr.fill_preserve()
        cr.set_source_rgb(0, 0, 0)
        cr.set_line_width(2)
        cr.stroke()
        cr.set_source_rgb(1, 1, 1)
        cr.rectangle(-18, -20, 36, 5)
        cr.fill()
    cr.restore()

    if win.arrow_01_surface:
        cr.save()
        cr.translate(win.settings_close_x, win.settings_close_y)
        scale_val = win.level_view_btn_back.current_scale * 0.563
        cs_w_orig = win.arrow_01_pb.get_width()
        if cs_w_orig <= 80.0:
            scale_val *= 2.0
        cr.scale(scale_val, scale_val)
        cr.set_source_surface(win.arrow_01_surface, -cs_w_orig/2.0, -win.arrow_01_pb.get_height()/2.0)
        cr.paint()
        cr.restore()

    footer_y = cy + 175.0
    
    lengths = ["Tiny", "Short", "Medium", "Long", "XL"]
    len_text = win.time_text_override if win.time_text_override else lengths[lvl.get("levelLength", 0)]
    song_text = win.music_text_override if win.music_text_override else lvl.get("song", "Stereo Madness")
    status_text = win.info_text_override if win.info_text_override else lvl.get("status", "Unverified")

    time_font_size, time_y_pos = calculate_time_text_layout(len_text, win.time_text_size, win.time_text_y)
    music_font_size, music_y_pos = calculate_music_text_layout(song_text, win.music_text_size, win.music_text_y)
    info_font_size, info_y_pos = win.info_text_size, win.info_text_y

    if win.big_font and win.big_font.surface:
        time_w = win.big_font.get_text_width(len_text, time_font_size / win.big_font.line_height)
        music_w = win.big_font.get_text_width(song_text, music_font_size / win.big_font.line_height)
        info_w = win.big_font.get_text_width(status_text, info_font_size / win.big_font.line_height)
    else:
        time_w = len(len_text) * (time_font_size * 0.55)
        music_w = len(song_text) * (music_font_size * 0.55)
        info_w = len(status_text) * (info_font_size * 0.55)

    time_icon_w = (win.time_icon_pb.get_width() if win.time_icon_pb else 50.0) * win.time_icon_scale
    music_icon_w = (win.music_icon_pb.get_width() if win.music_icon_pb else 50.0) * win.music_icon_scale
    info_icon_w = (win.info_icon_pb.get_width() if win.info_icon_pb else 50.0) * win.info_icon_scale

    group1_w = time_icon_w + win.icon_text_gap + time_w
    group2_w = music_icon_w + win.icon_text_gap + music_w
    group3_w = info_icon_w + win.icon_text_gap + info_w

    total_footer_w = group1_w + win.music_icon_gap + group2_w + win.info_icon_gap + group3_w
    footer_start_x = cx - total_footer_w / 2.0

    g1_icon_x = footer_start_x + time_icon_w / 2.0
    g1_text_x = footer_start_x + time_icon_w + win.icon_text_gap

    if win.time_icon_surface and win.time_icon_pb:
        cr.save()
        cr.translate(g1_icon_x, footer_y)
        cr.scale(win.time_icon_scale, win.time_icon_scale)
        iw = win.time_icon_pb.get_width()
        ih = win.time_icon_pb.get_height()
        cr.set_source_surface(win.time_icon_surface, -iw/2.0, -ih/2.0)
        cr.paint()
        cr.restore()
    else:
        cr.save()
        cr.translate(g1_icon_x, footer_y)
        cr.arc(0, 0, 10, 0, 2*math.pi)
        cr.set_source_rgb(1, 1, 1)
        cr.stroke()
        cr.move_to(0, 0)
        cr.line_to(0, -6)
        cr.line_to(5, 0)
        cr.stroke()
        cr.restore()

    cr.save()
    cr.select_font_face("Sans", cairo.FontSlant.NORMAL, cairo.FontWeight.BOLD)
    cr.set_font_size(time_font_size)
    cr.set_source_rgb(1, 1, 1)
    cr.move_to(g1_text_x, footer_y + (time_y_pos - 114.0))
    cr.show_text(len_text)
    cr.restore()

    g2_start_x = footer_start_x + group1_w + win.music_icon_gap
    g2_icon_x = g2_start_x + music_icon_w / 2.0
    g2_text_x = g2_start_x + music_icon_w + win.icon_text_gap

    if win.music_icon_surface and win.music_icon_pb:
        cr.save()
        cr.translate(g2_icon_x, footer_y)
        cr.scale(win.music_icon_scale, win.music_icon_scale)
        iw = win.music_icon_pb.get_width()
        ih = win.music_icon_pb.get_height()
        cr.set_source_surface(win.music_icon_surface, -iw/2.0, -ih/2.0)
        cr.paint()
        cr.restore()
    else:
        cr.save()
        cr.translate(g2_icon_x, footer_y)
        cr.set_source_rgb(1, 1, 1)
        cr.rectangle(-6, -8, 12, 4)
        cr.fill()
        cr.move_to(4, -8)
        cr.line_to(4, 6)
        cr.arc(0, 6, 4, 0, 2*math.pi)
        cr.fill()
        cr.stroke()
        cr.restore()

    cr.save()
    cr.select_font_face("Sans", cairo.FontSlant.NORMAL, cairo.FontWeight.BOLD)
    cr.set_font_size(music_font_size)
    cr.set_source_rgb(1, 1, 1)
    cr.move_to(g2_text_x, footer_y + (music_y_pos - 114.0))
    cr.show_text(song_text)
    cr.restore()

    g3_start_x = g2_start_x + group2_w + win.info_icon_gap
    g3_icon_x = g3_start_x + info_icon_w / 2.0
    g3_text_x = g3_start_x + info_icon_w + win.icon_text_gap

    if win.info_icon_surface and win.info_icon_pb:
        cr.save()
        cr.translate(g3_icon_x, footer_y)
        cr.scale(win.info_icon_scale, win.info_icon_scale)
        iw = win.info_icon_pb.get_width()
        ih = win.info_icon_pb.get_height()
        cr.set_source_surface(win.info_icon_surface, -iw/2.0, -ih/2.0)
        cr.paint()
        cr.restore()
    else:
        cr.save()
        cr.translate(g3_icon_x, footer_y)
        cr.arc(0, 0, 10, 0, 2*math.pi)
        cr.set_source_rgb(1, 1, 1)
        cr.stroke()
        cr.select_font_face("Sans", cairo.FontSlant.NORMAL, cairo.FontWeight.BOLD)
        cr.set_font_size(12)
        cr.move_to(-2, 4)
        cr.show_text("i")
        cr.restore()

    cr.save()
    cr.select_font_face("Sans", cairo.FontSlant.NORMAL, cairo.FontWeight.BOLD)
    cr.set_font_size(info_font_size)
    cr.set_source_rgb(1, 1, 1)
    cr.move_to(g3_text_x, footer_y + (info_y_pos - 114.0))
    cr.show_text(status_text)
    cr.restore()

    sub_y = cy + 225.0
    version_text = f"Version: {lvl.get('version', 1)}"
    id_text = f"ID: {lvl.get('levelId', 'na') or 'na'}"
    
    cr.save()
    cr.select_font_face("Sans", cairo.FontSlant.NORMAL, cairo.FontWeight.BOLD)
    cr.set_font_size(20)
    cr.set_source_rgb(1.0, 0.8, 0.0)
    
    ext = cr.text_extents(version_text)
    cr.move_to(cx - 180 - ext.width/2.0, sub_y)
    cr.show_text(version_text)
    
    ext = cr.text_extents(id_text)
    cr.move_to(cx + 180 - ext.width/2.0, sub_y)
    cr.show_text(id_text)
    cr.restore()