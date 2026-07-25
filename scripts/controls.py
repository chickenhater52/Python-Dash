import os
import urllib.parse
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf

from config import find_asset_path

class GDControlsWindow(Gtk.Window):
    def __init__(self, main_win_ref=None):
        super().__init__(title="GD External Controller")
        self.set_default_size(380, 250)
        self.set_resizable(True)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.main_win = main_win_ref
        self.updating_widgets = False

        scrolled_win = Gtk.ScrolledWindow()
        scrolled_win.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.add(scrolled_win)
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        main_box.set_border_width(15)
        scrolled_win.add(main_box)

        overlay_frame = Gtk.Frame(label="Overlay Controller")
        overlay_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        overlay_box.set_border_width(10)
        overlay_frame.add(overlay_box)
        main_box.pack_start(overlay_frame, False, False, 0)
        
        opacity_label = Gtk.Label(label="Overlay Opacity:")
        opacity_label.set_halign(Gtk.Align.START)
        overlay_box.pack_start(opacity_label, False, False, 0)
        self.opacity_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.0, 1.0, 0.05)
        self.opacity_scale.set_value(0.0)
        self.opacity_scale.connect("value-changed", self.on_opacity_changed)
        overlay_box.pack_start(self.opacity_scale, False, False, 0)
        
        self.dnd_area = Gtk.EventBox()
        dnd_frame = Gtk.Frame()
        self.dnd_label = Gtk.Label(label="Drag & Drop Image / Click to Add")
        self.dnd_label.set_size_request(-1, 80)
        dnd_frame.add(self.dnd_label)
        self.dnd_area.add(dnd_frame)
        overlay_box.pack_start(self.dnd_area, False, False, 5)
        self.dnd_area.drag_dest_set(Gtk.DestDefaults.ALL, [], Gdk.DragAction.COPY)
        self.dnd_area.drag_dest_add_uri_targets()
        self.dnd_area.connect("drag-data-received", self.on_drag_data_received)
        self.dnd_area.connect("button-press-event", self.on_dnd_click)

        self.update_popup_controls()
        self.show_all()

    def update_popup_controls(self):
        if not self.main_win:
            return
        self.updating_widgets = True
        self.opacity_scale.set_value(self.main_win.overlay_opacity)
        self.updating_widgets = False

    def on_opacity_changed(self, widget):
        if self.main_win: 
            self.main_win.overlay_opacity = self.opacity_scale.get_value()
            self.main_win.queue_draw()

    def load_overlay_image(self, file_path):
        if os.path.exists(file_path):
            resolved = file_path
        else:
            resolved = find_asset_path(file_path)

        if not os.path.exists(resolved):
            return
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(resolved)
            if self.main_win:
                img_h = pixbuf.get_height()
                fit_scale = 720.0 / img_h
                self.main_win.overlay_element.pixbuf = pixbuf
                self.main_win.overlay_element.missing = False
                self.main_win.overlay_element.x = 640.0
                self.main_win.overlay_element.y = 360.0
                self.main_win.overlay_element.scale = fit_scale
                self.main_win.overlay_element.current_scale = fit_scale
                self.main_win.overlay_element.surface = Gdk.cairo_surface_create_from_pixbuf(pixbuf, 1, None)
                self.main_win.overlay_element.half_w = pixbuf.get_width() / 2.0
                self.main_win.overlay_element.half_h = pixbuf.get_height() / 2.0
                self.main_win.overlay_text = ""
                if self.opacity_scale.get_value() == 0.0:
                    self.opacity_scale.set_value(0.8)
                self.main_win.queue_draw()
            self.dnd_label.set_text(f"Loaded: {os.path.basename(file_path)}")
        except Exception:
            self.dnd_label.set_text("Error loading image!")

    def on_drag_data_received(self, widget, context, x, y, data, info, time):
        uris = data.get_uris()
        if uris:
            uri = uris[0]
            if uri.startswith("file://"):
                path = urllib.parse.unquote(uri[7:])
                self.load_overlay_image(path)
            context.finish(True, False, time)

    def on_dnd_click(self, widget, event):
        dialog = Gtk.FileChooserDialog(title="Choose Overlay Image", parent=self, action=Gtk.FileChooserAction.OPEN)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        filter_img = Gtk.FileFilter()
        filter_img.set_name("Images")
        filter_img.add_mime_type("image/png")
        filter_img.add_mime_type("image/jpeg")
        filter_img.add_pattern("*.png")
        filter_img.add_pattern("*.jpg")
        filter_img.add_pattern("*.jpeg")
        dialog.add_filter(filter_img)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.load_overlay_image(dialog.get_filename())
        dialog.destroy()