"""
TEMPORARY board.py -- a stand-in so the UI (main.py) can be tested.
Person A will replace this with the real version. The UI only relies on:

    Board(rows, cols, mines)
    board.rows, board.cols, board.mines
    board.cells[row][col].is_mine / is_revealed / is_flagged / adjacent_count
    board.reveal(row, col)
    board.toggle_flag(row, col)
    board.flags_placed()      -> int
    board.state               -> "playing", "won", or "lost"
"""
import random


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
        
        target = self.rows * self.cols // 6
        best_mines = None
        best_size = 0

        for _ in range(100):
            mines = set(random.sample(candidates, self.mines))
            size = self._opening_size(safe_r, safe_c, mines)

            if size > best_size:
                best_size = size
                best_mines = mines

            if size >= target:
                break

        for r, c in best_mines:
            self.cells[r][c].is_mine = True
            
        for r in range(self.rows):
            for c in range(self.cols):
                self.cells[r][c].adjacent_count = sum(
                    self.cells[nr][nc].is_mine for nr, nc in self._neighbors(r, c))
        self._mines_placed = True

    def reveal(self, r, c):
        if self.state != "playing":
            return
        cell = self.cells[r][c]
        if cell.is_flagged or cell.is_revealed:
            return
        if not self._mines_placed:
            self._place_mines(r, c)

        if cell.is_mine:
            self.state = "lost"
            for row in self.cells:
                for other in row:
                    if other.is_mine:
                        other.is_revealed = True
            return

        # Flood fill (iterative, using a stack)
        stack = [(r, c)]
        while stack:
            cr, cc = stack.pop()
            current = self.cells[cr][cc]
            if current.is_revealed or current.is_flagged:
                continue
            current.is_revealed = True
            if current.adjacent_count == 0:
                stack.extend(self._neighbors(cr, cc))

        self._check_win()

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
