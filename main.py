"""
Charleston Minesweeper -- main.py (Person B: UI + input), tkinter version

Controls:
    Left click   reveal a tile
    Right click  place/remove a flag
    Click the center button (or press R) to restart
    Press 1 / 2 / 3 to switch difficulty (beginner / intermediate / expert)
"""
import math
import random
import time
import tkinter as tk
import tkinter.font as tkfont
from board import Board
from assets import load_images

# ---------- Constants ----------
ART_SIZE = 16           # pixel size of the artwork files (16x16)
HEADER_HEIGHT = 60
TICK_MS = 200           # how often the timer label refreshes

# water ripple settings, change these if it feels too fast or slow
ANIM_MS = 30            # ms between redraws
WAVE_SPEED = 5.0        # tiles per second (lower = slower)
MAX_WAVE_SECONDS = 4.0  # so huge openings don't drag on forever
LOSS_SPEED_BOOST = 2.0  # mines pop faster after a loss
EDGE_JITTER = 0.10      # a little randomness so the edge isn't perfect
RESET_SCALE = 4         # size of the pineapple picture
MOOD_MS = 1200          # how long the face stays worried

# rows, cols, mines, scale
# scale = how many times bigger each art pixel is drawn on screen.
# On screen, one tile is ART_SIZE * scale pixels wide (16 * 3 = 48, etc.)
# Use whole numbers only so the pixel art stays sharp.
DIFFICULTIES = {
    "beginner":     (9, 9, 10, 3),      # window about 432 x 554
    "intermediate": (16, 16, 40, 2),    # window about 512 x 634
    "expert":       (16, 30, 99, 2),    # window about 960 x 634
}

# Placeholder colors (only used when an image file is missing)
COLOR_BG = "#1e1e28"
COLOR_HIDDEN = "#9696a0"
COLOR_REVEALED = "#e1d7b9"
COLOR_GRID_LINE = "#5a5a64"
COLOR_MINE = "#141414"
COLOR_FLAG = "#c82828"
COLOR_TEXT = "#f0f0f0"
COLOR_BUBBLE = "#fff8d1"    # same sand color as the hidden tiles
COLOR_BUBBLE_TEXT = "#1d1652"
SHOW_BUBBLE = True          # False = just plain text, no bubble
BUBBLE_HEIGHT = 52          # room under the header for the bubble
# what the pineapple says for each face
FACE_LINES = {"chill": "we chilling",
              "tense": "oh that was close..",
              "scared": "TOO CLOSE",
              "dead": "man, im dead.",
              "won": "we made it!"}       # didn't get a win line from the team yet

# colors a tile goes through right before it turns into water
# (seconds before it shows up, color)
WAVE_EDGE = [(0.30, "#b3e5e8"),     # almost water
             (0.65, "#d3edde")]     # damp sand
NUMBER_COLORS = {
    1: "#1e3cc8", 2: "#1e8c32", 3: "#c82828", 4: "#141482",
    5: "#821414", 6: "#148282", 7: "#141414", 8: "#6e6e6e",
}


