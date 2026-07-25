import time
import math
import webbrowser
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
from home_renderer import draw_home_screen
from config import bounce_out, game_config

def bind_window_events(win):
    win.connect("key-press-event", lambda w, e: on_key_press(win, e))
    win.connect("key-release-event", lambda w, e: on_key_release(win, e))
    
    win.drawing_area.connect("draw", lambda w, cr: win_on_draw(win, cr))
    win.drawing_area.connect("button-press-event", lambda w, e: on_button_press(win, e))
    win.drawing_area.connect("button-release-event", lambda w, e: on_button_release(win, e))
    win.drawing_area.connect("motion-notify-event", lambda w, e: on_motion_notify(win, e))
    win.drawing_area.connect("scroll-event", lambda w, e: on_scroll(win, e))
    
    GLib.timeout_add(16, lambda: tick_update(win))

def win_on_draw(win, cr):
    draw_home_screen(win, cr)

def tick_update(win):
    now = time.perf_counter()
    dt_sec = now - win.last_fps_time
    win.last_fps_time = now
    
    if dt_sec > 0:
        win.fps_accum += dt_sec
        win.fps_frames += 1
        if win.fps_accum >= 0.5:
            win.current_fps = int(round(win.fps_frames / win.fps_accum))
            win.fps_accum = 0.0
            win.fps_frames = 0
            
    dt_ms = dt_sec * 1000.0

    if win.active_game_scene:
        win.active_game_scene.update(dt_ms)
        win.queue_draw()
        return True

    # Background animation & rainbow timer
    win.menu_rainbow_time += dt_sec
    win.bg_scroll_x += 25.0 * dt_sec
    win.ground_scroll_x += 120.0 * dt_sec

    # Popup animations
    if win.settings_popup_state == "opening":
        win.settings_popup_p = min(1.0, win.settings_popup_p + dt_sec * 6.0)
        if win.settings_popup_p >= 1.0:
            win.settings_popup_state = "open"
    elif win.settings_popup_state == "closing":
        win.settings_popup_p = max(0.0, win.settings_popup_p - dt_sec * 6.0)
        if win.settings_popup_p <= 0.0:
            win.settings_popup_state = "closed"
            win.settings_popup_active = False

    if win.graphics_popup_state == "opening":
        win.graphics_popup_p = min(1.0, win.graphics_popup_p + dt_sec * 6.0)
        if win.graphics_popup_p >= 1.0:
            win.graphics_popup_state = "open"
    elif win.graphics_popup_state == "closing":
        win.graphics_popup_p = max(0.0, win.graphics_popup_p - dt_sec * 6.0)
        if win.graphics_popup_p <= 0.0:
            win.graphics_popup_state = "closed"
            win.graphics_popup_active = False

    if win.newgrounds_popup_active and win.newgrounds_popup_scale < 1.0:
        win.newgrounds_popup_scale = min(1.0, win.newgrounds_popup_scale + dt_sec * 6.0)
    elif not win.newgrounds_popup_active and win.newgrounds_popup_scale > 0.0:
        win.newgrounds_popup_scale = max(0.0, win.newgrounds_popup_scale - dt_sec * 6.0)

    # Level select spring & slide transition logic
    if win.level_select_active and win.slide_state != "idle":
        if win.slide_state == "out":
            target = -1280.0 if win.slide_dir > 0 else 1280.0
            win.spring_x += (target - win.spring_x) * min(1.0, 12.0 * dt_sec)
            if abs(win.spring_x - target) < 10.0:
                win.current_level_index = win.target_level_index
                win.spring_x = 1280.0 if win.slide_dir > 0 else -1280.0
                win.slide_state = "in"
        elif win.slide_state == "in":
            win.spring_x += (0.0 - win.spring_x) * min(1.0, 12.0 * dt_sec)
            if abs(win.spring_x) < 2.0:
                win.spring_x = 0.0
                win.slide_state = "idle"

    # Transition alpha fade logic
    if win.transition_direction != 0:
        win.transition_time += dt_sec
        p = min(1.0, win.transition_time / win.transition_duration)
        if win.transition_direction == 1:
            win.transition_alpha = p
            if p >= 1.0:
                if win.transition_callback:
                    win.transition_callback()
                    win.transition_callback = None
                win.transition_direction = -1
                win.transition_time = 0.0
        elif win.transition_direction == -1:
            win.transition_alpha = 1.0 - p
            if p >= 1.0:
                win.transition_alpha = 0.0
                win.transition_direction = 0

    win.queue_draw()
    return True

