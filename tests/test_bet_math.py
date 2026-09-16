import importlib.util
import math
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "skills/sports-betting-expert/scripts/bet_math.py"
SPEC = importlib.util.spec_from_file_location("bet_math", SCRIPT)
bet_math = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bet_math)


class BetMathTests(unittest.TestCase):
    def test_market_normalizes_complete_two_way_market(self):
        result = bet_math.market([1.91, 1.91])
        self.assertAlmostEqual(result["overround"], 0.04712041884816753)
        self.assertEqual(result["normalized_market_benchmark"], [0.5, 0.5])

    def test_single_accounts_for_push(self):
        result = bet_math.single(1.90, 0.45, push=0.25, stake=10)
        self.assertAlmostEqual(result["expected_net_roi"], 0.105)
        self.assertAlmostEqual(result["expected_net_profit"], 1.05)
        self.assertAlmostEqual(result["model_fair_odds"], 1.6666666666666667)

    def test_parlay_requires_explicit_independence(self):
        with self.assertRaisesRegex(ValueError, "--assume-independent"):
            bet_math.parlay([1.8, 2.0], [0.6, 0.55])
        result = bet_math.parlay([1.8, 2.0, 1.75], [0.6, 0.55, 0.6], True)
        self.assertAlmostEqual(result["assumed_joint_win_probability"], 0.198)
        self.assertAlmostEqual(result["expected_net_roi"], 0.2474)

    def test_partial_settlement(self):
        result = bet_math.settlement(1.90, [0.4, 0.2, 0, 0.1, 0.3])
        self.assertAlmostEqual(result["expected_net_roi"], 0.1)

    def test_rejects_invalid_inputs(self):
        invalid = [
            lambda: bet_math.market([1.0, 2.0]),
            lambda: bet_math.single(2.0, 0.8, push=0.3),
            lambda: bet_math.single(2.0, math.nan),
            lambda: bet_math.single(math.inf, 0.5),
            lambda: bet_math.settlement(2.0, [0.2] * 4 + [0.3]),
            lambda: bet_math.parlay([1e308, 1e308]),
        ]
        for operation in invalid:
            with self.subTest(operation=operation):
                with self.assertRaises((ValueError, OverflowError)):
                    operation()


if __name__ == "__main__":
    unittest.main()

