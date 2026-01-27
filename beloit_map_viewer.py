import arcade

SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 900
SCREEN_TITLE = "Beloit Street Trainer - Map Viewer (Zoom + Pan)"

class MapWindow(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, resizable=False)
        arcade.set_background_color(arcade.color.BLACK)

        self.map_sprite = None

        # Zoom and camera
        self.zoom = 1.0
        self.min_zoom = 0.25
        self.max_zoom = 6.0

        # Camera center in map/image coordinates
        self.camera_x = 0.0
        self.camera_y = 0.0

        # Drag state
        self.dragging = False
        self.last_mouse_x = 0
        self.last_mouse_y = 0

    def setup(self):
        # Load your map image
        self.map_sprite = arcade.Sprite("beloit_map.png")

        # Start camera centered on the image
        tex = self.map_sprite.texture
        self.camera_x = tex.width / 2
        self.camera_y = tex.height / 2

    # ---------- coordinate helpers ----------

    def window_to_map(self, wx: float, wy: float):
        """Convert window coords (mouse) -> map image coords."""
        pixel_size = self.zoom

        cx = self.width / 2
        cy = self.height / 2

        dx = wx 
