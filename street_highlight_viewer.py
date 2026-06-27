from tkinter import Tk, Canvas, Button
from PIL import Image, ImageTk
import math
import random
import csv
from shapely import wkt  # pip install shapely


# -------------------------------------------------------------------
# Files exported from QGIS
# -------------------------------------------------------------------
IMAGE_FILE = "beloit_map.png"
CSV_FILE = "beloit_streets.csv"

# Geometry column name in your CSV
GEOM_COL = "WKT"

# Map canvas extent used for PNG export (EPSG:4326 – WGS 84)
MAP_MIN_X = -89.149630324  # West  (xmin, longitude)
MAP_MAX_X = -88.875148432  # East  (xmax, longitude)
MAP_MIN_Y = 42.461796857   # South (ymin, latitude)
MAP_MAX_Y = 42.604618935   # North (ymax, latitude)

# How close the mouse must be to a street (in image pixels)
HOVER_DISTANCE = 30.0

# Streets to always highlight as landmarks: name -> (color, width)
LANDMARK_STREETS = {
    "Cranston Road": ("lime green", 5),
    "Cranston Rd": ("lime green", 5),

    "Liberty Avenue": ("lime green", 5),
    "Liberty Ave": ("lime green", 5),
    "Liberty": ("lime green", 5),
    "East Liberty Avenue": ("lime green", 5),
    "East Liberty Ave": ("lime green", 5),
    "East Liberty": ("lime green", 5),

    "6th Street": ("lime green", 5),
    "6th St": ("lime green", 5),

    "South Afton Road": ("lime green", 5),
    "S Afton Road": ("lime green", 5),
    "South Afton Rd": ("lime green", 5),
    "S Afton Rd": ("lime green", 5),

    "Milwaukee Road": ("lime green", 5),
    "Milwaukee Rd": ("lime green", 5),

    "White Avenue": ("lime green", 5),
    "White Ave": ("lime green", 5),

    "Prairie Avenue": ("lime green", 5),
    "Prairie Ave": ("lime green", 5),

    "County Road G": ("lime green", 5),
    "County G": ("lime green", 5),
    "Highway G": ("lime green", 5),
    "State Highway G": ("lime green", 5),
}


# -------------------------------------------------------------------
# Data loading & coordinate mapping
# -------------------------------------------------------------------
def lonlat_to_image_xy(lon, lat, img_w, img_h):
    lon_span = MAP_MAX_X - MAP_MIN_X
    lat_span = MAP_MAX_Y - MAP_MIN_Y

    nx = (lon - MAP_MIN_X) / lon_span
    ny = (lat - MAP_MIN_Y) / lat_span

    x_img = nx * img_w
    y_img = (1.0 - ny) * img_h
    return x_img, y_img


def load_streets_from_csv(csv_path, img_w, img_h):
    streets = []

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("name", "").strip()
            if not name:
                continue

            wkt_text = row.get(GEOM_COL)
            if not wkt_text:
                continue

            try:
                geom = wkt.loads(wkt_text)
            except Exception:
                continue

            if geom.geom_type == "LineString":
                line_geoms = [geom]
            elif geom.geom_type == "MultiLineString":
                line_geoms = list(geom.geoms)
            else:
                continue

            for line in line_geoms:
                coords = list(line.coords)

                img_coords = []
                for lon, lat in coords:
                    x_img, y_img = lonlat_to_image_xy(lon, lat, img_w, img_h)
                    img_coords.append((x_img, y_img))

                for (x1, y1), (x2, y2) in zip(img_coords[:-1], img_coords[1:]):
                    streets.append(
                        {"name": name, "x1": x1, "y1": y1, "x2": x2, "y2": y2}
                    )

    return streets


