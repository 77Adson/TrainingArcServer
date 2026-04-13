import pytest
from app.services.workout_processor import calculate_e1rm, calculate_strength_metrics
from app.services.rpg_math import evaluate_level_progression, get_technique_multiplier

class TestWorkoutProcessor:
    def test_calculate_e1rm(self):
        # Wzór Epleya: W * (1 + R/30)
        assert calculate_e1rm(100, 1) == 100.0
        assert calculate_e1rm(100, 10) == pytest.approx(133.33, 0.01)
        assert calculate_e1rm(0, 10) == 0.0
        assert calculate_e1rm(100, 0) == 0.0

    def test_calculate_strength_metrics(self):
            raw_sets = [
                {"reps": 10, "weight": 100},  # vol: 1000, e1RM: 133.33
                {"reps": 5, "weight": 120}    # vol: 600, e1RM: 140.0
            ]
            
            # Test dla wolnych ciężarów (offset = 0)
            total_vol, best_e1rm = calculate_strength_metrics(raw_sets, body_weight_offset=0)
            assert total_vol == 1600
            assert best_e1rm == 140.0
            
            # Test dla kalisteniki (dodajemy wagę ciała, np. 80kg)
            total_vol_bw, best_e1rm_bw = calculate_strength_metrics(raw_sets, body_weight_offset=80)
            # set 1: 10 * 180 = 1800. set 2: 5 * 200 = 1000. Total = 2800
            assert total_vol_bw == 2800
            assert best_e1rm_bw == 240.0


class TestRpgEngineMath:
    def test_evaluate_level_progression(self):
        # Awans o 1 poziom (1000 XP wymagane na 1 lvl)
        lvl, xp, leveled = evaluate_level_progression(current_level=1, current_xp=0, xp_gained=1500, xp_per_level_multiplier=1000)
        assert lvl == 2
        assert xp == 500  # Reszta przechodzi na kolejny poziom
        assert leveled is True

        # Brak awansu
        lvl2, xp2, leveled2 = evaluate_level_progression(current_level=2, current_xp=500, xp_gained=400, xp_per_level_multiplier=1000)
        assert lvl2 == 2
        assert xp2 == 900
        assert leveled2 is False

        # Podwójny awans w jednej sesji (tzw. power leveling)
        lvl3, xp3, leveled3 = evaluate_level_progression(current_level=1, current_xp=0, xp_gained=3500, xp_per_level_multiplier=1000)
        # lvl 1->2 (koszt 1000), zostaje 2500
        # lvl 2->3 (koszt 2000), zostaje 500
        assert lvl3 == 3
        assert xp3 == 500
        assert leveled3 is True

    def test_get_technique_multiplier(self):
        # 3 gwiazdki = 1.0x (standard)
        assert get_technique_multiplier([{"technique_rating": 3}]) == 1.0
        # 5 gwiazdek = 1.5x
        assert get_technique_multiplier([{"technique_rating": 5}]) == 1.5
        # 1 gwiazdka = 0.5x
        assert get_technique_multiplier([{"technique_rating": 1}]) == 0.5
        # Średnia z dwóch (5 i 1 = 3) -> 1.0x
        assert get_technique_multiplier([{"technique_rating": 5}, {"technique_rating": 1}]) == 1.0