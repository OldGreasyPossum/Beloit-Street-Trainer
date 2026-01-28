from tkinter import Tk, Canvas
from PIL import Image, ImageTk
import math
import random

IMAGE_FILE = "beloit_map.png"

# Add more street dicts here as you capture them in simple_map_viewer.py
streets = [
    {"name": "St. Lawrence", "x1": 682.795456, "y1": 1662.413568, 
     "x2": 237.31449600000016, "y2": 1664.1338880000003},
    {'name': 'Brooks St', 'x1': 541.5986633187557, 'y1': 1665.0487515420446,
     'x2': 584.9778330083558, 'y2': 1685.6645945628445},
    {'name': 'Madison Rd', 'x1': 483.1040630222224, 'y1': 1547.675861422222,
     'x2': 203.599394577778, 'y2': 1262.3826347555553},
    {'name': 'Roosevelt Ave', 'x1': 684.668476088889, 'y1': 1634.4323623111113,
     'x2': 343.9704778666667, 'y2': 1635.7554613333334},
    {'name': 'Portland Ave', 'x1': 699.2225653333334, 'y1': 1604.0010848000002,
     'x2': 537.8044846222223, 'y2': 1604.0010848000002},
    {'name': 'Portland Ave', 'x1': 532.5120885333333, 'y1': 1607.9703818666667,
     'x2': 316.84694791111116, 'y2': 1609.293480888889},
    {'name': 'Liberty Ave', 'x1': 697.8994663111112, 'y1': 1545.7847278222223,
     'x2': 523.2503953777779, 'y2': 1552.4002229333335},
    {'name': 'Liberty Ave', 'x1': 517.9579992888889, 'y1': 1552.4002229333335,
     'x2': 95.74914719857803, 'y2': 1555.035546757689},
    {'name': 'Masters St', 'x1': 287.6470311111111, 'y1': 1557.0801688888891, 'x2': 288.68070222222224, 'y2': 1716.2655200000002},
    {'name': 'West St', 'x1': 234.22303182222225, 'y1': 1661.989388088889, 'x2': 232.2383832888889, 'y2': 1517.7715946666667},
    {'name': 'Crestview Dr', 'x1': 235.54613084444446, 'y1': 1536.2949809777779, 'x2': 258.03881422222224, 'y2': 1536.2949809777779},
    {'name': 'Laundale Dr', 'x1': 234.88458133333336, 'y1': 1517.1100451555558, 'x2': 258.03881422222224, 'y2': 1517.1100451555558},
    {'name': 'Ridgeway St', 'x1': 260.02346275555556, 'y1': 1550.1875207111111, 'x2': 260.6850122666667, 'y2': 1445.6626979555556},
    {'name': 'Forest Ave', 'x1': 263.33121031111114, 'y1': 1678.5281258666669, 'x2': 533.2434108444445, 'y2': 1675.8819278222225},
    {'name': 'West Grand Ave', 'x1': 263.99275982222224, 'y1': 1693.0822151111113, 'x2': 676.1381052444445, 'y2': 1690.4360170666669},
    {'name': 'West Grand Ave', 'x1': 676.1381052444445, 'y1': 1690.4360170666669, 'x2': 695.3230410666667, 'y2': 1695.0668636444445},
    {'name': 'West Grand Ave', 'x1': 697.3076896000001, 'y1': 1697.051512177778, 'x2': 704.5847342222223, 'y2': 1704.3285568000001},
    {'name': 'East Grand Ave', 'x1': 704.5847342222223, 'y1': 1704.3285568000001, 'x2': 715.1695264000001, 'y2': 1718.8826460444445},
    {'name': 'East Grand Ave', 'x1': 715.1695264000001, 'y1': 1718.8826460444445, 'x2': 852.834899322311, 'y2': 1718.6840313088},
    {'name': 'East Grand Ave', 'x1': 853.5123260216888, 'y1': 1719.3614580081778, 'x2': 860.6253063651554, 'y2': 1725.7970116522667},
    {'name': 'East Grand Ave', 'x1': 860.6253063651554, 'y1': 1725.7970116522667, 'x2': 860.6253063651554, 'y2': 1732.5712786460447},
    {'name': 'W Jackson St', 'x1': 265.0187170592998, 'y1': 1706.0381803887503, 'x2': 533.3431987659663, 'y2': 1703.9212219531948},
    {'name': 'Euclid Ave', 'x1': 274.54503001929976, 'y1': 1719.2691706109727, 'x2': 533.8724383748552, 'y2': 1718.2106913931948},
    {'name': 'Euclid Ave', 'x1': 538.1063552459664, 'y1': 1712.918295304306, 'x2': 643.4250374148552, 'y2': 1712.918295304306},
    {'name': 'Shirland Ave', 'x1': 318.4719175570775, 'y1': 1774.310089935417, 'x2': 631.2525264104107, 'y2': 1771.6638918909725},
    {'name': 'Kenwood Ave', 'x1': 359.22336744152193, 'y1': 1760.549860104306, 'x2': 533.8724383748552, 'y2': 1758.9621412776391},
    {'name': 'Kenwood Ave', 'x1': 539.1648344637441, 'y1': 1756.3159432331947, 'x2': 588.3841180904108, 'y2': 1757.9036620598615},
    {'name': 'Kenwood Ave', 'x1': 593.6765141792996, 'y1': 1755.7867036243058, 'x2': 632.8402452370774, 'y2': 1754.7282244065282},
    {'name': 'Vernon Ave', 'x1': 359.22336744152193, 'y1': 1747.3188698820836, 'x2': 533.3431987659663, 'y2': 1745.731151055417},
    {'name': 'Vernon Ave', 'x1': 537.5771156370774, 'y1': 1742.0264737931948, 'x2': 634.957203672633, 'y2': 1743.6141926198616},
    {'name': 'Highland Ave', 'x1': 345.46313761041085, 'y1': 1732.5001608331947, 'x2': 533.8724383748552, 'y2': 1731.441681615417},
    {'name': 'Highland Ave', 'x1': 538.1063552459664, 'y1': 1726.678525135417, 'x2': 642.8957978059663, 'y2': 1727.207764744306},
    {'name': 'Church St', 'x1': 797.200373688889, 'y1': 1689.8574196622226, 'x2': 794.7195630222224, 'y2': 1571.6054445511115},
]

