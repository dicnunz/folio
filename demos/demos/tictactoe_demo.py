"""Interactive command-line demo for the Folio tic-tac-toe engine."""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.tictactoe import COMPUTER, EMPTY, PLAYER, TicTacToeGame


def display_board(board):
    """Print the board, showing square numbers for empty cells."""
    cells = [str(index + 1) if cell == EMPTY else cell for index, cell in enumerate(board)]
    for row_start in range(0, 9, 3):
        print(" | ".join(cells[row_start : row_start + 3]))
        if row_start < 6:
            print("---------")


def ask_player_move(game):
    """Prompt until the player supplies a legal square from 1 through 9."""
    while True:
        response = input("Choose a square (1-9): ").strip()
        try:
            position = int(response) - 1
        except ValueError:
            print("Please enter a number from 1 through 9.")
            continue

        if game.is_legal_move(position):
            return position
        print("That square is unavailable. Choose another.")


def play_game(game):
    """Play one game and print its result."""
    print(f"{'You' if game.current_player == PLAYER else 'Computer'} start.")

    while not game.game_over:
        print()
        display_board(game.board)

        if game.current_player == PLAYER:
            game.make_move(ask_player_move(game))
        else:
            print("Computer is thinking...")
            move = game.computer_move()
            print(f"Computer chose square {move + 1}.")

    print()
    display_board(game.board)
    if game.winner == PLAYER:
        print("You win!")
    elif game.winner == COMPUTER:
        print("Computer wins.")
    else:
        print("Tie game.")


def main():
    print("--- Folio Tic-Tac-Toe Demo ---")
    game = TicTacToeGame()

    while True:
        play_game(game)
        if input("Play again? (y/n): ").strip().lower() != "y":
            break
        game.new_game()


if __name__ == "__main__":
    main()
