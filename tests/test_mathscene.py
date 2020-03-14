import unittest

import numpy as np

from pen.mathscene import AABB


class TestMathScene(unittest.TestCase):
    def test_aabb_points(self):
        aabb = AABB()
        aabb.add_point([0, 0])
        self.assertListEqual([0, 0, 0, 0], aabb.get_rect().to_xxyy())
        aabb.add_point([-1, 1])
        self.assertListEqual([-1, 0, 0, 1], aabb.get_rect().to_xxyy())
        aabb.add_point([0.0, 0.5])
        self.assertListEqual([-1, 0, 0, 1], aabb.get_rect().to_xxyy())

    def test_aabb_merge(self):
        aabb1 = AABB([
            [0, 0],
            [1, 1],
        ])
        self.assertListEqual([0, 1, 0, 1], aabb1.get_rect().to_xxyy())

        aabb2 = AABB([
            [-1, -1.5],
            [-0.5, -0.5],
        ])
        self.assertListEqual([-1, -0.5, -1.5, -0.5], aabb2.get_rect().to_xxyy())
        aabb1.merge_aabb(aabb2)
        self.assertListEqual([-1, 1, -1.5, 1], aabb1.get_rect().to_xxyy())
