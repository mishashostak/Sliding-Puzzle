import tkinter as tk
from tkinter import messagebox
import random
import subprocess
import sys
import os


class SlidingPuzzle(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Sliding Puzzle")
        self.resizable(False, False)

        # Current board size (NxN)
        self.size = tk.IntVar(value=4)

        # Mode: "Human" or "Bot"
        self.mode = tk.StringVar(value="Human")

        # Move counter
        self.move_count = tk.IntVar(value=0)

        # --- Top control bar ---
        control_frame = tk.Frame(self, padx=10, pady=10)
        control_frame.pack()

        tk.Label(control_frame, text="Size (N x N):").pack(side=tk.LEFT)

        self.size_spin = tk.Spinbox(
            control_frame,
            from_=2,
            to=8,
            width=5,
            textvariable=self.size
        )
        self.size_spin.pack(side=tk.LEFT, padx=5)

        # Mode selection
        tk.Label(control_frame, text="Mode:").pack(side=tk.LEFT, padx=(10, 0))

        tk.Radiobutton(
            control_frame, text="Human",
            variable=self.mode, value="Human"
        ).pack(side=tk.LEFT)

        tk.Radiobutton(
            control_frame, text="Bot",
            variable=self.mode, value="Bot"
        ).pack(side=tk.LEFT)

        new_game_btn = tk.Button(
            control_frame,
            text="New Game",
            command=self.new_game
        )
        new_game_btn.pack(side=tk.LEFT, padx=10)

        # --- Info bar (move counter) ---
        info_frame = tk.Frame(self)
        info_frame.pack()

        tk.Label(info_frame, text="Moves: ", font=("Helvetica", 12, "bold")).pack(side=tk.LEFT)
        self.move_label = tk.Label(info_frame, textvariable=self.move_count, font=("Helvetica", 12))
        self.move_label.pack(side=tk.LEFT)

        # --- Puzzle board ---
        self.board_frame = tk.Frame(self, padx=20, pady=20)
        self.board_frame.pack()

        self.tiles = []   # flat list representing the board
        self.buttons = {}  # (row, col) -> widget

        self.new_game()

    # --- Board logic -------------------------------------------------

    def new_game(self):
        """Initialize a new game with the chosen size."""
        n = self.size.get()
        if n < 2:
            n = 2
            self.size.set(2)
        if n > 8:
            n = 8
            self.size.set(8)

        # Reset move counter
        self.move_count.set(0)

        # Start from solved board
        self.tiles = list(range(1, n * n)) + [0]

        # Shuffle by making random valid moves so it's always solvable
        self.shuffle_board(moves=n * n * 20)

        # Redraw buttons
        self.draw_board()

        # If Bot mode, call external bot script
        if self.mode.get() == "Bot":
            self.call_bot_script()

    def shuffle_board(self, moves=200):
        """Randomly shuffle the puzzle by sliding tiles."""
        n = self.size.get()

        for _ in range(moves):
            br, bc = self.get_blank_pos()
            neighbors = self.get_neighbors(br, bc)

            if neighbors:
                nr, nc = random.choice(neighbors)
                blank_index = br * n + bc
                tile_index = nr * n + nc
                self.tiles[blank_index], self.tiles[tile_index] = (
                    self.tiles[tile_index],
                    self.tiles[blank_index],
                )

    def get_blank_pos(self):
        """Return (row, col) of the blank tile."""
        n = self.size.get()
        index = self.tiles.index(0)
        return divmod(index, n)

    def get_neighbors(self, r, c):
        """Return list of (row, col) positions adjacent to (r, c)."""
        n = self.size.get()
        neighbors = []
        if r > 0:
            neighbors.append((r - 1, c))
        if r < n - 1:
            neighbors.append((r + 1, c))
        if c > 0:
            neighbors.append((r, c - 1))
        if c < n - 1:
            neighbors.append((r, c + 1))
        return neighbors

    def is_solved(self):
        """Check if the puzzle is in the solved state."""
        n = self.size.get()
        return self.tiles == list(range(1, n * n)) + [0]

    # --- Bot script calling ------------------------------------------

    def call_bot_script(self):
        """
        Instead of implementing bot logic here, call an external Python file
        depending on the board size. For example:
            3x3 -> Bot3x3.py
            4x4 -> Bot4x4.py
        """
        script_name = "Bot.py"   # e.g. Bot3x3.py, Bot4x4.py, ...

        # Optional: look in the same directory as this script
        script_path = os.path.join(os.path.dirname(__file__), script_name)

        if not os.path.exists(script_path):
            messagebox.showerror(
                "Bot Error",
                "Bot script not found .\n"
                f"Expected file: {script_name}"
            )
            return

        try:
            # Use the same Python executable that runs this GUI
            subprocess.Popen([sys.executable, script_path])
        except Exception as e:
            messagebox.showerror(
                "Bot Error",
                f"Failed to start bot script:\n{e}"
            )

    # --- GUI drawing & events ----------------------------------------

    def draw_board(self):
        """Draw the tiles as buttons (bigger icons)."""
        # Clear old widgets
        for widget in self.board_frame.winfo_children():
            widget.destroy()

        self.buttons.clear()
        n = self.size.get()

        for r in range(n):
            for c in range(n):
                value = self.tiles[r * n + c]
                if value == 0:
                    # Blank tile
                    lbl = tk.Label(
                        self.board_frame,
                        text="",
                        width=6,
                        height=3,
                        borderwidth=1,
                        relief="solid",
                        bg="lightgray",
                    )
                    lbl.grid(row=r, column=c, padx=3, pady=3)
                    self.buttons[(r, c)] = lbl
                else:
                    btn = tk.Button(
                        self.board_frame,
                        text=str(value),
                        width=6,
                        height=3,
                        font=("Helvetica", 18, "bold"),
                        command=lambda row=r, col=c: self.on_tile_click(row, col),
                    )
                    btn.grid(row=r, column=c, padx=3, pady=3)
                    self.buttons[(r, c)] = btn

        # Adjust main window size to fit
        self.update_idletasks()
        w = self.board_frame.winfo_reqwidth() + 60
        h = self.board_frame.winfo_reqheight() + 150
        self.geometry(f"{w}x{h}")

    def on_tile_click(self, row, col):
        """Handle clicking a tile: move it if adjacent to blank."""
        # In Bot mode, user doesn't play
        if self.mode.get() != "Human":
            return

        n = self.size.get()
        index = row * n + col
        if self.tiles[index] == 0:
            return  # clicked the blank

        # Find blank tile
        blank_index = self.tiles.index(0)
        br, bc = divmod(blank_index, n)

        # Check adjacency
        if abs(br - row) + abs(bc - col) == 1:
            # Swap clicked tile and blank
            self.tiles[blank_index], self.tiles[index] = (
                self.tiles[index],
                self.tiles[blank_index],
            )

            # Increment move counter
            self.move_count.set(self.move_count.get() + 1)

            self.draw_board()

            if self.is_solved():
                messagebox.showinfo("Congratulations!", f"You solved the puzzle in {self.move_count.get()} moves!")


if __name__ == "__main__":
    app = SlidingPuzzle()
    app.mainloop()
