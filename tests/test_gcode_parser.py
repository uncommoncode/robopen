import unittest

import numpy as np

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
