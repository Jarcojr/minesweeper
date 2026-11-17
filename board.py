"""
board.py -- the game logic, no drawing in here. main.py uses:

    Board(rows, cols, mines)
    board.rows, board.cols, board.mines
    board.cells[row][col].is_mine / is_revealed / is_flagged / adjacent_count
    board.reveal(row, col)    -> list of (row, col, depth)
    board.toggle_flag(row, col)
    board.flags_placed()      -> int
    board.flag_all_mines()
    board.exploded            -> (row, col) of the clicked mine, None if no loss
    board.state               -> "playing", "won", or "lost"
"""
import math
import random
from collections import deque


class Cell:
    def __init__(self):
        self.is_mine = False
        self.is_revealed = False
        self.is_flagged = False
        self.adjacent_count = 0


class Board:
    def __init__(self, rows, cols, mines):
        self.rows = rows
        self.cols = cols
        self.mines = mines
        self.cells = [[Cell() for _ in range(cols)] for _ in range(rows)]
        self.state = "playing"
        self.exploded = None        # which mine got clicked (if we lost)
        self._mines_placed = False

    def flags_placed(self):
        return sum(cell.is_flagged for row in self.cells for cell in row)

    def _neighbors(self, r, c):
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    yield nr, nc

#for first click, counts how many squares should open to prevent unsolvable starts
    def _opening_size(self, safe_r, safe_c, mine_positions):
        stack = [(safe_r, safe_c)]
        seen = set()

        while stack:
            r, c = stack.pop()

            if (r, c) in seen or (r, c) in mine_positions:
                continue

            seen.add((r, c))
            neighbors = list(self._neighbors(r, c))

            if not any(pos in mine_positions for pos in neighbors):
                stack.extend(neighbors)

        return len(seen)


    def _place_mines(self, safe_r, safe_c):
        # Keep the first click and its neighbors mine-free
        candidates = [(r, c) for r in range(self.rows) for c in range(self.cols)
                      if abs(r - safe_r) > 1 or abs(c - safe_c) > 1]
        if len(candidates) < self.mines:  # tiny board fallback
            candidates = [(r, c) for r in range(self.rows) for c in range(self.cols)
                          if (r, c) != (safe_r, safe_c)]
        
        target = self.rows * self.cols // 6   #num of squares / 6
        best_mines = None
        best_size = -1

        for _ in range(30):   #up to 30 attempts - can make higher but will be slower
            mines = set(random.sample(candidates, self.mines))  #randomly choose mine spots
            size = self._opening_size(safe_r, safe_c, mines)    #calculate new starting size of board

            if size > best_size:
                best_size = size
                best_mines = mines

            if size >= target:
                break

        for r, c in best_mines:
            self.cells[r][c].is_mine = True  #place mines in best position after check

        for r in range(self.rows):
            for c in range(self.cols):
                self.cells[r][c].adjacent_count = sum(
                    self.cells[nr][nc].is_mine for nr, nc in self._neighbors(r, c))
        self._mines_placed = True

    def reveal(self, r, c):
        # returns a list of (row, col, depth) for every tile that just got revealed
        # (depth = how many steps away from the click), main.py uses the list for the animation
        if self.state != "playing":
            return []
        cell = self.cells[r][c]
        if cell.is_flagged or cell.is_revealed:
            return []
        if not self._mines_placed:
            self._place_mines(r, c)

        if cell.is_mine:
            self.state = "lost"
            self.exploded = (r, c)
            cell.is_revealed = True
            revealed = [(r, c, 0)]
            # show the rest of the mines too (skip the flagged ones)
            # farther mines get a bigger distance so they show up later
            for mr in range(self.rows):
                for mc in range(self.cols):
                    other = self.cells[mr][mc]
                    if other.is_mine and not other.is_revealed and not other.is_flagged:
                        other.is_revealed = True
                        distance = int(math.hypot(mr - r, mc - c) / 2) + 1
                        revealed.append((mr, mc, distance))
            return revealed

        # flood fill, switched from a stack to a queue so it goes outward in rings
        cell.is_revealed = True
        queue = deque([(r, c, 0)])
        revealed = []
        while queue:
            cr, cc, depth = queue.popleft()
            revealed.append((cr, cc, depth))
            if self.cells[cr][cc].adjacent_count == 0:
                for nr, nc in self._neighbors(cr, cc):
                    neighbor = self.cells[nr][nc]
                    if not neighbor.is_revealed and not neighbor.is_flagged:
                        neighbor.is_revealed = True   # mark it now so it only gets added once
                        queue.append((nr, nc, depth + 1))

        self._check_win()
        return revealed

    def toggle_flag(self, r, c):
        if self.state != "playing":
            return
        cell = self.cells[r][c]
        if not cell.is_revealed:
            cell.is_flagged = not cell.is_flagged

    def _check_win(self):
        for row in self.cells:
            for cell in row:
                if not cell.is_mine and not cell.is_revealed:
                    return
        self.state = "won"

    def flag_all_mines(self):
        # after a win, flag every mine so the counter ends at 0
        for row in self.cells:
            for cell in row:
                if cell.is_mine:
                    cell.is_flagged = True