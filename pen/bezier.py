import numpy as np

DEFAULT_DISTANCE_TOLERANCE = 0.5
DEFAULT_RECURSION_LIMIT = 100


class CubicBezier:
    # Code inspired by http://antigrain.com/research/adaptive_bezier/
    def __init__(self, p1, p2, p3, p4, recursion_limit=DEFAULT_RECURSION_LIMIT, distance_tolerance=DEFAULT_DISTANCE_TOLERANCE):
        self.p1 = np.array(p1)
        self.p2 = np.array(p2)
        self.p3 = np.array(p3)
        self.p4 = np.array(p4)
        self.points = None
        self.recursion_limit = recursion_limit
        self.distance_tolerance = distance_tolerance ** 2

    def _recursive_segment(self, p1, p2, p3, p4, level):
        # De Casteljau's algorithm
        if level > self.recursion_limit:
            return

        # Calculate mid points of line segments
        p12 = (p1 + p2) / 2
        p23 = (p2 + p3) / 2
        p34 = (p3 + p4) / 2
        p123 = (p12 + p23) / 2
        p234 = (p23 + p34) / 2
        p1234 = (p123 + p234) / 2

        # Approximate cubic curve by line segment
        dp = p4 - p1
        dx, dy = dp

        d2 = np.abs((p2[0] - p4[0]) * dy - (p2[1] - p4[1]) * dx)
        d3 = np.abs((p3[0] - p4[0]) * dy - (p3[1] - p4[1]) * dx)
        de = d2 + d3

        if de ** 2 < self.distance_tolerance * (dp ** 2).sum():
            point = p1234
            self.points.append(point)
            return

        self._recursive_segment(p1, p12, p123, p1234, level + 1)
        self._recursive_segment(p1234, p234, p34, p4, level + 1)

    def to_points(self):
        if self.points is not None:
            return np.array(self.points)
        self.points = []
        self.points.append(self.p1)
        self._recursive_segment(self.p1, self.p2, self.p3, self.p4, level=0)
        self.points.append(self.p4)
        return np.array(self.points)

    @classmethod
    def from_quadratic(cls, qp1, qp2, qp3, distance_tolerance=DEFAULT_DISTANCE_TOLERANCE):
        cp1 = qp1
        cp4 = qp3
        cp2 = qp1 + 2 / 3.0 * (qp2 - qp1)
        cp3 = qp3 + 2 / 3.0 * (qp2 - qp3)
        return cls(cp1, cp2, cp3, cp4, distance_tolerance=distance_tolerance)