# -------------------------------------------------------------------
# Main viewer
# -------------------------------------------------------------------
class StreetViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Beloit Street Trainer")

        self.canvas = Canvas(root, width=1200, height=900, bg="black")
        self.canvas.pack(fill="both", expand=True)

        # Hint button (larger)
        self.hint_button = Button(
            self.canvas,
            text="HINT",
            command=self.use_hint,
            bg="purple",
            fg="white",
            font=("Arial", 14, "bold"),
            width=8,
            height=2,
        )
        self.canvas.create_window(
            1180, 20, window=self.hint_button, anchor="ne", tags="hint_button"
        )

        # Skip button
        self.skip_button = Button(
            self.canvas,
            text="SKIP",
            command=self.skip_street,
            bg="gray",
            fg="white",
            font=("Arial", 14, "bold"),
            width=8,
            height=2,
        )
        self.canvas.create_window(
            1180, 90, window=self.skip_button, anchor="ne", tags="skip_button"
        )

        # Load map image
        self.image = Image.open(IMAGE_FILE)
        img_w, img_h = self.image.size

        # Load streets
        self.streets = load_streets_from_csv(CSV_FILE, img_w, img_h)
        self.street_names = sorted({s["name"] for s in self.streets})

        # Start zoomed
        scale_x = 1200 / img_w
        scale_y = 900 / img_h
        self.scale = min(scale_x, scale_y) * 2.0
        self.min_scale = self.scale
        self.max_scale = 6.0

        self.offset_x = (1200 - img_w * self.scale) / 2
        self.offset_y = (900 - img_h * self.scale) / 2

        self.tk_image = None
        self.image_id = None

        self.last_x = 0
        self.last_y = 0
        self.dragging = False

        self._zoom_after_id = None

        # Hover
        self.highlighted_street_name = None

        # Quiz
        self.current_target_name = None
        self.score = 0.0
        self.best_score = 0.0
        self.correct_count = 0
        self.status_text_id = None

        # Feedback
        self.last_result_message = None
        self.last_result_color = "red"
        self.correct_highlight_name = None
        self.wrong_highlight_name = None

        # Blinking for wrong answer correct street
        self.blink_state_on = True
        self.blink_remaining = 0
        self.blink_after_id = None

        # Hint state
        self.hint_used_for_current = False
        self.hint_street_names = []

        # Auto-clear feedback timer
        self.clear_after_id = None

        # Zoom animation state
        self._anim_after_id = None
        self._anim_gen = 0

        # Wrong-street blink state
        self.wrong_blink_on = True
        self.wrong_blink_after_id = None
        self.wrong_blink_gen = 0

        self.draw_image()
        self.draw_landmarks()
        self.pick_new_target()
        self.update_status_text()
        self.draw_result_message()

        # Mouse bindings
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind("<ButtonPress-2>", self.on_button_press)
        self.canvas.bind("<ButtonRelease-2>", self.on_button_release)
        self.canvas.bind("<B2-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonPress-3>", self.on_button_press)
        self.canvas.bind("<ButtonRelease-3>", self.on_button_release)
        self.canvas.bind("<B3-Motion>", self.on_mouse_drag)
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<Button-1>", self.on_left_click)
        self.root.bind("<Left>", self.on_arrow_key)
        self.root.bind("<Right>", self.on_arrow_key)
        self.root.bind("<Up>", self.on_arrow_key)
        self.root.bind("<Down>", self.on_arrow_key)

    # ---------- core image rendering ----------

    def draw_image(self):
        w, h = self.image.size
        scaled = self.image.resize(
            (int(w * self.scale), int(h * self.scale)),
            Image.Resampling.LANCZOS,
        )
        self.tk_image = ImageTk.PhotoImage(scaled)
        if self.image_id is None:
            self.image_id = self.canvas.create_image(
                self.offset_x, self.offset_y, anchor="nw", image=self.tk_image
            )
        else:
            self.canvas.itemconfig(self.image_id, image=self.tk_image)
            self.canvas.coords(self.image_id, self.offset_x, self.offset_y)

    def draw_landmarks(self):
        self.canvas.delete("landmark")

        for s in self.streets:
            name = s["name"]
            if name not in LANDMARK_STREETS:
                continue
            color, width = LANDMARK_STREETS[name]
            x1, y1, x2, y2 = s["x1"], s["y1"], s["x2"], s["y2"]
            sx1, sy1 = self.image_to_screen(x1, y1)
            sx2, sy2 = self.image_to_screen(x2, y2)
            self.canvas.create_line(
                sx1, sy1, sx2, sy2,
                fill=color,
                width=width,
                tags="landmark",
            )

    def screen_to_image(self, sx, sy):
        ix = (sx - self.offset_x) / self.scale
        iy = (sy - self.offset_y) / self.scale
        return ix, iy

    def image_to_screen(self, ix, iy):
        sx = ix * self.scale + self.offset_x
        sy = iy * self.scale + self.offset_y
        return sx, sy

    # ---------- zoom & pan ----------

    def on_mouse_wheel(self, event):
        self._cancel_anim()
        old_scale = self.scale

        if self.scale < 3.0:
            zoom_factor = 1.10
        elif self.scale < 4.5:
            zoom_factor = 1.07
        else:
            zoom_factor = 1.04

        if event.delta > 0:
            self.scale *= zoom_factor
        else:
            self.scale /= zoom_factor

        self.scale = max(self.min_scale, min(self.max_scale, self.scale))

        mx, my = event.x, event.y
        if abs(self.scale - old_scale) > 1e-9:
            self.offset_x = mx - (mx - self.offset_x) * (self.scale / old_scale)
            self.offset_y = my - (my - self.offset_y) * (self.scale / old_scale)

            if self._zoom_after_id is not None:
                self.canvas.after_cancel(self._zoom_after_id)

            self._zoom_after_id = self.canvas.after(30, self._apply_zoom_redraw)

    def _apply_zoom_redraw(self):
        self._zoom_after_id = None
        self.draw_image()
        self.draw_landmarks()
        self.draw_highlight()
        self.draw_hint_highlights()
        self.draw_result_highlights()
        self.draw_result_message()
        self.update_status_text()

    def on_button_press(self, event):
        self.dragging = True
        self.last_x = event.x
        self.last_y = event.y

    def on_button_release(self, event):
        self.dragging = False

    def on_mouse_drag(self, event):
        if not self.dragging:
            return

        self._cancel_anim()
        dx = event.x - self.last_x
        dy = event.y - self.last_y
        self.offset_x += dx
        self.offset_y += dy
        self.last_x = event.x
        self.last_y = event.y

        if self.image_id is not None:
            self.canvas.coords(self.image_id, self.offset_x, self.offset_y)

        self.draw_landmarks()
        self.draw_highlight()
        self.draw_hint_highlights()
        self.draw_result_highlights()
        self.draw_result_message()
        self.update_status_text()

    # ---------- street hover & click ----------

    @staticmethod
    def distance_point_to_segment(px, py, x1, y1, x2, y2):
        vx = x2 - x1
        vy = y2 - y1
        wx = px - x1
        wy = py - y1

        seg_len_sq = vx * vx + vy * vy
        if seg_len_sq == 0:
            return math.hypot(px - x1, py - y1)

        t = (wx * vx + wy * vy) / seg_len_sq
        t = max(0.0, min(1.0, t))

        proj_x = x1 + t * vx
        proj_y = y1 + t * vy
        return math.hypot(px - proj_x, py - proj_y)

    def find_street_under_mouse(self, ix, iy):
        best_street = None
        best_dist = HOVER_DISTANCE
        for s in self.streets:
            d = self.distance_point_to_segment(
                ix, iy, s["x1"], s["y1"], s["x2"], s["y2"]
            )
            if d < best_dist:
                best_dist = d
                best_street = s
        return best_street

    def on_mouse_move(self, event):
        ix, iy = self.screen_to_image(event.x, event.y)
        s = self.find_street_under_mouse(ix, iy)
        new_name = s["name"] if s else None

        if new_name != self.highlighted_street_name:
            self.highlighted_street_name = new_name
            self.draw_highlight()
            self.update_status_text()

    def on_left_click(self, event):
        """Left-click = answer: did they click the target street?"""
        ix, iy = self.screen_to_image(event.x, event.y)
        s = self.find_street_under_mouse(ix, iy)

        # Reset per-click feedback (but not hint info)
        self.last_result_message = None
        self.correct_highlight_name = None
        self.wrong_highlight_name = None
        self._cancel_blink()
        self._cancel_wrong_blink()
        self._cancel_anim()

        if s:
            clicked_name = s["name"]

            if (
                self.current_target_name is not None
                and clicked_name == self.current_target_name
            ):
                # Correct answer
                if self.hint_used_for_current:
                    self.score += 0.25
                else:
                    self.score += 1.0

                self.correct_count += 1
                if self.score > self.best_score:
                    self.best_score = self.score

                self.last_result_message = (
                    f"Correct! You found {clicked_name}"
                    + (" (with hint)" if self.hint_used_for_current else "")
                )
                self.last_result_color = "lime green"
                self.correct_highlight_name = clicked_name  # blue line

                # Clear hint for next question
                self.hint_used_for_current = False
                self.hint_street_names = []

                self.draw_result_highlights()
                self.draw_hint_highlights()
                self.draw_result_message()
                self.update_status_text()
                self.pick_new_target()
                self.schedule_clear_feedback()
            else:
                # Wrong answer
                self.score = 0.0

                old_correct = self.current_target_name

                self.last_result_message = f"Wrong!\nYou clicked: {clicked_name}"
                self.last_result_color = "red"

                self.correct_highlight_name = old_correct
                self.wrong_highlight_name = clicked_name

                self.hint_used_for_current = False
                self.hint_street_names = []
                self.pick_new_target()
                self._start_wrong_blink()
                self.zoom_out_to_street(old_correct)
                self.draw_result_highlights()
                self.draw_result_message()
                self.update_status_text()
                self.schedule_clear_feedback(6000)
        else:
            # Clicked on empty map: do nothing
            self.draw_result_highlights()
            self.draw_hint_highlights()
            self.draw_result_message()
            self.update_status_text()

    # ---------- hint logic ----------

    def use_hint(self):
        """Highlight 4 candidate streets in solid purple, including the correct one."""
        if not self.current_target_name or self.hint_used_for_current:
            return

        self.hint_used_for_current = True
        self.hint_button.config(state="disabled")

        other_names = [n for n in self.street_names if n != self.current_target_name]
        random.shuffle(other_names)
        candidates = [self.current_target_name] + other_names[:3]
        random.shuffle(candidates)

        self.hint_street_names = candidates
        self.draw_hint_highlights()
        self.update_status_text()

    def draw_hint_highlights(self):
        """Solid purple hint lines."""
        self.canvas.delete("hint_highlight")

        if not self.hint_street_names:
            return

        for s in self.streets:
            if s["name"] not in self.hint_street_names:
                continue
            x1, y1, x2, y2 = s["x1"], s["y1"], s["x2"], s["y2"]
            sx1, sy1 = self.image_to_screen(x1, y1)
            sx2, sy2 = self.image_to_screen(x2, y2)
            self.canvas.create_line(
                sx1,
                sy1,
                sx2,
                sy2,
                fill="purple",
                width=4,
                tags="hint_highlight",
            )

    # ---------- auto-clear feedback ----------

    def schedule_clear_feedback(self, delay_ms=4000):
        """Clear result highlights/messages after delay_ms milliseconds."""
        if self.clear_after_id is not None:
            self.canvas.after_cancel(self.clear_after_id)
            self.clear_after_id = None
        self.clear_after_id = self.canvas.after(delay_ms, self.clear_feedback)

    def clear_feedback(self):
        """Clear result highlights, messages, and hint lines."""
        self._cancel_wrong_blink()
        self.clear_after_id = None
        self.last_result_message = None
        self.correct_highlight_name = None
        self.wrong_highlight_name = None
        self.hint_street_names = []
        self.canvas.delete("result_highlight")
        self.canvas.delete("result_text")
        self.canvas.delete("hint_highlight")
        self.update_status_text()


    # ---------- blinking logic for correct street ----------

    def _cancel_blink(self):
        if self.blink_after_id is not None:
            self.canvas.after_cancel(self.blink_after_id)
            self.blink_after_id = None
        self.blink_remaining = 0
        self.blink_state_on = True

    def _blink_correct_street(self):
        """Toggle visibility of correct street a few times after a wrong answer."""
        self.canvas.delete("result_highlight")
        self.canvas.delete("result_text")

        # Wrong street (red) always visible
        if self.wrong_highlight_name:
            for s in self.streets:
                if s["name"] != self.wrong_highlight_name:
                    continue
                x1, y1, x2, y2 = s["x1"], s["y1"], s["x2"], s["y2"]
                sx1, sy1 = self.image_to_screen(x1, y1)
                sx2, sy2 = self.image_to_screen(x2, y2)
                self.canvas.create_line(
                    sx1,
                    sy1,
                    sx2,
                    sy2,
                    fill="red",
                    width=7,
                    tags="result_highlight",
                )

        # Correct street in purple when blink_state_on is True
        if self.correct_highlight_name and self.blink_state_on:
            for s in self.streets:
                if s["name"] != self.correct_highlight_name:
                    continue
                x1, y1, x2, y2 = s["x1"], s["y1"], s["x2"], s["y2"]
                sx1, sy1 = self.image_to_screen(x1, y1)
                sx2, sy2 = self.image_to_screen(x2, y2)
                self.canvas.create_line(
                    sx1,
                    sy1,
                    sx2,
                    sy2,
                    fill="purple",
                    width=9,
                    tags="result_highlight",
                )

        self.draw_result_message()

        self.blink_remaining -= 1
        if self.blink_remaining > 0:
            self.blink_state_on = not self.blink_state_on
            self.blink_after_id = self.canvas.after(200, self._blink_correct_street)
        else:
            self.blink_state_on = True
            self.blink_after_id = None
            self.draw_result_highlights()
            self.draw_result_message()

    # ---------- drawing highlights ----------

    def draw_highlight(self):
        """Yellow hover highlight."""
        self.canvas.delete("highlight")

        if not self.highlighted_street_name:
            return

        target_name = self.highlighted_street_name

        for s in self.streets:
            if s["name"] != target_name:
                continue

            x1, y1, x2, y2 = s["x1"], s["y1"], s["x2"], s["y2"]
            sx1, sy1 = self.image_to_screen(x1, y1)
            sx2, sy2 = self.image_to_screen(x2, y2)

            self.canvas.create_line(
                sx1,
                sy1,
                sx2,
                sy2,
                fill="yellow",
                width=6,
                tags="highlight",
            )

    def draw_result_highlights(self):
        """Blue for correct (on correct answer), red (blinking) for wrong street."""
        self.canvas.delete("result_highlight")

        if self.correct_highlight_name and self.wrong_blink_on:
            for s in self.streets:
                if s["name"] != self.correct_highlight_name:
                    continue
                x1, y1, x2, y2 = s["x1"], s["y1"], s["x2"], s["y2"]
                sx1, sy1 = self.image_to_screen(x1, y1)
                sx2, sy2 = self.image_to_screen(x2, y2)
                self.canvas.create_line(
                    sx1, sy1, sx2, sy2,
                    fill="blue", width=8, tags="result_highlight",
                )

        if self.wrong_highlight_name:
            for s in self.streets:
                if s["name"] != self.wrong_highlight_name:
                    continue
                x1, y1, x2, y2 = s["x1"], s["y1"], s["x2"], s["y2"]
                sx1, sy1 = self.image_to_screen(x1, y1)
                sx2, sy2 = self.image_to_screen(x2, y2)
                self.canvas.create_line(
                    sx1, sy1, sx2, sy2,
                    fill="red", width=7, tags="result_highlight",
                )

    def draw_result_message(self):
        """Correct message at center-top; wrong message under Skip button (right side)."""
        self.canvas.delete("result_text")

        if not self.last_result_message:
            return

        is_wrong = self.last_result_color == "red"

        if is_wrong:
            # Two lines, right-aligned under the Skip button
            lines = self.last_result_message.split("\n", 1)
            font_sizes = [18, 14]
            x, anchor = 1170, "ne"
            y = 148
            for i, line in enumerate(lines):
                fsize = font_sizes[min(i, len(font_sizes) - 1)]
                ft = ("Arial", fsize, "bold")
                for dx in (-1, 1):
                    for dy in (-1, 1):
                        self.canvas.create_text(
                            x + dx, y + dy, text=line,
                            fill="black", font=ft, anchor=anchor, tags="result_text",
                        )
                self.canvas.create_text(
                    x, y, text=line,
                    fill="red", font=ft, anchor=anchor, tags="result_text",
                )
                y += fsize + 4
        else:
            # Single line, centered at top
            ft = ("Arial", 24, "bold")
            for dx in (-2, 2):
                for dy in (-2, 2):
                    self.canvas.create_text(
                        600 + dx, 60 + dy,
                        text=self.last_result_message, fill="black",
                        font=ft, anchor="n", tags="result_text",
                    )
            self.canvas.create_text(
                600, 60,
                text=self.last_result_message, fill=self.last_result_color,
                font=ft, anchor="n", tags="result_text",
            )

    # ---------- quiz helpers ----------

    def pick_new_target(self):
        if not self.street_names:
            self.current_target_name = None
        else:
            candidates = [n for n in self.street_names if n != self.current_target_name]
            if not candidates:
                candidates = self.street_names
            self.current_target_name = random.choice(candidates)
        self.hint_button.config(state="normal")

    def draw_outlined_text(
        self,
        x,
        y,
        text,
        fill_color="yellow",
        stroke_color="black",
        stroke_width=2,
        font_size=16,
    ):
        font_tuple = ("Arial", font_size, "bold")

        for dx in range(-stroke_width, stroke_width + 1):
            for dy in range(-stroke_width, stroke_width + 1):
                if dx == 0 and dy == 0:
                    continue
                self.canvas.create_text(
                    x + dx,
                    y + dy,
                    text=text,
                    fill=stroke_color,
                    font=font_tuple,
                    anchor="nw",
                    tags="status",
                )

        return self.canvas.create_text(
            x,
            y,
            text=text,
            fill=fill_color,
            font=font_tuple,
            anchor="nw",
            tags="status",
        )

    def update_status_text(self):
        self.canvas.delete("status")

        self.draw_outlined_text(
            10, 10, "FIND:",
            fill_color="#aaaaaa", stroke_color="black", stroke_width=2, font_size=11,
        )
        name = self.current_target_name or "(no streets)"
        self.status_text_id = self.draw_outlined_text(
            10, 24, name,
            fill_color="yellow", stroke_color="black", stroke_width=2, font_size=22,
        )
        score_text = (
            f"Score: {self.score:.2f}  |  Best: {self.best_score:.2f}  |  Correct: {self.correct_count}"
        )
        self.draw_outlined_text(
            10, 52, score_text,
            fill_color="white", stroke_color="black", stroke_width=2, font_size=13,
        )


    def _start_wrong_blink(self):
        self._cancel_wrong_blink()
        gen = self.wrong_blink_gen
        def blink():
            if self.wrong_blink_gen != gen:
                return
            self.wrong_blink_on = not self.wrong_blink_on
            self.draw_result_highlights()
            self.wrong_blink_after_id = self.canvas.after(350, blink)
        self.wrong_blink_on = True
        self.wrong_blink_after_id = self.canvas.after(350, blink)

    def _cancel_wrong_blink(self):
        if self.wrong_blink_after_id is not None:
            self.canvas.after_cancel(self.wrong_blink_after_id)
            self.wrong_blink_after_id = None
        self.wrong_blink_gen += 1
        self.wrong_blink_on = True

    def _redraw_all(self):
        self.draw_image()
        self.draw_landmarks()
        self.draw_highlight()
        self.draw_hint_highlights()
        self.draw_result_highlights()
        self.draw_result_message()
        self.update_status_text()

    def _cancel_anim(self):
        if self._anim_after_id is not None:
            self.canvas.after_cancel(self._anim_after_id)
            self._anim_after_id = None
        self._anim_gen += 1

    def _animate_to(self, target_scale, target_ox, target_oy, duration_ms, on_done=None):
        frames = max(1, duration_ms // 16)
        start_scale = self.scale
        start_ox, start_oy = self.offset_x, self.offset_y
        step_ms = duration_ms // frames
        gen = self._anim_gen

        def step(i):
            if self._anim_gen != gen:
                return
            t = i / frames
            e = t * t * (3 - 2 * t)  # smoothstep
            self.scale = start_scale + (target_scale - start_scale) * e
            self.offset_x = start_ox + (target_ox - start_ox) * e
            self.offset_y = start_oy + (target_oy - start_oy) * e
            self._redraw_all()
            if i < frames:
                self._anim_after_id = self.canvas.after(step_ms, lambda: step(i + 1))
            else:
                self._anim_after_id = None
                if on_done:
                    on_done()

        step(0)

    def zoom_out_to_street(self, name):
        """Zoom out so the correct street is visible and centered on screen."""
        self._cancel_anim()
        xs, ys = [], []
        for s in self.streets:
            if s["name"] != name:
                continue
            xs.extend([s["x1"], s["x2"]])
            ys.extend([s["y1"], s["y2"]])
        if not xs:
            return

        cx = (min(xs) + max(xs)) / 2
        cy = (min(ys) + max(ys)) / 2
        W = (self.canvas.winfo_width() or 1200) / 2
        H = (self.canvas.winfo_height() or 900) / 2

        target_scale = self.min_scale * 1.25
        target_ox = W - cx * target_scale
        target_oy = H - cy * target_scale

        self._animate_to(target_scale, target_ox, target_oy, 900)

    def skip_street(self):
        """Skip the current street without penalty."""
        self._cancel_blink()
        self._cancel_wrong_blink()
        self._cancel_anim()
        self.hint_used_for_current = False
        self.hint_street_names = []
        self.last_result_message = None
        self.correct_highlight_name = None
        self.wrong_highlight_name = None
        self.canvas.delete("result_highlight")
        self.canvas.delete("result_text")
        self.canvas.delete("hint_highlight")
        self.pick_new_target()
        self.update_status_text()

    def on_arrow_key(self, event):
        """Pan the map with arrow keys."""
        self._cancel_anim()
        step = 40
        if event.keysym == "Left":
            self.offset_x += step
        elif event.keysym == "Right":
            self.offset_x -= step
        elif event.keysym == "Up":
            self.offset_y += step
        elif event.keysym == "Down":
            self.offset_y -= step

        if self.image_id is not None:
            self.canvas.coords(self.image_id, self.offset_x, self.offset_y)
        self.draw_landmarks()
        self.draw_highlight()
        self.draw_hint_highlights()
        self.draw_result_highlights()
        self.draw_result_message()
        self.update_status_text()


def main():
    root = Tk()
    app = StreetViewer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
