"""
chess_gui_.py
A Tkinter chessboard where you click to place/move pieces, then press 'Get Best Move'
to query Stockfish. Uses unicode chess pieces so no image files required.

Requires:
    pip install python-chess

Put Stockfish binary (stockfish.exe / stockfish) in same folder or set STOCKFISH_PATH variable.
"""

import tkinter as tk
from tkinter import simpledialog, messagebox
import chess
import chess.engine
import os

# --- CONFIG --- #
STOCKFISH_PATH = r"path to stockfish"
ENGINE_TIME = 0.25  # seconds to think for best-move (adjust to taste)

# Unicode pieces
UNICODE_PIECES = {
    ('P', True): "♙", ('N', True): "♘", ('B', True): "♗", ('R', True): "♖", ('Q', True): "♕", ('K', True): "♔",
    ('p', False): "♟", ('n', False): "♞", ('b', False): "♝", ('r', False): "♜", ('q', False): "♛", ('k', False): "♚",
}

# Colors for board squares
LIGHT = "#EEEED2"
DARK = "#769656"
HIGHLIGHT = "#f6f669"
MOVE_HIGHLIGHT = "#6fa8dc"

class ChessGUI:
    def __init__(self, master):
        self.master = master
        master.title("Cool Chess — Best Move Calculator")
        self.board = chess.Board()
        self.selected_square = None  # algebraic string e.g. 'e2'
        self.square_buttons = {}
        self.engine = None
        self.best_move_info = None

        # Top controls frame
        ctrl = tk.Frame(master)
        ctrl.pack(side=tk.TOP, pady=6)

        self.turn_label = tk.Label(ctrl, text="Side to move: White", font=("Helvetica", 12, "bold"))
        self.turn_label.grid(row=0, column=0, padx=6)

        tk.Button(ctrl, text="Reset Board", command=self.reset_board).grid(row=0, column=1, padx=6)
        tk.Button(ctrl, text="Flip Side", command=self.flip_side).grid(row=0, column=2, padx=6)
        tk.Button(ctrl, text="Clear Pieces", command=self.clear_pieces).grid(row=0, column=3, padx=6)
        tk.Button(ctrl, text="Load FEN", command=self.load_fen_dialog).grid(row=0, column=4, padx=6)

        tk.Label(ctrl, text="Engine time (s):").grid(row=0, column=5, padx=(12,0))
        self.time_var = tk.DoubleVar(value=ENGINE_TIME)
        tk.Entry(ctrl, textvariable=self.time_var, width=5).grid(row=0, column=6, padx=4)

        tk.Button(ctrl, text="Get Best Move", command=self.get_best_move).grid(row=0, column=7, padx=6)

        # Info labels
        info = tk.Frame(master)
        info.pack(side=tk.TOP)
        self.best_move_label = tk.Label(info, text="Best move: —", font=("Helvetica", 11))
        self.best_move_label.pack(side=tk.LEFT, padx=10)
        self.eval_label = tk.Label(info, text="Eval: —", font=("Helvetica", 11))
        self.eval_label.pack(side=tk.LEFT, padx=10)

        # The board frame
        board_frame = tk.Frame(master)
        board_frame.pack(pady=8)

        # 8x8 grid of buttons
        for rank in range(8, 0, -1):
            for file in range(1, 9):
                sq = chess.square_name(chess.square(file - 1, rank - 1))
                row = 8 - rank
                col = file - 1
                color = LIGHT if (row + col) % 2 == 0 else DARK
                b = tk.Button(board_frame, text="", font=("Arial", 28), width=2, height=1,
                              bg=color, activebackground=color,
                              command=lambda s=sq: self.on_square_click(s))
                b.grid(row=row, column=col)
                self.square_buttons[sq] = b

        # bottom instructions
        tk.Label(master, text="Click a piece to select, click destination to move. Right-click a square to place a piece.",
                 font=("Helvetica", 9)).pack(pady=(6,0))

        # bind right-click for placing pieces (Windows: <Button-3>, Mac may differ)
        for sq, btn in self.square_buttons.items():
            btn.bind("<Button-3>", lambda e, s=sq: self.right_click_place(e, s))

        self.update_board_display()

    def update_board_display(self, highlight_move: chess.Move=None):
        # Update the 64 squares with unicode piece characters
        for sq, btn in self.square_buttons.items():
            piece = self.board.piece_at(chess.parse_square(sq))
            if piece:
                glyph = UNICODE_PIECES[(piece.symbol(), piece.color == chess.WHITE)]
                btn.config(text=glyph)
            else:
                btn.config(text="")

            # set background color depending on square
            file = ord(sq[0]) - ord('a')
            rank = int(sq[1]) - 1
            color = LIGHT if (file + rank) % 2 == 0 else DARK
            btn.config(bg=color, activebackground=color)

        # update turn label
        self.turn_label.config(text=f"Side to move: {'White' if self.board.turn == chess.WHITE else 'Black'}")

        # highlight selected
        if self.selected_square:
            self.square_buttons[self.selected_square].config(bg=HIGHLIGHT)

        # highlight best move squares if provided
        if highlight_move:
            from_sq = chess.square_name(highlight_move.from_square)
            to_sq = chess.square_name(highlight_move.to_square)
            self.square_buttons[from_sq].config(bg=MOVE_HIGHLIGHT)
            self.square_buttons[to_sq].config(bg=MOVE_HIGHLIGHT)

    def on_square_click(self, sq):
        # If no selection, pick up piece (if any)
        if not self.selected_square:
            piece = self.board.piece_at(chess.parse_square(sq))
            if piece:
                self.selected_square = sq
            else:
                # nothing to pick up
                self.selected_square = None
        else:
            # try to move from selected_square -> sq
            uci = self.selected_square + sq
            move = None
            # handle promotion if pawn moves to last rank
            u = chess.Move.from_uci(uci)
            if u in self.board.legal_moves:
                move = u
            else:
                # try promotions (q,r,b,n)
                for promo in ['q','r','b','n']:
                    try_move = chess.Move.from_uci(uci + promo)
                    if try_move in self.board.legal_moves:
                        # if only one promotion legal, choose queen by default. If multiple, ask.
                        if promo == 'q':
                            move = try_move
                            break
                        else:
                            move = try_move
                            break
            if move and move in self.board.legal_moves:
                self.board.push(move)
                self.selected_square = None
                self.best_move_info = None
                self.best_move_label.config(text="Best move: —")
                self.eval_label.config(text="Eval: —")
            else:
                # invalid move: clear selection or reselect
                piece = self.board.piece_at(chess.parse_square(sq))
                if piece:
                    self.selected_square = sq
                else:
                    self.selected_square = None

        self.update_board_display()

    def right_click_place(self, event, sq):
        # Place a piece manually using a small dialog: choose color and piece type or remove
        options = ["White Pawn","White Knight","White Bishop","White Rook","White Queen","White King",
                   "Black Pawn","Black Knight","Black Bishop","Black Rook","Black Queen","Black King",
                   "Remove piece"]
        choice = simpledialog.askstring("Place Piece", "Enter (e.g.) 'wq' for White Queen, 'bp' for Black Pawn, or 'remove':\n"
                                        "w: white, b: black; p,n,b,r,q,k\n\nExamples: wq, bn, remove")
        if not choice:
            return
        choice = choice.strip().lower()
        if choice == "remove":
            self.board.remove_piece_at(chess.parse_square(sq))
        else:
            if len(choice) >= 2 and choice[0] in ('w','b') and choice[1] in ('p','n','b','r','q','k'):
                color = chess.WHITE if choice[0] == 'w' else chess.BLACK
                piece_map = {'p':'p','n':'n','b':'b','r':'r','q':'q','k':'k'}
                sym = piece_map[choice[1]]
                # python-chess uses uppercase for white, lowercase for black
                symbol = sym.upper() if color == chess.WHITE else sym.lower()
                piece = chess.Piece.from_symbol(symbol)
                self.board.set_piece_at(chess.parse_square(sq), piece)
            else:
                messagebox.showinfo("Input not valid", "Please enter like 'wq' (white queen) or 'bp' (black pawn) or 'remove'.")
                return

        self.best_move_info = None
        self.best_move_label.config(text="Best move: —")
        self.eval_label.config(text="Eval: —")
        self.update_board_display()

    def reset_board(self):
        self.board.reset()
        self.selected_square = None
        self.best_move_info = None
        self.best_move_label.config(text="Best move: —")
        self.eval_label.config(text="Eval: —")
        self.update_board_display()

    def clear_pieces(self):
        self.board.clear()
        self.selected_square = None
        self.best_move_info = None
        self.best_move_label.config(text="Best move: —")
        self.eval_label.config(text="Eval: —")
        self.update_board_display()

    def flip_side(self):
        # flip side to move without changing pieces by toggling board.turn
        self.board.turn = not self.board.turn
        self.update_board_display()

    def load_fen_dialog(self):
        fen = simpledialog.askstring("Load FEN", "Paste a FEN string (or cancel):")
        if fen:
            try:
                self.board.set_fen(fen)
                self.update_board_display()
            except Exception as e:
                messagebox.showerror("Invalid FEN", f"Couldn't load FEN: {e}")

    def get_best_move(self):
        # Try to run Stockfish
        path = STOCKFISH_PATH
        if not os.path.isfile(path):
            # try path as-is (maybe in PATH)
            # we'll attempt to run engine anyway and catch exception
            pass

        try:
            # open engine for this request
            engine = chess.engine.SimpleEngine.popen_uci(path)
        except Exception as e:
            messagebox.showerror("Engine not found",
                                 f"Could not start Stockfish engine at '{path}'.\n\n"
                                 "Download Stockfish and put the binary in the same folder as this script,\n"
                                 "or set STOCKFISH_PATH to the full path.\n\nError: " + str(e))
            return

        # ask engine for best move and evaluation
        t = float(self.time_var.get()) if self.time_var.get() > 0 else ENGINE_TIME
        try:
            # play to get best move
            result = engine.play(self.board, chess.engine.Limit(time=t))
            best = result.move
            if best is None:
                messagebox.showinfo("No legal move", "No legal move available (possible checkmate/stalemate).")
                engine.quit()
                return

            # get evaluation info
            try:
                info = engine.analyse(self.board, chess.engine.Limit(time=t))
                score = info.get("score")
                # convert score to human friendly
                if score is not None:
                    if score.is_mate():
                        val = f"Mate in {score.mate()}"
                    else:
                        # score is centipawns
                        cp = score.white().score(mate_score=100000)
                        val = f"{cp/100:.2f}"
                else:
                    val = "—"
            except Exception:
                val = "—"

            # display
            # SAN (human) and UCI
            try:
                san = self.board.san(best)
            except Exception:
                san = "—"

            self.best_move_label.config(text=f"Best move: {san}  ({best.uci()})")
            self.eval_label.config(text=f"Eval: {val}")
            self.best_move_info = best

            # highlight the move on the board temporarily
            self.update_board_display(highlight_move=best)

            # Ask user if they want to apply the move to the board
            apply_it = messagebox.askyesno("Apply move?", f"Best move {san} ({best.uci()}).\n\nApply to board?")
            if apply_it:
                self.board.push(best)
                self.update_board_display()
        finally:
            try:
                engine.quit()
            except Exception:
                pass


if __name__ == "__main__":
    root = tk.Tk()
    app = ChessGUI(root)
    root.mainloop()

