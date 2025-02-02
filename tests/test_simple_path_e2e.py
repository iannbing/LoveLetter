import json
import unittest
from fastapi.testclient import TestClient

from love_letter.models import Deck, Round


def _test_client() -> TestClient:
    from love_letter.web.app import app
    return TestClient(app)


class TestDeck(Deck):

    def shuffle(self, player_num: int):
        super().shuffle(player_num)
        from love_letter.models import find_card_by_name as c

        self.cards = [
            c('衛兵'),  # player-a 的初始手牌
            c('神父'),  # player-b 的初始手牌
            c('公主'),  # player-a 為 turn player 獲得的牌
            c('衛兵')
        ]


class LoveLetterSimpleCaseEndToEndTests(unittest.TestCase):

    def setUp(self) -> None:
        self.t: TestClient = _test_client()
        # disable random-picker for the first round
        # it always returns the first player
        self.origin_choose_one_randomly = Round.choose_one_randomly
        Round.choose_one_randomly = lambda x: x[0]

    def tearDown(self) -> None:
        Round.choose_one_randomly = self.origin_choose_one_randomly
        self.t.close()

    def test_start_game_with_predefined_state(self):
        player_a = "player-a"
        player_b = "player-b"

        # 將牌庫換成測試用牌庫
        import love_letter.models
        love_letter.models.deck_factory = lambda: TestDeck()

        # 建立遊戲
        game_id = self.t.post(f"/games/create/by_player/{player_a}").json()

        # 加入遊戲
        is_success = self.t.post(f"/games/{game_id}/player/{player_b}/join").json()
        self.assertTrue(is_success)

        # 開始遊戲
        is_started = self.t.post(f"/games/{game_id}/start").json()
        self.assertTrue(is_started)

        # 確認遊戲狀態
        response = self.t.get(f"/games/{game_id}/player/{player_a}/status").json()
        self.assertEqual({'game_id': game_id,
                          'rounds': [{'players': [{'cards': [{'description': '<description>',
                                                              'name': '衛兵',
                                                              'value': 1},
                                                             {'description': '<description>',
                                                              'name': '公主',
                                                              'value': 8}],
                                                   'name': 'player-a',
                                                   'out': False},
                                                  {'cards': [], 'name': 'player-b', 'out': False}],
                                      'turn_player': {'cards': [{'description': '<description>',
                                                                 'name': '衛兵',
                                                                 'value': 1},
                                                                {'description': '<description>',
                                                                 'name': '公主',
                                                                 'value': 8}],
                                                      'name': 'player-a',
                                                      'out': False},
                                      'winner': None}]}, response)

        # 玩家出牌
        request_body = {
            "chosen_player": "player-b",
            "guess_card": "神父"
        }
        response = self.t.post(f"/games/{game_id}/player/player-a/card/衛兵/play", json=request_body).json()
        self.assertEqual({'game_id': game_id,
                          'rounds': [{'players': [{'cards': [{'description': '<description>',
                                                              'name': '公主',
                                                              'value': 8}],
                                                   'name': 'player-a',
                                                   'out': False},
                                                  {'cards': [{'description': '<description>',
                                                              'name': '神父',
                                                              'value': 2}],
                                                   'name': 'player-b',
                                                   'out': True}],
                                      'turn_player': {'cards': [{'description': '<description>',
                                                                 'name': '公主',
                                                                 'value': 8}],
                                                      'name': 'player-a',
                                                      'out': False},
                                      'winner': 'player-a'},
                                     {'players': [{'cards': [{'description': '<description>',
                                                              'name': '衛兵',
                                                              'value': 1},
                                                             {'description': '<description>',
                                                              'name': '公主',
                                                              'value': 8}],
                                                   'name': 'player-a',
                                                   'out': False},
                                                  {'cards': [], 'name': 'player-b', 'out': False}],
                                      'turn_player': {'cards': [{'description': '<description>',
                                                                 'name': '衛兵',
                                                                 'value': 1},
                                                                {'description': '<description>',
                                                                 'name': '公主',
                                                                 'value': 8}],
                                                      'name': 'player-a',
                                                      'out': False},
                                      'winner': None}]}, response)
