from xml.dom import minidom
import re
import numpy as np

from .bezier import CubicBezier

# TODO(emmett):
#  * SVG gets generated from GCode (or viz code)
#
#  * PenViz is the ground truth
#    * core: path, arc
#    * higher level:
#       * helpers: path, circle, rect, triangle, bezier?
#       * path intersect
#       * path union
#       * path subtract
#
#  * Pen(thickness_mm, type={pencil, ballpoint, felttip}, color, mass=)
#     * Mostly used for emulating properties in SVG
#

class SVGNode:
    def __init__(self, name, attributes, tags=None):
        self.name = name
        self.attributes = attributes
        if tags is None:
            tags = set([])
        self.tags = set(tags)

    def has_tag(self, tag):
        return tag in self.tags

    def to_svg(self):
        attributes = ' '.join([key + '="' + '{}'.format(value) + '"' for key, value in self.attributes.items()])
        return '<' + self.name + ' ' + attributes + '/>'


class VectorViz:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.svg_tree = []
        self.lines = []
        self.arcs = []

    def arc(self):
        pass

    def line(self, xs, ys, stroke='black', fill=None, stroke_width=3, tags=None):
        if fill is None:
            fill = 'none'
        path_components = []
        self.lines.append((xs, ys))
        for x, y in zip(xs, ys):
            path_components.append('{},{}'.format(x, y))
        path_d = 'M' + 'L'.join(path_components)
        self.svg_tree.append(SVGNode(
            'path',
            {
                'd': path_d,
                'stroke': stroke,
                'stroke-width': stroke_width,
                'fill': fill,
            },
            tags=tags,
        ))

    def to_svg(self):
        svg = '\n'.join([node.to_svg() for node in self.svg_tree])
        svg = f'<svg width="{self.width}" height="{self.height}">' + svg + '</svg>'
        return svg

    def plot(self):
        from IPython.core.display import display, HTML
        display(HTML(self.to_svg()))

# === New Hotness === #


class CubicBezierLineCommand:
    def __init__(self, dp2, dp3, p4):
        # These are relative coordinates:
        self.dp2 = dp2
        self.dp3 = dp3
        self.p4 = p4


class QuadraticBezierLineCommand:
    def __init__(self, dp2, p3):
        # These are relative coordinates:
        self.dp2 = dp2
        self.p3 = p3


class LineCommand:
    def __init__(self, points, absolute=False):
        self.points = points
        self.absolute = absolute


class MoveCommand:
    def __init__(self, point, absolute=False):
        self.point = point
        self.absolute = absolute


class ClosePathCommand:
    pass


class VLineCommand:
    def __init__(self, v, absolute=False):
        self.v = v
        self.absolute = absolute


class HLineCommand:
    def __init__(self, h, absolute=False):
        self.h = h
        self.absolute = absolute


