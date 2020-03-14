import numpy as np

# TODO(emmett):
#  * Dynamic programming TSP
#  * Explore algorithm that picks between reversed line order or forward line order
#  * Remove pen tap (down/up/down) or (up/down/up)


class PenPath:
    def __init__(self, start_pt, end_pt):
        self.start_pt = start_pt
        self.end_pt = end_pt


class PointSearch:
    def __init__(self, draw_paths):
        self.draw_paths = draw_paths
        self.start_points = np.array([path.start_pt for path in self.draw_paths])
        self.end_points = np.array([path.end_pt for path in self.draw_paths])
        self.se_cost_matrix = np.zeros((len(draw_paths), len(draw_paths)))
        self.ss_cost_matrix = np.zeros_like(self.se_cost_matrix)
        self.es_cost_matrix = np.zeros_like(self.se_cost_matrix)
        self.ee_cost_matrix = np.zeros_like(self.se_cost_matrix)

    def build_cost_matrix(self):
        max_value = 1e9

        # Start-End
        for i in range(len(self.draw_paths)):
            source_pt = self.draw_paths[i].start_pt
            self.se_cost_matrix[i, :] = self.compute_distance(self.end_points, source_pt)
            self.se_cost_matrix[i, i] = max_value

        # Start-Start
        for i in range(len(self.draw_paths)):
            source_pt = self.draw_paths[i].start_pt
            self.ss_cost_matrix[i, :] = self.compute_distance(self.start_points, source_pt)
            self.ss_cost_matrix[i, i] = max_value

        # End-Start
        for i in range(len(self.draw_paths)):
            source_pt = self.draw_paths[i].end_pt
            self.es_cost_matrix[i, :] = self.compute_distance(self.start_points, source_pt)
            self.es_cost_matrix[i, i] = max_value

        # End-End
        for i in range(len(self.draw_paths)):
            source_pt = self.draw_paths[i].end_pt
            self.ee_cost_matrix[i, :] = self.compute_distance(self.end_points, source_pt)
            self.ee_cost_matrix[i, i] = max_value

    @staticmethod
    def compute_distance(points, point):
        d = np.sqrt(np.sum((points - point)**2))
        return d

    def find_order(self):
        # Start to start (reverse first)
        # Start to end (reverse first and second)
        # end to start (normal)
        # end to end (reverse second)

        visited = np.zeros(len(self.draw_paths), dtype=np.int)

        max_value = 1e9
        search_matrix = np.array([
            self.se_cost_matrix,
            self.ss_cost_matrix,
            self.es_cost_matrix,
            self.ee_cost_matrix,
        ])

        current_node = 0
        order = []
        reverse = []

        total_cost = 0
        current_reverse = False

        while (visited == 0).any():
            order.append(current_node)
            reverse.append(current_reverse)
            visited[current_node] = 1

            if not (visited == 0).any():
                break

            prior_node = current_node
            prior_reverse = current_reverse

            ordering_index = None
            while True:
                # if reverse path beats normal path, then go the reverse route
                # return reversal code with order
                search_offset = 0
                if not prior_reverse:
                    search_offset = 2
                search_indices = []
                search_values = []
                # NOTE(emmett): hardcoded from ordering of searches
                search_reverse = [False, True]
                for i in range(2):
                    index = search_matrix[prior_node, :, search_offset + i].argmin()
                    search_indices.append(())
                    search_values.append((
                        index,
                        search_offset + i,
                        search_reverse[i],
                        search_matrix[prior_node, index, search_offset + i],
                    ))

                # Search from lowest to highest cost. If something found abort this loop. Otherwise keep going.
                # NOTE(emmett): this is not optimal, because it could be the next item *not* reversed could be closer
                # than the current closest reversed item.
                # Ugh, maybe should just go ahead and make this a DP
                found_visited = False
                for (index, offset, reverse, value) in sorted(search_values, key=lambda t: t[3]):
                    current_node = index
                    ordering_index = offset
                    current_reverse = reverse
                    if not visited[current_node]:
                        found_visited = True
                        break

                if found_visited:
                    break

            # No one else can go to current node
            total_cost += search_matrix[prior_node, current_node, ordering_index]
            search_matrix[:, current_node, :] = max_value

        return order, reverse


def greedy_tsp(draw_paths):
    # TODO(emmett): refactor to allow reversal
    # TODO(emmett): coarsen to allow ~O(n^3) floyd-whatever shortest path traversal
    cost_matrix = np.zeros((len(draw_paths), len(draw_paths)))

    # O(n^2)
    for i in range(len(draw_paths)):
        xN, yN = draw_paths[i].end_pt

        for j in range(len(draw_paths)):
            if i == j:
                continue
            draw_path = draw_paths[j]
            x0, y0 = draw_path.start_pt

            dx = x0 - xN
            dy = y0 - yN

            distance = np.sqrt(dx * dx + dy * dy)
            cost_matrix[i, j] = distance

    min_i = 0
    min_distance = cost_matrix.max()

    for i in range(len(draw_paths)):
        x0, y0 = draw_paths[i].start_pt
        distance_to_origin = np.sqrt(x0 ** 2 + y0 ** 2)
        if distance_to_origin <= min_distance:
            min_i = i
            min_distance = distance_to_origin

    visited = np.zeros(cost_matrix.shape[0], dtype=np.int)

    max_value = 1e9
    search_matrix = cost_matrix + np.eye(cost_matrix.shape[0]) * max_value

    current_node = min_i
    order = []

    total_cost = 0

    while (visited == 0).any():
        order.append(current_node)
        visited[current_node] = 1

        if not (visited == 0).any():
            break

        prior_node = current_node
        while True:
            # TODO(emmett): have reversal_search_matrix
            # if reverse path beats normal path, then go the reverse route
            # return reversal code with order
            current_node = search_matrix[prior_node, :].argmin()
            if visited[current_node] == 0:
                break
            search_matrix[prior_node, current_node] = max_value

        # No one else can go to current node
        total_cost += search_matrix[prior_node, current_node]
        search_matrix[:, current_node] = max_value

    return order


def remove_repeated_ops(gcode_ops):
    output_ops = []
    last_op = None
    for op in gcode_ops:
        if op == last_op:
            continue
        last_op = op
        output_ops.append(op)
    return output_ops
