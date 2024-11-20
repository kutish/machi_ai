import random
import math

from constants import (
    starting_buildings_dict,
    landmarks_tuple,
    major_establishments_tuple,
    primary_industry_dict,
    secondary_industry_dict,
    restaurants_tuple,
    activation_dict,
    building_cost_dict,
)


class MachiKoroGame:
    def __init__(self, n_players: int):
        self.n_players = n_players
        self.players = {i: self._init_player(i) for i in range(n_players)}
        self.market = self._init_market(n_players)
        self.current_turn = 0

    @staticmethod
    def _init_player(player_id: int):
        """Initialize a player's state."""
        return {
            "id": player_id,
            "coins": 3,
            "establishments": {
                key: {"on_renovation": 0, "working": val}
                for key, val in starting_buildings_dict.items()
            },
            "landmarks": {landmark: False for landmark in landmarks_tuple},
            "is_first_turn": True,  # homerule: no dice rolls on first turn of each player
        }

    @staticmethod
    def _init_market(n_players: int):
        """Initialize the market with establishment cards."""
        market_dict = {landmark: 1 for landmark in landmarks_tuple}
        market_dict = {
            **market_dict,
            **{
                major_establishment: n_players
                for major_establishment in major_establishments_tuple
            },
        }
        for building in (
            list(primary_industry_dict.keys())
            + list(secondary_industry_dict.keys())
            + list(restaurants_tuple)
        ):
            market_dict[building] = 6

        return market_dict

    @staticmethod
    def roll_dice(num_dice=1):
        """Simulate rolling dice."""
        roll1 = random.randint(1, 6)
        roll2 = random.randint(1, 6) if num_dice == 2 else 0
        is_double = True if roll1 == roll2 else False
        return roll1 + roll2, is_double

    def get_reverse_player_order(self, player_id: int):
        order = [player_id - 1 if player_id - 1 >= 0 else self.n_players]
        for id_ in range(self.n_players):
            if order[-1] == 0:
                order.append(self.n_players)
            else:
                order.append(order[-1] - 1)

        return order[:-1]

    def activate_cards(self, current_player_id: int, roll: int):
        """Activate cards based on dice roll."""
        # red goes first
        reverse_player_order = self.get_reverse_player_order(current_player_id)
        for player_id in reverse_player_order:
            has_shopping_mall = self.players[player_id]["landmarks"]["shopping_mall"]
            for building_name, building_info in self.players[player_id][
                "establishments"
            ].items():
                if self.players[current_player_id]["coins"] == 0:
                    continue
                if building_name not in restaurants_tuple:
                    continue
                if building_info["working"] == 0:
                    if building_info['on_renovation'] > 0:
                        self.renovation('open', player_id, building_name)
                    continue
                if roll not in activation_dict[building_name]["roll"]:
                    continue
                coins_to_take = activation_dict[building_name]["value"]
                if coins_to_take == 'special':
                    kwargs = {'target_player_id': current_player_id, 'receiving_player_id': player_id}
                    self.activate_special_card(building_name, -1, building_info, **kwargs)
                    continue

                if has_shopping_mall:
                    coins_to_take += 1
                coins_to_take *= building_info["working"]
                coins_to_take = min(
                    coins_to_take, self.players[current_player_id]["coins"]
                )
                self.players[current_player_id]["coins"] -= coins_to_take
                self.players[player_id]["coins"] += coins_to_take

        # green goes second, loan office is the first of them
        if "loan_office" in self.players[current_player_id]["establishments"].keys():
            coins_to_take = activation_dict["loan_office"]["value"]
            coins_to_take *= self.players[current_player_id]["establishments"][
                "loan_office"
            ]["working"]
            coins_to_take = min(
                abs(coins_to_take), self.players[current_player_id]["coins"]
            )
            self.players[current_player_id]["coins"] -= coins_to_take
            if self.players[current_player_id]["establishments"][
                "loan_office"
            ]['on_renovation'] > 0:
                self.renovation('open', current_player_id, "loan_office")

        has_shopping_mall = self.players[current_player_id]["landmarks"][
            "shopping_mall"
        ]
        for building_name, building_info in self.players[current_player_id][
            "establishments"
        ].items():
            if building_name not in secondary_industry_dict:
                continue
            if building_info["working"] == 0:
                if building_info['on_renovation'] > 0:
                    self.renovation('open', current_player_id, building_name)
                continue
            if roll not in activation_dict[building_name]["roll"]:
                continue
            coins_to_take = activation_dict[building_name]["value"]
            if coins_to_take == "special":
                kwargs = {}
                if building_name == "moving_company":
                    kwargs["target_player_id"] = self.get_target_player_id(current_player_id)
                    kwargs["current_player_building"] = random.choice([
                        self.players[current_player_id]['establishments'].keys()
                    ])
                self.activate_special_card(building_name, current_player_id, building_info, **kwargs)

            if has_shopping_mall and secondary_industry_dict[building_name] == "bread":
                coins_to_take += 1

            coins_to_take *= building_info["working"]
            self.players[current_player_id]["coins"] += coins_to_take

        # blue goes next
        for player_id in self.players:
            for building_name, building_info in self.players[player_id][
                "establishments"
            ].items():
                if building_name not in primary_industry_dict:
                    continue
                if building_info["working"] == 0:
                    if building_info['on_renovation'] > 0:
                        self.renovation('open', player_id, building_name)
                    continue
                if roll not in activation_dict[building_name]["roll"]:
                    continue

                coins_to_take = activation_dict[building_name]["value"]
                if coins_to_take == "special":
                    self.activate_special_card(building_name, current_player_id, building_info)

                coins_to_take *= building_info["working"]
                self.players[player_id]["coins"] += coins_to_take

        # purple goes last
        for building_name, building_info in self.players[current_player_id][
            "establishments"
        ].items():
            if building_name not in major_establishments_tuple:
                continue
            if building_info["working"] == 0:
                if building_info['on_renovation'] > 0:
                    self.renovation('open', current_player_id, building_name)
                continue
            if roll not in activation_dict[building_name]["roll"]:
                continue

            kwargs = {}
            if building_name == "tv_station":
                kwargs["target_player_id"] = self.get_target_player_id(current_player_id)
            if building_name == "business_center":
                kwargs["target_player_id"] = self.get_target_player_id(current_player_id)
                kwargs["target_player_building"] = random.choice([
                    key for key in self.players[kwargs['target_player_id']]['establishments'].keys()
                    if self.players[current_player_id]['establishments'][key]['working'] > 0
                ])
                kwargs["current_player_building"] = random.choice([
                    self.players[current_player_id]['establishments'].keys()
                ])

            self.activate_special_card(building_name, current_player_id, building_info, **kwargs)

    def get_target_player_id(self, current_player_id: int):
        # just take from the richest
        target_player_id = sorted([
            (player_id, self.players[player_id]['coins'])
            for player_id in self.players
            if player_id != current_player_id
        ], key=lambda a: a[1], reverse=True)
        target_player_id = target_player_id[0][0]
        return target_player_id

    def activate_special_card(
        self, card_name: str, current_player_id: int, building_info: dict, **kwargs
    ):
        match card_name:
            case "fruit_and_vegetable_market":
                total_wheat_buildings = 0
                for b_name, b_info in self.players[current_player_id][
                    "establishments"
                ].items():
                    if primary_industry_dict.get(b_name, "") == "wheat":
                      total_wheat_buildings += b_info['working'] + b_info['on_renovation']
                coins_to_gain = 2 * total_wheat_buildings
                coins_to_gain *= building_info['working']
                self.players[current_player_id]['coins'] += coins_to_gain
                if building_info['on_renovation'] > 0:
                    self.renovation('open', current_player_id, card_name)
            case "cheese_factory":
                total_cow_buildings = 0
                for b_name, b_info in self.players[current_player_id][
                    "establishments"
                ].items():
                    if primary_industry_dict.get(b_name, "") == "cow":
                      total_cow_buildings += b_info['working'] + b_info['on_renovation']
                coins_to_gain = 3 * total_cow_buildings
                coins_to_gain *= building_info['working']
                self.players[current_player_id]['coins'] += coins_to_gain
                if building_info['on_renovation'] > 0:
                    self.renovation('open', current_player_id, card_name)
            case "furniture_factory":
                total_gear_buildings = 0
                for b_name, b_info in self.players[current_player_id][
                    "establishments"
                ].items():
                    if primary_industry_dict.get(b_name, "") == "gear":
                        total_gear_buildings += b_info['working'] + b_info['on_renovation']
                coins_to_gain = 3 * total_gear_buildings
                coins_to_gain *= building_info['working']
                self.players[current_player_id]['coins'] += coins_to_gain
                if building_info['on_renovation'] > 0:
                    self.renovation('open', current_player_id, card_name)
            case "stadium":
                reverse_player_order = self.get_reverse_player_order(current_player_id)
                for player_id in reverse_player_order:
                    coins_to_take = 2
                    coins_to_take *= building_info['working']
                    coins_to_take = min(coins_to_take, self.players[player_id]['coins'])
                    self.players[player_id] -= coins_to_take
                    self.players[current_player_id]['coins'] += coins_to_take
                if building_info['on_renovation'] > 0:
                    self.renovation('open', current_player_id, card_name)
            case "tv_station":
                target_player_id = kwargs["target_player_id"]
                coins_to_take = 5
                coins_to_take *= building_info['working']
                coins_to_take = min(coins_to_take, self.players[target_player_id]['coins'])
                self.players[target_player_id]['coins'] -= coins_to_take
                self.players[current_player_id]['coins'] += coins_to_take
                if building_info['on_renovation'] > 0:
                    self.renovation('open', current_player_id, card_name)
            case "business_center":
                for _ in building_info['working']:
                    target_player_id = kwargs['target_player_id']
                    target_player_building = kwargs["target_player_building"]
                    current_player_building = kwargs["current_player_building"]
                    self.players[target_player_id]["establishments"][target_player_building]['working'] -= 1
                    if kwargs['target_player_building'] not in self.players[current_player_id]['establishments']:
                        self.players[current_player_id]["establishments"][target_player_building] = {'working': 1}
                    else:
                        self.players[current_player_id]["establishments"][target_player_building]['working'] += 1

                    if self.players[current_player_id]["establishments"][current_player_building]['on_renovation'] > 0:
                        self.players[current_player_id]["establishments"][current_player_building]['on_renovation'] -= 1
                        is_renovated = True
                    else:
                        self.players[current_player_id]["establishments"][current_player_building][
                            'working'] -= 1
                        is_renovated = False
                    if current_player_building not in self.players[kwargs['target_player_id']]['establishments']:
                        if is_renovated:
                            self.players[target_player_id]["establishments"][current_player_building] = {'on_renovation': 1}
                        else:
                            self.players[target_player_id]["establishments"][
                                current_player_building] = {'working': 1}
                    else:
                        if is_renovated:
                            self.players[target_player_id]["establishments"][
                                current_player_building]['on_renovation'] += 1
                        else:
                            self.players[target_player_id]["establishments"][
                                current_player_building]['working'] += 1
                if building_info['on_renovation'] > 0:
                    self.renovation('open', current_player_id, card_name)
            case "tuna_boat":
                tuna_roll = self.roll_dice(num_dice=2)
                coins_to_gain = tuna_roll * building_info['working']
                self.players[current_player_id] += coins_to_gain
                if building_info['on_renovation'] > 0:
                    self.renovation('open', current_player_id, card_name)
            case "flower_shop":
                flower_gardens = self.players[current_player_id]['establishments'].get(
                    'flower_garden',
                    {"working": 0, "on_renovation": 0},
                )
                flower_gardens = flower_gardens['working'] + flower_gardens['on_renovation']
                coins_to_gain = flower_gardens * building_info['working']
                self.players[current_player_id] += coins_to_gain
                if building_info['on_renovation'] > 0:
                    self.renovation('open', current_player_id, card_name)
            case "food_warehouse":
                total_restaurants = 0
                for b_name, b_info in self.players[current_player_id]['establishments']:
                    if b_name in restaurants_tuple:
                        total_restaurants += b_info['working'] + b_info['on_renovation']
                coins_to_gain = total_restaurants * 2
                coins_to_gain *= building_info['working']
                self.players[current_player_id] += coins_to_gain
                if building_info['on_renovation'] > 0:
                    self.renovation('open', current_player_id, card_name)
            case "sushi_bar":
                target_player_id = kwargs['target_player_id']
                receiving_player_id = kwargs['receiving_player_id']
                coins_to_take = 3
                if self.players[receiving_player_id]['landmarks']['shopping_mall']:
                    coins_to_take += 1
                if not self.players[receiving_player_id]['landmarks']['harbor']:
                    coins_to_take = 0
                coins_to_take *= self.players[receiving_player_id]['establishments']['sushi_bar']['working']
                self.players[target_player_id]['coins'] -= coins_to_take
                self.players[receiving_player_id]['coins'] += coins_to_take
                if building_info['on_renovation'] > 0:
                    self.renovation('open', current_player_id, card_name)
            case "publisher":
                reverse_player_order = self.get_reverse_player_order(current_player_id)
                for target_player_id in reverse_player_order:
                    coins_to_take = 0
                    for b_name, b_info in self.players[target_player_id]['establishments']:
                        if b_name in restaurants_tuple or secondary_industry_dict.get(b_name, "") == "bread":
                            coins_to_take += b_info['working'] + b_info['on_renovation']
                    coins_to_take *= building_info['working']
                    coins_to_take = min(coins_to_take, self.players[target_player_id]['coins'])
                    self.players[target_player_id]['coins'] -= coins_to_take
                    self.players[current_player_id]['coins'] += coins_to_take
                if building_info['on_renovation'] > 0:
                    self.renovation('open', current_player_id, card_name)
            case "tax_office":
                reverse_player_order = self.get_reverse_player_order(current_player_id)
                for target_player_id in reverse_player_order:
                    if self.players[target_player_id]['coins'] >= 10:
                        coins_to_take = math.floor(self.players[target_player_id]['coins'] / 2)
                        coins_to_take *= building_info['working']
                        self.players[target_player_id]['coins'] -= coins_to_take
                        self.players[current_player_id]['coins'] += coins_to_take
                if building_info['on_renovation'] > 0:
                    self.renovation('open', current_player_id, card_name)
            case "corn_field":
                if sum(self.players[current_player_id]['landmarks']) < 2:
                    coins_to_gain = 2
                    coins_to_gain *= building_info["working"]
                else:
                    coins_to_gain = 0
                self.players[current_player_id]['coins'] += coins_to_gain
                if building_info['on_renovation'] > 0:
                    self.renovation('open', current_player_id, card_name)
            case "general_store":
                if sum(self.players[current_player_id]['landmarks']) < 2:
                    coins_to_gain = 2 if not self.players[current_player_id]['landmarks']['shopping_mall'] else 3
                    coins_to_gain *= building_info["working"]
                else:
                    coins_to_gain = 0
                self.players[current_player_id]['coins'] += coins_to_gain
                if building_info['on_renovation'] > 0:
                    self.renovation('open', current_player_id, card_name)
            case "moving_company":
                target_player_id = kwargs['target_player_id']
                current_player_building = kwargs["current_player_building"]

                for _ in building_info['working']:
                    if self.players[current_player_id]["establishments"][current_player_building]['on_renovation'] > 0:
                        self.players[current_player_id]["establishments"][current_player_building]['on_renovation'] -= 1
                        is_renovated = True
                    else:
                        self.players[current_player_id]["establishments"][current_player_building][
                            'working'] -= 1
                        is_renovated = False
                    if current_player_building not in self.players[kwargs['target_player_id']]['establishments']:
                        if is_renovated:
                            self.players[target_player_id]["establishments"][current_player_building] = {'on_renovation': 1}
                        else:
                            self.players[target_player_id]["establishments"][
                                current_player_building] = {'working': 1}
                    else:
                        if is_renovated:
                            self.players[target_player_id]["establishments"][
                                current_player_building]['on_renovation'] += 1
                        else:
                            self.players[target_player_id]["establishments"][
                                current_player_building]['working'] += 1

                coins_to_gain = 4
                coins_to_gain *= building_info['working']
                self.players[current_player_id]['coins'] += coins_to_gain
                if building_info['on_renovation'] > 0:
                    self.renovation('open', current_player_id, card_name)
            case "winery":
                coins_to_gain = 6
                vineyards = self.players[current_player_id]['establishments'].get('vineyard', {'working': 0, 'on_renovation': 0})
                vineyards = vineyards['working'] + vineyards['on_renovation']
                coins_to_gain *= vineyards
                coins_to_gain *= building_info['working']
                self.players[current_player_id]['coins'] += coins_to_gain
                working, on_renovation = building_info['working'], building_info['on_renovation']
                self.players[current_player_id]['establishments']['winery'] = {'working': on_renovation, 'on_renovation': working}
            case "demolition_company":
                pass
            case _:
                raise ValueError(f"Unknown card_name: {card_name}")

    def renovation(self, direction: str, player_id: int, card_name: str):
        if direction not in ('open', 'close'):
            raise ValueError(f'Unknown direction: {direction}')

        if direction == 'open':
            to_open = self.players[player_id][card_name]['on_renovation']
            self.players[player_id][card_name]['on_renovation'] = 0
            self.players[player_id][card_name]['working'] += to_open
        else:
            to_close = self.players[player_id][card_name]['working']
            self.players[player_id][card_name]['working'] = 0
            self.players[player_id][card_name]['on_renovation'] += to_close


    def take_turn(self):
        """Simulate one turn for the current player."""
        player = self.players[self.current_turn]

        if not player["is_first_turn"]:
            # Step 1: Roll Dice
            num_dice = (
                1 if not player["landmarks"]["train_station"] else random.choice([1, 2])
            )
            roll, is_double = self.roll_dice(num_dice)
            print(
                f"Player {player['id']} rolled {roll} ({'which is double' if is_double else 'not double'})."
            )

            # Step 2: player can choose to reroll if he has radio tower
            if player["landmarks"]["radio_tower"]:
                do_reroll = bool(random.random() < 0.5)
                if do_reroll:
                    print(f'Player {player["id"]} chose to reroll')
                    num_dice = (
                        1
                        if not player["landmarks"]["train_station"]
                        else random.choice([1, 2])
                    )
                    roll, is_double = self.roll_dice(num_dice)
                    print(
                        f"Player {player['id']} rolled {roll} ({'which is double' if is_double else 'not double'})."
                    )

            # Step 3: Activate Cards
            self.activate_cards(player["id"], roll)
        player["is_first_turn"] = False

        # Step 4: Сity hall gives a coin if active player does not have any
        player["coins"] = 1 if player["coins"] == 0 else player["coins"]

        # Step 5: Buy a card (randomly for now)
        if player["coins"] > 0:
            possible_purchases = [
                card
                for card, count in self.market.items()
                if building_cost_dict[card] <= player["coins"] and count > 0
            ]
            if possible_purchases:
                purchase = random.choice(possible_purchases)
                player["coins"] -= building_cost_dict[purchase]
                self.market[purchase] -= 1
                player["establishments"][purchase]["working"] = (
                    player["establishments"].get(purchase, 0) + 1
                )
                print(f"Player {player['id']} bought {purchase}.")

        # Move to next player
        self.current_turn = (self.current_turn + 1) % self.n_players

    def is_game_over(self):
        """Check if a player has won."""
        for player_id in self.players:
            if all(
                self.players[player_id]["landmarks"].values()
            ):  # All landmarks completed
                return True, player_id
        return False, -1

    def play_game(self):
        """Simulate a full game."""
        is_game_over, winning_player_id = self.is_game_over()
        while not is_game_over:
            self.take_turn()
            print(f"--- End of turn {self.current_turn} ---")
            is_game_over, winning_player_id = self.is_game_over()
        print("Game over!")
        print(f"Player {winning_player_id} wins!")
