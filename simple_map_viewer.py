from tkinter import Tk, Canvas, simpledialog
from PIL import Image, ImageTk

IMAGE_FILE = "beloit_map.png"

class MapViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Beloit Map - Simple Viewer (with street capture)")

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

        # Street capture state
        self.first_point = None      # (ix, iy)
        self.streets = []            # list of dicts with name, x1,y1,x2,y2

        self.draw_image()

        # Mouse bindings
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)

        # Middle mouse (scroll wheel button) for panning
        self.canvas.bind("<ButtonPress-2>", self.on_button_press)
        self.canvas.bind("<ButtonRelease-2>", self.on_button_release)
        self.canvas.bind("<B2-Motion>", self.on_mouse_drag)

        self.canvas.bind("<Motion>", self.on_mouse_move)

        # Right click to capture street endpoints
        self.canvas.bind("<Button-3>", self.on_right_click)

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

    def screen_to_image(self, sx, sy):
        ix = (sx - self.offset_x) / self.scale
        iy = (sy - self.offset_y) / self.scale
        return ix, iy

    # ------- zoom & pan -------

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

    def on_mouse_move(self, event):
        ix, iy = self.screen_to_image(event.x, event.y)
        print(f"Image coords under mouse: ({ix:.1f}, {iy:.1f})")

    # ------- street capture with right-click -------

    def on_right_click(self, event):
        ix, iy = self.screen_to_image(event.x, event.y)

        if self.first_point is None:
            # First endpoint
            self.first_point = (ix, iy)
            print(f"First point stored: ({ix:.1f}, {iy:.1f})")
        else:
            # Second endpoint → ask for name
            x1, y1 = self.first_point
            x2, y2 = ix, iy

            name = simpledialog.askstring(
                "Street Name",
                "Enter street name for this segment:",
                parent=self.root,
            )

            if name:
                street = {
                    "name": name,
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,
                }
                self.streets.append(street)
                print("Added street:", street)
                # Also print as a ready-to-paste line for a Python list
                print(
                    f'{{"name": "{name}", "x1": {x1:.6f}, "y1": {y1:.6f}, '
                    f'"x2": {x2:.6f}, "y2": {y2:.6f}}},'
                )
            else:
                print("Street name canceled; point discarded.")

            # Reset for next street
            self.first_point = None

def main():
    root = Tk()
    app = MapViewer(root)
    root.mainloop()
    # After closing, print all captured streets
    print("All captured streets:")
    for s in app.streets:
        print(s)

if __name__ == "__main__":
    main()