class SVGPathDataParser:
    def __init__(self):
        self.commands = []
        self.tokens = []

    def peek_token(self):
        if len(self.tokens) == 0:
            return None
        return self.tokens[0].strip()

    def pop_token(self):
        if len(self.tokens) == 0:
            return None
        token = self.tokens.pop(0)
        return token.strip()

    def parse_scalar(self):
        return float(self.pop_token())

    def parse_point(self):
        x = self.parse_scalar()
        y = self.parse_scalar()
        return x, y

    def parse_points(self):
        points = []

        while True:
            token = self.peek_token()
            if token is None:
                break
            if token.isalpha():
                break
            point = self.parse_point()
            points.append(point)

        return points

    def parse_bicubic_point(self):
        return self.parse_point(), self.parse_point(), self.parse_point()

    def parse_quadratic_point(self):
        return self.parse_point(), self.parse_point()

    def parse_commands(self, data):
        self.commands = []
        STATE_START = 0
        STATE_MOVE = 1
        STATE_LINE = 2
        STATE_CUBIC_BEZIER = 3
        STATE_QUADRATIC_BEZIER = 4
        STATE_ARC = 5
        STATE_CLOSE = 6
        STATE_PARSE_POINT = 7
        STATE_HLINE = 8
        STATE_VLINE = 9
        STATE_DRAW = 10

        self.tokens = re.split('[ ,]', data)
        state = STATE_START

        is_absolute = False

        while True:
            if len(self.tokens) == 0:
                break
            if state == STATE_START:
                token = self.pop_token()
                if token.lower() == 'm':
                    is_absolute = token.isupper()
                    command = MoveCommand(self.parse_point(), absolute=is_absolute)
                    self.commands.append(command)
                    state = STATE_MOVE
                else:
                    raise RuntimeError('Unknown start token: {} "{}"'.format(token, data))
            elif state == STATE_DRAW:
                token = self.peek_token()
                if token.lower() == 'm':
                    state = STATE_START
                    continue
                token = self.pop_token()
                if token.lower() == 'l':
                    is_absolute = token.isupper()
                    command = LineCommand(self.parse_points(), absolute=is_absolute)
                    self.commands.append(command)
                    state = STATE_LINE
                elif token == 'c':
                    dp2, dp3, p4 = self.parse_bicubic_point()
                    command = CubicBezierLineCommand(dp2, dp3, p4)
                    self.commands.append(command)
                    state = STATE_CUBIC_BEZIER
                elif token == 'q':
                    dp2, p3 = self.parse_quadratic_point()
                    command = QuadraticBezierLineCommand(dp2, p3)
                    self.commands.append(command)
                    state = STATE_QUADRATIC_BEZIER
                elif token == 'z':
                    self.commands.append(ClosePathCommand())
                elif token.lower() == 'v':
                    v = self.parse_scalar()
                    is_absolute = token.isupper()
                    command = VLineCommand(v, absolute=is_absolute)
                    self.commands.append(command)
                    state = STATE_VLINE
                elif token.lower() == 'h':
                    v = self.parse_scalar()
                    is_absolute = token.isupper()
                    command = HLineCommand(v, absolute=is_absolute)
                    self.commands.append(command)
                    state = STATE_HLINE
                elif token == '':
                    continue
                else:
                    raise RuntimeError('Unsupported token: {} "{}" {}'.format(token, data, self.commands[-1]))
            elif state == STATE_MOVE:
                token = self.peek_token()
                if token.isalpha():
                    state = STATE_DRAW
                    continue
                else:
                    # Implicit transition to line
                    command = LineCommand(self.parse_points(), absolute=is_absolute)
                    self.commands.append(command)
                    state = STATE_LINE
            elif state == STATE_CUBIC_BEZIER:
                token = self.peek_token()
                if token.isalpha():
                    state = STATE_DRAW
                    continue
                else:
                    dp2, dp3, p4 = self.parse_bicubic_point()
                    command = CubicBezierLineCommand(dp2, dp3, p4)
                    self.commands.append(command)
            elif state == STATE_QUADRATIC_BEZIER:
                token = self.peek_token()
                if token.isalpha():
                    state = STATE_DRAW
                    continue
                else:
                    dp2, p3 = self.parse_quadratic_point()
                    command = QuadraticBezierLineCommand(dp2, p3)
                    self.commands.append(command)
            elif state == STATE_CUBIC_BEZIER:
                token = self.peek_token()
                if token.isalpha():
                    state = STATE_DRAW
                    continue
                else:
                    dp2, dp3, p4 = self.parse_bicubic_point()
                    command = CubicBezierLineCommand(dp2, dp3, p4)
                    self.commands.append(command)
            elif state == STATE_VLINE:
                token = self.peek_token()
                if token.isalpha():
                    state = STATE_DRAW
                    continue
                else:
                    v = self.parse_scalar()
                    command = VLineCommand(v, absolute=is_absolute)
                    self.commands.append(command)
            elif state == STATE_HLINE:
                token = self.peek_token()
                if token.isalpha():
                    state = STATE_DRAW
                    continue
                else:
                    v = self.parse_scalar()
                    command = HLineCommand(v, absolute=is_absolute)
                    self.commands.append(command)
            elif state == STATE_LINE:
                state = STATE_DRAW
            else:
                raise RuntimeError('Unsupported state: {}'.format(state))

        return self.commands

    def data_to_segments(self, data, bezier_distance_tolerance=0.5):
        commands = self.parse_commands(data)
        position = np.array([0, 0])
        segments = []
        points = []
        for command in commands:
            if type(command) == MoveCommand:
                if len(points) != 0:
                    segments.append(np.array(points))
                    points = []
                if command.absolute:
                    position = np.array(command.point)
                else:
                    position = np.array(command.point) + position
                points.append(position)
            elif type(command) == CubicBezierLineCommand:
                p1 = np.array(position)
                p2 = p1 + command.dp2
                p3 = p1 + command.dp3
                p4 = command.p4 + p1
                cubic_bezier = CubicBezier(p1, p2, p3, p4, distance_tolerance=bezier_distance_tolerance)
                for point in cubic_bezier.to_points():
                    points.append(point)
                position = p4
            elif type(command) == QuadraticBezierLineCommand:
                qp1 = np.array(position)
                qp2 = qp1 + command.dp2
                qp3 = qp1 + command.p3
                cubic_bezier = CubicBezier.from_quadratic(qp1, qp2, qp3)
                for point in cubic_bezier.to_points():
                    points.append(point)
                position = qp3
            elif type(command) == LineCommand:
                if command.absolute:
                    for point in command.points:
                        pabs = point
                        points.append(pabs)
                        position = pabs
                else:
                    for point in command.points:
                        pabs = point + np.array(position)
                        points.append(pabs)
                        position = pabs
            elif type(command) == VLineCommand:
                if command.v == 0:
                    continue
                if command.absolute:
                    pabs = np.copy(position)
                    pabs[1] = command.v
                else:
                    vector = np.array([0, 1]) * command.v
                    pabs = position + vector
                points.append(pabs)
                position = pabs
            elif type(command) == HLineCommand:
                if command.h == 0:
                    continue
                if command.absolute:
                    pabs = np.copy(position)
                    pabs[0] = command.h
                else:
                    vector = np.array([1, 0]) * command.h
                    pabs = position + vector
                points.append(pabs)
                position = pabs
            elif type(command) == ClosePathCommand:
                points.append(points[0])
                position = points[-1]
            else:
                raise RuntimeError('Unknown type: {}'.format(type(command)))
        if len(points) != 0:
            segments.append(np.array(points))
        return segments


