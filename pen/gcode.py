import re
import enum

import numpy as np

from .mathscene import AABB
from .mathscene import Arc
from .mathscene import euclidian_distance


DEFAULT_MOVE_RATE = 2000
DEFAULT_FEED_RATE = 1000
DEFAULT_SERVO_DOWN = 60

RESOLUTION_EU = 1e-5


class GCode:
    @staticmethod
    def set_units_mm():
        return 'G21'

    @staticmethod
    def move_home():
        return 'G28'

    @staticmethod
    def set_coordinates_absolute():
        return 'G90'

    @staticmethod
    def set_coordinates_relative():
        return 'G91'

    @staticmethod
    def set_feed_rate(rate):
        return 'F{}'.format(rate)

    @staticmethod
    def move_fast(end_pt):
        x, y = end_pt
        return 'G0X{}Y{}'.format(x, y)

    @staticmethod
    def move_linear(end_pt, feed_rate=DEFAULT_FEED_RATE):
        x, y = end_pt
        return 'G1X{}Y{}F{}'.format(x, y, feed_rate)

    @staticmethod
    def move_arc(start_pt, end_pt, center_pt, feed_rate=DEFAULT_FEED_RATE):
        x, y = end_pt
        # Relative arc distance mode to the start
        i, j = np.array(center_pt) - np.array(start_pt)
        return 'G3X{}Y{}I{}J{}F{}'.format(x, y, i, j, feed_rate)

    @staticmethod
    def pen_up():
        return 'M5'

    @staticmethod
    def pen_down(servo=DEFAULT_SERVO_DOWN):
        # Lazer power is S0
        # TODO(remap pressure)
        return 'M3S{}'.format(servo)

    @staticmethod
    def is_pen_down_command(gcode):
        return gcode.lower().strip().startswith('m3')

    @staticmethod
    def dwell_milliseconds(milliseconds):
        # Unknown support?
        return 'G4 P{}'.format(milliseconds)

    @staticmethod
    def dwell_seconds(seconds):
        # Unknown support?
        return 'G4 S{}'.format(seconds)


class NGCParser:
    """Help parse NGC files created by inkscape and translate into plotter commands."""
    WAIT_FOR_PATH = 0
    START_PATH = 1
    START_DRAW = 2
    DRAWING = 3

    def __init__(self):
        self.state = self.WAIT_FOR_PATH
        self.commands = []

    def handle_line(self, line):
        if self.state == self.WAIT_FOR_PATH:
            if line.startswith('G00 Z'):
                self.add_command(GCode.pen_up())
                self.state = self.START_PATH
        elif self.state == self.START_PATH:
            if line.startswith('G00 '):
                self.add_command(line)
                self.state = self.START_DRAW
        elif self.state == self.START_DRAW:
            if line.startswith('G01 Z'):
                self.add_command(GCode.pen_down())
                self.state = self.DRAWING
        elif self.state == self.DRAWING:
            if line.startswith('G00 Z'):
                self.add_command(GCode.pen_up())
                self.state = self.WAIT_FOR_PATH
            else:
                self.add_command(line)

    def add_command(self, command):
        self.commands.append(command)


class GCodeOperator:
    def get_pen_distance(self):
        raise NotImplementedError()

    def get_aabb(self):
        raise NotImplementedError()

    def get_duration(self):
        raise NotImplementedError()

    def get_end_position(self):
        raise NotImplementedError()

    def get_pen_mode_update(self):
        return None


class MoveOperator(GCodeOperator):
    def __init__(self, start_position, end_position, rate_eu):
        # Compensate for something off with eu to mm?
        magic_scale = 0.75
        self.start_position = np.array(start_position)
        self.end_position = np.array(end_position)
        self.rate = rate_eu * magic_scale / 60.0

    def get_aabb(self):
        return AABB([self.start_position, self.end_position])

    def get_pen_distance(self):
        return euclidian_distance(self.end_position, self.start_position)

    def get_duration(self):
        return self.get_pen_distance() / self.rate

    def get_end_position(self):
        return self.end_position


