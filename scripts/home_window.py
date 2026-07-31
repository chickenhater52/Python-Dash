import os
import time
import math
import traceback
import json
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf
import cairo

from config import LEVELS, LEVEL_COLORS, load_uhd_pixbuf, pixbuf_to_surface, game_config, find_asset_path
from font import BMFont
from gui_elements import ScreenElement, VirtualElement
from layout_config import layout_config
from controls import GDControlsWindow
import level_decoder

class GDHomeScreen(Gtk.Window):
    def __init__(self, controls_win=None):
        Gtk.Window.__init__(self, title="Geometry Dash Web Port")
        self.set_default_size(1280, 720)
        self.set_resizable(True)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.controls_win = controls_win
        self.overlay_opacity = 0.0
        self.overlay_text = "Drag & Drop Image Here to Add Overlay"
        self.bg_surface = None
        self.bg_scroll_x = 0.0
        self.menu_rainbow_time = 0.0
        self.is_fullscreen = False
        
        self.colored_bg_surface = None
        self.colored_ground_surface = None
        
        self.zoom = 1.0
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.mouse_x = 640.0
        self.mouse_y = 360.0
        self.last_fps_time = time.perf_counter()
        self.fps_accum = 0.0
        self.fps_frames = 0
        self.current_fps = 0
        self.level_select_active = False
        self.creator_menu_active = False
        self.active_game_scene = None
        self.my_levels_active = False
        self.level_view_active = False
        
        self.current_level_index = 0
        self.target_level_index = 0
        self.spring_x = 0.0
        self.spring_velocity = 0.0
        self.slide_state = "idle"
        self.slide_dir = 0
        self.slide_speed_boost = 0.0
        self.transition_alpha = 0.0
        self.transition_direction = 0
        self.transition_time = 0.0
        self.transition_duration = 0.15
        self.transition_callback = None
        self.is_dragging_level = False
        self.drag_start_x = 0.0
        self.drag_start_offset = 0.0
        self.last_mouse_x = 0.0
        self.velocity_samples = []
        
        level_decoder.ensure_levels_directory()
        self.available_levels = level_decoder.list_local_levels()

        self.ground_x_offset = layout_config.ground_x_offset
        self.ground_y = layout_config.ground_y      
        self.ground_y_level_select = layout_config.ground_y_level_select
        self.ground_tile_scale = layout_config.ground_tile_scale 
        self.ground_scroll_x = 0.0
        self.bg_y_offset = layout_config.bg_y_offset
        self.floor_line_width = layout_config.floor_line_width
        
        self.dot_size = layout_config.dot_size
        self.dot_x = layout_config.dot_x
        self.dot_y = layout_config.dot_y
        self.dot_spacing = layout_config.dot_spacing

        self.newgrounds_popup_active = False
        self.newgrounds_popup_scale = 0.0
        self.popup_anim_time = 0.0
        self.popup_anim_duration = 0.66
        self.popup_speed_multiplier = 1.0
        self.popup_pressed_btn = None
        self.popup_title = "Newgrounds"
        self.popup_body_line1 = "Visit Newgrounds to find awesome"
        self.popup_body_line2 = "music?"
        self.popup_cancel_lbl = "Cancel"
        self.popup_open_lbl = "Ok"
        self.popup_width = 460.0
        self.popup_height = 240.0
        self.popup_cancel_btn = VirtualElement("Popup Cancel", 1.0)
        self.popup_open_btn = VirtualElement("Popup Open", 1.0)

        self.settings_popup_active = False
        self.settings_popup_state = "closed"
        self.settings_popup_p = 0.0
        self.settings_pressed_btn = None
        self.settings_btn_account = VirtualElement("Settings Account", 1.0)
        self.settings_btn_how_to_play = VirtualElement("Settings How To Play", 1.0)
        self.settings_btn_options = VirtualElement("Settings Options", 1.0)
        self.settings_btn_graphics = VirtualElement("Settings Graphics", 1.0)
        self.settings_btn_rate = VirtualElement("Settings Rate", 1.0)
        self.settings_btn_songs = VirtualElement("Settings Songs", 1.0)
        self.settings_btn_help = VirtualElement("Settings Help", 1.0)
        self.settings_btn_close = VirtualElement("Settings Close", 1.0)

        self.creator_back_btn = VirtualElement("Creator Back", 1.0)
        self.creator_bg_gradient = cairo.LinearGradient(0, 0, 0, 720)
        self.creator_bg_gradient.add_color_stop_rgb(0.00, 0.0, 101.0/255.0, 1.0)
        self.creator_bg_gradient.add_color_stop_rgb(1.00, 1.0/255.0, 44.0/255.0, 113.0/255.0)

        self.creator_sideart_tl_x = layout_config.creator_sideart_tl_x
        self.creator_sideart_tl_y = layout_config.creator_sideart_tl_y
        self.creator_sideart_tl_rot = layout_config.creator_sideart_tl_rot
        self.creator_sideart_tl_mirror_x = layout_config.creator_sideart_tl_mirror_x
        self.creator_sideart_tl_mirror_y = layout_config.creator_sideart_tl_mirror_y

        self.creator_sideart_bl_x = layout_config.creator_sideart_bl_x
        self.creator_sideart_bl_y = layout_config.creator_sideart_bl_y
        self.creator_sideart_bl_rot = layout_config.creator_sideart_bl_rot
        self.creator_sideart_bl_mirror_x = layout_config.creator_sideart_bl_mirror_x
        self.creator_sideart_bl_mirror_y = layout_config.creator_sideart_bl_mirror_y

        self.creator_btn_names = [
            "GJ_createBtn_001.png", "GJ_savedBtn_001.png", "GJ_highscoreBtn_001.png",
            "GJ_challengeBtn_001.png", "GJ_versusBtn_001.png", "GJ_mapBtn_001.png",
            "GJ_dailyBtn_001.png", "GJ_weeklyBtn_001.png", "GJ_eventBtn_001.png",
            "GJ_gauntletsBtn_001.png", "GJ_featuredBtn_001.png", "GJ_listsBtn_001.png",
            "GJ_pathsBtn_001.png", "GJ_mapPacksBtn_001.png", "GJ_searchBtn_001.png",
        ]

        for filename in self.creator_btn_names:
            name_key = filename.replace("GJ_", "").replace("Btn_001.png", "").lower()
            setattr(self, f"creator_{name_key}_x", getattr(layout_config, f"creator_{name_key}_x"))
            setattr(self, f"creator_{name_key}_y", getattr(layout_config, f"creator_{name_key}_y"))
            setattr(self, f"creator_{name_key}_scale", getattr(layout_config, f"creator_{name_key}_scale"))

        self.creator_elements = []
        for idx, filename in enumerate(self.creator_btn_names):
            name = filename.replace("GJ_", "").replace("Btn_001.png", "")
            elem = ScreenElement(name, filename, 0, 0, 1.0)
            elem.interactive = (filename in ("GJ_createBtn_001.png", "GJ_featuredBtn_001.png", "GJ_searchBtn_001.png"))
            self.creator_elements.append(elem)

        self.graphics_popup_active = False
        self.graphics_popup_state = "closed"
        self.graphics_popup_p = 0.0

        self.settings_table_bg_x = layout_config.settings_table_bg_x
        self.settings_table_bg_y = layout_config.settings_table_bg_y
        self.settings_table_bg_w = layout_config.settings_table_bg_w
        self.settings_table_bg_h = layout_config.settings_table_bg_h
        self.settings_table_top_x = layout_config.settings_table_top_x
        self.settings_table_top_y = layout_config.settings_table_top_y
        self.settings_table_top_w = layout_config.settings_table_top_w
        self.settings_table_top_h = layout_config.settings_table_top_h
        self.settings_table_bottom_x = layout_config.settings_table_bottom_x
        self.settings_table_bottom_y = layout_config.settings_table_bottom_y
        self.settings_table_bottom_w = layout_config.settings_table_bottom_w
        self.settings_table_bottom_h = layout_config.settings_table_bottom_h
        self.settings_table_left_x = layout_config.settings_table_left_x
        self.settings_table_left_y = layout_config.settings_table_left_y
        self.settings_table_left_w = layout_config.settings_table_left_w
        self.settings_table_left_h = layout_config.settings_table_left_h
        self.settings_table_right_x = layout_config.settings_table_right_x
        self.settings_table_right_y = layout_config.settings_table_right_y
        self.settings_table_right_w = layout_config.settings_table_right_w
        self.settings_table_right_h = layout_config.settings_table_right_h
        self.settings_chain_l_x = layout_config.settings_chain_l_x
        self.settings_chain_l_y = layout_config.settings_chain_l_y
        self.settings_chain_l_w = layout_config.settings_chain_l_w
        self.settings_chain_l_h = layout_config.settings_chain_l_h
        self.settings_chain_r_x = layout_config.settings_chain_r_x
        self.settings_chain_r_y = layout_config.settings_chain_r_y
        self.settings_chain_r_w = layout_config.settings_chain_r_w
        self.settings_chain_r_h = layout_config.settings_chain_r_h
        self.settings_close_x = layout_config.settings_close_x
        self.settings_close_y = layout_config.settings_close_y
        self.settings_close_w = layout_config.settings_close_w
        self.settings_close_h = layout_config.settings_close_h
        self.settings_title_x = layout_config.settings_title_x
        self.settings_title_y = layout_config.settings_title_y
        self.settings_title_size = layout_config.settings_title_size

        self.settings_account_x = layout_config.settings_account_x
        self.settings_account_y = layout_config.settings_account_y
        self.settings_account_w = layout_config.settings_account_w
        self.settings_account_h = layout_config.settings_account_h
        self.settings_how_to_play_x = layout_config.settings_how_to_play_x
        self.settings_how_to_play_y = layout_config.settings_how_to_play_y
        self.settings_how_to_play_w = layout_config.settings_how_to_play_w
        self.settings_how_to_play_h = layout_config.settings_how_to_play_h
        self.settings_options_x = layout_config.settings_options_x
        self.settings_options_y = layout_config.settings_options_y
        self.settings_options_w = layout_config.settings_options_w
        self.settings_options_h = layout_config.settings_options_h
        self.settings_graphics_x = layout_config.settings_graphics_x
        self.settings_graphics_y = layout_config.settings_graphics_y
        self.settings_graphics_w = layout_config.settings_graphics_w
        self.settings_graphics_h = layout_config.settings_graphics_h
        self.settings_rate_x = layout_config.settings_rate_x
        self.settings_rate_y = layout_config.settings_rate_y
        self.settings_rate_w = layout_config.settings_rate_w
        self.settings_rate_h = layout_config.settings_rate_h
        self.settings_songs_x = layout_config.settings_songs_x
        self.settings_songs_y = layout_config.settings_songs_y
        self.settings_songs_w = layout_config.settings_songs_w
        self.settings_songs_h = layout_config.settings_songs_h
        self.settings_help_x = layout_config.settings_help_x
        self.settings_help_y = layout_config.settings_help_y
        self.settings_help_w = layout_config.settings_help_w
        self.settings_help_h = layout_config.settings_help_h

        self.settings_account_font_size = layout_config.settings_account_font_size
        self.settings_how_to_play_font_size = layout_config.settings_how_to_play_font_size
        self.settings_options_font_size = layout_config.settings_options_font_size
        self.settings_graphics_font_size = layout_config.settings_graphics_font_size
        self.settings_rate_font_size = layout_config.settings_rate_font_size
        self.settings_songs_font_size = layout_config.settings_songs_font_size
        self.settings_help_font_size = layout_config.settings_help_font_size
        self.settings_button_corner_scale = layout_config.settings_button_corner_scale

        self.settings_account_text_offset_x = layout_config.settings_account_text_offset_x
        self.settings_account_text_offset_y = layout_config.settings_account_text_offset_y
        self.settings_how_to_play_text_offset_x = layout_config.settings_how_to_play_text_offset_x
        self.settings_how_to_play_text_offset_y = layout_config.settings_how_to_play_text_offset_y
        self.settings_options_text_offset_x = layout_config.settings_options_text_offset_x
        self.settings_options_text_offset_y = layout_config.settings_options_text_offset_y
        self.settings_graphics_text_offset_x = layout_config.settings_graphics_text_offset_x
        self.settings_graphics_text_offset_y = layout_config.settings_graphics_text_offset_y
        self.settings_rate_text_offset_x = layout_config.settings_rate_text_offset_x
        self.settings_rate_text_offset_y = layout_config.settings_rate_text_offset_y
        self.settings_songs_text_offset_x = layout_config.settings_songs_text_offset_x
        self.settings_songs_text_offset_y = layout_config.settings_songs_text_offset_y
        self.settings_help_text_offset_x = layout_config.settings_help_text_offset_x
        self.settings_help_text_offset_y = layout_config.settings_help_text_offset_y

        self.card_w = layout_config.card_w
        self.card_h = layout_config.card_h
        self.card_x = layout_config.card_x
        self.card_y = layout_config.card_y
        self.diff_offset_y = layout_config.diff_offset_y
        self.diff_size = layout_config.diff_size
        self.diff_icon_distance = layout_config.diff_icon_distance
        self.title_offset_x = layout_config.title_offset_x
        self.title_offset_y = layout_config.title_offset_y
        self.title_size = layout_config.title_size
        self.card_element = VirtualElement("Level Card", 1.0)
        self.pressed_card = False
        self.drag_occurred = False

        self.top_bar_visible = layout_config.top_bar_visible
        self.top_bar_x = layout_config.top_bar_x
        self.top_bar_y = layout_config.top_bar_y
        self.top_bar_w = layout_config.top_bar_w
        self.top_bar_h = layout_config.top_bar_h
        self.side_art_visible = layout_config.side_art_visible
        self.left_side_art_x = layout_config.left_side_art_x
        self.left_side_art_y = layout_config.left_side_art_y
        self.left_side_art_w = layout_config.left_side_art_w
        self.left_side_art_h = layout_config.left_side_art_h
        self.right_side_art_x = layout_config.right_side_art_x
        self.right_side_art_y = layout_config.right_side_art_y
        self.right_side_art_w = layout_config.right_side_art_w
        self.right_side_art_h = layout_config.right_side_art_h
        self.nav_arrow_left_x = layout_config.nav_arrow_left_x
        self.nav_arrow_left_y = layout_config.nav_arrow_left_y
        self.nav_arrow_left_w = layout_config.nav_arrow_left_w
        self.nav_arrow_left_h = layout_config.nav_arrow_left_h
        self.nav_arrow_right_x = layout_config.nav_arrow_right_x
        self.nav_arrow_right_y = layout_config.nav_arrow_right_y
        self.nav_arrow_right_w = layout_config.nav_arrow_right_w
        self.nav_arrow_right_h = layout_config.nav_arrow_right_h

        self.bar_norm_visible = layout_config.bar_norm_visible
        self.bar_norm_x = layout_config.bar_norm_x
        self.bar_norm_y = layout_config.bar_norm_y
        self.bar_norm_w = layout_config.bar_norm_w
        self.bar_norm_h = layout_config.bar_norm_h
        self.bar_norm_title_text = layout_config.bar_norm_title_text
        self.bar_norm_title_offset_x = layout_config.bar_norm_title_offset_x
        self.bar_norm_title_offset_y = layout_config.bar_norm_title_offset_y
        self.bar_norm_title_size = layout_config.bar_norm_title_size
        self.bar_norm_pct_offset_x = layout_config.bar_norm_pct_offset_x
        self.bar_norm_pct_offset_y = layout_config.bar_norm_pct_offset_y
        self.bar_norm_pct_size = layout_config.bar_norm_pct_size

        self.bar_pract_visible = layout_config.bar_pract_visible
        self.bar_pract_x = layout_config.bar_pract_x
        self.bar_pract_y = layout_config.bar_pract_y
        self.bar_pract_w = layout_config.bar_pract_w
        self.bar_pract_h = layout_config.bar_pract_h
        self.bar_pract_title_text = layout_config.bar_pract_title_text
        self.bar_pract_title_offset_x = layout_config.bar_pract_title_offset_x
        self.bar_pract_title_offset_y = layout_config.bar_pract_title_offset_y
        self.bar_pract_title_size = layout_config.bar_pract_title_size
        self.bar_pract_pct_offset_x = layout_config.bar_pract_pct_offset_x
        self.bar_pract_pct_offset_y = layout_config.bar_pract_pct_offset_y
        self.bar_pract_pct_size = layout_config.bar_pract_pct_size

        self.level_best_normal = [100, 84, 62, 45, 23, 11] + [0]*16
        self.level_best_practice = [100, 100, 80, 50, 0, 0] + [0]*16

        self.elements = [
            ScreenElement("Play Button", "GJ_playBtn_001.png", 640, 337.5, 0.563),
            ScreenElement("Icon Button (Garage)", "GJ_garageBtn_001.png", 392.5, 337.5, 0.563),
            ScreenElement("Creator Button", "GJ_creatorBtn_001.png", 887.5, 337.5, 0.563),
            ScreenElement("Daily Rewards Button", "GJ_dailyRewardBtn_001.png", 1190, 315, 0.563),
            ScreenElement("Chr Sel Decor", "GJ_chrSel_001.png", 280, 450, 0.563),
            ScreenElement("Lvl Edit Decor", "GJ_lvlEdit_001.png", 1000, 450, 0.563),
            ScreenElement("Main Logo", "GJ_logo_001.png", 640, 112.5, 0.563),
            ScreenElement("RobTop Logo", "RobTopLogoBig_001.png", 112.5, 664, 0.342),
            ScreenElement("Twitter", "gj_twIcon_001.png", 114.7, 596.3, 0.45),
            ScreenElement("YouTube", "gj_ytIcon_001.png", 180, 596.3, 0.45),
            ScreenElement("Facebook", "gj_fbIcon_001.png", 49.3, 596.3, 0.45),
            ScreenElement("Twitch", "gj_twitchIcon_001.png", 245.2, 596.3, 0.45),
            ScreenElement("Discord", "gj_discordIcon_001.png", 245.2, 661.5, 0.45),
            ScreenElement("Achievements", "GJ_achBtn_001.png", 447.5, 618.8, 0.563),
            ScreenElement("Options (Settings)", "GJ_optionsBtn_001.png", 573, 618.8, 0.563),
            ScreenElement("Stats", "GJ_statsBtn_001.png", 698, 618.8, 0.563),
            ScreenElement("Newgrounds", "GJ_ngBtn_001.png", 827.8, 618.8, 0.61),
            ScreenElement("More Games", "GJ_moreGamesBtn_001.png", 1183.5, 618.8, 0.506),
        ]
        
        self.nav_arrow_left = ScreenElement("LS Arrow Left", "navArrowBtn_001.png", self.nav_arrow_left_x, self.nav_arrow_left_y, 1.0)
        self.nav_arrow_right = ScreenElement("LS Arrow Right", "navArrowBtn_001.png", self.nav_arrow_right_x, self.nav_arrow_right_y, 1.0)
        
        self.ls_elements = [
            ScreenElement("LS Back Button", "GJ_arrow_01_001.png", 54.5, 49.5, 0.563),
            self.nav_arrow_left,
            self.nav_arrow_right
        ]
        self.overlay_element = ScreenElement("Custom Overlay Image", None, 640, 360, 1.0)
        
        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_size_request(1, 1) 
        self.drawing_area.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK | Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.SCROLL_MASK)

        self.my_levels_active = False
        self.level_view_active = False
        self.selected_level = None
        self.my_levels_scroll_y = 0.0
        self.my_levels_list = []
        
        self.my_levels_pressed_btn = None
        self.my_levels_dragging = False
        self.my_levels_drag_start_y = 0.0
        self.my_levels_drag_start_offset = 0.0
        self.my_levels_drag_occurred = False
        self.my_levels_view_btns = []
        
        self.my_levels_btn_back = VirtualElement("My Levels Back", 1.0)
        self.my_levels_btn_new = VirtualElement("My Levels New", 0.9)
        self.my_levels_btn_import = VirtualElement("My Levels Import", 1.0)
        
        self.level_view_active_input = None
        self.level_view_pressed_btn = None
        self.level_view_btn_back = VirtualElement("Level View Back", 1.0)
        self.level_view_btn_edit = VirtualElement("Level View Edit", 1.1)
        self.level_view_btn_play = VirtualElement("Level View Play", 1.1)
        self.level_view_btn_share = VirtualElement("Level View Share", 1.1)
        self.level_view_btn_delete = VirtualElement("Level View Delete", 0.8)

        self.time_icon_pb = None
        self.time_icon_surface = None
        self.music_icon_pb = None
        self.music_icon_surface = None
        self.info_icon_pb = None
        self.info_icon_surface = None
        self.new_btn_pb = None
        self.new_btn_surface = None
        
        self.edit_btn_pb = None
        self.edit_btn_surface = None
        self.play_btn2_pb = None
        self.play_btn2_surface = None
        self.share_btn_pb = None
        self.share_btn_surface = None
        self.delete_btn_pb = None
        self.delete_btn_surface = None

        self.time_icon_x = 41.0
        self.time_icon_y = 114.0
        self.time_icon_scale = 0.79
        
        self.time_text_x = 50.0
        self.time_text_y = 99.5
        self.time_text_size = 27.5
        
        self.music_icon_x = 150.0
        self.music_icon_y = 114.0
        self.music_icon_scale = 0.75
        
        self.music_text_x = 165.0
        self.music_text_y = 99.7
        self.music_text_size = 27.5
        
        self.info_icon_x = 380.0
        self.info_icon_y = 114.0
        self.info_icon_scale = 0.79
        
        self.info_text_x = 395.0
        self.info_text_y = 100.0
        self.info_text_size = 27.5
        
        self.level_title_x = 20.5
        self.level_title_y = 25.7
        self.level_title_size = 51.5
        
        self.new_btn_x = 1211.5
        self.new_btn_y = 651.5
        self.new_btn_scale = 1.25

        self.view_btn_x = 703.5
        self.view_btn_y = 80.0
        self.view_btn_w = 188.0
        self.view_btn_h = 90.0
        self.view_btn_scale = 1.0
        self.view_btn_corner_scale = 1.4
        self.view_btn_font_size = 59.0
        self.view_btn_text_x = -6.0
        self.view_btn_text_y = -6.0

        self.my_levels_row_w = 788.0
        self.my_levels_row_h = 158.8

        self.icon_text_gap = 2.0
        self.music_icon_gap = 23.0
        self.info_icon_gap = 24.0

        self.time_text_override = ""
        self.music_text_override = ""
        self.info_text_override = ""

        self.my_levels_min_scroll_y = 0.0
        self.my_levels_separator_thickness = 2.0

        self.arrow_01_pb = None
        self.arrow_01_surface = None
        self.arrow_03_pb = None
        self.arrow_03_surface = None

        from home_events import bind_window_events
        bind_window_events(self)

        self.add(self.drawing_area)
        self.set_can_focus(True)
        self.pressed_element = None
        
        self.check_and_load_assets()
        self.reposition_creator_elements()
        self.load_created_levels()

    def reposition_creator_elements(self):
        for elem in self.creator_elements:
            name_key = elem.name.lower()
            elem.x = getattr(self, f"creator_{name_key}_x")
            elem.y = getattr(self, f"creator_{name_key}_y")
            elem.scale = getattr(self, f"creator_{name_key}_scale")
            elem.current_scale = elem.scale
            elem.pressed = False
            elem.stop_tween()

    def kill_tweens_of(self, element):
        element.stop_tween()
        
    def add_tween(self, element, start_scale, target_scale, duration_ms, ease_func):
        element.current_scale = start_scale
        element.start_tween(target_scale, duration_ms, self.queue_draw)

    def get_quality_scale(self):
        return 1.0

    def start_scene_transition(self, callback):
        if self.transition_direction != 0:
            return
        self.transition_callback = callback
        self.transition_direction = 1
        self.transition_time = 0.0

    def swap_to_level_select(self):
        self.active_game_scene = None
        self.level_select_active = True
        self.creator_menu_active = False
        self.my_levels_active = False
        self.level_view_active = False
        self.spring_x = 0.0
        self.spring_velocity = 0.0
        self.slide_state = "idle"
        if self.controls_win:
            self.controls_win.update_popup_controls()

    def swap_to_creator(self):
        self.active_game_scene = None
        self.creator_menu_active = True
        self.level_select_active = False
        self.my_levels_active = False
        self.level_view_active = False
        self.reposition_creator_elements()
        if self.controls_win:
            self.controls_win.update_popup_controls()

    def swap_to_home(self):
        self.active_game_scene = None
        self.level_select_active = False
        self.creator_menu_active = False
        self.my_levels_active = False
        self.level_view_active = False
        if self.controls_win:
            self.controls_win.update_popup_controls()

    def switch_level(self, direction, initial_velocity=0.0):
        if self.slide_state == "out":
            self.current_level_index = self.target_level_index
        self.target_level_index = (self.current_level_index + direction) % len(LEVELS)
        self.slide_dir = direction
        self.slide_state = "out"
        if not self.is_dragging_level:
            self.spring_x = 0.0
        self.slide_speed_boost = min(1000.0, abs(initial_velocity) * 2.0)
        if self.controls_win:
            self.controls_win.update_popup_controls()

    def get_logical_coords(self, screen_x, screen_y):
        target_ratio = 16.0 / 9.0
        current_width = self.drawing_area.get_allocated_width()
        current_height = self.drawing_area.get_allocated_height()
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
        return (screen_x - x_offset) / scale_factor, (screen_y - y_offset) / scale_factor

    def get_element_at(self, lx, ly):
        if self.active_game_scene:
            return None
        world_x = (lx - self.offset_x) / self.zoom
        world_y = (ly - self.offset_y) / self.zoom
        if self.creator_menu_active:
            cx_close, cy_close = 54.5, 49.5
            cs_w_orig = self.settings_close_pb.get_width() if self.settings_close_pb else 80.0
            scale_val = self.creator_back_btn.current_scale * 0.563
            if cs_w_orig <= 80.0:
                scale_val *= 2.0
            w_close = cs_w_orig * scale_val
            if (cx_close - w_close/2 <= lx <= cx_close + w_close/2) and (cy_close - w_close/2 <= ly <= cy_close + w_close/2):
                return self.creator_back_btn
            for elem in reversed(self.creator_elements):
                if not elem.interactive:
                    continue
                w, h = elem.half_w * 2.0 * elem.scale, elem.half_h * 2.0 * elem.scale
                if (elem.x - w / 2 <= world_x <= elem.x + w / 2) and (elem.y - h / 2 <= world_y <= elem.y + h / 2):
                    return elem
            return None

        elements_to_check = self.ls_elements if self.level_select_active else self.elements
        for elem in reversed(elements_to_check):
            if elem.name in ("Main Logo", "Chr Sel Decor", "Lvl Edit Decor"):
                continue
            if elem.name == "LS Arrow Left":
                w, h = self.nav_arrow_left_w, self.nav_arrow_left_h
            elif elem.name == "LS Arrow Right":
                w, h = self.nav_arrow_right_w, self.nav_arrow_right_h
            else:
                w, h = elem.half_w * 2.0 * elem.scale, elem.half_h * 2.0 * elem.scale
            if (elem.x - w / 2 <= world_x <= elem.x + w / 2) and (elem.y - h / 2 <= world_y <= elem.y + h / 2):
                return elem
        return None

    def check_and_load_assets(self):
        quality = game_config.graphics_quality
        if quality == "Auto":
            quality = "High"

        res_bg = find_asset_path("game_bg_01_001-uhd.png")
        if os.path.exists(res_bg):
            try:
                t = GdkPixbuf.Pixbuf.new_from_file(res_bg)
                self.bg_h = int(960 * layout_config.bg_scale)
                self.bg_w = int(t.get_width() * (self.bg_h / t.get_height()))
                self.bg_surface = pixbuf_to_surface(t.scale_simple(self.bg_w, self.bg_h, GdkPixbuf.InterpType.BILINEAR))
            except Exception:
                self.bg_surface = None
        else:
            self.bg_surface = None

        for elem in self.elements + self.ls_elements + self.creator_elements:
            resolved = find_asset_path(elem.filename)
            if os.path.exists(resolved):
                try:
                    elem.pixbuf = GdkPixbuf.Pixbuf.new_from_file(resolved)
                    if quality == "Medium":
                        elem.pixbuf = elem.pixbuf.scale_simple(int(elem.pixbuf.get_width() * 2), int(elem.pixbuf.get_height() * 2), GdkPixbuf.InterpType.BILINEAR)
                    elif quality == "Low":
                        elem.pixbuf = elem.pixbuf.scale_simple(int(elem.pixbuf.get_width() * 4), int(elem.pixbuf.get_height() * 4), GdkPixbuf.InterpType.BILINEAR)
                    elem.surface = pixbuf_to_surface(elem.pixbuf)
                    elem.half_w = elem.pixbuf.get_width() / 2.0
                    elem.half_h = elem.pixbuf.get_height() / 2.0
                except Exception:
                    elem.pixbuf = None
                    elem.surface = None
                    elem.half_w = 45.0
                    elem.half_h = 45.0
            else: 
                elem.pixbuf = None
                elem.surface = None
                elem.half_w = 45.0
                elem.half_h = 45.0

        self.button_pb, self.button_surface = load_uhd_pixbuf("GJ_button_01-uhd.png")
        self.square_pb, self.square_surface = load_uhd_pixbuf("square01_001-uhd.png")
        self.bm_font = BMFont("uhd/ui/goldFont-uhd.fnt", "uhd/ui/goldFont-uhd.png")
        self.big_font = BMFont("uhd/ui/bigFont-uhd.fnt", "uhd/ui/bigFont-uhd.png")
        self.top_bar_pb, self.top_bar_surface = load_uhd_pixbuf("GJ_topBar_001.png")
        if self.top_bar_pb:
            self.top_bar_w_orig = self.top_bar_pb.get_width()
            self.top_bar_h_orig = self.top_bar_pb.get_height()
        self.side_art_pb, self.side_art_surface = load_uhd_pixbuf("GJ_sideArt_001.png")
        if self.side_art_pb:
            self.side_art_w_orig = self.side_art_pb.get_width()
            self.side_art_h_orig = self.side_art_pb.get_height()
        self.floor_line_pb, self.floor_line_surface = load_uhd_pixbuf("floorLine_01_001.png")
        if self.floor_line_pb:
            self.floor_line_w_orig = self.floor_line_pb.get_width()
            self.floor_line_h_orig = self.floor_line_pb.get_height()
        self.ground_pb, self.ground_surface = load_uhd_pixbuf("groundSquare_01_001-uhd.png")
        self.progress_bar_pb, self.progress_bar_surface = load_uhd_pixbuf("GJ_progressBar_001-uhd.png")
        if self.progress_bar_pb:
            self.progress_bar_w_orig = self.progress_bar_pb.get_width()
            self.progress_bar_h_orig = self.progress_bar_pb.get_height()
        
        self.table_bottom_pb, self.table_bottom_surface = load_uhd_pixbuf("GJ_table_bottom_001.png")
        self.table_corner_pb, self.table_corner_surface = load_uhd_pixbuf("GJ_table_corner_001.png")
        self.table_side_pb, self.table_side_surface = load_uhd_pixbuf("GJ_table_side_001.png")
        self.table_top_pb, self.table_top_surface = load_uhd_pixbuf("GJ_table_top_001.png")
        self.table_top02_pb, self.table_top02_surface = load_uhd_pixbuf("GJ_table_top02_001.png")
        self.chain_pb, self.chain_surface = load_uhd_pixbuf("chain_01_001.png")
        
        self.colored_bg_surface = None
        self.colored_ground_surface = None
        self.settings_close_pb, self.settings_close_surface = load_uhd_pixbuf("GJ_arrow_03_001.png")
        if not self.settings_close_pb:
            self.settings_close_pb, self.settings_close_surface = load_uhd_pixbuf("GJ_closeBtn_001.png")

        self.time_icon_pb, self.time_icon_surface = load_uhd_pixbuf("GJ_timeIcon_001.png")
        self.music_icon_pb, self.music_icon_surface = load_uhd_pixbuf("GJ_musicIcon_001.png")
        self.info_icon_pb, self.info_icon_surface = load_uhd_pixbuf("GJ_infoIcon_001.png")
        self.new_btn_pb, self.new_btn_surface = load_uhd_pixbuf("GJ_newBtn_001.png")
        
        self.edit_btn_pb, self.edit_btn_surface = load_uhd_pixbuf("GJ_editBtn_001.png")
        self.play_btn2_pb, self.play_btn2_surface = load_uhd_pixbuf("GJ_playBtn2_001.png")
        self.share_btn_pb, self.share_btn_surface = load_uhd_pixbuf("GJ_shareBtn_001.png")
        self.delete_btn_pb, self.delete_btn_surface = load_uhd_pixbuf("GJ_deleteBtn_001.png")

        self.arrow_01_pb, self.arrow_01_surface = load_uhd_pixbuf("GJ_arrow_01_001.png")
        self.arrow_03_pb, self.arrow_03_surface = load_uhd_pixbuf("GJ_arrow_03_001.png")

        self.diff_icons = {}
        for i in range(1, 7):
            resolved = find_asset_path(f"diffIcon_0{i}_btn_001.png")
            if os.path.exists(resolved):
                try:
                    pb = GdkPixbuf.Pixbuf.new_from_file(resolved)
                    self.diff_icons[i] = (pb, pixbuf_to_surface(pb), pb.get_width(), pb.get_height())
                except Exception:
                    pass

        self.bg_gradients = []
        for col in LEVEL_COLORS:
            grad = cairo.LinearGradient(0, 0, 0, 720)
            grad.add_color_stop_rgb(0.00, col[0], col[1], col[2])
            grad.add_color_stop_rgb(1.00, col[0] * 0.58, col[1] * 0.58, col[2] * 0.58)
            self.bg_gradients.append(grad)

    def start_gameplay(self):
        try:
            self.level_select_active = False
            self.creator_menu_active = False
            self.my_levels_active = False
            self.level_view_active = False
            
            if self.selected_level is None:
                level_num = self.current_level_index + 1
                temp_filename = f"level_{level_num}.txt"
                temp_path = os.path.join(level_decoder.LEVELS_DIR, temp_filename)
                if not os.path.exists(temp_path):
                    level_decoder.ensure_levels_directory()
            else:
                temp_filename = "level_temp.txt"
                temp_path = os.path.join(level_decoder.LEVELS_DIR, temp_filename)
                with open(temp_path, "w", encoding="utf-8") as f:
                    f.write(self.selected_level.get("levelString", ""))
            
            from game_scene import GameScene
            self.active_game_scene = GameScene(self, temp_filename)
        except Exception:
            self.active_game_scene = None
            self.level_view_active = True
            self.queue_draw()

    def return_to_level_view(self):
        self.active_game_scene = None
        self.level_view_active = True
        self.my_levels_active = False
        self.creator_menu_active = False
        self.level_select_active = False

    def load_created_levels(self):
        level_decoder.ensure_levels_directory()
        self.available_levels = level_decoder.list_local_levels()
        self.my_levels_list = []
        
        filtered_levels = [f for f in self.available_levels if f != "level_temp.txt"]
        
        for filename in filtered_levels:
            parsed = level_decoder.parse_level(filename)
            settings = parsed.get("settings", {}) if parsed else {}
            
            name = settings.get("k2", os.path.splitext(filename)[0].replace("_", " ").title())
            desc = settings.get("k3", "No description provided.")
            length_val = level_decoder.safe_int(settings.get("k23", "0"))
            song_name = settings.get("k8", "Stereo Madness")
            status_val = "Verified" if settings.get("k14") == "1" else "Unverified"
            ver_val = level_decoder.safe_int(settings.get("k16", "1"))
            level_id = settings.get("k1", "0")
            
            filepath = os.path.join(level_decoder.LEVELS_DIR, filename)
            level_string = ""
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    level_string = f.read()
            except Exception:
                pass
                
            self.my_levels_list.append({
                "filename": filename,
                "levelName": name,
                "description": desc,
                "levelLength": length_val,
                "song": song_name,
                "status": status_val,
                "version": ver_val,
                "levelId": level_id,
                "levelString": level_string
            })

    def open_my_levels(self):
        self.load_created_levels()
        self.my_levels_active = True
        self.creator_menu_active = False
        self.level_select_active = False
        self.level_view_active = False
        self.my_levels_scroll_y = 0.0
        self.queue_draw()

    def create_new_local_level(self):
        idx = 1
        while True:
            filename = f"my_level_{idx}.txt"
            filepath = os.path.join(level_decoder.LEVELS_DIR, filename)
            if not os.path.exists(filepath):
                break
            idx += 1
            
        default_content = f"kS38,1_255_2_255_3_255_6_1000,k2,My Level {idx},k3,My Description"
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(default_content)
        except Exception:
            pass
            
        self.load_created_levels()
        self.queue_draw()

    def import_local_level_gmd(self):
        dialog = Gtk.FileChooserDialog(
            title="Import GD Level",
            parent=self,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        filter_text = Gtk.FileFilter()
        filter_text.set_name("GD Level files (*.gmd, *.txt)")
        filter_text.add_pattern("*.gmd")
        filter_text.add_pattern("*.txt")
        dialog.add_filter(filter_text)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            chosen = dialog.get_filename()
            if os.path.exists(chosen):
                import shutil
                dest_name = os.path.basename(chosen)
                if not dest_name.endswith(".txt"):
                    dest_name = os.path.splitext(dest_name)[0] + ".txt"
                dest_path = os.path.join(level_decoder.LEVELS_DIR, dest_name)
                try:
                    shutil.copy(chosen, dest_path)
                    self.load_created_levels()
                except Exception:
                    pass
        dialog.destroy()
        self.queue_draw()

    def share_local_level_gmd(self):
        if not self.selected_level:
            return
        dialog = Gtk.FileChooserDialog(
            title="Export GD Level",
            parent=self,
            action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK
        )
        dialog.set_current_name(self.selected_level.get("levelName", "level") + ".gmd")
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            export_path = dialog.get_filename()
            source_path = os.path.join(level_decoder.LEVELS_DIR, self.selected_level["filename"])
            if os.path.exists(source_path):
                import shutil
                try:
                    shutil.copy(source_path, export_path)
                except Exception:
                    pass
        dialog.destroy()

    def delete_selected_local_level(self):
        if not self.selected_level:
            return
            
        dialog = Gtk.MessageDialog(
            parent=self,
            flags=Gtk.DialogFlags.MODAL,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=f"Are you sure you want to delete '{self.selected_level.get('levelName')}'?"
        )
        response = dialog.run()
        if response == Gtk.ResponseType.YES:
            filepath = os.path.join(level_decoder.LEVELS_DIR, self.selected_level["filename"])
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except Exception:
                    pass
            self.level_view_active = False
            self.my_levels_active = True
            self.selected_level = None
            self.load_created_levels()
        dialog.destroy()
        self.queue_draw()

    def start_gameplay_custom_level(self):
        self.start_gameplay()

    def prompt_edit_level_text(self, title, field):
        if not self.selected_level:
            return
        dialog = Gtk.MessageDialog(
            parent=self,
            flags=Gtk.DialogFlags.MODAL,
            message_type=Gtk.MessageType.OTHER,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text=title
        )
        entry = Gtk.Entry()
        entry.set_text(self.selected_level.get(field, ""))
        dialog.get_content_area().pack_start(entry, True, True, 10)
        dialog.show_all()
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            new_val = entry.get_text().strip()
            if new_val:
                self.selected_level[field] = new_val
                filename = self.selected_level["filename"]
                filepath = os.path.join(level_decoder.LEVELS_DIR, filename)
                if os.path.exists(filepath):
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            content = f.read()
                        
                        decompressed = level_decoder.decode_payload(content)
                        parts = decompressed.split(';')
                        settings = level_decoder.parse_settings(parts[0])
                        
                        if field == "levelName":
                            settings["k2"] = new_val
                        elif field == "description":
                            settings["k3"] = new_val
                            
                        serialized_settings = ",".join([f"{k},{v}" for k, v in settings.items()])
                        parts[0] = serialized_settings
                        updated_content = ";".join(parts)
                        
                        with open(filepath, "w", encoding="utf-8") as f:
                            f.write(updated_content)
                            
                        self.selected_level["levelString"] = updated_content
                    except Exception:
                        pass
                
                self.load_created_levels()
        dialog.destroy()
        self.queue_draw()