# --- main.py ---
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

# Load modules cleanly split below the 20KB limit
from home_window import GDHomeScreen
from controls import GDControlsWindow

if __name__ == "__main__":
    # Standard GTK loop sequence startup
    win = GDHomeScreen()
    ctrl = GDControlsWindow(win)
    
    # Safely connect window callbacks
    win.connect("destroy", Gtk.main_quit)
    ctrl.connect("destroy", Gtk.main_quit)
    
    # Display layouts
    win.show_all()
    ctrl.show_all()
    Gtk.main()