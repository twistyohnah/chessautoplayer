Setup & Usage
Requirements

Python 3.9+

Stockfish chess engine

python-chess library

Installation

Clone the repository

git clone https://github.com/twistyohnah/chessautoplayer.git
cd yourrepo


Install dependencies

pip install python-chess


Download Stockfish

Get Stockfish from the official site

Place the Stockfish binary in the same folder as the script
OR

Update STOCKFISH_PATH in the script with the full path to your Stockfish executable

Running the Program
python chess_gui_bestmove.py

How to Use

Left-click a piece, then left-click a square to move it

Right-click a square to place or remove pieces manually

Use Reset Board, Clear Pieces, or Load FEN to set up positions

Adjust engine time to control how long Stockfish thinks

Click Get Best Move to see Stockfish’s recommendation and evaluation

You can optionally apply the suggested move directly to the board



