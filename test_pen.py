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


from pen.gcode import GCode
from pen.gcode import PenMode
from pen.gcode import parse_gcode


class TestGCodeParser(unittest.TestCase):
    def test_pen_updown(self):
        op = parse_gcode(GCode.pen_down(), current_position=[0, 0])
        self.assertEqual(PenMode.PEN_DOWN, op.pen_mode)
        op = parse_gcode(GCode.pen_up(), current_position=[0, 0])
        self.assertEqual(PenMode.PEN_UP, op.pen_mode)
        self.assertEqual(0, op.get_pen_distance())
        op.get_duration()

    def test_move_fast(self):
        op = parse_gcode(GCode.move_fast([1, 1]), current_position=[0, 0])
        self.assertListEqual([0, 1, 0, 1], op.get_aabb().get_rect().to_xxyy())
        self.assertEqual(2**0.5, op.get_pen_distance())

    def test_move_linear(self):
        op = parse_gcode(GCode.move_linear([1, 1]), current_position=[0, 0])
        self.assertListEqual([0, 1, 0, 1], op.get_aabb().get_rect().to_xxyy())
        self.assertEqual(2**0.5, op.get_pen_distance())

    def test_full_arc(self):
        op = parse_gcode(GCode.move_arc([1, 1], [1, 1], [1, 2]), current_position=[1, 1])
        self.assertEqual(2.0 * np.pi, op.get_pen_distance())
        self.assertListEqual([0, 2, 1, 3], op.get_aabb().get_rect().to_xxyy())

    def test_partial_arc(self):
        op = parse_gcode(GCode.move_arc([1, 1], [2, 2], [1, 2]), current_position=[1, 1])
        self.assertEqual(0.5 * np.pi, op.get_pen_distance())
        self.assertListEqual([1, 2, 1, 2], op.get_aabb().get_rect().to_xxyy())


from pen.optimizer import remove_repeated_ops

class TestOptimizer(unittest.TestCase):
    def test_remove_repeated_ops(self):
        ops = [
            'M5',
            'G0X0Y0',
            'M3S60',
            'G1X100Y100F1000',
            'M5',
            'M5',
            'G0X50Y60',
            'M3S60',
            'G3X50Y60I0J0F1000',
            'M5',
            'M5',
            'G0X60Y30',
            'M3S60',
            'G3X60Y30I0J0F1000',
            'M5'
        ]

        expected = [
            'M5',
            'G0X0Y0',
            'M3S60',
            'G1X100Y100F1000',
            'M5',
            'G0X50Y60',
            'M3S60',
            'G3X50Y60I0J0F1000',
            'M5',
            'G0X60Y30',
            'M3S60',
            'G3X60Y30I0J0F1000',
            'M5'
        ]
        self.assertLessEqual(expected, remove_repeated_ops(ops))


if __name__ == '__main__':
    unittest.main()
