#!/usr/bin/env python3
"""OBD2 Viewer — GTK4/Adwaita OBD-II diagnostics viewer."""

import sys
import gettext
from datetime import datetime

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GLib

from . import __version__
from .connection import OBDConnection, ConnectionDialog
from .dashboard import DashboardPage
from .dtc import DTCPage
from .logger import LoggerPage
from .vehicle_info import VehicleInfoPage
from .freeze_frame import FreezeFramePage
from .export import ExportDialog
from obd2_viewer.accessibility import AccessibilityManager

# Set up gettext
TEXTDOMAIN = 'obd2-viewer'
gettext.textdomain(TEXTDOMAIN)
gettext.bindtextdomain(TEXTDOMAIN, '/usr/share/locale')
_ = gettext.gettext



def _wlc_settings_path():
    import os
    xdg = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    d = os.path.join(xdg, "obd2-viewer")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "welcome.json")

def _load_wlc_settings():
    import os, json
    p = _wlc_settings_path()
    if os.path.exists(p):
        with open(p) as f:
            return json.load(f)
    return {"welcome_shown": False}

def _save_wlc_settings(s):
    import json
    with open(_wlc_settings_path(), "w") as f:
        json.dump(s, f, indent=2)

class MainWindow(Adw.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_default_size(1000, 700)
        self.set_title(_("OBD2 Viewer"))

        # OBD connection
        self._obd = OBDConnection()
        self._obd.connect("connected", self._on_connected)
        self._obd.connect("disconnected", self._on_disconnected)
        self._obd.connect("error", self._on_connection_error)
        self._obd.connect("status-changed", self._on_status_changed)

        # Main layout
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(main_box)

        # Header bar
        header = Adw.HeaderBar()

        # Connection button
        self._connect_btn = Gtk.Button(icon_name="network-wired-symbolic")
        self._connect_btn.set_tooltip_text(_("Connect to Vehicle"))
        self._connect_btn.connect("clicked", self._on_connect_clicked)
        header.pack_start(self._connect_btn)

        # Connection status indicator
        self._conn_indicator = Gtk.Image.new_from_icon_name("network-offline-symbolic")
        self._conn_indicator.set_tooltip_text(_("Disconnected"))
        header.pack_start(self._conn_indicator)

        # Vehicle name label
        self._vehicle_label = Gtk.Label(label=_("No vehicle connected"))
        self._vehicle_label.add_css_class("dim-label")
        header.pack_start(self._vehicle_label)

        # View switcher in title
        self._view_stack = Adw.ViewStack()
        view_switcher = Adw.ViewSwitcher()
        view_switcher.set_stack(self._view_stack)
        view_switcher.set_policy(Adw.ViewSwitcherPolicy.WIDE)
        header.set_title_widget(view_switcher)

        # Menu button
        menu_btn = Gtk.MenuButton()
        menu_btn.set_icon_name("open-menu-symbolic")
        menu = Gio.Menu()
        menu.append(_("Keyboard Shortcuts"), "app.shortcuts")
        menu.append(_("About OBD2 Viewer"), "app.about")
        menu_btn.set_menu_model(menu)
        header.pack_end(menu_btn)

        main_box.append(header)

        # View stack with bottom switcher bar for narrow windows
        stack_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, vexpand=True)
        main_box.append(stack_box)

        stack_box.append(self._view_stack)

        switcher_bar = Adw.ViewSwitcherBar()
        switcher_bar.set_stack(self._view_stack)
        stack_box.append(switcher_bar)

        # Build pages
        self._dashboard = DashboardPage(self._obd)
        self._view_stack.add_titled_with_icon(
            self._dashboard, "dashboard", _("Dashboard"), "speedometer-symbolic"
        )

        self._dtc_page = DTCPage(self._obd)
        self._view_stack.add_titled_with_icon(
            self._dtc_page, "dtc", _("DTCs"), "dialog-warning-symbolic"
        )

        self._logger = LoggerPage(self._obd)
        self._view_stack.add_titled_with_icon(
            self._logger, "logger", _("Logger"), "media-record-symbolic"
        )

        self._vehicle_info = VehicleInfoPage(self._obd)
        self._view_stack.add_titled_with_icon(
            self._vehicle_info, "vehicle", _("Vehicle Info"), "emblem-system-symbolic"
        )

        self._freeze_frame = FreezeFramePage(self._obd)
        self._view_stack.add_titled_with_icon(
            self._freeze_frame, "freeze", _("Freeze Frame"), "media-playlist-consecutive-symbolic"
        )

        # Status bar
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        status_box.set_margin_start(12)
        status_box.set_margin_end(12)
        status_box.set_margin_top(4)
        status_box.set_margin_bottom(4)
        main_box.append(Gtk.Separator())
        main_box.append(status_box)

        self._status_label = Gtk.Label(label=_("Ready"))
        self._status_label.set_halign(Gtk.Align.START)
        self._status_label.set_hexpand(True)
        self._status_label.add_css_class("dim-label")
        status_box.append(self._status_label)

        self._protocol_label = Gtk.Label(label="")
        self._protocol_label.add_css_class("dim-label")
        status_box.append(self._protocol_label)

        self._time_label = Gtk.Label(label="")
        self._time_label.add_css_class("dim-label")
        status_box.append(self._time_label)

        # Update clock
        GLib.timeout_add_seconds(1, self._update_clock)
        self._update_clock()

    def _update_clock(self):
        self._time_label.set_text(datetime.now().strftime("%H:%M:%S"))
        return True

    def _on_connect_clicked(self, btn):
        if self._obd.is_connected:
            self._obd.disconnect()
        else:
            dialog = ConnectionDialog(self._obd)
            dialog.present(self)

    def _on_connected(self, conn):
        self._conn_indicator.set_from_icon_name("network-wired-symbolic")
        self._conn_indicator.set_tooltip_text(_("Connected"))
        self._conn_indicator.remove_css_class("error")
        self._conn_indicator.add_css_class("success")
        self._connect_btn.set_icon_name("network-wired-disconnecting-symbolic")
        self._connect_btn.set_tooltip_text(_("Disconnect"))

        proto = self._obd.protocol
        if proto:
            self._protocol_label.set_text(proto)

    def _on_disconnected(self, conn):
        self._conn_indicator.set_from_icon_name("network-offline-symbolic")
        self._conn_indicator.set_tooltip_text(_("Disconnected"))
        self._conn_indicator.remove_css_class("success")
        self._connect_btn.set_icon_name("network-wired-symbolic")
        self._connect_btn.set_tooltip_text(_("Connect to Vehicle"))
        self._vehicle_label.set_text(_("No vehicle connected"))
        self._protocol_label.set_text("")

    def _on_connection_error(self, conn, message):
        self._set_status(_("Error: %s") % message)
        self._conn_indicator.add_css_class("error")

    def _on_status_changed(self, conn, message):
        self._set_status(message)

    def _set_status(self, text):
        ts = datetime.now().strftime("%H:%M:%S")
        self._status_label.set_text(f"[{ts}] {text}")

    def show_about(self, action, param):
        about = Adw.AboutDialog()
        about.set_application_name(_("OBD2 Viewer"))
        about.set_application_icon("se.danielnylander.obd2-viewer")
        about.set_developer_name("Daniel Nylander")
        about.set_developers(["Daniel Nylander <daniel@danielnylander.se>"])
        about.set_version(__version__)
        about.set_website("https://github.com/yeager/obd2-viewer")
        about.set_issue_url("https://github.com/yeager/obd2-viewer/issues")
        about.set_copyright("© 2026 Daniel Nylander")
        about.set_license_type(Gtk.License.GPL_3_0)
        about.set_developers(["Daniel Nylander <daniel@danielnylander.se>"])
        about.set_translator_credits(_("Translate this app: https://www.transifex.com/danielnylander/obd2-viewer/"))
        about.present(self)

    def show_shortcuts(self, action, param):
        builder = Gtk.Builder()
        builder.add_from_string('''
        <interface>
          <object class="GtkShortcutsWindow" id="shortcuts">
            <property name="modal">True</property>
            <child>
              <object class="GtkShortcutsSection">
                <property name="section-name">shortcuts</property>
                <child>
                  <object class="GtkShortcutsGroup">
                    <property name="title" translatable="yes">General</property>
                    <child>
                      <object class="GtkShortcutsShortcut">
                        <property name="title" translatable="yes">Show Shortcuts</property>
                        <property name="accelerator">&lt;Primary&gt;slash</property>
                      </object>
                    </child>
                    <child>
                      <object class="GtkShortcutsShortcut">
                        <property name="title" translatable="yes">Refresh Data</property>
                        <property name="accelerator">F5</property>
                      </object>
                    </child>
                    <child>
                      <object class="GtkShortcutsShortcut">
                        <property name="title" translatable="yes">Export Data</property>
                        <property name="accelerator">&lt;Primary&gt;e</property>
                      </object>
                    </child>
                    <child>
                      <object class="GtkShortcutsShortcut">
                        <property name="title" translatable="yes">Quit</property>
                        <property name="accelerator">&lt;Primary&gt;q</property>
                      </object>
                    </child>
                  </object>
                </child>
              </object>
            </child>
          </object>
        </interface>
        ''')
        shortcuts = builder.get_object("shortcuts")
        shortcuts.set_transient_for(self)
        shortcuts.present()
        # Welcome dialog
        self._wlc_settings = _load_wlc_settings()
        if not self._wlc_settings.get("welcome_shown"):
            self._show_welcome(self.props.active_window or self)


    def show_export(self, action, param):
        data_sources = {
            _("Dashboard"): self._dashboard.get_current_values,
            _("DTCs"): self._dtc_page.get_dtc_data,
            _("Logger"): self._logger.get_log_data,
            _("Vehicle Info"): self._vehicle_info.get_vehicle_info,
            _("Freeze Frame"): self._freeze_frame.get_freeze_data,
        }
        dialog = ExportDialog(data_sources)
        dialog.present(self)

    def refresh_data(self, action, param):
        self._set_status(_("Refreshing…"))
        # Trigger refresh based on current view
        current = self._view_stack.get_visible_child_name()
        if current == "dashboard" and self._obd.is_connected:
            self._dashboard.stop_polling()
            self._dashboard.start_polling()
        self._set_status(_("Ready"))


