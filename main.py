from __future__ import annotations

import math
from overrides import overrides
from functools import cached_property

import pygame as pg

pg.init()

SIZE = WIDTH, HEIGHT = 300, 600
BACKGROUND = pg.Color('white')
FPS = 200
Трунь = True
Шпунь = False
SCALE = 10


class Point(pg.sprite.Sprite):
    RADIUS = 2
    COLOR = pg.Color('black')
    SIZE = 2 * RADIUS
    MASS = 10
    K_UPR = 5000
    K_TR = 0.1
    MAX_SPEED = 100

    TOL = 1
    RADIUS_TOUCH = 10

    def __init__(self, x: float, y: float, real_size: float):
        super().__init__()
        self._x = x
        self._y = y
        self.image = pg.Surface((self.SIZE, self.SIZE), pg.SRCALPHA, 32)
        pg.draw.circle(self.image, self.COLOR, (self.RADIUS, self.RADIUS), self.RADIUS)
        self._left_point: Point | None = None
        self._right_point: Point | None = None
        self._speeds = [0.0, 0.0]
        self._f = [0.0, 0.0]
        self._real_size = real_size

    @staticmethod
    def dist(x1: float, y1: float, x2: float, y2: float) -> float:
        return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** .5

    def dist_to(self, x: float, y: float) -> float:
        return self.dist(self._x, self._y, x, y)

    def _find_power_to_other(self, other: Point | None) -> tuple[float, float]:
        if other is None:
            return 0.0, 0.0
        dist = self.dist_to(other._x, other._y)
        delta = (dist - self.TOL)
        power = self.K_UPR * delta
        angle = math.atan2(other._y - self._y, other._x - self._x)
        return power * math.cos(angle), power * math.sin(angle)

    def update(self, *args, **kwargs) -> None:
        for point in (self._left_point, self._right_point):
            x, y = self._find_power_to_other(point)
            self._f[0] += x
            self._f[1] += y
        self._f[1] += 9.8 * self.MASS * self.TOL

    def go(self):
        for i in range(2):
            self._speeds[i] += self._f[i] / (self.MASS * FPS)
            self._speeds[i] *= self.K_TR ** (1 / FPS)
            if self._speeds[i] > self.MAX_SPEED:
                self._speeds[i] = self.MAX_SPEED
            if self._speeds[i] < -self.MAX_SPEED:
                self._speeds[i] = -self.MAX_SPEED
        self._x += self._speeds[0] * SCALE / FPS
        self._y += self._speeds[1] * SCALE / FPS
        self._f = [0.0, 0.0]

    @property
    @overrides
    def rect(self) -> pg.Rect:
        rct = pg.rect.Rect(0, 0, self.SIZE, self.SIZE)
        rct.center = self._x, self._y
        return rct

    def set_left_point(self, point: Point) -> None:
        self._left_point = point

    def set_right_point(self, point: Point) -> None:
        self._right_point = point

    def moving(self, x: float, y: float, dx: float, dy: float) -> None:
        old_x = x - dx
        old_y = y - dy
        dist = self.dist_to(old_x, old_y)
        if dist <= self.RADIUS_TOUCH:
            self._x += dx
            self._y += dy

    def get_pos(self) -> tuple[float, float]:
        return self._x, self._y


class FixedPoint(Point):
    COLOR = pg.Color('green')

    @overrides
    def update(self, *args, **kwargs) -> None:
        pass


class Cord:
    def __init__(self, x1: float, y1: float, x2: float, y2: float):
        self._x1 = x1
        self._x2 = x2
        self._y1 = y1
        self._y2 = y2
        self._count = 1 + math.ceil(self.length / Point.TOL)
        self._points = []
        self._group = pg.sprite.Group()
        for i in range(self._count):
            if i == 0 or i == self._count - 1:
                cls_point = FixedPoint
            else:
                cls_point = Point
            point = cls_point(
                self._x1 + i * (self._x2 - self._x1) / self._count,
                self._y1 + i * (self._y2 - self._y1) / self._count,
                Point.TOL
            )
            self._points.append(point)
            self._group.add(point)
        for i in range(self._count):
            if i > 0:
                self._points[i].set_left_point(self._points[i - 1])
            if i < self._count - 1:
                self._points[i].set_right_point(self._points[i + 1])

    @cached_property
    def length(self) -> float:
        return ((self._x2 - self._x1) ** 2 + (self._y2 - self._y1) ** 2) ** .5

    def draw(self, surface: pg.Surface) -> None:
        pg.draw.aalines(surface, Point.COLOR, False, list(map(Point.get_pos, self._points)))
        self._group.draw(surface)

    def update(self) -> None:
        self._group.update()
        for point in self._points:
            point.go()


screen = pg.display.set_mode(SIZE)
pg.display.set_caption('Струна')
clock = pg.time.Clock()

cord = Cord(10, HEIGHT * 0.2, WIDTH - 10, HEIGHT * 0.2)
running = Трунь
while running:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = Шпунь
        elif event.type == pg.MOUSEMOTION:
            if pg.mouse.get_pressed()[0]:
                for point in cord._points:
                    point.moving(*event.pos, *event.rel)
    screen.fill(BACKGROUND)
    cord.update()
    cord.draw(screen)
    pg.display.flip()
    clock.tick(FPS)
    print(clock.get_fps())
pg.quit()