class SVGEllipse:
    def __init__(self, cx, cy, rx, ry, style=None):
        self.cx = cx
        self.cy = cy
        self.rx = rx
        self.ry = ry
        self.style = style


class SVGRect:
    def __init__(self, x, y, width, height, style=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.style = style


class SVGPath:
    def __init__(self, data, style=None):
        self.data = data
        self.style = style

    def to_segments(self, bezier_distance_tolerance=0.5):
        # A path can annoyingly contain more than one segment.
        parser = SVGPathDataParser()
        segments = parser.data_to_segments(self.data, bezier_distance_tolerance=bezier_distance_tolerance)
        return segments


class SVGParser:
    def __init__(self):
        pass

    def handle_ellipse(self, ellipse):
        pass

    def handle_rect(self, rect):
        pass

    def handle_path(self, path):
        pass

    def parse(self, path):
        doc = minidom.parse(path)
        svg, = doc.getElementsByTagName('svg')

        for element in svg.getElementsByTagName('rect'):
            self.handle_rect(self.element_to_rect(element))

        for element in svg.getElementsByTagName('ellipse'):
            self.handle_ellipse(self.element_to_ellipse(element))

        for element in svg.getElementsByTagName('path'):
            self.handle_path(self.element_to_path(element))

    def element_to_rect(self, element):
        attrs = element.attributes
        return SVGRect(
            x=attrs['x'].value,
            y=attrs['y'].value,
            width=attrs['width'].value,
            height=attrs['height'].value,
            style=attrs['style'].value,
        )

    def element_to_ellipse(self, element):
        attrs = element.attributes
        return SVGEllipse(
            cx=attrs['cx'].value,
            cy=attrs['cy'].value,
            rx=attrs['rx'].value,
            ry=attrs['ry'].value,
            style=attrs['style'].value,
        )

    def element_to_path(self, element):
        attrs = element.attributes
        style = None
        if 'style' in attrs:
            style = attrs['style'].value
        return SVGPath(
            data=attrs['d'].value,
            style=style,
        )
