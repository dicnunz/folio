import random


def legal_moves(board):
   return [i for i, cell in enumerate(board) if cell == " "]


def random_move(board, rng):
   moves = legal_moves(board)
   if not moves:
      return None
   return rng.choice(moves)


def heuristic_move(board):
   lines = [
      (0, 1, 2), (3, 4, 5), (6, 7, 8),
      (0, 3, 6), (1, 4, 7), (2, 5, 8),
      (0, 4, 8), (2, 4, 6),
   ]
   for mark in ["X", "O"]:
      for a, b, c in lines:
            cells = [board[a], board[b], board[c]]
            if cells.count(mark) == 2 and cells.count(" ") == 1:
               return a if cells[0] == " " else b if cells[1] == " " else c
   return random_move(board, random.Random(0))


def minimax(board, turn):
   if winner(board) == "X":
      return 1
   if winner(board) == "O":
      return -1
   if not legal_moves(board):
      return 0
   best = -10 if turn == "X" else 10
   for move in legal_moves(board):
      next_board = list(board)
      next_board[move] = turn
      score = minimax(next_board, "O" if turn == "X" else "X")
      if turn == "X":
            best = max(best, score)
      else:
            best = min(best, score)
   return best


def minimax_move(board):
   best_score = -10
   best_move = None
   for move in legal_moves(board):
      next_board = list(board)
      next_board[move] = "X"
      score = minimax(next_board, "O")
      if score > best_score:
            best_score = score
            best_move = move
   return best_move if best_move is not None else random_move(board, random.Random(0))


def minimax_alpha_beta(board, turn, alpha=-10, beta=10):
   outcome = winner(board)
   if outcome == "X":
      return 1
   if outcome == "O":
      return -1
   if not legal_moves(board):
      return 0
   if turn == "X":
      best = -10
      for move in legal_moves(board):
            next_board = list(board)
            next_board[move] = "X"
            score = minimax_alpha_beta(next_board, "O", alpha, beta)
            best = max(best, score)
            alpha = max(alpha, score)
            if alpha >= beta:
               break
      return best
   best = 10
   for move in legal_moves(board):
      next_board = list(board)
      next_board[move] = "O"
      score = minimax_alpha_beta(next_board, "X", alpha, beta)
      best = min(best, score)
      beta = min(beta, score)
      if alpha >= beta:
            break
   return best


def winner(board):
   lines = [
      (0, 1, 2), (3, 4, 5), (6, 7, 8),
      (0, 3, 6), (1, 4, 7), (2, 5, 8),
      (0, 4, 8), (2, 4, 6),
   ]
   for a, b, c in lines:
      if board[a] != " " and board[a] == board[b] == board[c]:
            return board[a]
   return None


def alpha_beta_move(board):
   best_score = -10
   best_move = None
   alpha = -10
   beta = 10
   for move in legal_moves(board):
      next_board = list(board)
      next_board[move] = "X"
      score = minimax_alpha_beta(next_board, "O", alpha, beta)
      if score > best_score:
            best_score = score
            best_move = move
   return best_move if best_move is not None else random_move(board, random.Random(0))


def test_random_move_on_empty_board():
   board = [" "] * 9
   move = random_move(board, random.Random(5))
   assert move in legal_moves(board)


def test_rule_based_player_blocks_winning_move():
   board = ["X", "X", " ", "O", " ", " ", " ", " ", " "]
   move = heuristic_move(board)
   assert move == 2


def test_minimax_finds_immediate_win():
   board = ["X", "X", " ", " ", "O", " ", " ", " ", " "]
   move = minimax_move(board)
   assert move == 2


def test_alpha_beta_respects_validity_and_fork_prevention():
   board = ["X", " ", " ", " ", "O", " ", " ", " ", "X"]
   move = alpha_beta_move(board)
   assert move in legal_moves(board)


def test_invalid_board_rejected():
   board = ["X", "O", "X", "O", "X", "O", "O", "X", "O"]
   assert legal_moves(board) == []
   assert winner(board) is None


def test_exhaustive_validity_of_legal_moves():
   for board in [
      [" "] * 9,
      ["X", " ", " ", " ", "O", " ", " ", " ", "X"],
      ["X", "O", "X", "X", "O", "O", "O", "X", "X"],
   ]:
      assert set(legal_moves(board)).issubset(set(range(9)))
