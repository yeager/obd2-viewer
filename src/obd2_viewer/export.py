"""Export functionality — CSV/JSON export dialog."""

import csv
import json
import gettext
from datetime import datetime

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GLib

from obd2_viewer import __version__

_ = gettext.gettext

APP_LABEL = "OBD2 Viewer"
AUTHOR = "Daniel Nylander"


class ExportDialog(Adw.Dialog):
    """Export dialog for CSV/JSON."""

    def __init__(self, data_sources, **kwargs):
        super().__init__(**kwargs)
        self.set_title(_("Export Data"))
        self.set_content_width(400)
        self.set_content_height(400)
        self._data_sources = data_sources  # dict of {name: callable}

        toolbar_view = Adw.ToolbarView()
        self.set_child(toolbar_view)

        header = Adw.HeaderBar()
        toolbar_view.add_top_bar(header)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        toolbar_view.set_content(content)

        # What to export
        source_group = Adw.PreferencesGroup(title=_("Data to Export"))
        content.append(source_group)

        self._source_checks = {}
        for name in data_sources:
            row = Adw.ActionRow(title=name)
            check = Gtk.CheckButton()
            check.set_active(True)
            row.add_prefix(check)
            row.set_activatable_widget(check)
            source_group.add(row)
            self._source_checks[name] = check

        # Format
        format_group = Adw.PreferencesGroup(title=_("Export Format"))
        content.append(format_group)

        self._format_csv = Gtk.CheckButton(label="CSV")
        self._format_json = Gtk.CheckButton(label="JSON")
        self._format_json.set_group(self._format_csv)
        self._format_csv.set_active(True)

        csv_row = Adw.ActionRow(title="CSV", subtitle=_("Comma-separated values"))
        csv_row.add_prefix(self._format_csv)
        csv_row.set_activatable_widget(self._format_csv)
        format_group.add(csv_row)

        json_row = Adw.ActionRow(title="JSON", subtitle=_("JavaScript Object Notation"))
        json_row.add_prefix(self._format_json)
        json_row.set_activatable_widget(self._format_json)
        format_group.add(json_row)

        # Export button
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12,
                          margin_top=24, margin_bottom=12, margin_start=12, margin_end=12)
        btn_box.set_halign(Gtk.Align.END)
        content.append(btn_box)

        export_btn = Gtk.Button(label=_("Export"))
        export_btn.add_css_class("suggested-action")
        export_btn.connect("clicked", self._on_export)
        btn_box.append(export_btn)

    def _on_export(self, btn):
        # Collect selected data
        data = {}
        for name, check in self._source_checks.items():
            if check.get_active():
                try:
                    data[name] = self._data_sources[name]()
                except Exception:
                    pass

        if not data:
            return

        is_json = self._format_json.get_active()
        ext = "json" if is_json else "csv"
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        dialog = Gtk.FileDialog()
        dialog.set_initial_name(f"obd2_export_{ts}.{ext}")

        filters = Gio.ListStore.new(Gtk.FileFilter)
        f = Gtk.FileFilter()
        f.set_name(f"{ext.upper()} {_('Files')}")
        f.add_pattern(f"*.{ext}")
        filters.append(f)
        dialog.set_filters(filters)

        dialog.save(
            self.get_root(),
            None,
            lambda d, r: self._on_save_done(d, r, data, is_json),
        )

    def _on_save_done(self, dialog, result, data, is_json):
        try:
            f = dialog.save_finish(result)
            path = f.get_path()
            if is_json:
                self._write_json(path, data)
            else:
                self._write_csv(path, data)
            self.close()
        except Exception:
            pass

    def _write_json(self, path, data):
        """Write export data as JSON."""
        export = {
            "exported_at": datetime.now().isoformat(),
            "application": f"{APP_LABEL} v{__version__}",
            "author": AUTHOR,
        }
        export.update(data)
        with open(path, "w") as f:
            json.dump(export, f, indent=2, default=str)

    def _write_csv(self, path, data):
        """Write export data as CSV."""
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([_("Export from OBD2 Viewer — %s") % datetime.now().isoformat()])
            writer.writerow([])

            for section, section_data in data.items():
                writer.writerow([f"=== {section} ==="])
                if isinstance(section_data, dict):
                    for key, val in section_data.items():
                        if isinstance(val, dict):
                            writer.writerow([key, val.get("value", ""), val.get("unit", "")])
                        else:
                            writer.writerow([key, val])
                elif isinstance(section_data, list):
                    if section_data and isinstance(section_data[0], dict):
                        keys = list(section_data[0].keys())
                        writer.writerow(keys)
                        for item in section_data:
                            writer.writerow([item.get(k, "") for k in keys])
                    else:
                        for item in section_data:
                            writer.writerow([item])
                writer.writerow([])
            writer.writerow([f"{APP_LABEL} v{__version__} — {AUTHOR}"])
