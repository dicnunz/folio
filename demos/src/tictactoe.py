"""Reusable 3x3 tic-tac-toe engine with alpha-beta minimax."""

import random


PLAYER = "X"
COMPUTER = "O"
EMPTY = " "
TIE = "tie"

WINNING_LINES = (
    (0, 1, 2),
    (3, 4, 5),
    (6, 7, 8),
    (0, 3, 6),
    (1, 4, 7),
    (2, 5, 8),
    (0, 4, 8),
    (2, 4, 6),
)


def _board_result(board):
    """Return the winning mark, tie, or None for an unfinished board."""
    for first, second, third in WINNING_LINES:
        if board[first] != EMPTY and board[first] == board[second] == board[third]:
            return board[first]
    if EMPTY not in board:
        return TIE
    return None


def minimax(board, maximizing, alpha=float("-inf"), beta=float("inf"), depth=0):
    """Score a board using minimax with alpha-beta pruning."""
    result = _board_result(board)
    if result == COMPUTER:
        return 10 - depth
    if result == PLAYER:
        return depth - 10
    if result == TIE:
        return 0

    legal_moves = [index for index, cell in enumerate(board) if cell == EMPTY]

    if maximizing:
        best_score = float("-inf")
        for move in legal_moves:
            board[move] = COMPUTER
            score = minimax(board, False, alpha, beta, depth + 1)
            board[move] = EMPTY
            best_score = max(best_score, score)
            alpha = max(alpha, best_score)
            if beta <= alpha:
                break
        return best_score

    best_score = float("inf")
    for move in legal_moves:
        board[move] = PLAYER
        score = minimax(board, True, alpha, beta, depth + 1)
        board[move] = EMPTY
        best_score = min(best_score, score)
        beta = min(beta, best_score)
        if beta <= alpha:
            break
    return best_score


def choose_best_move(board):
    """Return the computer's best legal move without changing the board."""
    best_score = float("-inf")
    best_move = None

    for move, cell in enumerate(board):
        if cell != EMPTY:
            continue
        board[move] = COMPUTER
        score = minimax(board, False)
        board[move] = EMPTY
        if score > best_score:
            best_score = score
            best_move = move

    return best_move


class TicTacToeGame:
    """Maintain one tic-tac-toe game's state and rules."""

    def __init__(self):
        self.board = []
        self.current_player = PLAYER
        self.winner = None
        self.game_over = False
        self.new_game()

    def new_game(self, starting_player=None):
        """Reset the board and choose who takes the first turn."""
        if starting_player is not None and starting_player not in (PLAYER, COMPUTER):
            raise ValueError("Starting player must be X or O.")
        self.board = [EMPTY] * 9
        self.current_player = starting_player or random.choice((PLAYER, COMPUTER))
        self.winner = None
        self.game_over = False

    def get_legal_moves(self):
        """Return indexes for every currently playable square."""
        if self.game_over:
            return []
        return [index for index, cell in enumerate(self.board) if cell == EMPTY]

    def is_legal_move(self, position):
        """Return whether a position can be played now."""
        return (
            type(position) is int
            and 0 <= position < len(self.board)
            and self.board[position] == EMPTY
            and not self.game_over
        )

    def make_move(self, position):
        """Play the current mark, update the result, and change turns."""
        if not self.is_legal_move(position):
            return False

        self.board[position] = self.current_player
        self.check_winner()
        if not self.game_over:
            self.switch_player()
        return True

    def switch_player(self):
        """Switch between the human and computer marks."""
        if self.current_player == PLAYER:
            self.current_player = COMPUTER
        else:
            self.current_player = PLAYER

    def check_winner(self):
        """Update game state and return a winner, tie, or None."""
        result = _board_result(self.board)
        if result in (PLAYER, COMPUTER):
            self.winner = result
            self.game_over = True
        elif result == TIE:
            self.winner = None
            self.game_over = True
        return result

    def choose_best_move(self):
        """Return the best legal computer move for the current board."""
        return choose_best_move(self.board)

    def computer_move(self):
        """Play and return the best move when it is the computer's turn."""
        if self.current_player != COMPUTER or self.game_over:
            return None
        move = self.choose_best_move()
        if move is None:
            self.check_winner()
            return None
        self.make_move(move)
        return move
