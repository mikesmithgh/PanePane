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

def p(v):
	print(str(v))

def get_indices(orientation):
	return (X1, X2) if is_cols(orientation) else (Y1, Y2)

def is_cols(orientation):
	return orientation == COLS

def is_rows(orientation):
	return orientation == ROWS

def get_points(cols, rows, orientation):
	return cols if is_cols(orientation) else rows

def get_direction(cell, points, orientation):
	index = 0 if is_cols(orientation) else 1
	return 1 if (cell[index] <= (len(points) / 2) - 1) else -1

def get_point_index(cell, points, orientation, direction):
	p1, p2 = get_indices(orientation)
	point_index = cell[p2] if direction > 0 else cell[p1]
	if (point_index == (len(points) - 1)):
		point_index -= 1
	if (point_index == 0):
		point_index = 1
	return point_index

def get_adjacent_direction(orientation, direction):
	if is_cols(orientation):
		d1 = RIGHT
		d2 = LEFT
	else:
		d1 = DOWN
		d2 = UP
	return d1 if direction > 0 else d2

def get_similar_directions(orientation):
	return [UP, DOWN] if is_cols(orientation) else [LEFT, RIGHT]

def old_get_adjacent_cells(cell, cells, directions):
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
			if (cell[p1] == c[p2]):
				# todo clean up logic
				if (direction == UP) or (direction == DOWN):
					if (c[X1] <= cell[X1]) and (c[X2] >= cell[X1]):
						adjacent_cells.append(c)
					elif (c[X2] >= cell[X2]) and (c[X1] <= cell[X2]):
						adjacent_cells.append(c)
					elif (c[X1] >= cell[X1]) and (c[X2] <= cell[X2]):
						adjacent_cells.append(c)
				elif (direction == LEFT) or (direction == RIGHT):
					if (c[Y1] <= cell[Y1]) and (c[Y2] >= cell[Y1]):
						adjacent_cells.append(c)
					elif (c[Y2] >= cell[Y2]) and (c[Y1] <= cell[Y2]):
						adjacent_cells.append(c)
					elif (c[Y1] >= cell[Y1]) and (c[Y2] <= cell[Y2]):
						adjacent_cells.append(c)

	return adjacent_cells

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

def get_point_min_max(cell, cells, point_index, orientation, direction): 
	p1, p2 = get_indices(orientation)
	adjacent_direction = get_adjacent_direction(orientation, direction)
	p('dir')
	p(direction)
	if direction > 0:
		max_adj_cells = get_adjacent_cells(point_index, cells, [adjacent_direction])
		p(adjacent_direction)
		p("max")
		p(max_adj_cells)
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
		# min_adj_cells = get_adjacent_cells(cell, cells, [adjacent_direction])
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
			point_max = cell[p2]

	return point_min, point_max

def old_get_point_min_max(cell, cells, orientation, direction): 
	p1, p2 = get_indices(orientation)
	adjacent_direction = get_adjacent_direction(orientation, direction)
	# todo clean up logic
	if direction > 0:
		max_adj_cells = get_adjacent_cells(cell, cells, [adjacent_direction])
		if max_adj_cells:
			point_max = min(list(map(lambda c: c[p2], max_adj_cells)))
		else:
			point_max = cell[p2]

		opposite_direction = OPPOSITE[adjacent_direction]
		min_adj_cells = get_adjacent_cells(cell, cells, [opposite_direction])
		# min_adj_cells.append(cell)
		p(min_adj_cells)
		p("woo")
		p(cell)
		if min_adj_cells:
			point_min = max(list(map(lambda c: c[p2], min_adj_cells)))
		else:
			point_min = cell[p1]
		#testing similar logic
		# max_adj_cells = get_adjacent_cells(cell, cells, [adjacent_direction])
		# if max_adj_cells:
		# 	point_max = min(list(map(lambda c: c[p2], max_adj_cells)))
		# else:
		# 	point_max = cell[p2]

		# similar_directions = get_similar_directions(orientation)
		# min_adj_cells = get_adjacent_cells(cell, cells, similar_directions)
		# min_adj_cells.append(cell)
		# point_min = max(list(map(lambda c: c[p1], min_adj_cells)))
	else:
		min_adj_cells = get_adjacent_cells(cell, cells, [adjacent_direction])
		if min_adj_cells:
			point_min = max(list(map(lambda c: c[p1], min_adj_cells)))
		else:
			point_min = cell[p1]

		opposite_direction = OPPOSITE[adjacent_direction]
		max_adj_cells = get_adjacent_cells(cell, cells, [opposite_direction])
		if max_adj_cells:
			point_max = min(list(map(lambda c: c[p1], max_adj_cells)))
		else:
			point_max = cell[p2]

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


class ResizeCommand(sublime_plugin.WindowCommand):
	def run(self, orientation, amount = 5):
		p("**")
		self.resize(orientation, amount)

	def resize(self, orientation, amount):
		window = self.window
		cols, rows, cells, active_group = self.sort_and_get_layout()
		active_cell = cells[active_group]
		points = get_points(cols, rows, orientation)
		direction = get_direction(active_cell, points, orientation)
		amount *= direction
		point_index = get_point_index(active_cell, points, orientation, direction)
		point_min_index, point_max_index = get_point_min_max(active_cell, cells, point_index, orientation, direction)
		point_min = points[point_min_index]
		point_max = points[point_max_index]
		p("min_max")
		p(point_min_index)
		p(point_max_index)
		new_point_value = round(float(points[point_index]) + (amount / 100), 2) 
		if (new_point_value > point_min) and (new_point_value < point_max):
			# if (points[point_index - 1] > new_point_value):
			# 	points[point_index] = points[point_index - 1]
			# 	point_index = point_index - 1
			# elif (points[point_index + 1] < new_point_value):
			# 	points[point_index] = points[point_index + 1]
			# 	point_index = point_index + 1
			# might need to sort
			points[point_index] = new_point_value
			if (points[point_index] == points[point_index - 1]):
				points[point_index] += 0.01
			elif (points[point_index] == points[point_index + 1]):
				points[point_index] -= 0.01	


			if (is_cols(orientation)):
				cols = points
			else:
				rows = points

			cols, rows, cells, active_group = sort_layout(cols, rows, cells, active_group)
			active_cell = cells[active_group]
			new_direction = get_direction(active_cell, points, orientation)
			p("direction")
			p(direction)
			# self.sort_and_set_layout(cols, rows, cells, active_group)
			# do not set layout if this will revere the direction, this will flip each command and may be confusing
			if (direction == new_direction):
				self.set_layout(cols, rows, cells, active_group)	
			p(self.window.layout()["cols"])


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