class Game:
    """Owns the window, the Board, and drawing. tkinter runs the main loop."""

    def __init__(self, root):
        self.root = root
        root.title("Charleston Minesweeper")
        root.resizable(False, False)
        root.configure(bg=COLOR_BG)

        self.difficulty = "beginner"

        # Load the original 16x16 art once. Must happen after tk.Tk() exists.
        # Scaled copies for the current difficulty are made in start_new_game.
        self.base_images = load_images(ART_SIZE)
        self.images = {}

        # ----- Header: mine counter | restart button | timer -----
        header_font = ("Arial", 16, "bold")
        self.header = tk.Frame(root, bg=COLOR_BG, height=HEADER_HEIGHT)
        self.header.pack(fill="x")
        self.mine_label = tk.Label(self.header, font=header_font, fg=COLOR_TEXT,
                                   bg=COLOR_BG, width=11, anchor="w")
        self.mine_label.pack(side="left", padx=8, pady=8)
        self.timer_label = tk.Label(self.header, font=header_font, fg=COLOR_TEXT,
                                    bg=COLOR_BG, width=11, anchor="e")
        self.timer_label.pack(side="right", padx=8, pady=8)

        # reset button is a pineapple face now instead of the emoji
        # chill = clear tile, tense = clicked a 1, scared = 2 or more,
        # dead = lost, won = sunglasses (uses text if the images are missing)
        self.face_images = {}
        for face, key in (("chill", "face_chill"), ("tense", "face_tense"),
                          ("scared", "face_scared"), ("dead", "face_dead"),
                          ("won", "face_win")):
            if key in self.base_images:
                self.face_images[face] = self.base_images[key].zoom(RESET_SCALE)
        self.face_text = {"chill": ":)", "tense": ":|", "scared": ":O",
                          "dead": "X(", "won": "B)"}
        self.shown_face = None
        self.mood = "chill"          # face while the game is going
        self.mood_job = None         # timer for going back to chill
        # a Label instead of a Button so the see-through picture sits right on the
        # header color (real buttons draw their own grey box, esp. on mac)
        self.restart_button = tk.Label(self.header, font=header_font, fg=COLOR_TEXT,
                                       bg=COLOR_BG, cursor="hand2")
        self.restart_button.pack(expand=True, pady=2)
        self.restart_button.bind("<Button-1>", lambda event: self.start_new_game())

        # ----- Speech bubble under the header, the pineapple's dialogue -----
        self.speech_font = tkfont.Font(family="Arial", size=12, weight="bold")
        self.speech_canvas = tk.Canvas(root, bg=COLOR_BG, height=BUBBLE_HEIGHT,
                                       highlightthickness=0)
        self.speech_canvas.pack(fill="x")

        # ----- Canvas: where the grid is drawn -----
        self.canvas = tk.Canvas(root, bg=COLOR_BG, highlightthickness=0)
        self.canvas.pack()

        # ----- Input bindings -----
        self.canvas.bind("<Button-1>", self.on_left_click)
        self.canvas.bind("<Button-3>", self.on_right_click)
        root.bind("<Key>", self.on_key)
        # on mac right click comes through as Button-2 (or ctrl+click), so bind those too
        if root.tk.call("tk", "windowingsystem") == "aqua":
            self.canvas.bind("<Button-2>", self.on_right_click)
            self.canvas.bind("<Control-Button-1>", self.on_right_click)

        # animation stuff
        self.pending = {}        # {(row, col): time it should show up}
        self.anim_job = None     # the next scheduled redraw

        self.big_font = ("Arial", 28, "bold")
        self.small_font = ("Arial", 13, "bold")

        self.start_new_game()
        self.tick()   # starts the repeating timer refresh

    # ---------- Setup ----------
    def start_new_game(self):
        # stop the old animation if there was one
        if self.anim_job is not None:
            self.root.after_cancel(self.anim_job)
            self.anim_job = None
        self.pending = {}
        self.calm_down()             # back to chill

        rows, cols, mines, scale = DIFFICULTIES[self.difficulty]
        self.board = Board(rows, cols, mines)

        # Size of one tile on screen, and the whole grid
        self.cell_size = ART_SIZE * scale
        self.width = cols * self.cell_size
        self.height = rows * self.cell_size
        self.canvas.config(width=self.width, height=self.height)
        self.speech_canvas.config(width=self.width)
        self.shown_face = None       # forces the bubble to get redrawn at the new width

        # Make enlarged copies of every image. zoom(3) turns each pixel into a
        # 3x3 block. (This is a dictionary comprehension: build a new dict by
        # looping over the old one.)
        self.images = {key: image.zoom(scale) for key, image in self.base_images.items()}
        self.cell_font = ("Arial", int(self.cell_size * 0.45), "bold")

        self.start_time = None       # set on the first click
        self.final_seconds = None    # set when the game ends
        self.refresh()

    # ---------- Timer ----------
    def elapsed_seconds(self):
        if self.start_time is None:
            return 0
        if self.final_seconds is not None:
            return self.final_seconds
        return int(time.time() - self.start_time)

    def tick(self):
        """Runs every TICK_MS milliseconds, forever (like a Swing Timer)."""
        self.update_header()
        self.root.after(TICK_MS, self.tick)

    # ---------- Input ----------
    def on_key(self, event):
        key = event.keysym.lower()
        if key == "r":
            self.start_new_game()
        elif key in ("1", "2", "3"):
            self.difficulty = {"1": "beginner", "2": "intermediate", "3": "expert"}[key]
            self.start_new_game()

    def cell_from_event(self, event):
        """Convert pixel coordinates to (row, col). Returns None if outside."""
        row = event.y // self.cell_size   # // is integer division, like Java's int / int
        col = event.x // self.cell_size
        if 0 <= row < self.board.rows and 0 <= col < self.board.cols:
            return row, col
        return None

    def on_left_click(self, event):
        position = self.cell_from_event(event)
        if position is None:
            return
        if self.start_time is None:
            self.start_time = time.time()
        revealed = self.board.reveal(*position)    # * unpacks the (row, col) tuple
        if revealed:
            self.start_animation(revealed, position)
            self.react_to_click(*position)
        self.after_move()

    def on_right_click(self, event):
        position = self.cell_from_event(event)
        if position is None:
            return
        self.board.toggle_flag(*position)
        self.after_move()

    def after_move(self):
        # Freeze the timer when the game ends
        if self.board.state != "playing" and self.final_seconds is None:
            self.final_seconds = self.elapsed_seconds()
        self.refresh()

    # ---------- Pineapple face ----------
    def react_to_click(self, row, col):
        # picks the face from the tile you clicked, bigger number = more nervous
        cell = self.board.cells[row][col]
        if cell.is_mine:
            self.mood = "scared"         # turns into dead after the explosion
        elif cell.adjacent_count == 0:
            self.mood = "chill"
        elif cell.adjacent_count == 1:
            self.mood = "tense"
        else:
            self.mood = "scared"         # 2 or more

        # go back to chill after a bit, timer restarts on every click
        if self.mood_job is not None:
            self.root.after_cancel(self.mood_job)
        self.mood_job = self.root.after(MOOD_MS, self.calm_down)

    def calm_down(self):
        if self.mood_job is not None:
            self.root.after_cancel(self.mood_job)
            self.mood_job = None
        self.mood = "chill"
        if hasattr(self, "board"):       # no board yet on the first call
            self.update_header()

    def current_face(self):
        # winning or losing overrides the mood
        state = self.shown_state()
        if state == "won":
            return "won"
        if state == "lost":
            return "dead"
        return self.mood

    def draw_speech(self, text):
        c = self.speech_canvas
        c.delete("all")
        cx = self.width / 2          # pineapple sits in the middle of the header

        if not SHOW_BUBBLE:
            c.create_text(cx, BUBBLE_HEIGHT / 2, text=text, font=self.speech_font,
                          fill=COLOR_TEXT)
            return

        # size the bubble to fit the text
        pad_x, pad_y = 16, 7
        half_w = self.speech_font.measure(text) / 2 + pad_x
        text_h = self.speech_font.metrics("linespace")
        top = 12
        bottom = top + text_h + pad_y * 2
        left, right = cx - half_w, cx + half_w

        self.rounded_rect(left, top, right, bottom, 10)
        # little tail on top pointing up at the pineapple
        c.create_polygon(cx - 8, top, cx, top - 9, cx + 8, top,
                         fill=COLOR_BUBBLE, outline=COLOR_BUBBLE_TEXT, width=2)
        # cover the bubble's outline where the tail joins it
        c.create_line(cx - 7, top, cx + 7, top, fill=COLOR_BUBBLE, width=3)
        c.create_text(cx, (top + bottom) / 2, text=text, font=self.speech_font,
                      fill=COLOR_BUBBLE_TEXT)

    def rounded_rect(self, x1, y1, x2, y2, r):
        # tkinter has no rounded rectangle, so smooth a polygon instead
        points = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
                  x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
                  x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
        self.speech_canvas.create_polygon(points, smooth=True, fill=COLOR_BUBBLE,
                                          outline=COLOR_BUBBLE_TEXT, width=2)

    # REVEAL ANIMATION
    # the board reveals everything instantly, we just delay when each tile gets drawn.
    # tiles close to the click show up first and far ones later, using straight line
    # distance so it spreads in a circle. right before a tile shows up it goes through
    # a couple in-between colors so the edge looks soft
    def start_animation(self, revealed, origin):
        origin_row, origin_col = origin
        speed = WAVE_SPEED
        if self.board.state == "lost":
            speed *= LOSS_SPEED_BOOST       # mines go faster

        distances = {(r, c): math.hypot(r - origin_row, c - origin_col)
                     for r, c, _depth in revealed}
        # speed up if the opening is huge so it doesn't drag
        longest = max(distances.values())
        if longest / speed > MAX_WAVE_SECONDS:
            speed = longest / MAX_WAVE_SECONDS

        now = time.time()
        for pos, distance in distances.items():
            wobble = random.uniform(0, EDGE_JITTER) if distance > 0 else 0
            self.pending[pos] = now + distance / speed + wobble
        self.release_due_tiles()
        if self.pending and self.anim_job is None:
            self.anim_job = self.root.after(ANIM_MS, self.animate_step)

    def animate_step(self):
        self.anim_job = None
        self.release_due_tiles()
        if self.pending:
            self.anim_job = self.root.after(ANIM_MS, self.animate_step)
        self.refresh()

    def release_due_tiles(self):
        # show any tile whose time is up
        now = time.time()
        due = [pos for pos, when in self.pending.items() if when <= now]
        for pos in due:
            del self.pending[pos]
        # animation is done and we won, so flag the mines
        if not self.pending and self.board.state == "won":
            self.board.flag_all_mines()

    def shown_state(self):
        # what the player should see, a win/loss waits until the animation is done
        if self.pending:
            return "playing"
        return self.board.state

    # ---------- Drawing ----------
    def refresh(self):
        self.update_header()
        self.draw_grid()
        if self.shown_state() != "playing":
            self.draw_end_message()

    def update_header(self):
        remaining = self.board.mines - self.board.flags_placed()
        self.mine_label.config(text=f"Bombs: {remaining:03d}")
        self.timer_label.config(text=f"Timer: {min(self.elapsed_seconds(), 999):03d}")

        face = self.current_face()
        if face != self.shown_face:      # only change the button if the face is different
            self.shown_face = face
            self.draw_speech(FACE_LINES[face])
            if face in self.face_images:
                self.restart_button.config(image=self.face_images[face], text="")
            else:
                self.restart_button.config(image="", text=self.face_text[face], width=4)

    def draw_grid(self):
        self.canvas.delete("all")   # clear everything, then redraw
        for r in range(self.board.rows):
            for c in range(self.board.cols):
                x = c * self.cell_size
                y = r * self.cell_size
                self.draw_cell(r, c, x, y)

    def draw_cell(self, r, c, x, y):
        """Draws one tile with its top-left corner at (x, y). Reads the
        cell's state and picks which image (layer) to draw."""
        cell = self.board.cells[r][c]

        # revealed in the logic but the animation hasn't gotten to it yet
        if (r, c) in self.pending:
            seconds_left = self.pending[(r, c)] - time.time()
            for window, color in WAVE_EDGE:
                if seconds_left <= window:      # about to show up, tint it
                    self.draw_tint(x, y, color)
                    break
            else:                               # still far, just sand
                self.draw_layer("hidden", x, y, self.placeholder_hidden)
            return

        if not cell.is_revealed:
            # wrong flags get an X after a loss
            if (self.board.state == "lost" and cell.is_flagged and not cell.is_mine):
                self.draw_layer("notmine", x, y, self.draw_flag)
            else:
                self.draw_layer("hidden", x, y, self.placeholder_hidden)
                if cell.is_flagged:
                    self.draw_layer("flag", x, y, self.draw_flag)
        elif cell.is_mine:
            if (r, c) == self.board.exploded:      # the one you clicked
                self.draw_layer("exploded", x, y, self.placeholder_mine)
            else:
                self.draw_layer(0, x, y, self.placeholder_revealed)   # background
                self.draw_layer("mine", x, y, self.placeholder_mine)  # mine on top
        else:
            n = cell.adjacent_count
            self.draw_layer(n, x, y, lambda px, py: self.placeholder_number(n, px, py))

    def draw_tint(self, x, y, color):
        s = self.cell_size
        self.canvas.create_rectangle(x, y, x + s, y + s, fill=color, outline="")

    def draw_layer(self, key, x, y, fallback):
        """Draw the image stored under `key` if we have it; otherwise call
        the fallback function (a placeholder shape)."""
        image = self.images.get(key)
        if image is not None:
            self.canvas.create_image(x, y, image=image, anchor="nw")
        else:
            fallback(x, y)

    # ---------- Placeholder shapes (used only when an image file is missing) ----------
    def placeholder_hidden(self, x, y):
        s = self.cell_size
        self.canvas.create_rectangle(x, y, x + s, y + s,
                                     fill=COLOR_HIDDEN, outline=COLOR_GRID_LINE)

    def placeholder_revealed(self, x, y):
        s = self.cell_size
        self.canvas.create_rectangle(x, y, x + s, y + s,
                                     fill=COLOR_REVEALED, outline=COLOR_GRID_LINE)

    def placeholder_mine(self, x, y):
        s = self.cell_size
        pad = s // 4
        self.canvas.create_oval(x + pad, y + pad, x + s - pad, y + s - pad,
                                fill=COLOR_MINE, outline="")

    def placeholder_number(self, n, x, y):
        self.placeholder_revealed(x, y)
        if n > 0:
            self.canvas.create_text(x + self.cell_size / 2, y + self.cell_size / 2,
                                    text=str(n), font=self.cell_font,
                                    fill=NUMBER_COLORS[n])

    def draw_flag(self, x, y):
        s = self.cell_size
        self.placeholder_hidden(x, y)
        self.canvas.create_polygon(x + s * 0.3, y + s * 0.2,
                                   x + s * 0.75, y + s * 0.4,
                                   x + s * 0.3, y + s * 0.6,
                                   fill=COLOR_FLAG, outline="")
        self.canvas.create_line(x + s * 0.3, y + s * 0.2, x + s * 0.3, y + s * 0.85,
                                fill=COLOR_MINE, width=2)

    def draw_end_message(self):
        cx, cy = self.width / 2, self.height / 2
        box_w = min(self.width - 20, 260)
        self.canvas.create_rectangle(cx - box_w / 2, cy - 45, cx + box_w / 2, cy + 45,
                                     fill=COLOR_BG, outline=COLOR_TEXT, width=2)
        message = "You Win!" if self.shown_state() == "won" else "Game Over"
        self.canvas.create_text(cx, cy - 15, text=message,
                                font=self.big_font, fill=COLOR_TEXT)
        self.canvas.create_text(cx, cy + 25, text="Press R or click the button",
                                font=self.small_font, fill=COLOR_TEXT)


if __name__ == "__main__":
    root = tk.Tk()
    Game(root)
    root.mainloop()   # hands control to tkinter's event loop