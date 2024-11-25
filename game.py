import math
import random
from typing import Dict

from pydantic import BaseModel, Field

from constants import (
    activation_dict,
    building_cost_dict,
    landmarks_tuple,
    major_establishments_tuple,
    primary_industry_dict,
    restaurants_tuple,
    secondary_industry_dict,
    starting_buildings_dict,
)


class EstablishmentCount(BaseModel, validate_assignment=True):
    working: int = Field(ge=0, strict=True)
    on_renovation: int = Field(ge=0, strict=True)


class Player(BaseModel, validate_assignment=True):
    id: int = Field(frozen=True, strict=True)
    coins: int = Field(ge=0, strict=True)
    major_establishments: Dict[str, bool]
    landmarks: Dict[str, bool]
    establishments: Dict[str, EstablishmentCount]
    is_first_turn: bool = True


class MachiKoroGame:
    def __init__(
        self,
        n_players: int,
        starting_buildings: dict = starting_buildings_dict,
        starting_major_establishments: tuple = (),
    ):
        self.n_players = n_players
        self.players = {
            i: self._init_player(i, starting_buildings, starting_major_establishments)
            for i in range(n_players)
        }
        self.market = self._init_market(n_players)
        self.current_player = 0
        self.current_turn = 0
        self.tech_startups = {i: 0 for i in range(n_players)}

    @staticmethod
    def _init_player(
        player_id: int,
        starting_buildings: dict = starting_buildings_dict,
        starting_major_establishments: tuple = (),
    ):
        return Player(
            id=player_id,
            coins=3,
            major_establishments={
                key: True if key in starting_major_establishments else False
                for key in major_establishments_tuple
            },
            landmarks={landmark: False for landmark in landmarks_tuple},
            establishments={
                key: EstablishmentCount(working=val[0], on_renovation=val[1])
                for key, val in starting_buildings.items()
            },
            is_first_turn=True,
        )

    @staticmethod
    def _init_market(n_players: int):
        """Initialize the market with establishment cards."""
        market_dict = {landmark: n_players for landmark in landmarks_tuple}
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
        order = [player_id - 1 if player_id - 1 >= 0 else self.n_players - 1]
        for id_ in range(self.n_players - 1):
            if order[-1] == 0:
                order.append(self.n_players - 1)
            else:
                order.append(order[-1] - 1)

        return order[:-1]

    def activate_cards(self, current_player_id: int, roll: int):
        """Activate cards based on dice roll."""
        # red goes first
        reverse_player_order = self.get_reverse_player_order(current_player_id)
        for player_id in reverse_player_order:
            has_shopping_mall = self.players[player_id].landmarks["shopping_mall"]
            for building_name, building_info in self.players[
                player_id
            ].establishments.items():
                if self.players[current_player_id].coins == 0:
                    continue
                if building_name not in restaurants_tuple:
                    continue
                if building_info.working == 0:
                    if building_info.on_renovation > 0:
                        self.renovation("open", player_id, building_name)
                    continue
                if roll not in activation_dict[building_name]["roll"]:
                    continue
                coins_to_take = activation_dict[building_name]["value"]
                if coins_to_take == "special":
                    kwargs = {
                        "target_player_id": current_player_id,
                        "receiving_player_id": player_id,
                    }
                    self.activate_special_card(
                        building_name, -1, building_info, **kwargs
                    )
                    continue

                if has_shopping_mall:
                    coins_to_take += 1
                coins_to_take *= building_info.working
                coins_to_take = min(
                    coins_to_take, self.players[current_player_id].coins
                )
                self.players[current_player_id].coins -= coins_to_take
                print(
                    f"{current_player_id=} lost {coins_to_take=}, current player coins: {self.players[current_player_id].coins}"
                )
                self.players[player_id].coins += coins_to_take
                print(
                    f"{player_id=} gain {coins_to_take=}, current player coins: {self.players[player_id].coins}"
                )

        # green goes second, loan office is the first of them
        if "loan_office" in self.players[current_player_id].establishments.keys():
            coins_to_take = activation_dict["loan_office"]["value"]
            coins_to_take *= (
                self.players[current_player_id].establishments["loan_office"].working
            )
            coins_to_take = min(
                abs(coins_to_take), self.players[current_player_id].coins
            )
            self.players[current_player_id].coins -= coins_to_take
            if (
                self.players[current_player_id]
                .establishments["loan_office"]
                .on_renovation
                > 0
            ):
                self.renovation("open", current_player_id, "loan_office")

        # moving company is the second
        if (
            "moving_company" in self.players[current_player_id].establishments
            and roll in activation_dict["moving_company"]["roll"]
        ):
            building_info = self.players[current_player_id].establishments[
                "moving_company"
            ]
            for _ in range(building_info.working):
                self.clean_empty_cards()
                kwargs = {
                    "target_player_id": self.get_target_player_id(current_player_id),
                    "current_player_building": random.choice(
                        [
                            key
                            for key in self.players[
                                current_player_id
                            ].establishments.keys()
                            if self.players[current_player_id]
                            .establishments[key]
                            .working
                            > 0
                            or self.players[current_player_id]
                            .establishments[key]
                            .on_renovation
                            > 0
                        ]
                    ),
                }
                self.activate_special_card(
                    "moving_company", current_player_id, building_info, **kwargs
                )
                self.clean_empty_cards()
            if building_info.on_renovation:
                self.renovation("open", current_player_id, "moving_company")

        has_shopping_mall = self.players[current_player_id].landmarks["shopping_mall"]
        for building_name, building_info in self.players[
            current_player_id
        ].establishments.items():
            if building_name not in secondary_industry_dict:
                continue
            if building_name in ("loan_office", "moving_company"):
                continue
            if roll not in activation_dict[building_name]["roll"]:
                continue
            if building_info.working == 0:
                if building_info.on_renovation > 0:
                    self.renovation("open", current_player_id, building_name)
                continue

            coins_to_take = activation_dict[building_name]["value"]
            if coins_to_take == "special":
                self.activate_special_card(
                    building_name, current_player_id, building_info
                )
                continue

            if has_shopping_mall and secondary_industry_dict[building_name] == "bread":
                coins_to_take += 1

            coins_to_take *= building_info.working
            self.players[current_player_id].coins += coins_to_take

        # blue goes next
        for player_id in self.players:
            for building_name, building_info in self.players[
                player_id
            ].establishments.items():
                if building_name not in primary_industry_dict:
                    continue
                if building_info.working == 0:
                    if building_info.on_renovation > 0:
                        self.renovation("open", player_id, building_name)
                    continue
                if roll not in activation_dict[building_name]["roll"]:
                    continue

                coins_to_take = activation_dict[building_name]["value"]
                if coins_to_take == "special":
                    self.activate_special_card(building_name, player_id, building_info)
                    continue

                coins_to_take *= building_info.working
                self.players[player_id].coins += coins_to_take

        # purple goes last
        for building_name in self.players[current_player_id].major_establishments:
            if building_name == "business_center":
                continue
            if roll not in activation_dict[building_name]["roll"]:
                continue

            kwargs = {}
            if building_name == "tv_station":
                kwargs["target_player_id"] = self.get_target_player_id(
                    current_player_id
                )
            if building_name == "renovation_company":
                choose_from = [
                    building_name
                    for player_id in self.players
                    for building_name in self.players[player_id].establishments
                ]
                choose_from = list(set(choose_from))
                kwargs["target_building_name"] = random.choice(choose_from)

            self.activate_special_card(
                building_name,
                current_player_id,
                EstablishmentCount(working=1, on_renovation=0),
                **kwargs,
            )

        # special treatment for business center
        if (
            "business_center" in self.players[current_player_id].major_establishments
            and roll in activation_dict["business_center"]["roll"]
        ):
            kwargs = {"target_player_id": self.get_target_player_id(current_player_id)}  # noqa
            kwargs["target_player_building"] = random.choice(
                [
                    key
                    for key in self.players[
                        kwargs["target_player_id"]
                    ].establishments.keys()
                    if self.players[kwargs["target_player_id"]]
                    .establishments[key]
                    .working
                    > 0
                    or self.players[kwargs["target_player_id"]]
                    .establishments[key]
                    .on_renovation
                    > 0
                ]
            )
            kwargs["current_player_building"] = random.choice(
                list(
                    key
                    for key in self.players[current_player_id].establishments.keys()
                    if self.players[current_player_id].establishments[key].working > 0
                    or self.players[current_player_id].establishments[key].on_renovation
                    > 0
                )
            )
            self.activate_special_card(
                "business_center",
                current_player_id,
                EstablishmentCount(working=1, on_renovation=0),
                **kwargs,
            )

    def get_target_player_id(self, current_player_id: int):
        # just take from the richest
        target_player_id = sorted(
            [
                (player_id, self.players[player_id].coins)
                for player_id in self.players
                if player_id != current_player_id
            ],
            key=lambda a: a[1],
            reverse=True,
        )
        target_player_id = target_player_id[0][0]
        return target_player_id

    def activate_special_card(
        self,
        card_name: str,
        current_player_id: int,
        building_info: EstablishmentCount,
        **kwargs,
    ):
        match card_name:
            case "fruit_and_vegetable_market":
                total_wheat_buildings = 0
                for b_name, b_info in self.players[
                    current_player_id
                ].establishments.items():
                    if primary_industry_dict.get(b_name, "") == "wheat":
                        total_wheat_buildings += b_info.working + b_info.on_renovation
                coins_to_gain = 2 * total_wheat_buildings
                coins_to_gain *= building_info.working
                self.players[current_player_id].coins += coins_to_gain
                if building_info.on_renovation > 0:
                    self.renovation("open", current_player_id, card_name)
            case "cheese_factory":
                total_cow_buildings = 0
                for b_name, b_info in self.players[
                    current_player_id
                ].establishments.items():
                    if primary_industry_dict.get(b_name, "") == "cow":
                        total_cow_buildings += b_info.working + b_info.on_renovation
                coins_to_gain = 3 * total_cow_buildings
                coins_to_gain *= building_info.working
                self.players[current_player_id].coins += coins_to_gain
                if building_info.on_renovation > 0:
                    self.renovation("open", current_player_id, card_name)
            case "furniture_factory":
                total_gear_buildings = 0
                for b_name, b_info in self.players[
                    current_player_id
                ].establishments.items():
                    if primary_industry_dict.get(b_name, "") == "gear":
                        total_gear_buildings += b_info.working + b_info.on_renovation
                coins_to_gain = 3 * total_gear_buildings
                coins_to_gain *= building_info.working
                self.players[current_player_id].coins += coins_to_gain
                if building_info.on_renovation > 0:
                    self.renovation("open", current_player_id, card_name)
            case "stadium":
                reverse_player_order = self.get_reverse_player_order(current_player_id)
                for player_id in reverse_player_order:
                    coins_to_take = 2
                    coins_to_take *= building_info.working
                    coins_to_take = min(coins_to_take, self.players[player_id].coins)
                    self.players[player_id].coins -= coins_to_take
                    self.players[current_player_id].coins += coins_to_take
            case "tv_station":
                target_player_id = kwargs["target_player_id"]
                coins_to_take = 5
                coins_to_take *= building_info.working
                coins_to_take = min(coins_to_take, self.players[target_player_id].coins)
                self.players[target_player_id].coins -= coins_to_take
                self.players[current_player_id].coins += coins_to_take
            case "business_center":
                target_player_id = kwargs["target_player_id"]
                target_player_building = kwargs["target_player_building"]
                current_player_building = kwargs["current_player_building"]

                b_info = self.players[target_player_id].establishments[
                    target_player_building
                ]
                transferring_renovated = False
                if b_info.working > 0:
                    self.players[target_player_id].establishments[
                        target_player_building
                    ].working -= 1
                elif b_info.on_renovation > 0:
                    transferring_renovated = True
                    self.players[target_player_id].establishments[
                        target_player_building
                    ].on_renovation -= 1

                b_info = self.players[target_player_id].establishments[
                    target_player_building
                ]
                if b_info.working == 0 and b_info.on_renovation == 0:
                    self.players[target_player_id].establishments.pop(
                        target_player_building
                    )

                if (
                    target_player_building
                    in self.players[current_player_id].establishments
                ):
                    if transferring_renovated:
                        self.players[current_player_id].establishments[
                            target_player_building
                        ].on_renovation += 1
                    else:
                        self.players[current_player_id].establishments[
                            target_player_building
                        ].working += 1
                else:
                    if transferring_renovated:
                        self.players[current_player_id].establishments[
                            target_player_building
                        ] = EstablishmentCount(working=0, on_renovation=1)
                    else:
                        self.players[current_player_id].establishments[
                            target_player_building
                        ] = EstablishmentCount(working=1, on_renovation=0)

                b_info = self.players[current_player_id].establishments[
                    current_player_building
                ]
                if b_info.on_renovation > 0:
                    transferring_renovated = True
                    self.players[current_player_id].establishments[
                        current_player_building
                    ].on_renovation -= 1
                elif b_info.working > 0:
                    transferring_renovated = False
                    self.players[current_player_id].establishments[
                        current_player_building
                    ].working -= 1

                b_info = self.players[current_player_id].establishments[
                    current_player_building
                ]
                if b_info == EstablishmentCount(working=0, on_renovation=0):
                    self.players[current_player_id].establishments.pop(
                        current_player_building
                    )

                if (
                    current_player_building
                    in self.players[target_player_id].establishments
                ):
                    if transferring_renovated:
                        self.players[target_player_id].establishments[
                            current_player_building
                        ].on_renovation += 1
                    else:
                        self.players[target_player_id].establishments[
                            current_player_building
                        ].working += 1
                else:
                    if transferring_renovated:
                        self.players[target_player_id].establishments[
                            current_player_building
                        ] = EstablishmentCount(working=0, on_renovation=1)
                    else:
                        self.players[target_player_id].establishments[
                            current_player_building
                        ] = EstablishmentCount(working=1, on_renovation=0)
            case "tuna_boat":
                tuna_roll, _ = self.roll_dice(num_dice=2)
                coins_to_gain = tuna_roll * building_info.working
                self.players[current_player_id].coins += coins_to_gain
                if building_info.on_renovation > 0:
                    self.renovation("open", current_player_id, card_name)
            case "flower_shop":
                flower_gardens = self.players[current_player_id].establishments.get(
                    "flower_garden",
                    EstablishmentCount(working=0, on_renovation=0),
                )
                flower_gardens = flower_gardens.working + flower_gardens.on_renovation
                coins_to_gain = flower_gardens * building_info.working
                self.players[current_player_id].coins += coins_to_gain
                if building_info.on_renovation > 0:
                    self.renovation("open", current_player_id, card_name)
            case "food_warehouse":
                total_restaurants = 0
                for b_name, b_info in self.players[
                    current_player_id
                ].establishments.items():
                    if b_name in restaurants_tuple:
                        total_restaurants += b_info.working + b_info.on_renovation
                coins_to_gain = total_restaurants * 2
                coins_to_gain *= building_info.working
                self.players[current_player_id].coins += coins_to_gain
                if building_info.on_renovation > 0:
                    self.renovation("open", current_player_id, card_name)
            case "sushi_bar":
                target_player_id = kwargs["target_player_id"]
                receiving_player_id = kwargs["receiving_player_id"]
                coins_to_take = 3
                if self.players[receiving_player_id].landmarks["shopping_mall"]:
                    coins_to_take += 1
                if not self.players[receiving_player_id].landmarks["harbor"]:
                    coins_to_take = 0
                coins_to_take *= (
                    self.players[receiving_player_id]
                    .establishments["sushi_bar"]
                    .working
                )
                coins_to_take = min(coins_to_take, self.players[target_player_id].coins)
                self.players[target_player_id].coins -= coins_to_take
                self.players[receiving_player_id].coins += coins_to_take
                if building_info.on_renovation > 0:
                    self.renovation("open", receiving_player_id, card_name)
            case "publisher":
                reverse_player_order = self.get_reverse_player_order(current_player_id)
                for target_player_id in reverse_player_order:
                    coins_to_take = 0
                    for b_name, b_info in self.players[
                        target_player_id
                    ].establishments.items():
                        if (
                            b_name in restaurants_tuple
                            or secondary_industry_dict.get(b_name, "") == "bread"
                        ):
                            coins_to_take += b_info.working + b_info.on_renovation
                    coins_to_take *= building_info.working
                    coins_to_take = min(
                        coins_to_take, self.players[target_player_id].coins
                    )
                    self.players[target_player_id].coins -= coins_to_take
                    self.players[current_player_id].coins += coins_to_take
            case "tax_office":
                reverse_player_order = self.get_reverse_player_order(current_player_id)
                for target_player_id in reverse_player_order:
                    if self.players[target_player_id].coins >= 10:
                        coins_to_take = math.floor(
                            self.players[target_player_id].coins / 2
                        )
                        coins_to_take *= building_info.working
                        self.players[target_player_id].coins -= coins_to_take
                        self.players[current_player_id].coins += coins_to_take
            case "corn_field":
                if sum(self.players[current_player_id].landmarks.values()) < 2:
                    coins_to_gain = 2
                    coins_to_gain *= building_info.working
                else:
                    coins_to_gain = 0
                self.players[current_player_id].coins += coins_to_gain
                if building_info.on_renovation > 0:
                    self.renovation("open", current_player_id, card_name)
            case "general_store":
                if sum(self.players[current_player_id].landmarks.values()) < 2:
                    coins_to_gain = (
                        3
                        if self.players[current_player_id].landmarks["shopping_mall"]
                        else 2
                    )
                    coins_to_gain *= building_info.working
                else:
                    coins_to_gain = 0
                self.players[current_player_id].coins += coins_to_gain
                if building_info.on_renovation > 0:
                    self.renovation("open", current_player_id, card_name)
            case "moving_company":
                target_player_id = kwargs["target_player_id"]
                current_player_building = kwargs["current_player_building"]

                if (
                    self.players[current_player_id]
                    .establishments[current_player_building]
                    .on_renovation
                    > 0
                ):
                    self.players[current_player_id].establishments[
                        current_player_building
                    ].on_renovation -= 1
                    is_renovated = True
                else:
                    self.players[current_player_id].establishments[
                        current_player_building
                    ].working -= 1
                    is_renovated = False
                if (
                    current_player_building
                    not in self.players[kwargs["target_player_id"]].establishments
                ):
                    if is_renovated:
                        self.players[target_player_id].establishments[
                            current_player_building
                        ] = EstablishmentCount(on_renovation=1, working=0)
                    else:
                        self.players[target_player_id].establishments[
                            current_player_building
                        ] = EstablishmentCount(on_renovation=0, working=1)
                else:
                    if is_renovated:
                        self.players[target_player_id].establishments[
                            current_player_building
                        ].on_renovation += 1
                    else:
                        self.players[target_player_id].establishments[
                            current_player_building
                        ].working += 1

                coins_to_gain = 4
                self.players[current_player_id].coins += coins_to_gain
            case "winery":
                coins_to_gain = 6
                vineyards = self.players[current_player_id].establishments.get(
                    "vineyard", EstablishmentCount(working=0, on_renovation=0)
                )
                vineyards = vineyards.working + vineyards.on_renovation
                coins_to_gain *= vineyards
                coins_to_gain *= building_info.working
                self.players[current_player_id].coins += coins_to_gain
                working, on_renovation = (
                    building_info.working,
                    building_info.on_renovation,
                )
                self.players[current_player_id].establishments["winery"] = (
                    EstablishmentCount(
                        working=on_renovation,
                        on_renovation=working,
                    )
                )
            case "demolition_company":
                landmarks_with_costs = sorted(
                    [
                        (landmark, building_cost_dict[landmark])
                        for landmark in landmarks_tuple
                    ],
                    key=lambda a: a[1],
                )
                landmarks_with_costs = [
                    (landmark, cost)
                    for landmark, cost in landmarks_with_costs
                    if self.players[current_player_id].landmarks[landmark]
                ]
                for _ in range(building_info.working):
                    if not len(landmarks_with_costs):
                        break
                    landmark_to_close = landmarks_with_costs[0][0]
                    self.players[current_player_id].landmarks[landmark_to_close] = False
                    self.market[landmark_to_close] += 1
                    self.players[current_player_id].coins += 8
                    landmarks_with_costs = landmarks_with_costs[1:]

                if building_info.on_renovation > 0:
                    self.renovation("open", current_player_id, card_name)
            case "soda_bottling_plant":
                total_restaurants_from_players = 0
                for player_info in self.players.values():
                    for b_name, b_info in player_info.establishments.items():
                        if b_name in restaurants_tuple:
                            total_restaurants_from_players += (
                                b_info.working + b_info.on_renovation
                            )
                coins_to_gain = 1 * total_restaurants_from_players
                self.players[current_player_id].coins += coins_to_gain
                if building_info.on_renovation > 0:
                    self.renovation("open", current_player_id, card_name)
            case "french_restaurant":
                target_player_id = kwargs["target_player_id"]
                receiving_player_id = kwargs["receiving_player_id"]
                has_shopping_mall = self.players[receiving_player_id].landmarks[
                    "shopping_mall"
                ]
                is_eligible = (
                    sum(self.players[target_player_id].landmarks.values()) >= 2
                )
                for _ in range(building_info.working):
                    if not is_eligible:
                        break
                    coins_to_take = 5
                    if has_shopping_mall:
                        coins_to_take += 1
                    coins_to_take = min(
                        coins_to_take, self.players[target_player_id].coins
                    )
                    self.players[target_player_id].coins -= coins_to_take
                    self.players[receiving_player_id].coins += coins_to_take
                if building_info.on_renovation > 0:
                    self.renovation("open", receiving_player_id, card_name)
            case "park":
                player_coins = sum(
                    self.players[player_id].coins for player_id in self.players
                )
                new_player_coins = math.ceil(player_coins / self.n_players)
                for player_id in self.players:
                    self.players[player_id].coins = new_player_coins
            case "renovation_company":
                building_to_close = kwargs["target_building_name"]
                for player_id in self.players:
                    if building_to_close in self.players[player_id].establishments:
                        close_count = (
                            self.players[player_id]
                            .establishments[building_to_close]
                            .working
                        )
                        self.players[player_id].establishments[
                            building_to_close
                        ].working -= close_count
                        self.players[player_id].establishments[
                            building_to_close
                        ].on_renovation += close_count
            case "tech_startup":
                reverse_player_order = self.get_reverse_player_order(current_player_id)
                for _ in range(building_info.working):
                    for player_id in reverse_player_order:
                        coins_to_take = self.tech_startups[current_player_id]
                        coins_to_take = min(
                            coins_to_take, self.players[player_id].coins
                        )
                        self.players[player_id].coins -= coins_to_take
                        self.players[current_player_id].coins += coins_to_take

    def renovation(self, direction: str, player_id: int, card_name: str):
        if direction == "open":
            to_open = self.players[player_id].establishments[card_name].on_renovation
            self.players[player_id].establishments[card_name].on_renovation = 0
            self.players[player_id].establishments[card_name].working += to_open
        elif direction == "close":
            to_close = self.players[player_id].establishments[card_name].working
            self.players[player_id].establishments[card_name].working = 0
            self.players[player_id].establishments[card_name].on_renovation += to_close

    def clean_empty_cards(self):
        for player_id in self.players:
            to_pop = []
            for building_name, building_info in self.players[
                player_id
            ].establishments.items():
                if building_info == EstablishmentCount(working=0, on_renovation=0):
                    to_pop.append(building_name)
            for building_name in to_pop:
                self.players[player_id].establishments.pop(building_name)

    def take_turn(self):
        """Simulate one turn for the current player."""
        current_player_id = self.current_player
        is_double = False
        self.current_turn += 1
        print(f"START OF TURN {self.current_turn}")
        for player_id in self.players:
            print(f"\t{player_id=}, coins: {self.players[player_id].coins}")
        if not self.players[current_player_id].is_first_turn:
            # Step 1: Roll Dice
            num_dice = (
                1
                if not self.players[current_player_id].landmarks["train_station"]
                else random.choice([1, 2])
            )
            roll, is_double = self.roll_dice(num_dice)
            print(
                f"Player {current_player_id} rolled {roll} {'(which is double)' if is_double else ''}."
            )

            # Step 2: player can choose to reroll if they have radio tower
            if self.players[current_player_id].landmarks["radio_tower"]:
                do_reroll = bool(random.random() < 0.5)
                if do_reroll:
                    print(f"Player {current_player_id} chose to reroll")
                    num_dice = (
                        1
                        if not self.players[current_player_id].landmarks[
                            "train_station"
                        ]
                        else random.choice([1, 2])
                    )
                    roll, is_double = self.roll_dice(num_dice)
                    print(
                        f"Player {current_player_id} rolled {roll} {'(which is double)' if is_double else ''}."
                    )

            # Step 3: Activate Cards
            self.activate_cards(current_player_id, roll)
            # technical step: clean empty cards
            self.clean_empty_cards()
        self.players[current_player_id].is_first_turn = False

        # Step 4: Сity hall gives a coin if active player does not have any
        self.players[current_player_id].coins = (
            1
            if self.players[current_player_id].coins == 0
            else self.players[current_player_id].coins
        )

        # Step 5: Buy a card (randomly for now)
        possible_purchases = [
            card
            for card, count in self.market.items()
            if building_cost_dict[card] <= self.players[current_player_id].coins
            and self.market[card] > 0
            and not self.players[current_player_id].major_establishments.get(
                card, False
            )
            and not self.players[current_player_id].landmarks.get(card, False)
        ]
        print(f"{possible_purchases=}")
        has_built = False
        if possible_purchases:
            purchase = random.choice(possible_purchases)
            if purchase in landmarks_tuple:
                self.market[purchase] -= 1
                self.players[current_player_id].coins -= building_cost_dict[purchase]
                self.players[current_player_id].landmarks[purchase] = True
            elif purchase in major_establishments_tuple:
                self.market[purchase] -= 1
                self.players[current_player_id].coins -= building_cost_dict[purchase]
                self.players[current_player_id].major_establishments[purchase] = True
            else:
                self.players[current_player_id].coins -= building_cost_dict[purchase]
                self.market[purchase] -= 1
                if purchase not in self.players[current_player_id].establishments:
                    self.players[current_player_id].establishments[purchase] = (
                        EstablishmentCount(
                            working=1,
                            on_renovation=0,
                        )
                    )
                else:
                    self.players[current_player_id].establishments[
                        purchase
                    ].working += 1
            has_built = True
            print(f"Player {current_player_id} bought {purchase}.")

        # Step 6: player can choose to put one of their coins on the tech startup
        if "tech_startup" in self.players[current_player_id].major_establishments:
            is_put_a_coin = int(random.random() < 0.5)
            is_put_a_coin = min(is_put_a_coin, self.players[current_player_id].coins)
            self.players[current_player_id].coins -= is_put_a_coin
            self.tech_startups[current_player_id] += is_put_a_coin

        # Step 7: airport trigger
        if not has_built and self.players[current_player_id].landmarks["airport"]:
            self.players[current_player_id].coins += 10

        for player_id in self.players:
            print(
                f"\t{player_id=}, coins: {self.players[player_id].coins}, landmarks: {self.players[player_id].landmarks}"
            )
        if is_double and self.players[current_player_id].landmarks["amusement_park"]:
            # no reason not to take a second turn
            pass
        else:
            self.current_player = (self.current_player + 1) % self.n_players

    def is_game_over(self):
        """Check if a player has won."""
        for player_id in self.players:
            if all(
                self.players[player_id].landmarks.values()
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
