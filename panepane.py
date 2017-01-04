import sublime, sublime_plugin
import itertools

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

def get_direction(point, points):
	return 1 if (point <= (len(points) / 2) - 1) else -1

def get_point_index(cell, points, dimension, direction):
	p1, p2 = get_indices(dimension)
	point_index, other_index = (cell[p2], cell[p1]) if direction > 0 else (cell[p1], cell[p2])
	if (cell[p1] == 0) and cell[p2] == (len(points) - 1):
		# cell takes up entire row/column so there is no point index
		return -1, 0
	elif (point_index == 0) or point_index == (len(points) - 1):
		# edge case, take opposite point to avoid overflowing
		point_index = other_index
		direction = get_direction(point_index, points) * -1
	return point_index, direction

def get_adjacent_direction(dimension, direction):
	if is_cols(dimension):
		d1 = RIGHT
		d2 = LEFT
	else:
		d1 = DOWN
		d2 = UP
	return d1 if direction > 0 else d2

def get_similar_directions(dimension):
	return [UP, DOWN] if is_cols(dimension) else [LEFT, RIGHT]

def get_adjacent_cells(point_index, cells, directions):
	cooridinate_map = {
		LEFT: (X1, X2),
		UP: (Y1, Y2),
		RIGHT: (X2, X1),
		DOWN: (Y2, Y1)
	}
	adjacent_cells = []
	for c in cells:
		for direction in directions:
			p1, p2 = cooridinate_map[direction]
			if (point_index == c[p2]):
				adjacent_cells.append(c)
	return adjacent_cells

def get_point_min_max(cell, cells, point_index, dimension, direction): 
	p1, p2 = get_indices(dimension)
	adjacent_direction = get_adjacent_direction(dimension, direction)
	if direction > 0:
		max_adj_cells = get_adjacent_cells(point_index, cells, [adjacent_direction])
		if max_adj_cells:
			point_max = min(list(map(lambda c: c[p2], max_adj_cells)))
		else:
			point_max = cell[p2]

		opposite_direction = OPPOSITE[adjacent_direction]
		min_adj_cells = get_adjacent_cells(cell[p2], cells, [opposite_direction])
		if min_adj_cells:
			point_min = max(list(map(lambda c: c[p1], min_adj_cells)))
		else:
			point_min = cell[p1]
	else:
		min_adj_cells = get_adjacent_cells(point_index, cells, [adjacent_direction])
		if min_adj_cells:
			point_min = max(list(map(lambda c: c[p1], min_adj_cells)))
		else:
			point_min = cell[p1]

		opposite_direction = OPPOSITE[adjacent_direction]
		max_adj_cells = get_adjacent_cells(cell[p2], cells, [opposite_direction])
		if max_adj_cells:
			point_max = min(list(map(lambda c: c[p1], max_adj_cells)))
		else:
			max_adj_cells = get_adjacent_cells(cell[p1], cells, [opposite_direction])
			point_max = min(list(map(lambda c: c[p2], max_adj_cells)))
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
	for i in range(len(pos)):
		if pos[i] != swap_pos[i]:
			sorted_index = swap_pos.index(pos[i])
			swaps.append(sorted([i, sorted_index]))
	swaps = list(swaps for swaps,_ in itertools.groupby(swaps))
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
	cells, active_cell = swap_cells(sorted_cols, cols, cells, active_cell, [X1, X2])
	sorted_rows = sorted(rows)
	cells, active_cell = swap_cells(sorted_rows, rows, cells, active_cell, [Y1, Y2])
	sorted_cells = sorted(cells)
	sorted_active_group = sorted_cells.index(active_cell)
	return sorted_cols, sorted_rows, sorted_cells, sorted_active_group


class PanePaneResizeCommand(sublime_plugin.WindowCommand):

	def run(self, dimension, resize):
		settings = sublime.load_settings("panepane.sublime-settings")
		amount = settings.get("resize_amount")
		if (resize == "decrease"):
			amount *= -1 
		self.resize(dimension, amount)

	def resize(self, dimension, amount):
		window = self.window
		cols, rows, cells, active_group = self.sort_and_get_layout()
		active_cell = cells[active_group]
		points = get_points(cols, rows, dimension)
		p1, p2 = get_indices(dimension)
		direction = get_direction(active_cell[p1], points)
		point_index, direction = get_point_index(active_cell, points, dimension, direction)
		# if point_index is less than zero, cell takes up entire row/column so there is no need to resize
		if (point_index < 0):
			return
		amount *= direction
		point_min_index, point_max_index = get_point_min_max(active_cell, cells, point_index, dimension, direction)
		point_min = points[point_min_index]
		point_max = points[point_max_index]
		new_point_value = round(float(points[point_index]) + (amount / 100), 2) 

		if (new_point_value > point_min and
			new_point_value < point_max and
			new_point_value != point_min and
			new_point_value != point_max):
			points[point_index] = new_point_value
			if (is_cols(dimension)):
				cols = points
			else:
				rows = points
			cols, rows, sorted_cells, active_group = sort_layout(cols, rows, cells, active_group)
			active_cell = sorted_cells[active_group]
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
		window.set_layout({ COLS: cols, ROWS: rows, CELLS: cells })
		window.focus_group(active_group)

	def sort_and_get_layout(self):
		cols, rows, cells, active_group = self.get_layout()
		self.set_layout(*sort_layout(cols, rows, cells, active_group))
		return cols, rows, cells, active_group

	def sort_and_set_layout(self, cols, rows, cells, active_group):
		self.set_layout(*sort_layout(cols, rows, cells, active_group))

	def swap_views(self, sorted_cells, cells):
		window = self.window
		swaps = []
		for i in range(len(cells)):
			if cells[i] != sorted_cells[i]:
				sorted_index = sorted_cells.index(cells[i])
				swaps.append(sorted([i, sorted_index]))
		swaps = list(swaps for swaps,_ in itertools.groupby(swaps))
		for swap in swaps:
			views = []
			views.append(window.views_in_group(swap[0]))
			views.append(window.views_in_group(swap[1]))
			for i, v in enumerate(views[0]):
				window.set_view_index(v, swap[1], i)
			for i, v in enumerate(views[1]):
				window.set_view_index(v, swap[0], i)
