"""Vehicle information page — VIN, ECU, protocol, supported PIDs."""

import threading
import gettext

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib

_ = gettext.gettext

# Commands to query for vehicle info
INFO_COMMANDS = [
    ("VIN", _("VIN")),
    ("ELM_VERSION", _("ECU Name")),
    ("CALIBRATION_ID", _("Calibration ID")),
]


class VehicleInfoPage(Gtk.Box):
    """Vehicle identification and info page."""

    def __init__(self, obd_connection):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self._obd = obd_connection
        self._info_rows = {}

        self.set_margin_top(12)
        self.set_margin_bottom(12)
        self.set_margin_start(12)
        self.set_margin_end(12)

        # Read button
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.append(btn_box)

        read_btn = Gtk.Button(label=_("Read Vehicle Info"))
        read_btn.add_css_class("suggested-action")
        read_btn.connect("clicked", self._on_read)
        btn_box.append(read_btn)

        spacer = Gtk.Box(hexpand=True)
        btn_box.append(spacer)

        self._status = Gtk.Label(label="")
        self._status.add_css_class("dim-label")
        btn_box.append(self._status)

        # Info list
        scroll = Gtk.ScrolledWindow(vexpand=True)
        self.append(scroll)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        scroll.set_child(box)

        # Vehicle info group
        info_group = Adw.PreferencesGroup(title=_("Vehicle Identification"))
        box.append(info_group)

        for cmd_name, label in INFO_COMMANDS:
            row = Adw.ActionRow(title=label, subtitle="—")
            self._info_rows[cmd_name] = row
            info_group.add(row)

        # Protocol row
        self._protocol_row = Adw.ActionRow(title=_("OBD Protocol"), subtitle="—")
        info_group.add(self._protocol_row)
        self._info_rows["protocol"] = self._protocol_row

        # Supported PIDs group
        self._pids_group = Adw.PreferencesGroup(title=_("Supported PIDs"))
        box.append(self._pids_group)

        self._pids_label = Gtk.Label(label=_("Connect and read to see supported PIDs"))
        self._pids_label.set_wrap(True)
        self._pids_label.set_halign(Gtk.Align.START)
        self._pids_label.add_css_class("dim-label")
        self._pids_group.add(self._pids_label)

    def _on_read(self, btn):
        if not self._obd.is_connected:
            self._status.set_text(_("Not connected"))
            return
        self._status.set_text(_("Reading vehicle info…"))
        threading.Thread(target=self._do_read, daemon=True).start()

    def _do_read(self):
        try:
            import obd
        except ImportError:
            GLib.idle_add(self._status.set_text, _("python-obd is not installed"))
            return

        results = {}

        for cmd_name, label in INFO_COMMANDS:
            try:
                cmd = obd.commands[cmd_name]
                resp = self._obd.query(cmd)
                if resp and not resp.is_null():
                    results[cmd_name] = str(resp.value)
            except (KeyError, Exception):
                pass

        # Protocol
        proto = self._obd.protocol
        if proto:
            results["protocol"] = proto

        # Supported PIDs
        supported = self._obd.supported_commands()
        pid_names = sorted([str(c) for c in supported]) if supported else []

        GLib.idle_add(self._update_info, results, pid_names)

    def _update_info(self, results, pid_names):
        for key, value in results.items():
            row = self._info_rows.get(key)
            if row:
                row.set_subtitle(value)

        if pid_names:
            self._pids_label.set_text(", ".join(pid_names))
            self._status.set_text(_("%d supported PIDs") % len(pid_names))
        else:
            self._status.set_text(_("Vehicle info read"))

        return False

    def get_vehicle_info(self):
        """Return vehicle info for export."""
        data = {}
        for cmd_name, label in INFO_COMMANDS:
            row = self._info_rows.get(cmd_name)
            if row:
                data[label] = row.get_subtitle()
        proto_row = self._info_rows.get("protocol")
        if proto_row:
            data[_("OBD Protocol")] = proto_row.get_subtitle()
        return data
