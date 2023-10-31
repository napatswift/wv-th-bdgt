import numpy as np
from typing import List, Dict, T, Union
from fitz import Rect

import numpy as np


def is_on_line(point, line_start, line_end, tolerance=0.0001):
    # Unpack the x and y coordinates of the line start, line end, and point
    x1, y1 = line_start
    x2, y2 = line_end
    x3, y3 = point

    # Calculate the distance between the line start and line end
    dist = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)

    # If the distance is 0, the line is actually a point, so return False
    if dist == 0:
        return False

    # Calculate the distances between the point and the line start and line end
    dist1 = np.sqrt((x3 - x1)**2 + (y3 - y1)**2)
    dist2 = np.sqrt((x3 - x2)**2 + (y3 - y2)**2)

    # Calculate the dot product of the vectors from the line start to the point and from the line start to the line end
    dot_product = ((x3 - x1) * (x2 - x1) + (y3 - y1) * (y2 - y1)) / (dist**2)

    # If the dot product is outside the range [0, 1] or the point is outside the line segment, return False
    if dot_product < 0 or dot_product > 1 or dist1 > dist or dist2 > dist:
        return False

    # Calculate the distance between the point and the line, and return True if it's within the tolerance
    return np.abs((y2 - y1) * x3 - (x2 - x1) * y3 + x2 * y1 - y2 * x1) / dist < tolerance



def get_connected_lines(rects: List[Rect], tolerance: int = 10) -> Dict[Rect, List[Rect]]:
    """
    Returns a dictionary of lists of rects that are connected by lines.

    Args:
      rects: A list of Rect objects.
      tolerance: The tolerance for determining if a point is on a line.

    Returns:
      A dictionary of lists of rects that are connected by lines.
    """
    connected_lines = {}
    for rect in rects:
        start = rect.top_left
        end = rect.bottom_right
        connected_lines[rect] = []

        for line in rects:
            # Skip the rect if it is the same as the rect we are checking
            if line is rect:
                continue

            is_top_left_on_the_line = is_on_line(
                line.top_left, start, end, tolerance)
            is_bottom_right_on_the_line = is_on_line(
                line.bottom_right, start, end, tolerance)

            if is_top_left_on_the_line or is_bottom_right_on_the_line:
                connected_lines[rect].append(line)

    return connected_lines


def dfs(visited: List[T], graph: Dict[T, T], node: T, start: T = None) -> Union['0', '1']:
    """
    The dfs function is a depth-first search algorithm
    that traverses a graph and returns 1 if the start node
    is connected to the given node, and 0 otherwise.

    Args:
        visited: A list of visited nodes.
        graph: A dictionary of lists of nodes.
        node: The current node.
        start: The starting node.
    """

    # if the start node is not given, set it to the current node
    if start is None:
        start = node

    # if the current node has not been visited
    # add it to the list of visited nodes
    if node not in visited:
        visited.append(node)

        # recursively call dfs on each neighbour of the current node
        for neighbour in graph[node]:
            dfs(visited, graph, neighbour, start)

    # return 1 if the start node is in the list of visited nodes
    return 1 if start in graph[visited[-1]] else 0


def merge_rects(rects: List[Rect]) -> Rect:
    """
    Returns a rect that contains all of the given rects.

    Args:
        rects: A list of Rect objects.
    """
    big_rect = rects[0]
    for rect in rects[1:]:
        big_rect = big_rect | rect
    return big_rect


