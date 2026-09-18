from src.tictactoe import (
    COMPUTER,
    EMPTY,
    PLAYER,
    TIE,
    TicTacToeGame,
    choose_best_move,
)


def test_new_board_is_empty_and_starting_player_is_valid():
    game = TicTacToeGame()

    assert game.board == [EMPTY] * 9
    assert game.current_player in (PLAYER, COMPUTER)
    assert game.winner is None
    assert game.game_over is False


def test_legal_move_is_accepted_and_turn_changes():
    game = TicTacToeGame()
    game.new_game(PLAYER)

    assert game.make_move(4) is True
    assert game.board[4] == PLAYER
    assert game.current_player == COMPUTER


def test_occupied_square_is_rejected_without_changing_it():
    game = TicTacToeGame()
    game.new_game(PLAYER)
    game.make_move(4)

    assert game.make_move(4) is False
    assert game.board[4] == PLAYER


def test_out_of_range_and_noninteger_moves_are_rejected():
    game = TicTacToeGame()

    assert game.make_move(-1) is False
    assert game.make_move(9) is False
    assert game.make_move("1") is False


def test_horizontal_win_is_detected():
    game = TicTacToeGame()
    game.board = [PLAYER, PLAYER, PLAYER, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY]

    assert game.check_winner() == PLAYER
    assert game.winner == PLAYER
    assert game.game_over is True


def test_vertical_win_is_detected():
    game = TicTacToeGame()
    game.board = [COMPUTER, EMPTY, EMPTY, COMPUTER, EMPTY, EMPTY, COMPUTER, EMPTY, EMPTY]

    assert game.check_winner() == COMPUTER


def test_diagonal_win_is_detected():
    game = TicTacToeGame()
    game.board = [PLAYER, EMPTY, EMPTY, EMPTY, PLAYER, EMPTY, EMPTY, EMPTY, PLAYER]

    assert game.check_winner() == PLAYER


def test_tie_is_detected():
    game = TicTacToeGame()
    game.board = [PLAYER, COMPUTER, PLAYER, PLAYER, COMPUTER, COMPUTER, COMPUTER, PLAYER, PLAYER]

    assert game.check_winner() == TIE
    assert game.winner is None
    assert game.game_over is True


def test_new_game_clears_board_and_old_result():
    game = TicTacToeGame()
    game.board = [PLAYER, PLAYER, PLAYER, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY]
    game.check_winner()

    game.new_game(COMPUTER)

    assert game.board == [EMPTY] * 9
    assert game.current_player == COMPUTER
    assert game.winner is None
    assert game.game_over is False


def test_minimax_returns_a_legal_move_without_mutating_board():
    board = [PLAYER, EMPTY, EMPTY, EMPTY, COMPUTER, EMPTY, EMPTY, EMPTY, EMPTY]
    before = board.copy()

    move = choose_best_move(board)

    assert move in [index for index, cell in enumerate(before) if cell == EMPTY]
    assert board == before


def test_minimax_takes_immediate_winning_move():
    board = [COMPUTER, COMPUTER, EMPTY, PLAYER, PLAYER, EMPTY, EMPTY, EMPTY, EMPTY]

    assert choose_best_move(board) == 2


def test_minimax_blocks_immediate_player_win():
    board = [PLAYER, PLAYER, EMPTY, COMPUTER, EMPTY, EMPTY, EMPTY, COMPUTER, EMPTY]

    assert choose_best_move(board) == 2


def test_computer_never_overwrites_occupied_cells():
    game = TicTacToeGame()
    game.board = [PLAYER, COMPUTER, PLAYER, EMPTY, COMPUTER, EMPTY, EMPTY, EMPTY, PLAYER]
    game.current_player = COMPUTER
    occupied_before = {
        index: cell for index, cell in enumerate(game.board) if cell != EMPTY
    }

    move = game.computer_move()

    assert move not in occupied_before
    assert all(game.board[index] == cell for index, cell in occupied_before.items())
