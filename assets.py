"""
assets.py -- loads the tile images from the visuals/ folder.

Expected files (all PNG, all the same size as CELL_SIZE in main.py):

    visuals/tile_hidden.png     unrevealed tile
    visuals/tile_0.png          revealed tile with no adjacent mines
    visuals/tile_1.png ... tile_8.png   revealed tile showing that number
    visuals/mine.png            mine (shown when the game is lost)
    visuals/flag.png            flag (drawn on top of a hidden tile)

If a file is missing, it is simply skipped and main.py draws a placeholder
shape instead. To rename a file, change it in IMAGE_FILES below -- nowhere else.
"""
import os
import tkinter as tk

# __file__ is THIS file's location, so the path works on every teammate's
# computer no matter where they cloned the repo or where VS Code's terminal is.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(BASE_DIR, "visuals")

# key used by main.py  ->  file name in the visuals folder
IMAGE_FILES = {
    "hidden": "tile_hidden.png",
    "mine": "mine.png",
    "flag": "flag.png",
    0: "tile_0.png",
    1: "tile_1.png",
    2: "tile_2.png",
    3: "tile_3.png",
    4: "tile_4.png",
    5: "tile_5.png",
    6: "tile_6.png",
    7: "tile_7.png",
    8: "tile_8.png",
}


def load_images(cell_size):
    """Returns a dictionary {key: PhotoImage} for every image file found.

    IMPORTANT: call this AFTER the tk.Tk() window has been created, and keep
    the returned dictionary stored somewhere (like self.images). If the
    PhotoImage objects get garbage-collected, tkinter shows blank tiles.
    """
    images = {}
    missing = []

    for key, filename in IMAGE_FILES.items():
        path = os.path.join(IMAGE_DIR, filename)
        if not os.path.exists(path):
            missing.append(filename)
            continue

        image = tk.PhotoImage(file=path)
        if image.width() != cell_size or image.height() != cell_size:
            print(f"WARNING: {filename} is {image.width()}x{image.height()} "
                  f"but CELL_SIZE is {cell_size}. It will look misaligned.")
        images[key] = image

    print(f"Loaded {len(images)} images from {IMAGE_DIR}")
    if missing:
        print("Using placeholders for:", ", ".join(missing))
    return images
