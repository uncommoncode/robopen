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