import itertools
import sublime
import sublime_plugin

LEFT, UP, RIGHT, DOWN = list(range(4))
X1, Y1, X2, Y2 = list(range(4))
COLS = "cols"
ROWS = "rows"
CELLS = "cells"
OPPOSITE = {
    UP: DOWN,
    RIGHT: LEFT,
    DOWN: UP,
    LEFT: RIGHT
}


def get_indices(dimension):
    return (X1, X2) if is_cols(dimension) else (Y1, Y2)


def is_cols(dimension):
    return dimension == "width"


def is_rows(dimension):
    return dimension == "height"


def get_points(cols, rows, dimension):
    return cols if is_cols(dimension) else rows


def get_sign(point, points):
    return 1 if (point <= (len(points) / 2) - 1) else -1


def get_point_index(cell, points, dimension, sign):
    point1, point2 = get_indices(dimension)
    point_index, other_index = (
        cell[point2], cell[point1]) if sign > 0 else (cell[point1], cell[point2])
    if (cell[point1] == 0) and cell[point2] == (len(points) - 1):
        # cell takes up entire row/column so there is no point index
        return -1, 0
    elif (point_index == 0) or point_index == (len(points) - 1):
        # edge case, take opposite point to avoid overflowing
        point_index = other_index
        sign = get_sign(point_index, points) * -1
    return point_index, sign


def get_adjacent_direction(dimension, sign):
    if is_cols(dimension):
        direction1 = RIGHT
        direction2 = LEFT
    else:
        direction1 = DOWN
        direction2 = UP
    return direction1 if sign > 0 else direction2


def get_similar_signs(dimension):
    return [UP, DOWN] if is_cols(dimension) else [LEFT, RIGHT]


def get_adjacent_cells(point_index, cells, signs):
    cooridinate_map = {
        LEFT: (X1, X2),
        UP: (Y1, Y2),
        RIGHT: (X2, X1),
        DOWN: (Y2, Y1)
    }
    adjacent_cells = []
    for cell in cells:
        for sign in signs:
            _, point = cooridinate_map[sign]
            if point_index == cell[point]:
                adjacent_cells.append(cell)
    return adjacent_cells


def get_point_min_max(cell, cells, point_index, dimension, sign):
    point1, point2 = get_indices(dimension)
    direction = get_adjacent_direction(dimension, sign)
    if sign > 0:
        max_adj_cells = get_adjacent_cells(
            point_index, cells, [direction])
        if max_adj_cells:
            point_max = min([c[point2] for c in max_adj_cells])
        else:
            point_max = cell[point2]

        opposite_sign = OPPOSITE[direction]
        min_adj_cells = get_adjacent_cells(
            cell[point2], cells, [opposite_sign])
        if min_adj_cells:
            point_min = max([c[point1] for c in min_adj_cells])
        else:
            point_min = cell[point1]
    else:
        min_adj_cells = get_adjacent_cells(
            point_index, cells, [direction])
        if min_adj_cells:
            point_min = max([c[point1] for c in min_adj_cells])
        else:
            point_min = cell[point1]

        opposite_sign = OPPOSITE[direction]
        max_adj_cells = get_adjacent_cells(
            cell[point2], cells, [opposite_sign])
        if max_adj_cells:
            point_max = min([c[point1] for c in max_adj_cells])
        else:
            max_adj_cells = get_adjacent_cells(
                cell[point1], cells, [opposite_sign])
            point_max = min([c[point2] for c in max_adj_cells])
    return point_min, point_max


def swap_cell(cell, swap, indices):
    for i in indices:
        if cell[i] == swap[0]:
            cell[i] = swap[1]
        elif cell[i] == swap[1]:
            cell[i] = swap[0]
    return cell


