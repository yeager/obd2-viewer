"""Data logger page — record OBD-II PIDs over time with chart."""

import csv
import math
import threading
import time
import gettext
from datetime import datetime

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib

_ = gettext.gettext

# Available PIDs for logging
LOGGABLE_PIDS = [
    "RPM", "SPEED", "COOLANT_TEMP", "INTAKE_TEMP",
    "THROTTLE_POS", "ENGINE_LOAD", "INTAKE_PRESSURE",
    "MAF", "TIMING_ADVANCE", "SHORT_FUEL_TRIM_1",
    "LONG_FUEL_TRIM_1", "FUEL_PRESSURE",
]


class ChartWidget(Gtk.DrawingArea):
    """Simple line chart rendered with Cairo."""

    def __init__(self):
        super().__init__()
        self.set_content_height(250)
        self.set_draw_func(self._draw)
        self._series = {}  # {pid_name: [(timestamp, value), ...]}
        self._colors = [
            (0.3, 0.75, 0.4),
            (0.3, 0.5, 0.9),
            (0.9, 0.3, 0.3),
            (0.95, 0.75, 0.1),
            (0.7, 0.3, 0.9),
            (0.3, 0.9, 0.9),
            (0.9, 0.6, 0.3),
            (0.6, 0.9, 0.3),
        ]

    def set_data(self, series):
        self._series = series
        self.queue_draw()

    def _draw(self, area, cr, width, height):
        margin_l, margin_r, margin_t, margin_b = 50, 20, 20, 30
        plot_w = width - margin_l - margin_r
        plot_h = height - margin_t - margin_b

        if plot_w <= 0 or plot_h <= 0:
            return

        # Background
        cr.set_source_rgba(0.15, 0.15, 0.15, 0.5)
        cr.rectangle(margin_l, margin_t, plot_w, plot_h)
        cr.fill()

        if not self._series:
            cr.set_source_rgba(0.5, 0.5, 0.5, 0.8)
            cr.select_font_face("sans-serif", 0, 0)
            cr.set_font_size(14)
            text = _("No data recorded")
            ext = cr.text_extents(text)
            cr.move_to(width / 2 - ext.width / 2, height / 2)
            cr.show_text(text)
            return

        # Find global time and value range
        all_times = []
        all_vals = []
        for pts in self._series.values():
            for t, v in pts:
                all_times.append(t)
                all_vals.append(v)

        if not all_times:
            return

        t_min, t_max = min(all_times), max(all_times)
        v_min, v_max = min(all_vals), max(all_vals)
        if t_max == t_min:
            t_max = t_min + 1
        if v_max == v_min:
            v_max = v_min + 1

        # Grid lines
        cr.set_source_rgba(0.3, 0.3, 0.3, 0.5)
        cr.set_line_width(0.5)
        for i in range(5):
            y = margin_t + plot_h * i / 4
            cr.move_to(margin_l, y)
            cr.line_to(margin_l + plot_w, y)
            cr.stroke()

            val = v_max - (v_max - v_min) * i / 4
            cr.set_font_size(10)
            cr.set_source_rgba(0.6, 0.6, 0.6, 0.8)
            cr.move_to(4, y + 4)
            cr.show_text(f"{val:.0f}")
            cr.set_source_rgba(0.3, 0.3, 0.3, 0.5)

        # Plot each series
        for idx, (name, pts) in enumerate(self._series.items()):
            if len(pts) < 2:
                continue
            color = self._colors[idx % len(self._colors)]
            cr.set_source_rgb(*color)
            cr.set_line_width(2)

            first = True
            for t, v in pts:
                x = margin_l + plot_w * (t - t_min) / (t_max - t_min)
                y = margin_t + plot_h * (1 - (v - v_min) / (v_max - v_min))
                if first:
                    cr.move_to(x, y)
                    first = False
                else:
                    cr.line_to(x, y)
            cr.stroke()

        # Legend
        cr.set_font_size(11)
        legend_x = margin_l + 8
        legend_y = margin_t + 16
        for idx, name in enumerate(self._series.keys()):
            color = self._colors[idx % len(self._colors)]
            cr.set_source_rgb(*color)
            cr.rectangle(legend_x, legend_y + idx * 18 - 8, 12, 12)
            cr.fill()
            cr.move_to(legend_x + 16, legend_y + idx * 18 + 2)
            cr.show_text(name)


