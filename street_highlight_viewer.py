from tkinter import Tk, Canvas
from PIL import Image, ImageTk
import math

IMAGE_FILE = "beloit_map.png"

# Add more street dicts here as you capture them in simple_map_viewer.py
streets = [
    
        {"name": "St. Lawrence",
        "x1": 682.795456,
        "y1": 1662.413568,
        "x2": 237.31449600000016,
        "y2": 1664.1338880000003,},
        {'name': 'Brooks St', 'x1': 541.5986633187557, 'y1': 1665.0487515420446, 'x2': 584.9778330083558, 'y2': 1685.6645945628445},
        {'name': 'Madison Rd', 'x1': 483.1040630222224, 'y1': 1547.675861422222, 'x2': 203.599394577778, 'y2': 1262.3826347555553},
]

HOVER_DISTANCE = 10.0  # how close (in image pixels) the mouse must be to highlight

class StreetViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Beloit Street Trainer - Street Highlight Demo")

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
        self.offset_y = (900  - img_h * self.scale) / 2


        self.tk_image = None
        self.image_id = None

        self.last_x = 0
        self.last_y = 0
        self.dragging = False  # for panning with middle mouse

        self.highlighted_street = None  # current street under mouse

        self.draw_image()

        # Mouse bindings
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)

        # Middle mouse (scroll wheel button) for panning
        self.canvas.bind("<ButtonPress-2>", self.on_button_press)
        self.canvas.bind("<ButtonRelease-2>", self.on_button_release)
        self.canvas.bind("<B2-Motion>", self.on_mouse_drag)

        self.canvas.bind("<Motion>", self.on_mouse_move)

        # Left-click to "select" a street
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
        """Distance from point (px,py) to line segment (x1,y1)-(x2,y2) in image coords."""
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
        # Determine which street, if any, is under mouse
        self.highlighted_street = self.find_street_under_mouse(ix, iy)
        self.draw_image()  # redraw highlight

    def on_left_click(self, event):
        ix, iy = self.screen_to_image(event.x, event.y)
        s = self.find_street_under_mouse(ix, iy)
        if s:
            print(f"You clicked: {s['name']}")
        else:
            print("You clicked: no street")

    def draw_highlight(self):
        # Remove any existing highlight overlays
        self.canvas.delete("highlight")

        if not self.highlighted_street:
            return

        s = self.highlighted_street
        x1, y1, x2, y2 = s["x1"], s["y1"], s["x2"], s["y2"]

        # Convert endpoints to screen coords
        sx1, sy1 = self.image_to_screen(x1, y1)
        sx2, sy2 = self.image_to_screen(x2, y2)

        # Draw a thick line to highlight the street
        self.canvas.create_line(
            sx1, sy1, sx2, sy2,
            fill="yellow",
            width=6,
            tags="highlight",
        )

def main():
    root = Tk()
    app = StreetViewer(root)
    root.mainloop()

if __name__ == "__main__":
    main()
