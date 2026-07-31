import time
import math
import webbrowser
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
from home_renderer import draw_home_screen
from config import bounce_out, game_config, LEVELS

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

    # Background animation
    win.menu_rainbow_time += dt_sec
    win.bg_scroll_x += 25.0 * dt_sec
    win.ground_scroll_x += 120.0 * dt_sec

    # Popups
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

    # 1:1 Phaser Spring-Mass-Damper Physics for Level Selection
    if win.level_select_active and not win.is_dragging_level:
        card_w = win.card_w
        slide_dist = card_w - 200.0  # 1:1 match with game-scene.txt (cardW - 200)
        
        if win.slide_state == "out":
            target = -win.slide_dir * slide_dist
            slide_out_speed = slide_dist * 14.0 + getattr(win, "slide_speed_boost", 0.0)
            
            win.spring_x += (-win.slide_dir) * slide_out_speed * dt_sec
            
            if (win.slide_dir > 0 and win.spring_x <= target) or (win.slide_dir < 0 and win.spring_x >= target):
                win.current_level_index = win.target_level_index
                win.slide_state = "in"
                win.spring_x = win.slide_dir * slide_dist
                win.spring_velocity = (-win.slide_dir) * (slide_dist * 6.0)

        elif win.slide_state in ("in", "snap"):
            tension = 300.0  # 1:1 match with game-scene.txt
            friction = 15.0  # 1:1 match with game-scene.txt
            force = -tension * win.spring_x - friction * win.spring_velocity
            win.spring_velocity += force * dt_sec
            win.spring_x += win.spring_velocity * dt_sec
            
            if abs(win.spring_x) < 1.0 and abs(win.spring_velocity) < 15.0:
                win.spring_x = 0.0
                win.spring_velocity = 0.0
                win.slide_state = "idle"

    # Transition alpha fade
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
    elif win.level_select_active:
        if keyname in ("Left", "a", "A"):
            win.switch_level(-1)
            return True
        elif keyname in ("Right", "d", "D"):
            win.switch_level(1)
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

    # --- GRAPHICS POPUP ---
    if win.graphics_popup_p > 0.0 and win.graphics_popup_state in ("open", "opening"):
        if (860.0 - 25 <= lx <= 860.0 + 25) and (190.0 - 25 <= ly <= 190.0 + 25):
            win.graphics_pressed_btn = "close"
            win.add_tween(win.settings_btn_close, 1.0, 1.26, 300, bounce_out)
            return True

        options = ["Low", "Medium", "High", "Auto"]
        for idx, opt in enumerate(options):
            y_pos = 260.0 + idx * 60.0
            if (500.0 <= lx <= 780.0) and (y_pos - 20.0 <= ly <= y_pos + 20.0):
                win.graphics_pressed_btn = opt
                return True
        return True

    # --- NEWGROUNDS POPUP ---
    if win.newgrounds_popup_scale > 0.0 and win.newgrounds_popup_active:
        if (570.0 - 82.5 <= lx <= 570.0 + 82.5) and (425.0 - 27.5 <= ly <= 425.0 + 27.5):
            win.popup_pressed_btn = "cancel"
            win.add_tween(win.popup_cancel_btn, 1.0, 1.26, 300, bounce_out)
            return True

        if (730.0 - 62.5 <= lx <= 730.0 + 62.5) and (425.0 - 27.5 <= ly <= 425.0 + 27.5):
            win.popup_pressed_btn = "open"
            win.add_tween(win.popup_open_btn, 1.0, 1.26, 300, bounce_out)
            return True
        return True

    # --- SETTINGS POPUP ---
    if win.settings_popup_p > 0.0 and win.settings_popup_state in ("open", "opening"):
        if (win.settings_close_x - 30 <= lx <= win.settings_close_x + 30) and (win.settings_close_y - 30 <= ly <= win.settings_close_y + 30):
            win.settings_pressed_btn = "close"
            win.add_tween(win.settings_btn_close, 1.0, 1.26, 300, bounce_out)
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
                win.add_tween(elem, 1.0, 1.26, 300, bounce_out)
                return True
        return True

    # --- MY LEVELS SCREEN ---
    if win.my_levels_active:
        left = win.settings_table_bg_x - win.my_levels_row_w / 2.0
        top = win.settings_table_bg_y - win.settings_table_bg_h / 2.0
        table_w = win.my_levels_row_w
        table_h = win.settings_table_bg_h

        if (win.settings_close_x - 30 <= lx <= win.settings_close_x + 30) and (win.settings_close_y - 30 <= ly <= win.settings_close_y + 30):
            win.my_levels_pressed_btn = "back"
            win.add_tween(win.my_levels_btn_back, 1.0, 1.26, 300, bounce_out)
            return True

        if (win.new_btn_x - 40 <= lx <= win.new_btn_x + 40) and (win.new_btn_y - 40 <= ly <= win.new_btn_y + 40):
            win.my_levels_pressed_btn = "new"
            win.add_tween(win.my_levels_btn_new, 0.9, 0.9 * 1.26, 300, bounce_out)
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
                    win.add_tween(win.my_levels_view_btns[i], 1.0, 1.26, 300, bounce_out)
                    return True

            win.my_levels_dragging = True
            win.my_levels_drag_start_y = ly
            win.my_levels_drag_start_offset = win.my_levels_scroll_y
            win.my_levels_drag_occurred = False
            return True

    # --- LEVEL VIEW SCREEN ---
    elif win.level_view_active:
        if (win.settings_close_x - 30 <= lx <= win.settings_close_x + 30) and (win.settings_close_y - 30 <= ly <= win.settings_close_y + 30):
            win.level_view_pressed_btn = "back"
            win.add_tween(win.level_view_btn_back, 1.0, 1.26, 300, bounce_out)
            return True

        cx, cy = win.settings_table_bg_x, win.settings_table_bg_y
        btn_y = cy + 60.0

        if (cx - 220 - 60 <= lx <= cx - 220 + 60) and (btn_y - 35 <= ly <= btn_y + 35):
            win.level_view_pressed_btn = "edit"
            win.add_tween(win.level_view_btn_edit, 1.1, 1.1 * 1.26, 300, bounce_out)
            return True

        if (cx - 60 <= lx <= cx + 60) and (btn_y - 35 <= ly <= btn_y + 35):
            win.level_view_pressed_btn = "play"
            win.add_tween(win.level_view_btn_play, 1.1, 1.1 * 1.26, 300, bounce_out)
            return True

        if (cx + 220 - 60 <= lx <= cx + 220 + 60) and (btn_y - 35 <= ly <= btn_y + 35):
            win.level_view_pressed_btn = "share"
            win.add_tween(win.level_view_btn_share, 1.1, 1.1 * 1.26, 300, bounce_out)
            return True

        if (1230.0 - 25 <= lx <= 1230.0 + 25) and (48.0 - 25 <= ly <= 48.0 + 25):
            win.level_view_pressed_btn = "delete"
            win.add_tween(win.level_view_btn_delete, 0.8, 0.8 * 1.26, 300, bounce_out)
            return True

    # --- LEVEL SELECT SCREEN ---
    elif win.level_select_active:
        elem = win.get_element_at(lx, ly)
        if elem:
            win.pressed_element = elem
            win.add_tween(elem, elem.scale, elem.scale * 1.26, 300, bounce_out)
            return True

        # Screen-wide level drag tracking
        win.level_select_touch_down = True
        win.drag_start_x = lx
        win.drag_start_y_val = ly
        win.last_mouse_x = lx
        win.is_dragging_level = False
        win.velocity_samples = []

        card_l = win.card_x - win.card_w / 2.0
        card_r = win.card_x + win.card_w / 2.0
        card_t = win.card_y - win.card_h / 2.0
        card_b = win.card_y + win.card_h / 2.0

        if card_l <= lx <= card_r and card_t <= ly <= card_b:
            win.pressed_card = True
            win.add_tween(win.card_element, 1.0, 1.26, 300, bounce_out)
        else:
            win.pressed_card = False

        return True

    # --- CREATOR / HOME MENU ---
    else:
        elem = win.get_element_at(lx, ly)
        if elem:
            win.pressed_element = elem
            win.add_tween(elem, elem.scale, elem.scale * 1.26, 300, bounce_out)
            return True

    return True

