"""
Charleston Minesweeper -- main.py (Person B: UI + input), tkinter version

Controls:
    Left click   reveal a tile
    Right click  place/remove a flag (on a Mac trackpad: two-finger click
                 or Control+click)
    Click the center button (or press R) to restart
    Press 1 / 2 / 3 to switch difficulty (beginner / intermediate / expert)
"""
import time
import tkinter as tk
from board import Board
from assets import load_images

# ---------- Constants ----------
CELL_SIZE = 16          # change this to match Person C's image size
HEADER_HEIGHT = 60
TICK_MS = 200           # how often the timer label refreshes

DIFFICULTIES = {
    "beginner":     (9, 9, 10),     # rows, cols, mines
    "intermediate": (16, 16, 40),
    "expert":       (16, 30, 99),
}

# Placeholder colors (these go away once the real images are in)
COLOR_BG = "#1e1e28"
COLOR_HIDDEN = "#9696a0"
COLOR_REVEALED = "#e1d7b9"
COLOR_GRID_LINE = "#5a5a64"
COLOR_MINE = "#141414"
COLOR_FLAG = "#c82828"
COLOR_TEXT = "#f0f0f0"
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

        # Load the tile art once. Must happen after the tk.Tk() window exists
        # and the result must stay stored on self, or the images disappear.
        self.images = load_images(CELL_SIZE)

        # ----- Header: mine counter | restart button | timer -----
        header_font = ("Arial", 22, "bold")
        self.header = tk.Frame(root, bg=COLOR_BG, height=HEADER_HEIGHT)
        self.header.pack(fill="x")
        self.mine_label = tk.Label(self.header, font=header_font, fg=COLOR_TEXT,
                                   bg=COLOR_BG, width=4)
        self.mine_label.pack(side="left", padx=8, pady=8)
        self.timer_label = tk.Label(self.header, font=header_font, fg=COLOR_TEXT,
                                    bg=COLOR_BG, width=4)
        self.timer_label.pack(side="right", padx=8, pady=8)
        # Placeholder: later you can use a tk.PhotoImage here instead of text
        self.restart_button = tk.Button(self.header, text=":)", font=header_font,
                                        width=4, command=self.start_new_game)
        self.restart_button.pack(expand=True, pady=8)

        # ----- Canvas: where the grid is drawn -----
        self.canvas = tk.Canvas(root, bg=COLOR_BG, highlightthickness=0)
        self.canvas.pack()

        # ----- Input bindings -----
        self.canvas.bind("<Button-1>", self.on_left_click)
        self.canvas.bind("<Button-3>", self.on_right_click)           # Windows/Linux
        self.canvas.bind("<Button-2>", self.on_right_click)           # Mac right-click
        self.canvas.bind("<Control-Button-1>", self.on_right_click)   # Mac ctrl+click
        root.bind("<Key>", self.on_key)

        self.cell_font = ("Arial", int(CELL_SIZE * 0.45), "bold")
        self.big_font = ("Arial", 32, "bold")
        self.small_font = ("Arial", 13, "bold")

        self.start_new_game()
        self.tick()   # starts the repeating timer refresh

    # ---------- Setup ----------
    def start_new_game(self):
        rows, cols, mines = DIFFICULTIES[self.difficulty]
        self.board = Board(rows, cols, mines)
        self.width = cols * CELL_SIZE
        self.height = rows * CELL_SIZE
        self.canvas.config(width=self.width, height=self.height)

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
        row = event.y // CELL_SIZE    # // is integer division, like Java's int / int
        col = event.x // CELL_SIZE
        if 0 <= row < self.board.rows and 0 <= col < self.board.cols:
            return row, col
        return None

    def on_left_click(self, event):
        position = self.cell_from_event(event)
        if position is None:
            return
        if self.start_time is None:
            self.start_time = time.time()
        self.board.reveal(*position)    # * unpacks the (row, col) tuple
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

    # ---------- Drawing ----------
    def refresh(self):
        self.update_header()
        self.draw_grid()
        if self.board.state != "playing":
            self.draw_end_message()

    def update_header(self):
        remaining = self.board.mines - self.board.flags_placed()
        self.mine_label.config(text=f"{remaining:03d}")
        self.timer_label.config(text=f"{min(self.elapsed_seconds(), 999):03d}")
        face = {"playing": ":)", "won": "B)", "lost": "X("}[self.board.state]
        self.restart_button.config(text=face)

    def draw_grid(self):
        self.canvas.delete("all")   # clear everything, then redraw
        for r in range(self.board.rows):
            for c in range(self.board.cols):
                x = c * CELL_SIZE
                y = r * CELL_SIZE
                self.draw_cell(self.board.cells[r][c], x, y)

    def draw_cell(self, cell, x, y):
        """Draws one tile with its top-left corner at (x, y). Reads the
        cell's state and picks which image (layer) to draw."""
        if not cell.is_revealed:
            self.draw_layer("hidden", x, y, self.placeholder_hidden)
            if cell.is_flagged:
                self.draw_layer("flag", x, y, self.draw_flag)
        elif cell.is_mine:
            self.draw_layer(0, x, y, self.placeholder_revealed)   # background
            self.draw_layer("mine", x, y, self.placeholder_mine)  # mine on top
        else:
            n = cell.adjacent_count
            self.draw_layer(n, x, y, lambda px, py: self.placeholder_number(n, px, py))

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
        s = CELL_SIZE
        self.canvas.create_rectangle(x, y, x + s, y + s,
                                     fill=COLOR_HIDDEN, outline=COLOR_GRID_LINE)

    def placeholder_revealed(self, x, y):
        s = CELL_SIZE
        self.canvas.create_rectangle(x, y, x + s, y + s,
                                     fill=COLOR_REVEALED, outline=COLOR_GRID_LINE)

    def placeholder_mine(self, x, y):
        s = CELL_SIZE
        pad = s // 4
        self.canvas.create_oval(x + pad, y + pad, x + s - pad, y + s - pad,
                                fill=COLOR_MINE, outline="")

    def placeholder_number(self, n, x, y):
        self.placeholder_revealed(x, y)
        if n > 0:
            self.canvas.create_text(x + CELL_SIZE / 2, y + CELL_SIZE / 2,
                                    text=str(n), font=self.cell_font,
                                    fill=NUMBER_COLORS[n])

    def draw_flag(self, x, y):
        s = CELL_SIZE
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
        message = "You Win!" if self.board.state == "won" else "Game Over"
        self.canvas.create_text(cx, cy - 15, text=message,
                                font=self.big_font, fill=COLOR_TEXT)
        self.canvas.create_text(cx, cy + 25, text="Press R or click the button",
                                font=self.small_font, fill=COLOR_TEXT)


if __name__ == "__main__":
    root = tk.Tk()
    Game(root)
    root.mainloop()   # hands control to tkinter's event loop
