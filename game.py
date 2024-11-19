import random
from constants import (
    starting_buildings_dict,
    landmarks_tuple,
    major_establishments_tuple,
    primary_industry_dict,
    secondary_industry_dict,
    restaurants_tuple,
    activation_dict,
    building_cost_dict
)


class MachiKoroGame:
    def __init__(self, n_players: int):
        self.n_players = n_players
        self.players = [self._init_player(i) for i in range(n_players)]
        self.market = self._init_market()
        self.current_turn = 0

    @staticmethod
    def _init_player(player_id: int):
        """Initialize a player's state."""
        return {
            "id": player_id,
            "coins": 3,
            "establishments": starting_buildings_dict,
            "landmarks": {landmark: False for landmark in landmarks_tuple},
        }

    @staticmethod
    def _init_market():
        """Initialize the market with establishment cards."""
        market_dict = {landmark: 1 for landmark in landmarks_tuple}
        market_dict = {
            **market_dict,
            **{major_establishment: 4 for major_establishment in major_establishments_tuple}
        }
        for building in primary_industry_dict + secondary_industry_dict + restaurants_tuple:
            market_dict[building] = 6

        return market_dict

    @staticmethod
    def roll_dice(num_dice=1):
        """Simulate rolling dice."""
        roll1 = random.randint(1, 6)
        roll2 = random.randint(1, 6) if num_dice == 2 else 0
        is_double = True if roll1 == roll2 else False
        return roll1 + roll2, is_double

    def activate_cards(self, roll: int):
        """Activate cards based on dice roll."""
        pass

    def activate_special_card(self, card_name: str):
        pass

    def take_turn(self):
        """Simulate one turn for the current player."""
        player = self.players[self.current_turn]

        # Step 1: Roll Dice
        num_dice = 1 if not player["landmarks"]["train_station"] else random.choice([1, 2])
        roll, is_double = self.roll_dice(num_dice)
        print(f"Player {player['id']} rolled {roll} ({'which is double' if is_double else 'not double'}).")

        # Step 2: Activate Cards
        self.activate_cards(roll)

        # Step 3: town hall gives a coin if active player does not have any
        player['coins'] = 1 if player['coins'] == 0 else player['coins']

        # Step 4: Buy a card (randomly for now)
        if player["coins"] > 0:
            possible_purchases = [card for card, count in self.market.items() if
                                  building_cost_dict[card] <= player["coins"] and count > 0]
            if possible_purchases:
                purchase = random.choice(possible_purchases)
                player["coins"] -= building_cost_dict[purchase]
                self.market[purchase] -= 1
                player["establishments"][purchase] = player["establishments"].get(purchase, 0) + 1
                print(f"Player {player['id']} bought {purchase}.")

        # Move to next player
        self.current_turn = (self.current_turn + 1) % self.n_players

    def is_game_over(self):
        """Check if a player has won."""
        for player in self.players:
            if all(player["landmarks"].values()):  # All landmarks completed
                return True
        return False

    def play_game(self):
        """Simulate a full game."""
        while not self.is_game_over():
            self.take_turn()
            print(f"--- End of turn {self.current_turn} ---")
        print("Game over!")
        winner = max(self.players, key=lambda p: sum(p["landmarks"].values()))
        print(f"Player {winner['id']} wins!")
