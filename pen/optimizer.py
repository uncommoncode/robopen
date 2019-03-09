import numpy as np

# TODO(emmett):
#  * Dynamic programming TSP
#  * Explore algorithm that picks between reversed line order or forward line order
#  * Remove pen tap (down/up/down) or (up/down/up)


class PenPath:
    def __init__(self, start_pt, end_pt):
        self.start_pt = start_pt
        self.end_pt = end_pt


def greedy_tsp(draw_paths):
    # TODO(emmett): refactor to allow reversal
    cost_matrix = np.zeros((len(draw_paths), len(draw_paths)))

    for i in range(len(draw_paths)):
        xN, yN = draw_paths[i].end_pt

        for j in range(len(draw_paths)):
            if i == j:
                continue
            x0, y0 = draw_paths[j].start_pt

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