class LoggerPage(Gtk.Box):
    """Data logger page with PID selection, recording, and chart."""

    def __init__(self, obd_connection):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self._obd = obd_connection
        self._recording = False
        self._log_data = {}  # {pid: [(timestamp, value), ...]}
        self._selected_pids = set()
        self._start_time = None

        self.set_margin_top(12)
        self.set_margin_bottom(12)
        self.set_margin_start(12)
        self.set_margin_end(12)

        # Controls
        ctrl_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.append(ctrl_box)

        self._record_btn = Gtk.Button(label=_("Start Recording"))
        self._record_btn.add_css_class("suggested-action")
        self._record_btn.connect("clicked", self._on_toggle_recording)
        ctrl_box.append(self._record_btn)

        self._save_btn = Gtk.Button(label=_("Save to CSV"))
        self._save_btn.set_sensitive(False)
        self._save_btn.connect("clicked", self._on_save_csv)
        ctrl_box.append(self._save_btn)

        clear_btn = Gtk.Button(label=_("Clear"))
        clear_btn.connect("clicked", self._on_clear)
        ctrl_box.append(clear_btn)

        spacer = Gtk.Box(hexpand=True)
        ctrl_box.append(spacer)

        self._status = Gtk.Label(label="")
        self._status.add_css_class("dim-label")
        ctrl_box.append(self._status)

        # Horizontal split: PID selection + chart
        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        paned.set_vexpand(True)
        self.append(paned)

        # PID selection
        pid_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        pid_label = Gtk.Label(label=_("Select PIDs to log:"))
        pid_label.set_halign(Gtk.Align.START)
        pid_label.add_css_class("heading")
        pid_box.append(pid_label)

        pid_scroll = Gtk.ScrolledWindow()
        pid_scroll.set_size_request(180, -1)
        pid_box.append(pid_scroll)

        self._pid_list = Gtk.ListBox()
        self._pid_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self._pid_list.add_css_class("boxed-list")
        pid_scroll.set_child(self._pid_list)

        for pid in LOGGABLE_PIDS:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            row.set_margin_start(8)
            row.set_margin_end(8)
            row.set_margin_top(4)
            row.set_margin_bottom(4)
            check = Gtk.CheckButton(label=pid)
            check.connect("toggled", self._on_pid_toggled, pid)
            row.append(check)
            self._pid_list.append(row)

        paned.set_start_child(pid_box)
        paned.set_position(200)

        # Chart
        self._chart = ChartWidget()
        paned.set_end_child(self._chart)

    def _on_pid_toggled(self, check, pid):
        if check.get_active():
            self._selected_pids.add(pid)
        else:
            self._selected_pids.discard(pid)

    def _on_toggle_recording(self, btn):
        if self._recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self):
        if not self._selected_pids:
            self._status.set_text(_("Select at least one PID"))
            return
        if not self._obd.is_connected:
            self._status.set_text(_("Not connected"))
            return

        self._recording = True
        self._start_time = time.time()
        self._record_btn.set_label(_("Stop Recording"))
        self._record_btn.remove_css_class("suggested-action")
        self._record_btn.add_css_class("destructive-action")
        self._save_btn.set_sensitive(False)
        self._status.set_text(_("Recording…"))

        self._timer_id = GLib.timeout_add(500, self._record_tick)

    def _stop_recording(self):
        self._recording = False
        self._record_btn.set_label(_("Start Recording"))
        self._record_btn.remove_css_class("destructive-action")
        self._record_btn.add_css_class("suggested-action")
        self._save_btn.set_sensitive(bool(self._log_data))

        samples = sum(len(v) for v in self._log_data.values())
        self._status.set_text(_("Stopped — %d samples recorded") % samples)

    def _record_tick(self):
        if not self._recording:
            return False
        threading.Thread(target=self._read_and_store, daemon=True).start()
        return True

    def _read_and_store(self):
        try:
            import obd
        except ImportError:
            return

        now = time.time()
        elapsed = now - (self._start_time or now)
        results = {}

        for pid in self._selected_pids:
            try:
                cmd = obd.commands[pid]
                resp = self._obd.query(cmd)
                if resp and not resp.is_null():
                    try:
                        val = resp.value.magnitude
                    except AttributeError:
                        val = float(resp.value)
                    results[pid] = (elapsed, val)
            except (KeyError, Exception):
                pass

        if results:
            GLib.idle_add(self._store_results, results)

    def _store_results(self, results):
        for pid, (t, v) in results.items():
            if pid not in self._log_data:
                self._log_data[pid] = []
            self._log_data[pid].append((t, v))

        self._chart.set_data(self._log_data)
        samples = sum(len(v) for v in self._log_data.values())
        elapsed = time.time() - (self._start_time or time.time())
        self._status.set_text(_("Recording… %d samples (%.0fs)") % (samples, elapsed))
        return False

    def _on_save_csv(self, btn):
        dialog = Gtk.FileDialog()
        dialog.set_initial_name(f"obd2_log_{datetime.now():%Y%m%d_%H%M%S}.csv")

        filters = Gio.ListStore.new(Gtk.FileFilter)
        csv_filter = Gtk.FileFilter()
        csv_filter.set_name(_("CSV Files"))
        csv_filter.add_pattern("*.csv")
        filters.append(csv_filter)
        dialog.set_filters(filters)

        dialog.save(self.get_root(), None, self._on_save_done)

    def _on_save_done(self, dialog, result):
        try:
            f = dialog.save_finish(result)
            path = f.get_path()
            self._write_csv(path)
            self._status.set_text(_("Saved to %s") % path)
        except Exception as e:
            self._status.set_text(str(e))

    def _write_csv(self, path):
        """Write logged data to CSV."""
        pids = sorted(self._log_data.keys())
        if not pids:
            return

        # Merge all timestamps
        all_times = set()
        for pts in self._log_data.values():
            for t, v in pts:
                all_times.add(t)
        times = sorted(all_times)

        # Build lookup
        lookup = {}
        for pid, pts in self._log_data.items():
            for t, v in pts:
                lookup[(pid, t)] = v

        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([_("Time (s)")] + pids)
            for t in times:
                row = [f"{t:.2f}"]
                for pid in pids:
                    val = lookup.get((pid, t), "")
                    row.append(f"{val:.2f}" if isinstance(val, float) else str(val))
                writer.writerow(row)

    def _on_clear(self, btn):
        self._log_data.clear()
        self._chart.set_data({})
        self._save_btn.set_sensitive(False)
        self._status.set_text(_("Log cleared"))

    def get_log_data(self):
        """Return log data for export."""
        return {pid: [(t, v) for t, v in pts]
                for pid, pts in self._log_data.items()}