def on_key_press(win, event):
    if win.active_game_scene:
        win.active_game_scene.handle_key_press(event.keyval)
        return True
    keyname = Gdk.keyval_name(event.keyval)
    if keyname == "Escape":
        if win.graphics_popup_p > 0.0:
            win.graphics_popup_state = "closing"
            win.queue_draw()
            return True
        elif win.newgrounds_popup_scale > 0.0:
            win.newgrounds_popup_active = False
            win.queue_draw()
            return True
        elif win.settings_popup_p > 0.0:
            win.settings_popup_state = "closing"
            win.queue_draw()
            return True
        elif win.level_view_active:
            win.level_view_active = False
            win.my_levels_active = True
            win.queue_draw()
            return True
        elif win.my_levels_active:
            win.swap_to_creator()
            return True
        elif win.creator_menu_active or win.level_select_active:
            win.swap_to_home()
            return True
        return True
    return False

def on_key_release(win, event):
    if win.active_game_scene:
        win.active_game_scene.handle_key_release(event.keyval)
        return True
    return False

def on_button_press(win, event):
    if win.active_game_scene:
        win.active_game_scene.handle_button_press()
        return True

    lx, ly = win.get_logical_coords(event.x, event.y)

    # --- GRAPHICS POPUP INTERACTION ---
    if win.graphics_popup_p > 0.0 and win.graphics_popup_state in ("open", "opening"):
        if (860.0 - 25 <= lx <= 860.0 + 25) and (190.0 - 25 <= ly <= 190.0 + 25):
            win.graphics_pressed_btn = "close"
            win.add_tween(win.settings_btn_close, 1.0, 0.85, 100, bounce_out)
            return True

        options = ["Low", "Medium", "High", "Auto"]
        for idx, opt in enumerate(options):
            y_pos = 260.0 + idx * 60.0
            if (500.0 <= lx <= 780.0) and (y_pos - 20.0 <= ly <= y_pos + 20.0):
                win.graphics_pressed_btn = opt
                return True
        return True

    # --- NEWGROUNDS POPUP INTERACTION ---
    if win.newgrounds_popup_scale > 0.0 and win.newgrounds_popup_active:
        if (570.0 - 82.5 <= lx <= 570.0 + 82.5) and (425.0 - 27.5 <= ly <= 425.0 + 27.5):
            win.popup_pressed_btn = "cancel"
            win.add_tween(win.popup_cancel_btn, 1.0, 0.85, 100, bounce_out)
            return True

        if (730.0 - 62.5 <= lx <= 730.0 + 62.5) and (425.0 - 27.5 <= ly <= 425.0 + 27.5):
            win.popup_pressed_btn = "open"
            win.add_tween(win.popup_open_btn, 1.0, 0.85, 100, bounce_out)
            return True
        return True

    # --- SETTINGS POPUP INTERACTION ---
    if win.settings_popup_p > 0.0 and win.settings_popup_state in ("open", "opening"):
        if (win.settings_close_x - 30 <= lx <= win.settings_close_x + 30) and (win.settings_close_y - 30 <= ly <= win.settings_close_y + 30):
            win.settings_pressed_btn = "close"
            win.add_tween(win.settings_btn_close, 1.0, 0.85, 100, bounce_out)
            return True

        buttons = [
            ("account", win.settings_account_x, win.settings_account_y, win.settings_account_w, win.settings_account_h, win.settings_btn_account),
            ("how_to_play", win.settings_how_to_play_x, win.settings_how_to_play_y, win.settings_how_to_play_w, win.settings_how_to_play_h, win.settings_btn_how_to_play),
            ("options", win.settings_options_x, win.settings_options_y, win.settings_options_w, win.settings_options_h, win.settings_btn_options),
            ("graphics", win.settings_graphics_x, win.settings_graphics_y, win.settings_graphics_w, win.settings_graphics_h, win.settings_btn_graphics),
            ("rate", win.settings_rate_x, win.settings_rate_y, win.settings_rate_w, win.settings_rate_h, win.settings_btn_rate),
            ("songs", win.settings_songs_x, win.settings_songs_y, win.settings_songs_w, win.settings_songs_h, win.settings_btn_songs),
            ("help", win.settings_help_x, win.settings_help_y, win.settings_help_w, win.settings_help_h, win.settings_btn_help)
        ]

        for b_name, bx, by, bw, bh, elem in buttons:
            if (bx - bw / 2.0 <= lx <= bx + bw / 2.0) and (by - bh / 2.0 <= ly <= by + bh / 2.0):
                win.settings_pressed_btn = b_name
                win.add_tween(elem, 1.0, 0.85, 100, bounce_out)
                return True
        return True

    # --- MY LEVELS SCREEN INTERACTION ---
    if win.my_levels_active:
        left = win.settings_table_bg_x - win.my_levels_row_w / 2.0
        top = win.settings_table_bg_y - win.settings_table_bg_h / 2.0
        table_w = win.my_levels_row_w
        table_h = win.settings_table_bg_h

        if (win.settings_close_x - 30 <= lx <= win.settings_close_x + 30) and (win.settings_close_y - 30 <= ly <= win.settings_close_y + 30):
            win.my_levels_pressed_btn = "back"
            win.add_tween(win.my_levels_btn_back, 1.0, 0.85, 100, bounce_out)
            return True

        if (win.new_btn_x - 40 <= lx <= win.new_btn_x + 40) and (win.new_btn_y - 40 <= ly <= win.new_btn_y + 40):
            win.my_levels_pressed_btn = "new"
            win.add_tween(win.my_levels_btn_new, 0.9, 0.75, 100, bounce_out)
            return True

        if left <= lx <= left + table_w and top <= ly <= top + table_h:
            for i, lvl in enumerate(win.my_levels_list):
                row_y_offset = -1.25 * i
                row_y = top + i * win.my_levels_row_h - win.my_levels_scroll_y + row_y_offset
                if row_y + win.my_levels_row_h < top or row_y > top + table_h:
                    continue

                vx = left + win.view_btn_x
                vy = row_y + win.view_btn_y
                vw = win.view_btn_w * win.view_btn_scale
                vh = win.view_btn_h * win.view_btn_scale

                if (vx - vw / 2.0 <= lx <= vx + vw / 2.0) and (vy - vh / 2.0 <= ly <= vy + vh / 2.0):
                    win.my_levels_pressed_btn = ("view", i)
                    while len(win.my_levels_view_btns) <= i:
                        from gui_elements import VirtualElement
                        win.my_levels_view_btns.append(VirtualElement("View Button", 1.0))
                    win.add_tween(win.my_levels_view_btns[i], 1.0, 0.85, 100, bounce_out)
                    return True

            win.my_levels_dragging = True
            win.my_levels_drag_start_y = ly
            win.my_levels_drag_start_offset = win.my_levels_scroll_y
            win.my_levels_drag_occurred = False
            return True

    # --- LEVEL VIEW SCREEN INTERACTION ---
    elif win.level_view_active:
        if (win.settings_close_x - 30 <= lx <= win.settings_close_x + 30) and (win.settings_close_y - 30 <= ly <= win.settings_close_y + 30):
            win.level_view_pressed_btn = "back"
            win.add_tween(win.level_view_btn_back, 1.0, 0.85, 100, bounce_out)
            return True

        cx, cy = win.settings_table_bg_x, win.settings_table_bg_y
        btn_y = cy + 60.0

        if (cx - 220 - 60 <= lx <= cx - 220 + 60) and (btn_y - 35 <= ly <= btn_y + 35):
            win.level_view_pressed_btn = "edit"
            win.add_tween(win.level_view_btn_edit, 1.1, 0.95, 100, bounce_out)
            return True

        if (cx - 60 <= lx <= cx + 60) and (btn_y - 35 <= ly <= btn_y + 35):
            win.level_view_pressed_btn = "play"
            win.add_tween(win.level_view_btn_play, 1.1, 0.95, 100, bounce_out)
            return True

        if (cx + 220 - 60 <= lx <= cx + 220 + 60) and (btn_y - 35 <= ly <= btn_y + 35):
            win.level_view_pressed_btn = "share"
            win.add_tween(win.level_view_btn_share, 1.1, 0.95, 100, bounce_out)
            return True

        if (1230.0 - 25 <= lx <= 1230.0 + 25) and (48.0 - 25 <= ly <= 48.0 + 25):
            win.level_view_pressed_btn = "delete"
            win.add_tween(win.level_view_btn_delete, 0.8, 0.65, 100, bounce_out)
            return True

    # --- LEVEL SELECT SCREEN INTERACTION ---
    elif win.level_select_active:
        card_l = win.card_x - win.card_w / 2.0
        card_r = win.card_x + win.card_w / 2.0
        card_t = win.card_y - win.card_h / 2.0
        card_b = win.card_y + win.card_h / 2.0

        if card_l <= lx <= card_r and card_t <= ly <= card_b:
            win.pressed_card = True
            win.add_tween(win.card_element, 1.0, 0.95, 100, bounce_out)
            return True

        elem = win.get_element_at(lx, ly)
        if elem:
            win.pressed_element = elem
            win.add_tween(elem, elem.scale, elem.scale * 0.85, 100, bounce_out)
            return True

    # --- CREATOR MENU INTERACTION ---
    elif win.creator_menu_active:
        elem = win.get_element_at(lx, ly)
        if elem:
            win.pressed_element = elem
            win.add_tween(elem, elem.scale, elem.scale * 0.85, 100, bounce_out)
            return True

    # --- HOME SCREEN INTERACTION ---
    else:
        elem = win.get_element_at(lx, ly)
        if elem:
            win.pressed_element = elem
            win.add_tween(elem, elem.scale, elem.scale * 0.85, 100, bounce_out)
            return True

    return True

