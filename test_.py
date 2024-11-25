from game import MachiKoroGame
from constants import primary_industry_dict, secondary_industry_dict, restaurants_tuple, major_establishments_tuple


def test_reverse_order_2_0():
    game = MachiKoroGame(n_players=2)
    assert game.get_reverse_player_order(0) == [
        1,
    ]


def test_reverse_order_2_1():
    game = MachiKoroGame(n_players=2)
    assert game.get_reverse_player_order(1) == [
        0,
    ]


def test_reverse_order_3_0():
    game = MachiKoroGame(n_players=3)
    assert game.get_reverse_player_order(0) == [
        2,
        1,
    ]


def test_reverse_order_3_1():
    game = MachiKoroGame(n_players=3)
    assert game.get_reverse_player_order(1) == [0, 2]


def test_reverse_order_3_2():
    game = MachiKoroGame(n_players=3)
    assert game.get_reverse_player_order(2) == [1, 0]


def test_reverse_order_4_0():
    game = MachiKoroGame(n_players=4)
    assert game.get_reverse_player_order(0) == [3, 2, 1]


def test_reverse_order_4_1():
    game = MachiKoroGame(n_players=4)
    assert game.get_reverse_player_order(1) == [0, 3, 2]


def test_reverse_order_4_2():
    game = MachiKoroGame(n_players=4)
    assert game.get_reverse_player_order(2) == [1, 0, 3]


def test_reverse_order_4_3():
    game = MachiKoroGame(n_players=4)
    assert game.get_reverse_player_order(3) == [2, 1, 0]


def test_reverse_order_5_0():
    game = MachiKoroGame(n_players=5)
    assert game.get_reverse_player_order(0) == [4, 3, 2, 1]


def test_reverse_order_5_1():
    game = MachiKoroGame(n_players=5)
    assert game.get_reverse_player_order(1) == [0, 4, 3, 2]


def test_reverse_order_5_2():
    game = MachiKoroGame(n_players=5)
    assert game.get_reverse_player_order(2) == [1, 0, 4, 3]


def test_reverse_order_5_3():
    game = MachiKoroGame(n_players=5)
    assert game.get_reverse_player_order(3) == [2, 1, 0, 4]


def test_reverse_order_5_4():
    game = MachiKoroGame(n_players=5)
    assert game.get_reverse_player_order(4) == [3, 2, 1, 0]


def test_game_2():
    for _ in range(100):
        game = MachiKoroGame(n_players=2)
        game.play_game()


def test_game_3():
    for _ in range(100):
        game = MachiKoroGame(n_players=3)
        game.play_game()


def test_game_4():
    for _ in range(100):
        game = MachiKoroGame(n_players=4)
        game.play_game()


def test_game_5():
    for _ in range(100):
        game = MachiKoroGame(n_players=5)
        game.play_game()


def test_game_2_all_buildings():
    starting_establishments = {
        key: (1, 1)
        for key
        in list(primary_industry_dict.keys()) + list(secondary_industry_dict.keys()) + list(restaurants_tuple)
    }
    starting_major_establishments = major_establishments_tuple
    for _ in range(100):
        game = MachiKoroGame(n_players=2, starting_buildings=starting_establishments, starting_major_establishments=starting_major_establishments)
        game.play_game()


def test_game_3_all_buildings():
    starting_establishments = {
        key: (1, 1)
        for key
        in list(primary_industry_dict.keys()) + list(secondary_industry_dict.keys()) + list(restaurants_tuple)
    }
    starting_major_establishments = major_establishments_tuple
    for _ in range(100):
        game = MachiKoroGame(n_players=3, starting_buildings=starting_establishments,
                             starting_major_establishments=starting_major_establishments)
        game.play_game()


def test_game_4_all_buildings():
    starting_establishments = {
        key: (1, 1)
        for key
        in list(primary_industry_dict.keys()) + list(secondary_industry_dict.keys()) + list(restaurants_tuple)
    }
    starting_major_establishments = major_establishments_tuple
    for _ in range(100):
        game = MachiKoroGame(n_players=4, starting_buildings=starting_establishments,
                             starting_major_establishments=starting_major_establishments)
        game.play_game()


def test_game_5_all_buildings():
    starting_establishments = {
        key: (1, 1)
        for key
        in list(primary_industry_dict.keys()) + list(secondary_industry_dict.keys()) + list(restaurants_tuple)
    }
    starting_major_establishments = major_establishments_tuple
    for _ in range(100):
        game = MachiKoroGame(n_players=5, starting_buildings=starting_establishments,
                             starting_major_establishments=starting_major_establishments)
        game.play_game()
