"""Test the MVP components work correctly."""

import unittest
from src.env.scenes import make_scene, make_batch
from src.env.scoring import avg_len, count_collisions, score_fn
from src.grammar.utils import load_base_grammar, validate_grammar
from src.loop.evaluate import calculate_grammar_complexity

class TestMVP(unittest.TestCase):

    def setUp(self):
        self.colors = ["red", "blue", "green"]
        self.shapes = ["circle", "square", "triangle"]
        self.sizes = ["small", "medium", "large"]

    def test_scene_generation(self):
        """Test scene generation creates unique objects."""
        scene = make_scene(self.colors, self.shapes, self.sizes, k=3)

        # Check structure
        self.assertIn("target_idx", scene)
        self.assertIn("objects", scene)
        self.assertEqual(len(scene["objects"]), 3)

        # Check target index is valid
        self.assertGreaterEqual(scene["target_idx"], 0)
        self.assertLess(scene["target_idx"], 3)

        # Check objects are unique
        obj_tuples = [(obj["color"], obj["shape"], obj["size"]) for obj in scene["objects"]]
        self.assertEqual(len(obj_tuples), len(set(obj_tuples)))

    def test_batch_generation(self):
        """Test batch generation."""
        batch = make_batch(self.colors, self.shapes, self.sizes, batch_size=5, k=3)
        self.assertEqual(len(batch), 5)

        for scene in batch:
            self.assertEqual(len(scene["objects"]), 3)

    def test_scoring_functions(self):
        """Test scoring functions."""
        messages = ["color:red", "shape:circle", "color:red"]

        # Test average length
        avg_length = avg_len(messages)
        self.assertEqual(avg_length, 10.0)  # (9 + 12 + 9) / 3

        # Test collision counting
        collisions = count_collisions(messages)
        self.assertEqual(collisions, 1)  # "color:red" appears twice

        # Test score function
        score = score_fn(
            acc=0.8,
            avg_chars=10.0,
            complexity={"productions": 5, "avg_rhs_symbols": 2.0},
            collisions=0.1,
            lambdas={"len_per_char": 0.02, "complexity_per_prod": 0.5, "complexity_per_rhs_symbol": 0.1, "collisions": 5.0}
        )
        expected = 0.8 - 0.02*10 - 0.5*5 - 0.1*2 - 5.0*0.1
        self.assertAlmostEqual(score, expected, places=3)

    def test_grammar_utils(self):
        """Test grammar utilities."""
        grammar = load_base_grammar()
        self.assertIn("start:", grammar)
        self.assertTrue(validate_grammar(grammar))

        complexity = calculate_grammar_complexity(grammar)
        self.assertIn("productions", complexity)
        self.assertIn("avg_rhs_symbols", complexity)
        self.assertGreater(complexity["productions"], 0)

if __name__ == "__main__":
    unittest.main()
