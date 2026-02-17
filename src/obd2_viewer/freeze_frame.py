"""Freeze frame data reader."""

import threading
import gettext

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib

_ = gettext.gettext

# Freeze frame PIDs to read
FREEZE_FRAME_PIDS = [
    "FUEL_STATUS",
    "ENGINE_LOAD",
    "COOLANT_TEMP",
    "SHORT_FUEL_TRIM_1",
    "LONG_FUEL_TRIM_1",
    "INTAKE_PRESSURE",
    "RPM",
    "SPEED",
    "TIMING_ADVANCE",
    "INTAKE_TEMP",
    "MAF",
    "THROTTLE_POS",
]


class FreezeFramePage(Gtk.Box):
    """Freeze frame data reader page."""

    def __init__(self, obd_connection):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self._obd = obd_connection
        self._data = []

        self.set_margin_top(12)
        self.set_margin_bottom(12)
        self.set_margin_start(12)
        self.set_margin_end(12)

        # Controls
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.append(btn_box)

        read_btn = Gtk.Button(label=_("Read Freeze Frame"))
        read_btn.add_css_class("suggested-action")
        read_btn.connect("clicked", self._on_read)
        btn_box.append(read_btn)

        spacer = Gtk.Box(hexpand=True)
        btn_box.append(spacer)

        self._status = Gtk.Label(label="")
        self._status.add_css_class("dim-label")
        btn_box.append(self._status)

        # Data list
        scroll = Gtk.ScrolledWindow(vexpand=True)
        self.append(scroll)

        self._list = Gtk.ListBox()
        self._list.set_selection_mode(Gtk.SelectionMode.NONE)
        self._list.add_css_class("boxed-list")
        scroll.set_child(self._list)

        self._show_empty()

    def _show_empty(self):
        self._clear_list()
        row = Adw.ActionRow(
            title=_("No freeze frame data"),
            subtitle=_("Connect to a vehicle and read freeze frame data from stored DTCs"),
        )
        row.add_prefix(Gtk.Image.new_from_icon_name("dialog-information-symbolic"))
        self._list.append(row)

    def _clear_list(self):
        while True:
            child = self._list.get_first_child()
            if child is None:
                break
            self._list.remove(child)

    def _on_read(self, btn):
        if not self._obd.is_connected:
            self._status.set_text(_("Not connected"))
            return
        self._status.set_text(_("Reading freeze frame data…"))
        threading.Thread(target=self._do_read, daemon=True).start()

    def _do_read(self):
        try:
            import obd
        except ImportError:
            GLib.idle_add(self._status.set_text, _("python-obd is not installed"))
            return

        results = []
        for pid_name in FREEZE_FRAME_PIDS:
            try:
                # Freeze frame uses frame 0 by default
                cmd = obd.commands["FREEZE_DTC"]
                resp = self._obd.query(cmd)
                if resp and not resp.is_null():
                    results.append((pid_name, str(resp.value)))
            except (KeyError, Exception):
                pass

            # Also try reading the PID directly (some adapters return freeze data this way)
            try:
                cmd = obd.commands[pid_name]
                resp = self._obd.query(cmd)
                if resp and not resp.is_null():
                    try:
                        val = f"{resp.value.magnitude:.1f} {resp.value.units}"
                    except AttributeError:
                        val = str(resp.value)
                    results.append((pid_name, val))
            except (KeyError, Exception):
                pass

        GLib.idle_add(self._display_results, results)

    def _display_results(self, results):
        self._clear_list()
        self._data = results

        if not results:
            row = Adw.ActionRow(
                title=_("No freeze frame data available"),
                subtitle=_("No DTCs with freeze frame data stored"),
            )
            row.add_prefix(Gtk.Image.new_from_icon_name("emblem-ok-symbolic"))
            self._list.append(row)
            self._status.set_text(_("No freeze frame data"))
            return

        self._status.set_text(_("%d parameters read") % len(results))

        for pid_name, value in results:
            row = Adw.ActionRow(title=pid_name, subtitle=value)
            self._list.append(row)

        return False

    def get_freeze_data(self):
        """Return freeze frame data for export."""
        return [{"pid": p, "value": v} for p, v in self._data]