def swap_cells(swap_pos, pos, cells, active_cell, points):
    swaps = []
    for i, position in enumerate(pos):
        if position != swap_pos[i]:
            sorted_index = swap_pos.index(position)
            swaps.append(sorted([i, sorted_index]))
    swaps = list(swaps for swaps, _ in itertools.groupby(swaps))
    for i, cell in enumerate(cells):
        for swap in swaps:
            swap_active_cell = (active_cell == cell)
            cell = swap_cell(cell, swap, points)
            if swap_active_cell:
                active_cell = cell
    return cells, active_cell


def sort_layout(cols, rows, cells, active_group):
    active_cell = cells[active_group]
    sorted_cols = sorted(cols)
    cells, active_cell = swap_cells(
        sorted_cols, cols, cells, active_cell, [X1, X2])
    sorted_rows = sorted(rows)
    cells, active_cell = swap_cells(
        sorted_rows, rows, cells, active_cell, [Y1, Y2])
    sorted_cells = sorted(cells)
    sorted_active_group = sorted_cells.index(active_cell)
    return sorted_cols, sorted_rows, sorted_cells, sorted_active_group


class PanePaneResizeCommand(sublime_plugin.WindowCommand):

    def run(self, dimension, resize):
        settings = sublime.load_settings("panepane.sublime-settings")
        amount = settings.get("resize_amount")
        if resize == "decrease":
            amount *= -1
        self.resize(dimension, amount)

    def resize(self, dimension, amount):
        cols, rows, cells, active_group = self.sort_and_get_layout()
        active_cell = cells[active_group]
        points = get_points(cols, rows, dimension)
        point, _ = get_indices(dimension)
        sign = get_sign(active_cell[point], points)
        point_index, sign = get_point_index(
            active_cell, points, dimension, sign)
        # if point_index is less than zero, cell takes up entire row/column so
        # there is no need to resize
        if point_index < 0:
            return
        amount *= sign
        point_min_index, point_max_index = get_point_min_max(
            active_cell, cells, point_index, dimension, sign)
        point_min = points[point_min_index]
        point_max = points[point_max_index]
        new_point_value = round(float(points[point_index]) + (amount / 100), 2)

        # if point value is greater/less than or equal to max/min then snap to
        # edge of respective pane
        if new_point_value >= point_max:
            new_point_value = point_max - 0.01
        if new_point_value <= point_min:
            new_point_value = point_min + 0.01

        if (new_point_value > point_min and
                new_point_value < point_max and
                new_point_value != point_min and
                new_point_value != point_max):
            points[point_index] = new_point_value
            if is_cols(dimension):
                cols = points
            else:
                rows = points
            cols, rows, sorted_cells, active_group = sort_layout(
                cols, rows, cells, active_group)
            self.swap_views(cells, sorted_cells)
            self.set_layout(cols, rows, sorted_cells, active_group)

    def get_layout(self):
        window = self.window
        layout = window.get_layout()
        cols = layout[COLS]
        rows = layout[ROWS]
        cells = layout[CELLS]
        active_group = window.active_group()
        return cols, rows, cells, active_group

    def set_layout(self, cols, rows, cells, active_group):
        window = self.window
        window.set_layout({COLS: cols, ROWS: rows, CELLS: cells})
        window.focus_group(active_group)
        # todo focus view

    def sort_and_get_layout(self):
        cols, rows, cells, active_group = self.get_layout()
        self.set_layout(*sort_layout(cols, rows, cells, active_group))
        return cols, rows, cells, active_group

    def sort_and_set_layout(self, cols, rows, cells, active_group):
        self.set_layout(*sort_layout(cols, rows, cells, active_group))

    def swap_views(self, cells, sorted_cells):
        window = self.window
        swaps = []
        for i, cell in enumerate(cells):
            if cell != sorted_cells[i]:
                swaps.append({
                    "group": sorted_cells.index(cell),
                    "views": window.views_in_group(i),
                    "active_view": window.active_view_in_group(i)
                })
        for swap in swaps:
            for index, view in enumerate(swap["views"]):
                window.set_view_index(view, swap["group"], index)
            # focus currently edited view in new group
            window.focus_view(swap["active_view"])
