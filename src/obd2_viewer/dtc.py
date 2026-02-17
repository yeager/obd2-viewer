"""DTC (Diagnostic Trouble Codes) reader page."""

import threading
import gettext

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio, GObject

from .dtc_database import lookup_dtc, SEVERITY_CRITICAL, SEVERITY_WARNING

_ = gettext.gettext


class DTCPage(Gtk.Box):
    """DTC reader page with stored/pending codes and clear functionality."""

    def __init__(self, obd_connection):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self._obd = obd_connection

        self.set_margin_top(12)
        self.set_margin_bottom(12)
        self.set_margin_start(12)
        self.set_margin_end(12)

        # Header with buttons
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.append(btn_box)

        read_stored_btn = Gtk.Button(label=_("Read Stored DTCs"))
        read_stored_btn.add_css_class("suggested-action")
        read_stored_btn.connect("clicked", self._on_read_stored)
        btn_box.append(read_stored_btn)

        read_pending_btn = Gtk.Button(label=_("Read Pending DTCs"))
        read_pending_btn.connect("clicked", self._on_read_pending)
        btn_box.append(read_pending_btn)

        clear_btn = Gtk.Button(label=_("Clear DTCs"))
        clear_btn.add_css_class("destructive-action")
        clear_btn.connect("clicked", self._on_clear_dtcs)
        btn_box.append(clear_btn)

        spacer = Gtk.Box(hexpand=True)
        btn_box.append(spacer)

        self._status = Gtk.Label(label="")
        self._status.add_css_class("dim-label")
        btn_box.append(self._status)

        # DTC list with ColumnView
        scroll = Gtk.ScrolledWindow(vexpand=True, hexpand=True)
        self.append(scroll)

        # Use a ListBox with Adw.ActionRow for simplicity and Adwaita style
        self._list = Gtk.ListBox()
        self._list.set_selection_mode(Gtk.SelectionMode.NONE)
        self._list.add_css_class("boxed-list")
        scroll.set_child(self._list)

        self._dtc_data = []  # [(code, description, severity)]

        self._show_empty()

    def _show_empty(self):
        self._clear_list()
        row = Adw.ActionRow(title=_("No DTCs loaded"),
                            subtitle=_("Connect to a vehicle and read DTCs"))
        row.add_prefix(Gtk.Image.new_from_icon_name("dialog-information-symbolic"))
        self._list.append(row)

    def _clear_list(self):
        while True:
            child = self._list.get_first_child()
            if child is None:
                break
            self._list.remove(child)

    def _on_read_stored(self, btn):
        if not self._obd.is_connected:
            self._status.set_text(_("Not connected"))
            return
        self._status.set_text(_("Reading stored DTCs…"))
        threading.Thread(target=self._read_dtcs, args=("GET_DTC",), daemon=True).start()

    def _on_read_pending(self, btn):
        if not self._obd.is_connected:
            self._status.set_text(_("Not connected"))
            return
        self._status.set_text(_("Reading pending DTCs…"))
        threading.Thread(target=self._read_dtcs, args=("GET_CURRENT_DTC",), daemon=True).start()

    def _read_dtcs(self, command_name):
        try:
            import obd
            cmd = obd.commands[command_name]
            resp = self._obd.query(cmd)
            if resp and not resp.is_null():
                dtcs = resp.value  # list of (code, description) tuples
                results = []
                for code, _desc in dtcs:
                    desc, severity = lookup_dtc(code)
                    results.append((code, desc, severity))
                GLib.idle_add(self._display_dtcs, results)
            else:
                GLib.idle_add(self._display_dtcs, [])
        except ImportError:
            GLib.idle_add(self._status.set_text,
                          _("python-obd is not installed"))
        except Exception as e:
            GLib.idle_add(self._status.set_text, str(e))

    def _display_dtcs(self, dtcs):
        self._clear_list()
        self._dtc_data = dtcs

        if not dtcs:
            row = Adw.ActionRow(title=_("No DTCs found"),
                                subtitle=_("No diagnostic trouble codes stored"))
            row.add_prefix(Gtk.Image.new_from_icon_name("emblem-ok-symbolic"))
            self._list.append(row)
            self._status.set_text(_("No DTCs found"))
            return

        self._status.set_text(_("%d DTC(s) found") % len(dtcs))

        for code, desc, severity in dtcs:
            row = Adw.ActionRow(title=code, subtitle=desc)

            # Severity icon
            if severity == SEVERITY_CRITICAL:
                icon = Gtk.Image.new_from_icon_name("dialog-error-symbolic")
                icon.add_css_class("error")
            else:
                icon = Gtk.Image.new_from_icon_name("dialog-warning-symbolic")
                icon.add_css_class("warning")
            row.add_prefix(icon)

            # Severity label
            sev_label = Gtk.Label(label=severity.capitalize())
            if severity == SEVERITY_CRITICAL:
                sev_label.add_css_class("error")
            else:
                sev_label.add_css_class("warning")
            sev_label.set_valign(Gtk.Align.CENTER)
            row.add_suffix(sev_label)

            self._list.append(row)
        return False

    def _on_clear_dtcs(self, btn):
        if not self._obd.is_connected:
            self._status.set_text(_("Not connected"))
            return

        dialog = Adw.AlertDialog(
            heading=_("Clear Diagnostic Trouble Codes?"),
            body=_("This will reset all stored DTCs and freeze frame data. "
                   "The check engine light will turn off. This action cannot be undone."),
        )
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("clear", _("Clear DTCs"))
        dialog.set_response_appearance("clear", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        dialog.connect("response", self._on_clear_response)

        window = self.get_root()
        dialog.present(window)

    def _on_clear_response(self, dialog, response):
        if response != "clear":
            return
        self._status.set_text(_("Clearing DTCs…"))
        threading.Thread(target=self._do_clear_dtcs, daemon=True).start()

    def _do_clear_dtcs(self):
        try:
            import obd
            cmd = obd.commands["CLEAR_DTC"]
            self._obd.query(cmd)
            GLib.idle_add(self._on_dtcs_cleared)
        except ImportError:
            GLib.idle_add(self._status.set_text, _("python-obd is not installed"))
        except Exception as e:
            GLib.idle_add(self._status.set_text, str(e))

    def _on_dtcs_cleared(self):
        self._status.set_text(_("DTCs cleared successfully"))
        self._show_empty()
        return False

    def get_dtc_data(self):
        """Return current DTC data for export."""
        return [{"code": c, "description": d, "severity": s}
                for c, d, s in self._dtc_data]