def on_button_release(win, event):
    if win.active_game_scene:
        win.active_game_scene.handle_button_release()
        return True

    lx, ly = win.get_logical_coords(event.x, event.y)

    # Helper function for instant scale reset on pointerup (1:1 with Phaser)
    def instant_reset(elem, base_scale):
        if elem:
            elem.stop_tween()
            elem.current_scale = base_scale

    # --- GRAPHICS POPUP RELEASE ---
    if win.graphics_popup_p > 0.0 and getattr(win, "graphics_pressed_btn", None):
        btn = win.graphics_pressed_btn
        win.graphics_pressed_btn = None
        if btn == "close":
            instant_reset(win.settings_btn_close, 1.0)
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
            instant_reset(win.popup_cancel_btn, 1.0)
            win.newgrounds_popup_active = False
        elif btn == "open":
            instant_reset(win.popup_open_btn, 1.0)
            win.newgrounds_popup_active = False
            webbrowser.open("https://www.newgrounds.com/audio")
        win.queue_draw()
        return True

    # --- SETTINGS POPUP RELEASE ---
    if win.settings_popup_p > 0.0 and getattr(win, "settings_pressed_btn", None):
        btn = win.settings_pressed_btn
        win.settings_pressed_btn = None
        buttons_map = {
            "close": (win.settings_btn_close, 1.0),
            "account": (win.settings_btn_account, 1.0),
            "how_to_play": (win.settings_btn_how_to_play, 1.0),
            "options": (win.settings_btn_options, 1.0),
            "graphics": (win.settings_btn_graphics, 1.0),
            "rate": (win.settings_btn_rate, 1.0),
            "songs": (win.settings_btn_songs, 1.0),
            "help": (win.settings_btn_help, 1.0)
        }
        if btn in buttons_map:
            instant_reset(buttons_map[btn][0], buttons_map[btn][1])

        if btn == "close":
            win.settings_popup_state = "closing"
        elif btn == "graphics":
            win.graphics_popup_active = True
            win.graphics_popup_state = "opening"
            win.graphics_popup_p = 0.01
        win.queue_draw()
        return True

    # --- MY LEVELS RELEASE ---
    if win.my_levels_active:
        win.my_levels_dragging = False
        if win.my_levels_pressed_btn == "back":
            instant_reset(win.my_levels_btn_back, 1.0)
            win.my_levels_pressed_btn = None
            win.my_levels_active = False
            win.swap_to_creator()
            return True
        elif win.my_levels_pressed_btn == "new":
            instant_reset(win.my_levels_btn_new, 0.9)
            win.my_levels_pressed_btn = None
            win.create_new_local_level()
            return True
        elif isinstance(win.my_levels_pressed_btn, tuple) and win.my_levels_pressed_btn[0] == "view":
            idx = win.my_levels_pressed_btn[1]
            if idx < len(win.my_levels_view_btns):
                instant_reset(win.my_levels_view_btns[idx], 1.0)
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
            instant_reset(win.level_view_btn_back, 1.0)
            win.level_view_active = False
            win.my_levels_active = True
            win.queue_draw()
        elif btn == "edit":
            instant_reset(win.level_view_btn_edit, 1.1)
            win.prompt_edit_level_text("Edit Level Name", "levelName")
        elif btn == "play":
            instant_reset(win.level_view_btn_play, 1.1)
            win.start_gameplay_custom_level()
        elif btn == "share":
            instant_reset(win.level_view_btn_share, 1.1)
            win.share_local_level_gmd()
        elif btn == "delete":
            instant_reset(win.level_view_btn_delete, 0.8)
            win.delete_selected_local_level()
        return True

    # --- LEVEL SELECT SCREEN RELEASE ---
    if win.level_select_active and getattr(win, "level_select_touch_down", False):
        win.level_select_touch_down = False
        
        if win.pressed_card:
            win.pressed_card = False
            instant_reset(win.card_element, 1.0)
            
        was_dragging = win.is_dragging_level
        total_dx = lx - win.drag_start_x
        win.is_dragging_level = False
        
        avg_vel = (sum(win.velocity_samples) / len(win.velocity_samples)) if win.velocity_samples else 0.0
        drag_threshold = win.card_w * 0.18

        if was_dragging and (abs(total_dx) > drag_threshold or abs(avg_vel) > 150.0):
            # Dragged left -> Next Level (+1), Dragged right -> Prev Level (-1)
            direction = 1 if total_dx < 0 else -1
            win.switch_level(direction, initial_velocity=avg_vel)
            return True
        elif was_dragging:
            win.slide_state = "snap"
            win.spring_velocity = avg_vel
            return True
        else:
            # Clicked without dragging! Check if click started on the Card -> Start Level
            card_l = win.card_x - win.card_w / 2.0
            card_r = win.card_x + win.card_w / 2.0
            card_t = win.card_y - win.card_h / 2.0
            card_b = win.card_y + win.card_h / 2.0
            if card_l <= win.drag_start_x <= card_r and card_t <= win.drag_start_y_val <= card_b:
                win.selected_level = None
                win.start_gameplay()
            return True

    # --- GENERAL ELEMENT RELEASE ---
    if win.pressed_element:
        elem = win.pressed_element
        win.pressed_element = None
        instant_reset(elem, elem.scale)

        if win.creator_menu_active:
            if elem == win.creator_back_btn:
                win.swap_to_home()
            elif elem.name.lower() in ("create", "create button", "createbtn_001", "gj_createbtn_001"):
                win.open_my_levels()
            win.reposition_creator_elements()
            return True

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
    lx, ly = win.get_logical_coords(event.x, event.y)
    
    # --- POINTEROUT BOUNDS CHECK (Smooth release only on drag-off) ---
    if win.pressed_element:
        elem = win.pressed_element
        if elem.name == "LS Arrow Left":
            w, h = win.nav_arrow_left_w, win.nav_arrow_left_h
        elif elem.name == "LS Arrow Right":
            w, h = win.nav_arrow_right_w, win.nav_arrow_right_h
        else:
            w, h = elem.half_w * 2.0 * elem.scale, elem.half_h * 2.0 * elem.scale
            
        if not (elem.x - w / 2.0 <= lx <= elem.x + w / 2.0 and elem.y - h / 2.0 <= ly <= elem.y + h / 2.0):
            win.pressed_element = None
            win.add_tween(elem, elem.current_scale, elem.scale, 400, bounce_out)

    if getattr(win, "settings_pressed_btn", None):
        btn_name = win.settings_pressed_btn
        buttons_map = {
            "close": (win.settings_close_x, win.settings_close_y, 60, 60, win.settings_btn_close),
            "account": (win.settings_account_x, win.settings_account_y, win.settings_account_w, win.settings_account_h, win.settings_btn_account),
            "how_to_play": (win.settings_how_to_play_x, win.settings_how_to_play_y, win.settings_how_to_play_w, win.settings_how_to_play_h, win.settings_btn_how_to_play),
            "options": (win.settings_options_x, win.settings_options_y, win.settings_options_w, win.settings_options_h, win.settings_btn_options),
            "graphics": (win.settings_graphics_x, win.settings_graphics_y, win.settings_graphics_w, win.settings_graphics_h, win.settings_btn_graphics),
            "rate": (win.settings_rate_x, win.settings_rate_y, win.settings_rate_w, win.settings_rate_h, win.settings_btn_rate),
            "songs": (win.settings_songs_x, win.settings_songs_y, win.settings_songs_w, win.settings_songs_h, win.settings_btn_songs),
            "help": (win.settings_help_x, win.settings_help_y, win.settings_help_w, win.settings_help_h, win.settings_btn_help)
        }
        if btn_name in buttons_map:
            bx, by, bw, bh, elem = buttons_map[btn_name]
            if not (bx - bw/2.0 <= lx <= bx + bw/2.0 and by - bh/2.0 <= ly <= by + bh/2.0):
                win.settings_pressed_btn = None
                win.add_tween(elem, elem.current_scale, 1.0, 400, bounce_out)

    if getattr(win, "popup_pressed_btn", None):
        btn_name = win.popup_pressed_btn
        if btn_name == "cancel" and not (570.0 - 82.5 <= lx <= 570.0 + 82.5 and 425.0 - 27.5 <= ly <= 425.0 + 27.5):
            win.popup_pressed_btn = None
            win.add_tween(win.popup_cancel_btn, win.popup_cancel_btn.current_scale, 1.0, 400, bounce_out)
        elif btn_name == "open" and not (730.0 - 62.5 <= lx <= 730.0 + 62.5 and 425.0 - 27.5 <= ly <= 425.0 + 27.5):
            win.popup_pressed_btn = None
            win.add_tween(win.popup_open_btn, win.popup_open_btn.current_scale, 1.0, 400, bounce_out)

    if getattr(win, "graphics_pressed_btn", None):
        btn_name = win.graphics_pressed_btn
        if btn_name == "close" and not (860.0 - 25 <= lx <= 860.0 + 25 and 190.0 - 25 <= ly <= 190.0 + 25):
            win.graphics_pressed_btn = None
            win.add_tween(win.settings_btn_close, win.settings_btn_close.current_scale, 1.0, 400, bounce_out)

    # --- SCREEN-WIDE LEVEL DRAGGING & VELOCITY TRACKING ---
    if win.level_select_active and getattr(win, "level_select_touch_down", False):
        dx = lx - win.drag_start_x
        frame_delta = lx - win.last_mouse_x
        win.last_mouse_x = lx
        
        win.velocity_samples.append(frame_delta * 60.0)
        if len(win.velocity_samples) > 5:
            win.velocity_samples.pop(0)

        if not win.is_dragging_level and abs(dx) > 12.0:
            win.is_dragging_level = True
            if win.pressed_card:
                win.add_tween(win.card_element, win.card_element.current_scale, 1.0, 200, bounce_out)

        if win.is_dragging_level:
            win.spring_x = dx
            win.queue_draw()
            return True

    if win.my_levels_active and win.my_levels_dragging:
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