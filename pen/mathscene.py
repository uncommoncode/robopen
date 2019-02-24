import numpy as np

DISTANCE_EPSILON = 1e-6


def polar_to_euclidian(theta, r):
    return r * np.array([np.cos(theta), np.sin(theta)])


def euclidian_distance(p0, p1):
    p0 = np.array(p0)
    p1 = np.array(p1)
    return np.sqrt(((p0 - p1)**2).sum())


class RadianRange:
    def __init__(self, start_theta, end_theta):
        self.start_theta = start_theta
        self.end_theta = end_theta

        while self.start_theta < 0.0:
            self.start_theta += 2.0 * np.pi

        while self.end_theta < self.start_theta:
            self.end_theta += 2.0 * np.pi

        if np.abs(self.start_theta - self.end_theta) < DISTANCE_EPSILON:
            self.end_theta += 2.0 * np.pi

        if self.end_theta < self.start_theta:
            raise RuntimeError('Invalid thetas! {} {}'.format(self.end_theta, self.start_theta))

    def contains(self, theta):
        while theta < self.start_theta:
            theta += 2.0 * np.pi
        if theta < 0:
            raise RuntimeError('Nope!')
        if theta < self.start_theta:
            return False
        if theta > self.end_theta:
            return False
        return True

    def get_width(self):
        return self.end_theta - self.start_theta


class Rectangle:
    def __init__(self, x0, x1, y0, y1):
        self.x0 = min(x0, x1)
        self.x1 = max(x1, x0)
        self.y0 = min(y0, y1)
        self.y1 = max(y1, y0)

    def get_width(self):
        return self.x1 - self.x0

    def get_height(self):
        return self.y1 - self.y0

    def to_xxyy(self):
        return [self.x0, self.x1, self.y0, self.y1]

    def contains_point(self, point):
        if point[0] < self.x0:
            return False
        if point[0] > self.x1:
            return False
        if point[1] < self.y0:
            return False
        if point[1] > self.y1:
            return False
        return True

    def contains_rect(self, rect):
        if rect.x0 < self.x0:
            return False
        if rect.x1 > self.x1:
            return False
        if rect.y0 < self.y0:
            return False
        if rect.y1 > self.y1:
            return False
        return True

    def get_aabb(self):
        return AABB([[self.x0, self.y0], [self.x1, self.y1]])

    def get_line_distance(self):
        return 2 * self.get_width() + 2 * self.get_height()

    @classmethod
    def from_xxyy(cls, xxyy):
        return cls(xxyy[0], xxyy[1], xxyy[2], xxyy[3])

    @classmethod
    def from_xywh(cls, x, y, width, height):
        return cls(x, x + width, y, y + height)


class Path:
    def __init__(self, points):
        self.points = points

    def get_aabb(self):
        return AABB(self.points)

    def get_line_distance(self):
        distance = 0
        for p0, p1 in zip(self.points, self.points[1:]):
            distance += euclidian_distance(p0, p1)
        return distance


class Arc:
    def __init__(self, start_position, end_position, relative_center):
        self.start_position = start_position
        self.end_position = end_position
        relative_center = np.array(relative_center)
        self.center_position = relative_center + self.start_position

        self.radius = euclidian_distance(start_position, self.center_position)
        start_vec = start_position - self.center_position
        end_vec = end_position - self.center_position
        start_theta = np.arctan2(start_vec[1], start_vec[0])
        end_theta = np.arctan2(end_vec[1], end_vec[0])
        self.radian_range = RadianRange(start_theta, end_theta)

    def get_aabb(self):
        aabb = AABB([self.start_position, self.end_position])
        # Grow AABB to include any extrema we pass thru.
        vecs = [
            [0, 1],
            [1, 0],
            [0, -1],
            [-1, 0],
        ]
        for vec in vecs:
            point = self.radius * np.array(vec) + self.center_position
            if self.point_intersects(point):
                aabb.add_point(point)
        return aabb

    def point_intersects(self, point):
        radius = euclidian_distance(point, self.center_position)
        if np.abs(radius - self.radius) > DISTANCE_EPSILON:
            return False
        vec = point - self.center_position
        theta = np.arctan2(vec[1], vec[0])
        return self.radian_range.contains(theta)

    def get_line_distance(self):
        c = 2.0 * np.pi * self.radius
        t = self.radian_range.get_width() / (2.0 * np.pi)
        return c * t

    @classmethod
    def from_polar(cls, center, radius, start_theta, end_theta):
        center_pt = np.array(center)
        start_pt = center + polar_to_euclidian(start_theta, radius)
        end_pt = center_pt + polar_to_euclidian(end_theta, radius)
        return cls.from_absolute_points(start_pt, end_pt, center_pt)

    @classmethod
    def from_relative_points(cls, start, end, relative_center):
        return cls(start, end, relative_center)

    @classmethod
    def from_absolute_points(cls, start, end, absolute_center):
        relative_center = np.array(absolute_center) - np.array(start)
        return cls.from_relative_points(start, end, relative_center)


class AABB:
    def __init__(self, points=None):
        self.x0 = None
        self.x1 = None
        self.y0 = None
        self.y1 = None
        if points is None:
            points = []
        for point in points:
            self.add_point(point)

    def add_point(self, point):
        if self.x0 is None:
            self.x0 = point[0]
            self.x1 = point[0]
            self.y0 = point[1]
            self.y1 = point[1]
            return
        self.x0 = min(self.x0, point[0])
        self.x1 = max(self.x1, point[0])
        self.y0 = min(self.y0, point[1])
        self.y1 = max(self.y1, point[1])

    def merge_aabb(self, aabb):
        self.add_point([aabb.x0, aabb.y0])
        self.add_point([aabb.x1, aabb.y1])

    def get_rect(self):
        return Rectangle(self.x0, self.x1, self.y0, self.y1)