class Application(Adw.Application):
    def __init__(self):
        super().__init__(application_id="se.danielnylander.obd2-viewer")

    def do_activate(self):
        window = self.props.active_window
        if not window:
            window = MainWindow(application=self)
        window.present()

    def do_startup(self):
        Adw.Application.do_startup(self)

        # Actions
        actions = [
            ("quit", self.quit_app),
            ("about", self.show_about),
            ("shortcuts", self.show_shortcuts),
            ("refresh", self.refresh_data),
            ("export", self.show_export),
        ]
        for name, callback in actions:
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", callback)
            self.add_action(action)

        # Keyboard shortcuts
        self.set_accels_for_action("app.quit", ["<Primary>q"])
        self.set_accels_for_action("app.shortcuts", ["<Primary>slash"])
        self.set_accels_for_action("app.refresh", ["F5"])
        self.set_accels_for_action("app.export", ["<Primary>e"])

    def quit_app(self, action, param):
        self.quit()

    def show_about(self, action, param):
        window = self.props.active_window
        if window:
            window.show_about(action, param)

    def show_shortcuts(self, action, param):
        window = self.props.active_window
        if window:
            window.show_shortcuts(action, param)

    def refresh_data(self, action, param):
        window = self.props.active_window
        if window:
            window.refresh_data(action, param)

    def show_export(self, action, param):
        window = self.props.active_window
        if window:
            window.show_export(action, param)


