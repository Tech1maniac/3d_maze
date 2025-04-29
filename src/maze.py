import math
import random
from random import choice

import components_3d as com
import glm
import resources as res


def unites(i, j, world, w, h, depth, model_id, diffuse):
    """
    Places one cuboid (wall segment) at position (i, j) of size w×h×depth.
    """
    world.create_entity(
        com.Model3D(model_id),
        com.Transformation(
            position=glm.vec3(i + w / 2, j + h / 2, depth / 2),
            scale=glm.vec3(float(w), float(h), depth)
        ),
        com.BoundingBox(com.Rectangle3D(float(w), float(h), depth)),
        com.TransformationMatrix(),
        com.ObjectMaterial(diffuse=diffuse)
    )


def _setup_maze(world, width, height, depth=2.0, wall_width=1.0, path_width=3.0):
    """
    Generate a maze using DFS backtracker and spawn 3D entities for floor and walls.
    Returns a Maze object with .empty_areas_loc and .center populated.
    """
    cube_id = world.model_registry.get_model_id(res.ModelRegistry.CUBE)
    maze = Maze(w=width, l=height)
    grid = maze.generate_maze()
    rows, cols = maze.shape

    # Compute overall floor size and center
    total_w = width * (wall_width + path_width) / 2
    total_h = height * (wall_width + path_width) / 2
    maze.center = glm.vec3(
        total_w / 2 + wall_width / 2,
        total_h / 2 + wall_width / 2,
        0.0
    )

    # Create floor entity
    world.create_entity(
        com.Model3D(cube_id),
        com.Transformation(
            position=glm.vec3(maze.center.x, maze.center.y, -path_width / 2),
            scale=glm.vec3(total_w, total_h, path_width)
        ),
        com.BoundingBox(com.Rectangle3D(total_w, total_h, path_width)),
        com.TransformationMatrix(),
        com.ObjectMaterial(
            diffuse=glm.vec3(0.6, 0.6, 0.6),
            specular=glm.vec3(0.2, 0.3, 0.6),
            shininess=6
        )
    )

    empty_cells = []
    # Spawn walls and record empty spaces
    for i in range(rows):
        row = grid[i]
        h = wall_width if i % 2 == 0 else path_width
        y = sum((wall_width if r % 2 == 0 else path_width) for r in range(i))

        j = 0
        while j < cols:
            w = wall_width if j % 2 == 0 else path_width
            x = sum((wall_width if c % 2 == 0 else path_width) for c in range(j))

            if row[j]:
                # merge contiguous walls
                run_w = w
                j += 1
                while j < cols and row[j]:
                    run_w += (wall_width if j % 2 == 0 else path_width)
                    j += 1
                diffuse = glm.vec3(x / total_w, y / total_h, abs(math.cos(y / 10.0)))
                unites(x, y, world, run_w, h, depth, cube_id, diffuse)
            else:
                # path cell
                cx = x + path_width / 2
                cy = y + path_width / 2
                empty_cells.append([cx, cy])
                j += 1

    maze.empty_areas_loc = empty_cells
    return maze


class Maze:
    def __init__(self, w=30, l=30):
        # ensure odd dimensions
        self.width = w
        self.height = l
        self.shape = ((self.height // 2) * 2 + 1,
                      (self.width  // 2) * 2 + 1)
        self.maze = []
        self.center = glm.vec3()
        self.empty_areas_loc = []

    def generate_maze(self):
        rows, cols = self.shape
        # start with all walls
        m = [[True] * cols for _ in range(rows)]

        # carve out a perfect maze via recursive backtracker
        def carve(x, y):
            m[y][x] = False
            dirs = [(2, 0), (-2, 0), (0, 2), (0, -2)]
            random.shuffle(dirs)
            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                if 0 < nx < cols - 1 and 0 < ny < rows - 1 and m[ny][nx]:
                    # knock down wall between
                    m[y + dy//2][x + dx//2] = False
                    carve(nx, ny)

        carve(1, 1)

        # optionally add loops to increase randomness
        loops = (rows * cols) // 20
        for _ in range(loops):
            i = random.randint(1, rows - 2)
            j = random.randint(1, cols - 2)
            if m[i][j]:
                m[i][j] = False

        self.maze = m
        return m