def on_button_release(win, event):
    if win.active_game_scene:
        win.active_game_scene.handle_button_release()
        return True

    lx, ly = win.get_logical_coords(event.x, event.y)

    # --- GRAPHICS POPUP RELEASE ---
    if win.graphics_popup_p > 0.0 and getattr(win, "graphics_pressed_btn", None):
        btn = win.graphics_pressed_btn
        win.graphics_pressed_btn = None
        if btn == "close":
            win.add_tween(win.settings_btn_close, 0.85, 1.0, 100, bounce_out)
            win.graphics_popup_state = "closing"
        elif btn in ("Low", "Medium", "High", "Auto"):
            game_config.graphics_quality = btn
            win.check_and_load_assets()
        win.queue_draw()
        return True

    # --- NEWGROUNDS POPUP RELEASE ---
    if win.newgrounds_popup_scale > 0.0 and getattr(win, "popup_pressed_btn", None):
        btn = win.popup_pressed_btn
        win.popup_pressed_btn = None
        if btn == "cancel":
            win.add_tween(win.popup_cancel_btn, 0.85, 1.0, 100, bounce_out)
            win.newgrounds_popup_active = False
        elif btn == "open":
            win.add_tween(win.popup_open_btn, 0.85, 1.0, 100, bounce_out)
            win.newgrounds_popup_active = False
            webbrowser.open("https://www.newgrounds.com/audio")
        win.queue_draw()
        return True

    # --- SETTINGS POPUP RELEASE ---
    if win.settings_popup_p > 0.0 and getattr(win, "settings_pressed_btn", None):
        btn = win.settings_pressed_btn
        win.settings_pressed_btn = None
        if btn == "close":
            win.add_tween(win.settings_btn_close, 0.85, 1.0, 100, bounce_out)
            win.settings_popup_state = "closing"
        elif btn == "graphics":
            win.add_tween(win.settings_btn_graphics, 0.85, 1.0, 100, bounce_out)
            win.graphics_popup_active = True
            win.graphics_popup_state = "opening"
            win.graphics_popup_p = 0.01
        elif btn == "account":
            win.add_tween(win.settings_btn_account, 0.85, 1.0, 100, bounce_out)
        elif btn == "how_to_play":
            win.add_tween(win.settings_btn_how_to_play, 0.85, 1.0, 100, bounce_out)
        elif btn == "options":
            win.add_tween(win.settings_btn_options, 0.85, 1.0, 100, bounce_out)
        elif btn == "rate":
            win.add_tween(win.settings_btn_rate, 0.85, 1.0, 100, bounce_out)
        elif btn == "songs":
            win.add_tween(win.settings_btn_songs, 0.85, 1.0, 100, bounce_out)
        elif btn == "help":
            win.add_tween(win.settings_btn_help, 0.85, 1.0, 100, bounce_out)
        win.queue_draw()
        return True

    # --- MY LEVELS RELEASE ---
    if win.my_levels_active:
        win.my_levels_dragging = False
        if win.my_levels_pressed_btn == "back":
            win.add_tween(win.my_levels_btn_back, 0.85, 1.0, 100, bounce_out)
            win.my_levels_pressed_btn = None
            win.my_levels_active = False
            win.swap_to_creator()
            return True
        elif win.my_levels_pressed_btn == "new":
            win.add_tween(win.my_levels_btn_new, 0.75, 0.9, 100, bounce_out)
            win.my_levels_pressed_btn = None
            win.create_new_local_level()
            return True
        elif isinstance(win.my_levels_pressed_btn, tuple) and win.my_levels_pressed_btn[0] == "view":
            idx = win.my_levels_pressed_btn[1]
            if idx < len(win.my_levels_view_btns):
                win.add_tween(win.my_levels_view_btns[idx], 0.85, 1.0, 100, bounce_out)
            win.my_levels_pressed_btn = None
            if idx < len(win.my_levels_list):
                win.selected_level = win.my_levels_list[idx]
                win.my_levels_active = False
                win.level_view_active = True
                win.queue_draw()
            return True

    # --- LEVEL VIEW RELEASE ---
    elif win.level_view_active:
        btn = win.level_view_pressed_btn
        win.level_view_pressed_btn = None
        if btn == "back":
            win.add_tween(win.level_view_btn_back, 0.85, 1.0, 100, bounce_out)
            win.level_view_active = False
            win.my_levels_active = True
            win.queue_draw()
        elif btn == "edit":
            win.add_tween(win.level_view_btn_edit, 0.95, 1.1, 100, bounce_out)
            win.prompt_edit_level_text("Edit Level Name", "levelName")
        elif btn == "play":
            win.add_tween(win.level_view_btn_play, 0.95, 1.1, 100, bounce_out)
            win.start_gameplay_custom_level()
        elif btn == "share":
            win.add_tween(win.level_view_btn_share, 0.95, 1.1, 100, bounce_out)
            win.share_local_level_gmd()
        elif btn == "delete":
            win.add_tween(win.level_view_btn_delete, 0.65, 0.8, 100, bounce_out)
            win.delete_selected_local_level()
        return True

    # --- LEVEL SELECT CARD RELEASE ---
    if win.level_select_active and win.pressed_card:
        win.pressed_card = False
        win.add_tween(win.card_element, 0.95, 1.0, 100, bounce_out)
        win.selected_level = None
        win.start_gameplay()
        return True

    # --- GENERAL ELEMENT RELEASE ---
    if win.pressed_element:
        elem = win.pressed_element
        win.pressed_element = None
        win.add_tween(elem, elem.current_scale, elem.scale, 100, bounce_out)

        # Creator screen actions
        if win.creator_menu_active:
            if elem == win.creator_back_btn:
                win.swap_to_home()
            elif elem.name.lower() in ("create", "create button", "createbtn_001", "gj_createbtn_001"):
                win.open_my_levels()
            win.reposition_creator_elements()
            return True

        # Home screen actions
        if elem.name == "Creator Button":
            win.swap_to_creator()
        elif elem.name == "Play Button":
            win.swap_to_level_select()
        elif elem.name in ("Options (Settings)", "Options"):
            win.settings_popup_active = True
            win.settings_popup_state = "opening"
            win.settings_popup_p = 0.01
        elif elem.name == "Newgrounds":
            win.newgrounds_popup_active = True
            win.newgrounds_popup_scale = 0.01
        elif elem.name == "LS Back Button":
            win.swap_to_home()
        elif elem.name == "LS Arrow Left":
            win.switch_level(-1)
        elif elem.name == "LS Arrow Right":
            win.switch_level(1)

    return True

def on_motion_notify(win, event):
    if win.my_levels_active and win.my_levels_dragging:
        lx, ly = win.get_logical_coords(event.x, event.y)
        dy = ly - win.my_levels_drag_start_y
        if abs(dy) > 3.0:
            win.my_levels_drag_occurred = True
        win.my_levels_scroll_y = max(win.my_levels_min_scroll_y, win.my_levels_drag_start_offset - dy)
        win.queue_draw()
        return True
    return False

def on_scroll(win, event):
    if win.my_levels_active:
        if event.direction == Gdk.ScrollDirection.UP:
            win.my_levels_scroll_y = max(win.my_levels_min_scroll_y, win.my_levels_scroll_y - 40.0)
        elif event.direction == Gdk.ScrollDirection.DOWN:
            win.my_levels_scroll_y += 40.0
        win.queue_draw()
        return True
    return False