class ArcOperator(MoveOperator):
    def __init__(self, start_position, end_position, relative_center, rate_eu):
        super(ArcOperator, self).__init__(start_position, end_position, rate_eu)
        self.arc = Arc.from_relative_points(start_position, end_position, relative_center)

    def get_aabb(self):
        return self.arc.get_aabb()

    def get_pen_distance(self):
        return self.arc.get_line_distance()


class PenMode(enum.Enum):
    PEN_UP = 0
    PEN_DOWN = 1


class PenOperator(GCodeOperator):
    def __init__(self, point, pen_mode):
        self.point = point
        self.pen_mode = pen_mode

    def get_duration(self):
        return 0.1

    def get_pen_distance(self):
        return 0.0

    def get_aabb(self):
        return AABB([self.point])

    def get_end_position(self):
        return self.point

    def get_pen_mode_update(self):
        return self.pen_mode


def parse_gcode(command, current_position):
    m = re.search('([mg])([0-9]+)', command.lower())
    if not m:
        return
    g_command = m.group(1)
    command_type = g_command[0]
    if command_type == 'm':
        pen_type = int(m.group(2))
        if pen_type == 3:
            return PenOperator(current_position, PenMode.PEN_DOWN)
        elif pen_type == 5:
            return PenOperator(current_position, PenMode.PEN_UP)
        else:
            raise RuntimeError('Unsupported pen type: {}'.format(pen_type))
    elif command_type == 'g':
        m = re.search('G([0-9]+)[ ]*', command)
        if not m:
            raise RuntimeError('Bug parsing command: {}'.format(command))
        gcode = int(m.group(1))
        if gcode == 0:
            m = re.search('X[ ]*([^ ]*)[ ]*Y[ ]*([^ ]*)[ ]*', command)
            x = float(m.group(1))
            y = float(m.group(2))
            return MoveOperator(current_position, [x, y], rate_eu=DEFAULT_MOVE_RATE)
        elif gcode == 1:
            m = re.search('X[ ]*([^ ]*)[ ]*Y[ ]*([^ ]*)[ ]*F[ ]*([^ ]*)[ ]*', command)
            x = float(m.group(1))
            y = float(m.group(2))
            rate = int(m.group(3))
            return MoveOperator(current_position, [x, y], rate_eu=rate)
        elif gcode == 3:
            m = re.search('X[ ]*([^ ]*)[ ]*Y[ ]*([^ ]*)[ ]*I[ ]*([^ ]*)[ ]*J[ ]*([^ ]*)[ ]*F[ ]*([^ ]*)[ ]*', command)
            x = float(m.group(1))
            y = float(m.group(2))
            i = float(m.group(3))
            j = float(m.group(4))
            rate = int(m.group(5))
            return ArcOperator(current_position, [x, y], [i, j], rate_eu=rate)
        else:
            raise NotImplementedError('Unsupported gcode type: {} in: {}'.format(gcode, command))


def get_gcode_bounds(commands):
    position = np.array([0, 0])
    aabb = AABB()

    for command in commands:
        op = parse_gcode(command, position)
        aabb.merge_aabb(op.get_aabb())
        position = op.get_end_position()

    return aabb.get_rect()


class GCodeEmulator:
    def __init__(self):
        self.pen_position = np.array([0.0, 0.0])
        self.pen_distance = 0.0
        self.pen_down_distance = 0.0
        self.time = 0.0
        self.pen_down = False

    def handle_command(self, command):
        op = parse_gcode(command, self.pen_position)
        pen_mode = op.get_pen_mode_update()
        if pen_mode is not None:
            self.pen_down = pen_mode == PenMode.PEN_DOWN
        self.time += op.get_duration()
        pen_distance = op.get_pen_distance()
        self.pen_distance += pen_distance
        if self.pen_down:
            self.pen_down_distance += pen_distance
        self.pen_position = op.get_end_position()

    def run(self, gcodes):
        for command in gcodes:
            self.handle_command(command)
        efficiency = self.pen_down_distance / self.pen_distance
        return self.time, efficiency
