"""Live dashboard with real-time OBD-II gauges."""

import threading
import gettext

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib

from .gauges import ArcGauge, BarGauge

_ = gettext.gettext

# PID definitions: (obd command name, label, unit, min, max, warn, danger, gauge_type)
DASHBOARD_PIDS = [
    ("RPM", _("RPM"), _("rpm"), 0, 8000, 6500, 7500, "arc"),
    ("SPEED", _("Speed"), _("km/h"), 0, 300, None, None, "arc"),
    ("COOLANT_TEMP", _("Coolant Temp"), "°C", -40, 150, 100, 115, "arc"),
    ("INTAKE_TEMP", _("Intake Temp"), "°C", -40, 80, 50, 65, "arc"),
    ("THROTTLE_POS", _("Throttle"), "%", 0, 100, None, None, "bar"),
    ("ENGINE_LOAD", _("Engine Load"), "%", 0, 100, 85, 95, "bar"),
    ("INTAKE_PRESSURE", _("Boost"), _("kPa"), 0, 300, 200, 255, "arc"),
    ("FUEL_STATUS", _("Fuel Status"), "", 0, 1, None, None, "text"),
]


class DashboardPage(Gtk.Box):
    """Live dashboard page with gauge grid."""

    def __init__(self, obd_connection):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self._obd = obd_connection
        self._gauges = {}
        self._timer_id = None
        self._refresh_hz = 2
        self._fuel_status_label = None

        self.set_margin_top(12)
        self.set_margin_bottom(12)
        self.set_margin_start(12)
        self.set_margin_end(12)

        # Refresh rate control
        rate_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        rate_box.set_halign(Gtk.Align.END)
        rate_label = Gtk.Label(label=_("Refresh rate:"))
        rate_box.append(rate_label)

        self._rate_spin = Gtk.SpinButton.new_with_range(1, 10, 1)
        self._rate_spin.set_value(self._refresh_hz)
        self._rate_spin.connect("value-changed", self._on_rate_changed)
        rate_box.append(self._rate_spin)

        hz_label = Gtk.Label(label=_("Hz"))
        rate_box.append(hz_label)
        self.append(rate_box)

        # Scroll container
        scroll = Gtk.ScrolledWindow(vexpand=True, hexpand=True)
        self.append(scroll)

        # Gauge grid
        self._grid = Gtk.FlowBox()
        self._grid.set_max_children_per_line(4)
        self._grid.set_min_children_per_line(2)
        self._grid.set_selection_mode(Gtk.SelectionMode.NONE)
        self._grid.set_homogeneous(True)
        self._grid.set_row_spacing(12)
        self._grid.set_column_spacing(12)
        scroll.set_child(self._grid)

        self._build_gauges()

        # Connect to connection signals
        self._obd.connect("connected", self._on_connected)
        self._obd.connect("disconnected", self._on_disconnected)

    def _build_gauges(self):
        for cmd_name, label, unit, min_v, max_v, warn, danger, gtype in DASHBOARD_PIDS:
            if gtype == "arc":
                gauge = ArcGauge(label=label, unit=unit, min_val=min_v,
                                 max_val=max_v, warn_threshold=warn,
                                 danger_threshold=danger)
            elif gtype == "bar":
                gauge = BarGauge(label=label, unit=unit, min_val=min_v,
                                 max_val=max_v, warn_threshold=warn,
                                 danger_threshold=danger)
            elif gtype == "text":
                # Simple label for fuel status
                frame = Gtk.Frame()
                box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
                box.set_margin_top(8)
                box.set_margin_bottom(8)
                box.set_margin_start(8)
                box.set_margin_end(8)
                title = Gtk.Label(label=label)
                title.add_css_class("dim-label")
                box.append(title)
                self._fuel_status_label = Gtk.Label(label="—")
                self._fuel_status_label.add_css_class("title-2")
                box.append(self._fuel_status_label)
                frame.set_child(box)
                self._grid.append(frame)
                self._gauges[cmd_name] = None
                continue
            else:
                continue

            self._grid.append(gauge)
            self._gauges[cmd_name] = gauge

    def _on_connected(self, conn):
        self.start_polling()

    def _on_disconnected(self, conn):
        self.stop_polling()

    def _on_rate_changed(self, spin):
        self._refresh_hz = int(spin.get_value())
        if self._timer_id:
            self.stop_polling()
            self.start_polling()

    def start_polling(self):
        """Start polling OBD data."""
        if self._timer_id:
            return
        interval_ms = max(100, int(1000 / self._refresh_hz))
        self._timer_id = GLib.timeout_add(interval_ms, self._poll_data)

    def stop_polling(self):
        """Stop polling."""
        if self._timer_id:
            GLib.source_remove(self._timer_id)
            self._timer_id = None

    def _poll_data(self):
        """Poll OBD data in background thread."""
        if not self._obd.is_connected:
            self._timer_id = None
            return False

        thread = threading.Thread(target=self._read_pids, daemon=True)
        thread.start()
        return True

    def _read_pids(self):
        """Read PIDs and update gauges on main thread."""
        try:
            import obd
        except ImportError:
            return

        results = {}
        for cmd_name, *_ in DASHBOARD_PIDS:
            try:
                cmd = obd.commands[cmd_name]
                resp = self._obd.query(cmd)
                if resp and not resp.is_null():
                    results[cmd_name] = resp.value
            except (KeyError, Exception):
                pass

        GLib.idle_add(self._update_gauges, results)

    def _update_gauges(self, results):
        """Update gauge values on the main thread."""
        for cmd_name, value in results.items():
            if cmd_name == "FUEL_STATUS" and self._fuel_status_label:
                self._fuel_status_label.set_text(str(value))
                continue

            gauge = self._gauges.get(cmd_name)
            if gauge is None:
                continue

            # python-obd returns Pint quantities
            try:
                val = value.magnitude
            except AttributeError:
                val = float(value)

            gauge.value = val
        return False

    def get_current_values(self):
        """Return current dashboard values as dict for export."""
        data = {}
        for cmd_name, label, unit, *_ in DASHBOARD_PIDS:
            gauge = self._gauges.get(cmd_name)
            if gauge is not None:
                data[label] = {"value": gauge.value, "unit": unit}
            elif cmd_name == "FUEL_STATUS" and self._fuel_status_label:
                data[label] = {"value": self._fuel_status_label.get_text(), "unit": ""}
        return data
