"""Connection manager for ELM327/OBD-II adapters."""

import glob
import json
import os
import threading
import gettext

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio, GObject

_ = gettext.gettext

PROFILES_DIR = os.path.expanduser("~/.config/obd2-viewer")
PROFILES_FILE = os.path.join(PROFILES_DIR, "connections.json")

BAUD_RATES = [
    ("auto", _("Auto")),
    ("9600", "9600"),
    ("38400", "38400"),
    ("115200", "115200"),
]


def detect_serial_ports():
    """Auto-detect common OBD-II serial ports."""
    patterns = [
        "/dev/ttyUSB*",
        "/dev/ttyACM*",
        "/dev/rfcomm*",
        "/dev/tty.OBD*",
        "/dev/tty.usbserial*",
        "/dev/cu.OBD*",
        "/dev/cu.usbserial*",
    ]
    ports = []
    for pattern in patterns:
        ports.extend(glob.glob(pattern))
    return sorted(set(ports))


def load_profiles():
    """Load saved connection profiles."""
    if not os.path.exists(PROFILES_FILE):
        return []
    try:
        with open(PROFILES_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_profiles(profiles):
    """Save connection profiles."""
    os.makedirs(PROFILES_DIR, exist_ok=True)
    with open(PROFILES_FILE, "w") as f:
        json.dump(profiles, f, indent=2)


class OBDConnection(GObject.Object):
    """Manages OBD-II connection state."""

    __gsignals__ = {
        "connected": (GObject.SignalFlags.RUN_FIRST, None, ()),
        "disconnected": (GObject.SignalFlags.RUN_FIRST, None, ()),
        "error": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        "status-changed": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    def __init__(self):
        super().__init__()
        self._connection = None
        self._port = None
        self._baud = None
        self._protocol = None
        self._lock = threading.Lock()

    @property
    def is_connected(self):
        return self._connection is not None and self._connection.is_connected()

    @property
    def connection(self):
        return self._connection

    @property
    def protocol(self):
        if self._connection and self._connection.is_connected():
            try:
                return str(self._connection.protocol_name())
            except Exception:
                pass
        return None

    def connect(self, port, baud="auto"):
        """Connect in a background thread."""
        self._port = port
        self._baud = baud
        thread = threading.Thread(target=self._do_connect, daemon=True)
        thread.start()

    def _do_connect(self):
        try:
            import obd
            GLib.idle_add(self.emit, "status-changed", _("Connecting to %s…") % self._port)

            kwargs = {"portstr": self._port, "fast": False}
            if self._baud and self._baud != "auto":
                kwargs["baudrate"] = int(self._baud)

            conn = obd.OBD(**kwargs)
            if conn.is_connected():
                with self._lock:
                    self._connection = conn
                GLib.idle_add(self.emit, "connected")
                GLib.idle_add(self.emit, "status-changed",
                              _("Connected to %s") % self._port)
            else:
                GLib.idle_add(self.emit, "error", _("Failed to connect to %s") % self._port)
                GLib.idle_add(self.emit, "status-changed", _("Connection failed"))
        except ImportError:
            GLib.idle_add(self.emit, "error",
                          _("python-obd is not installed. Install it with: pip install obd"))
            GLib.idle_add(self.emit, "status-changed", _("Missing python-obd"))
        except Exception as e:
            GLib.idle_add(self.emit, "error", str(e))
            GLib.idle_add(self.emit, "status-changed", _("Connection error"))

    def disconnect(self):
        """Disconnect from OBD adapter."""
        with self._lock:
            if self._connection:
                try:
                    self._connection.close()
                except Exception:
                    pass
                self._connection = None
        self.emit("disconnected")
        self.emit("status-changed", _("Disconnected"))

    def query(self, command):
        """Thread-safe OBD query."""
        with self._lock:
            if self._connection and self._connection.is_connected():
                try:
                    return self._connection.query(command)
                except Exception:
                    return None
        return None

    def supported_commands(self):
        """Return set of supported OBD commands."""
        with self._lock:
            if self._connection and self._connection.is_connected():
                return self._connection.supported_commands
        return set()


class ConnectionDialog(Adw.Dialog):
    """Dialog for configuring OBD connection."""

    def __init__(self, obd_connection, **kwargs):
        super().__init__(**kwargs)
        self.set_title(_("Connect to Vehicle"))
        self.set_content_width(400)
        self.set_content_height(500)
        self._obd = obd_connection
        self._profiles = load_profiles()

        toolbar_view = Adw.ToolbarView()
        self.set_child(toolbar_view)

        header = Adw.HeaderBar()
        toolbar_view.add_top_bar(header)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        toolbar_view.set_content(content)

        # Profiles group
        profiles_group = Adw.PreferencesGroup(title=_("Saved Profiles"))
        content.append(profiles_group)

        self._profiles_list = Gtk.ListBox()
        self._profiles_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self._profiles_list.add_css_class("boxed-list")
        profiles_group.add(self._profiles_list)
        self._refresh_profiles()

        # Connection settings group
        settings_group = Adw.PreferencesGroup(title=_("Connection Settings"))
        content.append(settings_group)

        # Port selector
        self._port_row = Adw.ComboRow(title=_("Serial Port"))
        port_model = Gtk.StringList()
        detected = detect_serial_ports()
        if not detected:
            port_model.append(_("No ports detected"))
        for p in detected:
            port_model.append(p)
        self._port_row.set_model(port_model)
        settings_group.add(self._port_row)

        # Custom port entry
        self._custom_port_row = Adw.EntryRow(title=_("Custom Port Path"))
        settings_group.add(self._custom_port_row)

        # Baud rate
        self._baud_row = Adw.ComboRow(title=_("Baud Rate"))
        baud_model = Gtk.StringList()
        for val, label in BAUD_RATES:
            baud_model.append(label)
        self._baud_row.set_model(baud_model)
        settings_group.add(self._baud_row)

        # Buttons
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12,
                          margin_top=24, margin_bottom=12, margin_start=12, margin_end=12)
        btn_box.set_halign(Gtk.Align.END)
        content.append(btn_box)

        save_btn = Gtk.Button(label=_("Save Profile"))
        save_btn.connect("clicked", self._on_save_profile)
        btn_box.append(save_btn)

        connect_btn = Gtk.Button(label=_("Connect"))
        connect_btn.add_css_class("suggested-action")
        connect_btn.connect("clicked", self._on_connect)
        btn_box.append(connect_btn)

    def _get_selected_port(self):
        custom = self._custom_port_row.get_text().strip()
        if custom:
            return custom
        ports = detect_serial_ports()
        idx = self._port_row.get_selected()
        if ports and 0 <= idx < len(ports):
            return ports[idx]
        return None

    def _get_selected_baud(self):
        idx = self._baud_row.get_selected()
        if 0 <= idx < len(BAUD_RATES):
            return BAUD_RATES[idx][0]
        return "auto"

    def _on_connect(self, btn):
        port = self._get_selected_port()
        if not port:
            return
        baud = self._get_selected_baud()
        self._obd.connect(port, baud)
        self.close()

    def _on_save_profile(self, btn):
        port = self._get_selected_port()
        if not port:
            return
        baud = self._get_selected_baud()
        profile = {"port": port, "baud": baud}
        # Don't duplicate
        if profile not in self._profiles:
            self._profiles.append(profile)
            save_profiles(self._profiles)
            self._refresh_profiles()

    def _refresh_profiles(self):
        while True:
            child = self._profiles_list.get_first_child()
            if child is None:
                break
            self._profiles_list.remove(child)

        for i, p in enumerate(self._profiles):
            row = Adw.ActionRow(
                title=p.get("port", _("Unknown")),
                subtitle=_("Baud: %s") % p.get("baud", "auto"),
            )
            use_btn = Gtk.Button(label=_("Use"), valign=Gtk.Align.CENTER)
            use_btn.connect("clicked", self._on_use_profile, p)
            row.add_suffix(use_btn)

            del_btn = Gtk.Button(icon_name="user-trash-symbolic", valign=Gtk.Align.CENTER)
            del_btn.add_css_class("flat")
            del_btn.connect("clicked", self._on_delete_profile, i)
            row.add_suffix(del_btn)

            self._profiles_list.append(row)

        if not self._profiles:
            row = Adw.ActionRow(title=_("No saved profiles"))
            self._profiles_list.append(row)

    def _on_use_profile(self, btn, profile):
        self._obd.connect(profile["port"], profile.get("baud", "auto"))
        self.close()

    def _on_delete_profile(self, btn, index):
        if 0 <= index < len(self._profiles):
            self._profiles.pop(index)
            save_profiles(self._profiles)
            self._refresh_profiles()