class Table:
    def __init__(self, rects: List[Rect]):
        self.rects = rects
        self.table_rect = merge_rects(rects)
        self.horizontals = []
        self.verticals = []

        self._find_horizontals()
        self._find_verticals()

        self.table_cells = []
        self._initialize_table_cells()

    def _find_horizontals(self):
        """
        Finds the horizontal lines in the table.
        """
        horizontal_y0_list = []

        def is_in_horizontal(rect):
            threshold = 5
            for horizontal in horizontal_y0_list:
                if abs(rect.y0 - horizontal) < threshold:
                    return True
            return False
        for rect in self.rects:
            if rect.width > rect.height and not is_in_horizontal(rect):
                horizontal_y0_list.append(rect.y0)

        self.horizontals = horizontal_y0_list

    def _find_verticals(self):
        """
        Finds the vertical lines in the table.
        """
        vertical_x0_list = []

        def is_in_vertical(rect):
            threshold = 5
            for vertical in vertical_x0_list:
                if abs(rect.x0 - vertical) < threshold:
                    return True
            return False
        for rect in self.rects:
            if rect.width < rect.height and not is_in_vertical(rect):
                vertical_x0_list.append(rect.x0)

        self.verticals = vertical_x0_list

    def _initialize_table_cells(self):
        """
        Initializes the table cells.
        """
        horizontals = self.horizontals[:]
        if all([abs(self.table_rect.y0 - horizontal) > 5 for horizontal in horizontals]):
            horizontals = [self.table_rect.y0, *self.horizontals,]

        verticals = self.verticals[:]
        if all([abs(self.table_rect.x0 - vertical) > 5 for vertical in verticals]):
            verticals = [self.table_rect.x0, *self.verticals,]

        horizontals.sort()
        verticals.sort()
        for i in range(len(horizontals) - 1):
            for j in range(len(verticals) - 1):
                cell = Rect(
                    verticals[j],
                    horizontals[i],
                    verticals[j+1],
                    horizontals[i+1],
                )
                self.table_cells.append((i, j, cell, []))

    def add_word(self, word, x0, y0, x1, y1):
        """
        Adds a word to the table cell it belongs to.
        """
        added = False
        for ci, cj, cell, cwords in self.table_cells:
            if cell.contains(((x0+x1)/2, (y0+y1)/2)):
                cwords.append(word)
                added = True
                break

        if not added:
            raise Exception(
                "Word not added to table cell. It is not contained in any table cell.")

    def __repr__(self) -> str:
        return f"Table(horz={len(self.horizontals)}, vert={len(self.verticals)})"


def extract_tables(rects: List[Rect]) -> List[Table]:
    """
    Extracts tables from a list of rectangles.

    Args:
        rects: A list of `Rect` objects representing the rectangles to extract tables from.

    Returns:
        A list of `Table` objects representing the extracted tables.
    """

    # Get a dictionary of lists of connected lines
    connected_lines = get_connected_lines(rects)

    # Define a list of table rectangles
    table_rects = list()

    # Loop through each rectangle in the list of rectangles
    for rect in rects:
        # Create an empty list to keep track of visited rectangles
        visited = list()

        # Call the dfs function to find all rectangles connected to the current rectangle
        ret = dfs(visited, connected_lines, rect)

        # If the dfs function returns 0, the current rectangle is not connected to any other rectangles
        if ret == 0:
            continue

        # Merge all visited rectangles into a single "big" rectangle
        big_rect = merge_rects(visited)

        # Append the big rectangle to the list of table rectangles if:
        # the list is empty
        if len(table_rects) == 0:
            table_rects.append(big_rect)
        # the big rectangle is not contained in any of the existing table rectangles
        else:
            contained = False
            for table in table_rects:
                # check if the big rectangle is contained in the table rectangle
                if table.contains(big_rect):
                    contained = True
                    break

                # check if the big rectangle contains the table rectangle
                elif big_rect.contains(table):
                    table_rects.remove(table)
            # if the big rectangle is not contained in
            # any of the existing table rectangles, append it to the list
            if not contained:
                table_rects.append(big_rect)

    table_list = []

    # Loop through each table rectangle
    for table in table_rects:
        # Create an empty list to keep track of table rectangles
        tab_rects = []
        # page_image = new_image()

        for rect in rects:
            # If the rectangle is contained in the table rectangle,
            # append it to the list of table rectangles
            if table.contains(rect):
                tab_rects.append(rect)

        # Append the list of table rectangles to the list of tables
        table_list.append(Table(tab_rects))

    return table_list

