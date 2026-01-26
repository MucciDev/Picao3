import pygame
import random
import numpy as np
import math
from typing import List, Tuple
from collections import deque
from dataclasses import dataclass
from enum import Enum
from pygame import Surface, SRCALPHA

class Colors(Enum):
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    GRAY = (150, 150, 150)
    YELLOW = (255, 255, 0)
    BLUE = (0, 0, 255)

@dataclass(slots=True, frozen=True)
class Position:
    x: int
    y: int
    
    def __add__(self, other):
        return Position(self.x + other.x, self.y + other.y)
    
    def to_tuple(self):
        return (self.x, self.y)

class MenuParticle:
    def __init__(self, screen_width, screen_height):
        self.x = random.randint(0, screen_width)
        self.y = random.randint(0, screen_height)
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-2, 2)
        self.radius = random.randint(5, 15)
        self.hue = random.random()
        self.sw, self.sh = screen_width, screen_height

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.hue = (self.hue + 0.01) % 1.0
        
        if self.x < 0 or self.x > self.sw: self.vx *= -1
        if self.y < 0 or self.y > self.sh: self.vy *= -1

    def draw(self, screen):
        color = pygame.Color(0)
        color.hsva = (self.hue * 360, 80, 100, 100)
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.radius)

class MainMenu:
    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        self.font_large = pygame.font.Font(None, 120) # Made title bigger
        self.font = pygame.font.Font(None, 36)
        
        # Party Particles
        self.particles = [MenuParticle(self.width, self.height) for _ in range(50)]
        
        bw, bh = 200, 50
        self.buttons = {
            "Play": pygame.Rect((self.width - bw) // 2, self.height // 2 - 50, bw, bh),
            "Quit": pygame.Rect((self.width - bw) // 2, self.height // 2 + 50, bw, bh)
        }

    def draw(self):
        self.screen.fill(Colors.BLACK.value) # Dark background for neon party look
        
        for p in self.particles:
            p.update()
            p.draw(self.screen)

        # Title with shadow for readability
        title_surf = self.font_large.render("Picão 3", True, Colors.WHITE.value)
        title_rect = title_surf.get_rect(center=(self.width // 2, 425))
        self.screen.blit(title_surf, title_rect)

        for text, rect in self.buttons.items():
            pygame.draw.rect(self.screen, Colors.WHITE.value, rect, 2) # Outline buttons
            label = self.font.render(text, True, Colors.WHITE.value)
            self.screen.blit(label, (rect.centerx - label.get_width() // 2, rect.centery - label.get_height() // 2))
        pygame.display.flip()

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "quit"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = pygame.mouse.get_pos()
                if self.buttons["Play"].collidepoint(pos): return "play"
                if self.buttons["Quit"].collidepoint(pos): return "quit"
        return "menu"

class MazeGame:
    DIRECTIONS = [Position(0, -1), Position(1, 0), Position(0, 1), Position(-1, 0)]
    
    def __init__(self, initial_size: int = 7, cell_size: int = 40):
        pygame.init()
        self.cell_size = cell_size
        self.maze_size = initial_size
        self.screen_size = 1200
        self.screen = pygame.display.set_mode((self.screen_size, self.screen_size))
        pygame.display.set_caption("Picão 3 - Party Edition")
        
        self.level = 1
        self.score = 0
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        
        self._init_assets()
        self.initialize_new_maze()
        
        self.state = "menu"
        self.main_menu = MainMenu(self.screen)
        self.running = True

    def _init_assets(self):
        self.hud_bg = Surface((200, 80), SRCALPHA)
        self.hud_bg.fill((50, 50, 50, 200)) # Darker HUD
        self.player_surf = Surface((self.cell_size, self.cell_size), SRCALPHA)

    def initialize_new_maze(self):
        self.maze = np.full((self.maze_size, self.maze_size), 1, dtype=int)
        self._generate_prim_maze()
        
        self.start_pos = Position(1, 1)
        self.end_pos = Position(self.maze_size - 2, self.maze_size - 2)
        self.maze[self.start_pos.y, self.start_pos.x] = 0
        self.maze[self.end_pos.y, self.end_pos.x] = 0
        
        self.player_pos = Position(self.start_pos.x, self.start_pos.y)
        self.camera_pos = [float(self.player_pos.x), float(self.player_pos.y)]
        
        self._prerender_maze()
        self.blue_cube_path = self.find_shortest_path(self.start_pos, self.end_pos)
        self.blue_cube_pos = Position(self.start_pos.x, self.start_pos.y)

    def _generate_prim_maze(self):
        walls = []
        start_x, start_y = 1, 1
        self.maze[start_y, start_x] = 0
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            walls.append((start_x + dx, start_y + dy, start_x, start_y))

        while walls:
            wx, wy, px, py = walls.pop(random.randint(0, len(walls) - 1))
            if 0 < wx < self.maze_size - 1 and 0 < wy < self.maze_size - 1:
                if self.maze[wy, wx] == 1:
                    nx, ny = wx + (wx - px), wy + (wy - py)
                    if 0 < nx < self.maze_size - 1 and 0 < ny < self.maze_size - 1:
                        if self.maze[ny, nx] == 1:
                            self.maze[wy, wx] = 0
                            self.maze[ny, nx] = 0
                            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                                walls.append((nx + dx, ny + dy, nx, ny))

    def _prerender_maze(self):
        self.maze_surface = Surface((self.maze_size * self.cell_size, self.maze_size * self.cell_size))
        self.maze_surface.fill(Colors.WHITE.value)
        for y in range(self.maze_size):
            for x in range(self.maze_size):
                if self.maze[y, x] == 1:
                    pygame.draw.rect(self.maze_surface, Colors.BLACK.value, 
                                   (x * self.cell_size, y * self.cell_size, self.cell_size, self.cell_size))
        pygame.draw.rect(self.maze_surface, Colors.GREEN.value,
                        (self.end_pos.x * self.cell_size, self.end_pos.y * self.cell_size, self.cell_size, self.cell_size))

    def draw_player(self, x, y):
        self.player_surf.fill(Colors.RED.value)
        dx, dy = self.end_pos.x - self.player_pos.x, self.end_pos.y - self.player_pos.y
        angle = math.atan2(dy, dx)
        center = self.cell_size // 2
        end_x = center + (center - 5) * math.cos(angle)
        end_y = center + (center - 5) * math.sin(angle)
        pygame.draw.line(self.player_surf, Colors.YELLOW.value, (center, center), (end_x, end_y), 3)
        self.screen.blit(self.player_surf, (x, y))

    def draw_maze(self):
        self.camera_pos[0] += (self.player_pos.x - self.camera_pos[0]) * 0.1
        self.camera_pos[1] += (self.player_pos.y - self.camera_pos[1]) * 0.1
        
        offset_x = self.screen_size // 2 - int(self.camera_pos[0] * self.cell_size)
        offset_y = self.screen_size // 2 - int(self.camera_pos[1] * self.cell_size)
        
        self.screen.fill(Colors.WHITE.value)
        self.screen.blit(self.maze_surface, (offset_x, offset_y))
        self.draw_player(self.player_pos.x * self.cell_size + offset_x, self.player_pos.y * self.cell_size + offset_y)
        
        bx = self.blue_cube_pos.x * self.cell_size + offset_x
        by = self.blue_cube_pos.y * self.cell_size + offset_y
        pygame.draw.rect(self.screen, Colors.BLUE.value, (bx, by, self.cell_size, self.cell_size))
        self._draw_hud()
        pygame.display.flip()

    def _draw_hud(self):
        self.screen.blit(self.hud_bg, (10, 10))
        lines = [f"Level: {self.level}", f"Score: {self.score}", f"Size: {self.maze_size}"]
        for i, text in enumerate(lines):
            surf = self.font.render(text, True, Colors.WHITE.value)
            self.screen.blit(surf, (20, 15 + i * 25))

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.running = False
            if event.type == pygame.KEYDOWN:
                dx, dy = 0, 0
                if event.key == pygame.K_w: dy = -1
                elif event.key == pygame.K_s: dy = 1
                elif event.key == pygame.K_a: dx = -1
                elif event.key == pygame.K_d: dx = 1
                
                new_pos = Position(self.player_pos.x + dx, self.player_pos.y + dy)
                if 0 <= new_pos.x < self.maze_size and 0 <= new_pos.y < self.maze_size:
                    if self.maze[new_pos.y, new_pos.x] == 0:
                        self.player_pos = new_pos
                        if self.player_pos == self.end_pos:
                            self.next_level()

    def next_level(self):
        self.level += 1
        self.score += self.maze_size * 20
        self.maze_size += 2
        self.initialize_new_maze()

    def find_shortest_path(self, start, end):
        queue = deque([(start, [])])
        visited = {start.to_tuple()}
        while queue:
            curr, path = queue.popleft()
            if curr == end: return path
            for d in self.DIRECTIONS:
                next_p = curr + d
                if (0 <= next_p.x < self.maze_size and 0 <= next_p.y < self.maze_size and 
                    self.maze[next_p.y, next_p.x] == 0 and next_p.to_tuple() not in visited):
                    visited.add(next_p.to_tuple())
                    queue.append((next_p, path + [next_p]))
        return []

    def run(self):
        move_timer = 0
        while self.running:
            if self.state == "menu":
                self.state = self.main_menu.handle_input()
                self.main_menu.draw()
                self.clock.tick(60)
            elif self.state == "play":
                self.handle_input()
                move_timer += 1
                if move_timer > 5 and self.blue_cube_path:
                    self.blue_cube_pos = self.blue_cube_path.pop(0)
                    move_timer = 0
                self.draw_maze()
                self.clock.tick(60)
            elif self.state == "quit":
                self.running = False
        pygame.quit()

if __name__ == "__main__":
    MazeGame().run()