HOVER_DISTANCE = 10.0  # how close (in image pixels) the mouse must be to highlight


class StreetViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Beloit Street Trainer")

        self.canvas = Canvas(root, width=1200, height=900, bg="black")
        self.canvas.pack(fill="both", expand=True)

        self.image = Image.open(IMAGE_FILE)

        # Start scaled to fit window
        img_w, img_h = self.image.size
        scale_x = 1200 / img_w
        scale_y = 900 / img_h
        self.scale = min(scale_x, scale_y)

        # Center the image
        self.offset_x = (1200 - img_w * self.scale) / 2
        self.offset_y = (900 - img_h * self.scale) / 2

        self.tk_image = None
        self.image_id = None

        self.last_x = 0
        self.last_y = 0
        self.dragging = False  # for panning with middle mouse

        # Hover highlight tracks the street name under the mouse
        self.highlighted_street_name = None

        # Quiz state
        self.street_names = sorted({s["name"] for s in streets})
        self.current_target_name = None
        self.score = 0
        self.best_score = 0
        self.status_text_id = None  # canvas text item

        self.draw_image()
        self.pick_new_target()
        self.update_status_text()

        # Mouse bindings
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)

        # Middle mouse (scroll wheel button) for panning
        self.canvas.bind("<ButtonPress-2>", self.on_button_press)
        self.canvas.bind("<ButtonRelease-2>", self.on_button_release)
        self.canvas.bind("<B2-Motion>", self.on_mouse_drag)

        self.canvas.bind("<Motion>", self.on_mouse_move)

        # Left-click to answer (select a street)
        self.canvas.bind("<Button-1>", self.on_left_click)

    # --------- core image rendering ---------

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

        # After drawing the map, draw any highlight overlay
        self.draw_highlight()
        # Re-draw status text so it stays visible
        self.update_status_text()

    def screen_to_image(self, sx, sy):
        ix = (sx - self.offset_x) / self.scale
        iy = (sy - self.offset_y) / self.scale
        return ix, iy

    def image_to_screen(self, ix, iy):
        sx = ix * self.scale + self.offset_x
        sy = iy * self.scale + self.offset_y
        return sx, sy

    # --------- zoom & pan ---------

    def on_mouse_wheel(self, event):
        old_scale = self.scale
        if event.delta > 0:
            self.scale *= 1.25
        else:
            self.scale /= 1.25

        self.scale = max(0.25, min(6.0, self.scale))

        mx, my = event.x, event.y
        if self.scale != old_scale:
            self.offset_x = mx - (mx - self.offset_x) * (self.scale / old_scale)
            self.offset_y = my - (my - self.offset_y) * (self.scale / old_scale)

        self.draw_image()

    def on_button_press(self, event):
        self.dragging = True
        self.last_x = event.x
        self.last_y = event.y

    def on_button_release(self, event):
        self.dragging = False

    def on_mouse_drag(self, event):
        dx = event.x - self.last_x
        dy = event.y - self.last_y
        self.offset_x += dx
        self.offset_y += dy
        self.last_x = event.x
        self.last_y = event.y
        self.draw_image()

    # --------- street hover & click ---------

    def distance_point_to_segment(self, px, py, x1, y1, x2, y2):
        """Distance from point (px,py) to line segment (x1,y1)-(x2,y2)."""
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
        for s in streets:
            d = self.distance_point_to_segment(ix, iy, s["x1"], s["y1"], s["x2"], s["y2"])
            if d < best_dist:
                best_dist = d
                best_street = s
        return best_street

    def on_mouse_move(self, event):
        ix, iy = self.screen_to_image(event.x, event.y)
        s = self.find_street_under_mouse(ix, iy)
        self.highlighted_street_name = s["name"] if s else None
        self.draw_image()

    def on_left_click(self, event):
        """Treat a left-click as an answer: did they click the target street?"""
        ix, iy = self.screen_to_image(event.x, event.y)
        s = self.find_street_under_mouse(ix, iy)
        if s:
            clicked_name = s["name"]
            print(f"You clicked: {clicked_name}")
            if self.current_target_name is not None and clicked_name == self.current_target_name:
                # Correct
                self.score += 1
                if self.score > self.best_score:
                    self.best_score = self.score
                self.pick_new_target()
            else:
                # Wrong street
                self.score = 0
                self.pick_new_target()
        else:
            print("You clicked: no street")
            # Missed completely = reset score
            self.score = 0
            self.pick_new_target()

        self.update_status_text()

    def draw_highlight(self):
        # Remove any existing highlight overlays
        self.canvas.delete("highlight")

        if not self.highlighted_street_name:
            return

        target_name = self.highlighted_street_name

        # Draw all segments that share this street name
        for s in streets:
            if s["name"] != target_name:
                continue

            x1, y1, x2, y2 = s["x1"], s["y1"], s["x2"], s["y2"]
            sx1, sy1 = self.image_to_screen(x1, y1)
            sx2, sy2 = self.image_to_screen(x2, y2)

            self.canvas.create_line(
                sx1, sy1, sx2, sy2,
                fill="yellow",
                width=6,
                tags="highlight",
            )

    # --------- quiz helpers ---------

    def pick_new_target(self):
        """Choose a new random street name for the next question."""
        if not self.street_names:
            self.current_target_name = None
        else:
            self.current_target_name = random.choice(self.street_names)
        print(f"Find: {self.current_target_name}")

    def draw_outlined_text(self, x, y, text, fill_color="yellow",
                           stroke_color="black", stroke_width=2, font_size=16):
        """Draw yellow text with a black outline using multiple create_text calls."""
        font_tuple = ("Arial", font_size, "bold")

        # Stroke: draw text around the center in a small square
        for dx in range(-stroke_width, stroke_width + 1):
            for dy in range(-stroke_width, stroke_width + 1):
                if dx == 0 and dy == 0:
                    continue
                self.canvas.create_text(
                    x + dx, y + dy,
                    text=text,
                    fill=stroke_color,
                    font=font_tuple,
                    anchor="nw",
                    tags="status",
                )

        # Main text on top
        return self.canvas.create_text(
            x, y,
            text=text,
            fill=fill_color,
            font=font_tuple,
            anchor="nw",
            tags="status",
        )

    def update_status_text(self):
        """Show current target, score, and best score at the top."""
        # Remove old text (all status-tagged items)
        self.canvas.delete("status")

        if self.current_target_name is None:
            text = f"Find: (no streets) | Score: {self.score} | Best: {self.best_score}"
        else:
            text = f"Find: {self.current_target_name} | Score: {self.score} | Best: {self.best_score}"

        # Draw near top-left of window (in screen coords) with yellow fill and black edge
        self.status_text_id = self.draw_outlined_text(
            10, 10, text,
            fill_color="yellow",
            stroke_color="black",
            stroke_width=2,
            font_size=16,
        )


def main():
    root = Tk()
    app = StreetViewer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
