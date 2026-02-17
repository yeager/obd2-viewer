"""Cairo-based gauge widgets for the dashboard."""

import math
import gettext

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk

_ = gettext.gettext


class ArcGauge(Gtk.DrawingArea):
    """A circular arc gauge rendered with Cairo."""

    def __init__(self, label="", unit="", min_val=0, max_val=100,
                 warn_threshold=None, danger_threshold=None):
        super().__init__()
        self._label = label
        self._unit = unit
        self._min_val = min_val
        self._max_val = max_val
        self._value = 0
        self._warn_threshold = warn_threshold
        self._danger_threshold = danger_threshold

        self.set_content_width(180)
        self.set_content_height(160)
        self.set_draw_func(self._draw)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, val):
        self._value = max(self._min_val, min(self._max_val, val))
        self.queue_draw()

    def _draw(self, area, cr, width, height):
        # Center and radius
        cx = width / 2
        cy = height * 0.55
        radius = min(width, height) * 0.38

        # Arc angles (from 135° to 405° = 270° sweep)
        start_angle = math.radians(135)
        end_angle = math.radians(405)
        sweep = end_angle - start_angle

        # Background arc
        cr.set_line_width(12)
        cr.set_source_rgba(0.3, 0.3, 0.3, 0.4)
        cr.arc(cx, cy, radius, start_angle, end_angle)
        cr.stroke()

        # Value arc
        frac = (self._value - self._min_val) / max(1, self._max_val - self._min_val)
        frac = max(0, min(1, frac))
        val_angle = start_angle + sweep * frac

        # Color based on thresholds
        if self._danger_threshold and self._value >= self._danger_threshold:
            cr.set_source_rgb(0.9, 0.2, 0.2)
        elif self._warn_threshold and self._value >= self._warn_threshold:
            cr.set_source_rgb(0.95, 0.75, 0.1)
        else:
            cr.set_source_rgb(0.3, 0.75, 0.4)

        cr.set_line_width(12)
        cr.set_line_cap(1)  # ROUND
        if frac > 0.001:
            cr.arc(cx, cy, radius, start_angle, val_angle)
            cr.stroke()

        # Value text
        cr.set_source_rgb(0.9, 0.9, 0.9)
        cr.select_font_face("sans-serif", 0, 1)  # BOLD

        # Main value
        val_str = f"{self._value:.0f}" if self._value == int(self._value) else f"{self._value:.1f}"
        cr.set_font_size(radius * 0.6)
        extents = cr.text_extents(val_str)
        cr.move_to(cx - extents.width / 2, cy + extents.height / 3)
        cr.show_text(val_str)

        # Unit
        cr.set_font_size(radius * 0.25)
        cr.set_source_rgba(0.7, 0.7, 0.7, 0.9)
        extents = cr.text_extents(self._unit)
        cr.move_to(cx - extents.width / 2, cy + radius * 0.55)
        cr.show_text(self._unit)

        # Label
        cr.set_font_size(radius * 0.22)
        cr.set_source_rgba(0.6, 0.6, 0.6, 0.8)
        cr.select_font_face("sans-serif", 0, 0)  # NORMAL
        extents = cr.text_extents(self._label)
        cr.move_to(cx - extents.width / 2, height - 4)
        cr.show_text(self._label)

        # Min/Max labels
        cr.set_font_size(radius * 0.18)
        min_str = str(int(self._min_val))
        max_str = str(int(self._max_val))
        min_ext = cr.text_extents(min_str)
        max_ext = cr.text_extents(max_str)

        # Min label at start of arc
        min_x = cx + radius * 1.15 * math.cos(start_angle)
        min_y = cy + radius * 1.15 * math.sin(start_angle)
        cr.move_to(min_x - min_ext.width / 2, min_y)
        cr.show_text(min_str)

        # Max label at end of arc
        max_x = cx + radius * 1.15 * math.cos(end_angle)
        max_y = cy + radius * 1.15 * math.sin(end_angle)
        cr.move_to(max_x - max_ext.width / 2, max_y)
        cr.show_text(max_str)


class BarGauge(Gtk.DrawingArea):
    """A horizontal bar gauge rendered with Cairo."""

    def __init__(self, label="", unit="", min_val=0, max_val=100,
                 warn_threshold=None, danger_threshold=None):
        super().__init__()
        self._label = label
        self._unit = unit
        self._min_val = min_val
        self._max_val = max_val
        self._value = 0
        self._warn_threshold = warn_threshold
        self._danger_threshold = danger_threshold

        self.set_content_width(200)
        self.set_content_height(60)
        self.set_draw_func(self._draw)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, val):
        self._value = max(self._min_val, min(self._max_val, val))
        self.queue_draw()

    def _draw(self, area, cr, width, height):
        margin = 8
        bar_h = 16
        bar_y = height / 2 - bar_h / 2 + 6
        bar_w = width - 2 * margin

        # Background
        cr.set_source_rgba(0.3, 0.3, 0.3, 0.4)
        self._rounded_rect(cr, margin, bar_y, bar_w, bar_h, bar_h / 2)
        cr.fill()

        # Value
        frac = (self._value - self._min_val) / max(1, self._max_val - self._min_val)
        frac = max(0, min(1, frac))
        fill_w = bar_w * frac

        if self._danger_threshold and self._value >= self._danger_threshold:
            cr.set_source_rgb(0.9, 0.2, 0.2)
        elif self._warn_threshold and self._value >= self._warn_threshold:
            cr.set_source_rgb(0.95, 0.75, 0.1)
        else:
            cr.set_source_rgb(0.3, 0.75, 0.4)

        if fill_w > 1:
            self._rounded_rect(cr, margin, bar_y, fill_w, bar_h, bar_h / 2)
            cr.fill()

        # Label + value text
        cr.set_source_rgb(0.85, 0.85, 0.85)
        cr.select_font_face("sans-serif", 0, 0)
        cr.set_font_size(12)
        val_str = f"{self._value:.0f}" if self._value == int(self._value) else f"{self._value:.1f}"
        text = f"{self._label}: {val_str} {self._unit}"
        extents = cr.text_extents(text)
        cr.move_to(margin, bar_y - 4)
        cr.show_text(text)

    def _rounded_rect(self, cr, x, y, w, h, r):
        cr.new_sub_path()
        cr.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
        cr.arc(x + w - r, y + r, r, 1.5 * math.pi, 2 * math.pi)
        cr.arc(x + w - r, y + h - r, r, 0, 0.5 * math.pi)
        cr.arc(x + r, y + h - r, r, 0.5 * math.pi, math.pi)
        cr.close_path()