def main():
    app = Application()
    return app.run(sys.argv)


if __name__ == '__main__':
    main()

    def _show_welcome(self, win):
        dialog = Adw.Dialog()
        dialog.set_title(_("Welcome"))
        dialog.set_content_width(420)
        dialog.set_content_height(480)
        page = Adw.StatusPage()
        page.set_icon_name("speedometer-symbolic")
        page.set_title(_("Welcome to OBD2 Viewer"))
        page.set_description(_("Read vehicle diagnostics via OBD-II.\n\n✓ Read diagnostic trouble codes\n✓ Real-time sensor data\n✓ Export reports"))
        btn = Gtk.Button(label=_("Get Started"))
        btn.add_css_class("suggested-action")
        btn.add_css_class("pill")
        btn.set_halign(Gtk.Align.CENTER)
        btn.set_margin_top(12)
        btn.connect("clicked", self._on_welcome_close, dialog)
        page.set_child(btn)
        box = Adw.ToolbarView()
        hb = Adw.HeaderBar()
        hb.set_show_title(False)
        box.add_top_bar(hb)
        box.set_content(page)
        dialog.set_child(box)
        dialog.present(win)

    def _on_welcome_close(self, btn, dialog):
        self._wlc_settings["welcome_shown"] = True
        _save_wlc_settings(self._wlc_settings)
        dialog.close()



# --- Session restore ---
import json as _json
import os as _os

def _save_session(window, app_name):
    config_dir = _os.path.join(_os.path.expanduser('~'), '.config', app_name)
    _os.makedirs(config_dir, exist_ok=True)
    state = {'width': window.get_width(), 'height': window.get_height(),
             'maximized': window.is_maximized()}
    try:
        with open(_os.path.join(config_dir, 'session.json'), 'w') as f:
            _json.dump(state, f)
    except OSError:
        pass

def _restore_session(window, app_name):
    path = _os.path.join(_os.path.expanduser('~'), '.config', app_name, 'session.json')
    try:
        with open(path) as f:
            state = _json.load(f)
        window.set_default_size(state.get('width', 800), state.get('height', 600))
        if state.get('maximized'):
            window.maximize()
    except (FileNotFoundError, _json.JSONDecodeError, OSError):
        pass


# --- Fullscreen toggle (F11) ---
def _setup_fullscreen(window, app):
    """Add F11 fullscreen toggle."""
    from gi.repository import Gio
    if not app.lookup_action('toggle-fullscreen'):
        action = Gio.SimpleAction.new('toggle-fullscreen', None)
        action.connect('activate', lambda a, p: (
            window.unfullscreen() if window.is_fullscreen() else window.fullscreen()
        ))
        app.add_action(action)
        app.set_accels_for_action('app.toggle-fullscreen', ['F11'])


# --- Plugin system ---
import importlib.util
import os as _pos

def _load_plugins(app_name):
    """Load plugins from ~/.config/<app>/plugins/."""
    plugin_dir = _pos.path.join(_pos.path.expanduser('~'), '.config', app_name, 'plugins')
    plugins = []
    if not _pos.path.isdir(plugin_dir):
        return plugins
    for fname in sorted(_pos.listdir(plugin_dir)):
        if fname.endswith('.py') and not fname.startswith('_'):
            path = _pos.path.join(plugin_dir, fname)
            try:
                spec = importlib.util.spec_from_file_location(fname[:-3], path)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                plugins.append(mod)
            except Exception as e:
                print(f"Plugin {fname}: {e}")
    return plugins
