import unittest

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
