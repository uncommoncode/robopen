import enum

import numpy as np

from .mathscene import Path
from .mathscene import Arc
from .svg import SVGNode
from .gcode import GCode
from .mathscene import AABB
from .mathscene import euclidian_distance
from .eleksdraw import DRAW_WIDTH_EU
from .eleksdraw import DRAW_HEIGHT_EU

# TODO(emmett):
#  * to_svg occurs elsewhere on gcode
#  * pen_viz -> primitives -> gcode
#  * gcode -> svg (optional)
#  * plot gcode -> svg -> html


class OriginMode(enum.Enum):
    LOWER_RIGHT = 0  # (portrait mode)
    UPPER_RIGHT = 1  # (landscape mode)


class Pen:
    def __init__(
            self,
            stroke_width_mm=0.3,
            color='black',
            draw_feed_rate=1000,
            move_feed_rate=2000,
            servo_down=60,
            origin_mode=OriginMode.LOWER_RIGHT,
            draw_width=DRAW_WIDTH_EU,
            draw_height=DRAW_HEIGHT_EU,
    ):
        self.draw_feed_rate = draw_feed_rate
        self.move_feed_rate = move_feed_rate
        self.servo_down = servo_down
        self.stroke_width_mm = stroke_width_mm
        self.color = color
        self.origin_mode = origin_mode
        self.draw_width = draw_width
        self.draw_height = draw_height

    def get_svg_stroke(self):
        return self.color

    def get_svg_stroke_width(self):
        # Output in mm
        return '{}'.format(self.stroke_width_mm)

    def translate_point_device(self, point):
        # Origin is lower right with Eleksdraw in portrait mode
        #
        #       ^ +y
        #       |
        #  +x <--
        #
        #  In this case, we need to reflect the x axis.
        if self.origin_mode == OriginMode.LOWER_RIGHT:
            tx = np.array(point)
            tx[0] = self.draw_width - tx[0]
            return tx
        raise NotImplemented('Unsupported mode: {}'.format(self.origin_mode))

    def translate_point_svg(self, point):
        # SVG has the origin at the top left, we need to get to positive is up with y components.
        if self.origin_mode == OriginMode.LOWER_RIGHT:
            tx = np.array(point)
            tx[1] = self.draw_height - tx[1]
            return tx
        raise NotImplemented('Unsupported mode: {}'.format(self.origin_mode))


class Drawable:
    def to_gcode(self, pen):
        raise NotImplemented()

    def to_svg_node(self, pen):
        raise NotImplemented()

    def get_aabb(self):
        raise NotImplemented()


class DrawPath(Drawable):
    def __init__(self, points):
        self.path = Path(points)

    def get_aabb(self):
        return self.path.get_aabb()

    def to_svg_node(self, pen):
        path_components = []
        for point in self.path.points:
            x, y = pen.translate_point_svg(point)
            path_components.append('{},{}'.format(x, y))
        path_d = 'M' + 'L'.join(path_components)
        return SVGNode(
            'path',
            {
                'd': path_d,
                'stroke': pen.get_svg_stroke(),
                'stroke-width': pen.get_svg_stroke_width(),
                'fill': 'none',
            },
        )

    def to_gcode(self, pen):
        move_linears = []

        # Skip first point because we have already moved fast there.
        for point in self.path.points[1:]:
            move_linears.append(GCode.move_linear(
                end_pt=pen.translate_point_device(point),
                feed_rate=pen.draw_feed_rate,
            ))

        return [
            GCode.pen_up(),
            GCode.move_fast(pen.translate_point_device(self.path.points[0])),
            GCode.pen_down(pen.servo_down),
            ] + move_linears + [
            GCode.pen_up(),
        ]


class DrawArc(Drawable):
    def __init__(self, start_pt, end_pt, center_pt):
        self.arc = Arc.from_absolute_points(start_pt, end_pt, center_pt)

    def get_aabb(self):
        return self.arc.get_aabb()

    def to_svg_node(self, pen):
        # SVG doesnt like closed arcs (circles) because they are ambiguous.
        # Detect circles and draw them instead.
        if euclidian_distance(self.arc.start_position, self.arc.end_position) < 1e-7:
            cx, cy = pen.translate_point_svg(self.arc.center_position)
            radius = self.arc.radius
            return SVGNode(
                'circle',
                {
                    'cx': cx,
                    'cy': cy,
                    'r': radius,
                    'stroke': pen.get_svg_stroke(),
                    'stroke-width': pen.get_svg_stroke_width(),
                    'fill': 'none',
                }
            )

        sx, sy = pen.translate_point_svg(self.arc.start_position)
        ex, ey = pen.translate_point_svg(self.arc.end_position)

        if pen.origin_mode == OriginMode.LOWER_RIGHT:
            flip_y = 0
        else:
            raise RuntimeError('Unknown mode: {}'.format(pen.origin_mode))

        path_d = 'M{sx} {sy} A {radius} {radius} 0 {flip_y} 1 {ex} {ey}'.format(
            sx=sx,
            sy=sy,
            radius=self.arc.radius,
            flip_y=flip_y,
            ex=ex,
            ey=ey,
        )
        return SVGNode(
            'path',
            {
                'd': path_d,
                'stroke': pen.get_svg_stroke(),
                'stroke-width': pen.get_svg_stroke_width(),
                'fill': 'none',
            },
        )

    def to_gcode(self, pen):
        return [
            GCode.pen_up(),
            GCode.move_fast(pen.translate_point_device(self.arc.start_position)),
            GCode.pen_down(pen.servo_down),
            GCode.move_arc(
                start_pt=pen.translate_point_device(self.arc.start_position),
                end_pt=pen.translate_point_device(self.arc.end_position),
                center_pt=pen.translate_point_device(self.arc.center_position),
                feed_rate=pen.draw_feed_rate,
            ),
            GCode.pen_up(),
        ]


class PenViz:
    def __init__(self):
        self.drawables = []

    def draw_path(self, points):
        self.drawables.append(DrawPath(points))

    def draw_arc(self, start_pt, end_pt, center_pt):
        self.drawables.append(DrawArc(start_pt, end_pt, center_pt))

    def draw_circle(self, center_pt, radius):
        point = center_pt + np.array([0, radius])
        self.draw_arc(point, point, center_pt)

    def to_gcode(self, pen):
        commands = []
        for drawable in self.drawables:
            commands += drawable.to_gcode(pen)
        return commands

    def get_aabb(self):
        aabb = AABB()
        for drawable in self.drawables:
            aabb.merge_aabb(drawable.get_aabb())
        return aabb

    def to_svg(self, pen):
        width = pen.draw_width
        height = pen.draw_height
        svg = '\n'.join([drawable.to_svg_node(pen).to_svg() for drawable in self.drawables])
        svg = f'<svg width="{width}mm" height="{height}mm" version="1.1" viewBox="0 0 {width} {height}">' + svg + '</svg>'
        return svg

    def plot(self, pen):
        from IPython.core.display import display, HTML
        display(HTML(self.to_svg(pen)))

    def save_gcode(self, out_path, pen):
        with open(out_path, 'w') as w:
            w.write(self.to_gcode(pen))
