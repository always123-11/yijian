"""动画系统。

作业要求「箭头成功飞出和发生碰撞时, 应有基本的动画或视觉反馈」,
这里实现四种效果:

    CellFly      箭头成功飞出: 沿朝向滑出棋盘并淡出缩小
    Shake        箭头被挡住: 原地抖动 + 变红
    FloatText    文字提示从棋盘上方飘起并淡出
    Burst        通关时的小粒子爆开
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

import pygame

from . import theme as T
from .render import draw_arrow, draw_text


# --------------------------------------------------------------------------- #
# 基类
# --------------------------------------------------------------------------- #
class Anim:
    """所有动画的基类: 用 t 表示进度 (0 -> 1), done 表示结束。"""

    def __init__(self, duration: float):
        self.duration = max(1e-6, duration)
        self.t = 0.0

    def update(self, dt: float) -> None:
        self.t = min(1.0, self.t + dt / self.duration)

    @property
    def done(self) -> bool:
        return self.t >= 1.0

    @property
    def progress(self) -> float:
        return self.t

    def draw(self, surface) -> None:      # pragma: no cover - 由子类实现
        raise NotImplementedError


def ease_out_cubic(x: float) -> float:
    return 1 - (1 - x) ** 3


def ease_out_back(x: float) -> float:
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


# --------------------------------------------------------------------------- #
# 箭头飞出
# --------------------------------------------------------------------------- #
@dataclass
class CellFly(Anim):
    """箭头沿 direction 飞出棋盘。"""

    center: tuple[float, float]
    direction: str
    size: float
    distance: float
    delay: float = 0.0
    color: tuple[int, int, int] = T.ARROW_OK

    def __init__(self, center, direction, size, distance, delay=0.0,
                 color=T.ARROW_OK, duration=0.34):
        super().__init__(duration)
        self.center = center
        self.direction = direction
        self.size = size
        self.distance = distance
        self.delay = delay
        self.color = color

    def update(self, dt: float) -> None:
        if self.delay > 0:
            self.delay -= dt
            return
        super().update(dt)

    @property
    def done(self) -> bool:
        return self.delay <= 0 and self.t >= 1.0

    def draw(self, surface) -> None:
        if self.delay > 0:
            # 延迟期间先原地画着, 形成错开的效果
            draw_arrow(surface, self.center, self.size, self.direction,
                       self.color, scale=1.0)
            return
        p = ease_out_cubic(self.progress)
        dx = {"<": -1, ">": 1}.get(self.direction, 0)
        dy = {"^": -1, "v": 1}.get(self.direction, 0)
        cx = self.center[0] + dx * self.distance * p
        cy = self.center[1] + dy * self.distance * p
        alpha = int(255 * (1.0 - max(0.0, (self.progress - 0.45) / 0.55)))
        scale = 1.0 - 0.35 * self.progress
        draw_arrow(surface, (cx, cy), self.size, self.direction, self.color,
                   shadow=False, alpha=max(0, alpha), scale=scale)


# --------------------------------------------------------------------------- #
# 被挡住: 抖动
# --------------------------------------------------------------------------- #
@dataclass
class Shake(Anim):
    """某个格子上的箭头左右抖动 (方向沿其朝向的垂直方向)。"""

    center: tuple[float, float]
    direction: str
    size: float
    amplitude: float = 7.0
    color: tuple[int, int, int] = T.ARROW_BLOCKED

    def __init__(self, center, direction, size, amplitude=7.0,
                 color=T.ARROW_BLOCKED, duration=0.42):
        super().__init__(duration)
        self.center = center
        self.direction = direction
        self.size = size
        self.amplitude = amplitude
        self.color = color

    def _offset(self) -> tuple[float, float]:
        p = self.progress
        # 衰减正弦, 抖动约 3 个来回
        decay = 1.0 - p
        s = math.sin(p * math.pi * 6) * decay * self.amplitude
        if self.direction in ("^", "v"):
            return s, 0.0
        return 0.0, s

    def draw(self, surface) -> None:
        ox, oy = self._offset()
        # 抖动期间颜色在红/正常之间闪, 强调"错误"
        flash = 0.5 + 0.5 * math.sin(self.progress * math.pi * 6)
        color = tuple(
            int(T.ARROW_HOVER[i] + (self.color[i] - T.ARROW_HOVER[i]) * flash)
            for i in range(3)
        )
        draw_arrow(surface, (self.center[0] + ox, self.center[1] + oy),
                   self.size, self.direction, color)


# --------------------------------------------------------------------------- #
# 飘字
# --------------------------------------------------------------------------- #
@dataclass
class FloatText(Anim):
    """在棋盘上方飘起的文字提示。"""

    text: str
    center: tuple[float, float]
    color: tuple[int, int, int] = T.WARN_RED
    size: int = T.FS_H1
    rise: float = 52.0

    def __init__(self, text, center, color=T.WARN_RED, size=T.FS_H1,
                 rise=52.0, duration=0.9):
        super().__init__(duration)
        self.text = text
        self.center = center
        self.color = color
        self.size = size
        self.rise = rise

    def draw(self, surface) -> None:
        p = ease_out_cubic(self.progress)
        cy = self.center[1] - self.rise * p
        alpha = int(255 * (1.0 - max(0.0, (self.progress - 0.5) / 0.5)))
        if alpha <= 0:
            return
        font_img = None
        from .render import get_font
        font_img = get_font(self.size, True).render(self.text, True, self.color)
        font_img.set_alpha(alpha)
        rect = font_img.get_rect(center=(self.center[0], cy))
        # 描边增强可读性
        outline = get_font(self.size, True).render(self.text, True, (0, 0, 0))
        outline.set_alpha(int(alpha * 0.55))
        for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
            surface.blit(outline, (rect.x + ox, rect.y + oy))
        surface.blit(font_img, rect)


# --------------------------------------------------------------------------- #
# 粒子爆开
# --------------------------------------------------------------------------- #
@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    color: tuple[int, int, int]
    size: float

    def update(self, dt: float, gravity: float = 420.0) -> bool:
        self.life -= dt
        self.vy += gravity * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        return self.life > 0


@dataclass
class Burst(Anim):
    """一组粒子。"""

    center: tuple[float, float]
    count: int = 26
    colors: tuple = (T.ARROW_OK, T.ACCENT, T.ARROW_IDLE)

    def __init__(self, center, count=26, duration=0.9,
                 colors=(T.ARROW_OK, T.ACCENT, T.ARROW_IDLE)):
        super().__init__(duration)
        self.center = center
        self.count = count
        self.particles: list[Particle] = []
        rng = random.Random(20260917)
        for _ in range(count):
            ang = rng.uniform(0, math.tau)
            spd = rng.uniform(90, 320)
            life = rng.uniform(0.45, duration)
            self.particles.append(Particle(
                x=center[0], y=center[1],
                vx=math.cos(ang) * spd, vy=math.sin(ang) * spd - 60,
                life=life, max_life=life,
                color=colors[rng.randrange(len(colors))],
                size=rng.uniform(3, 7),
            ))

    def update(self, dt: float) -> None:
        super().update(dt)
        self.particles = [p for p in self.particles if p.update(dt)]

    @property
    def done(self) -> bool:
        return not self.particles

    def draw(self, surface) -> None:
        for p in self.particles:
            a = max(0.0, p.life / p.max_life)
            r = max(1, int(p.size * a))
            dot = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(dot, (*p.color, int(220 * a)), (r, r), r)
            surface.blit(dot, (p.x - r, p.y - r))


# --------------------------------------------------------------------------- #
# 动画管理器
# --------------------------------------------------------------------------- #
class AnimationManager:
    """
    管理一组动画。分成两层:

      * board 层: 只作用于棋盘格子 (飞出的箭头、抖动), 随棋盘绘制顺序绘制
      * top 层: 覆盖层 (飘字、粒子), 在棋盘之后绘制
    """

    def __init__(self):
        self.board: list[Anim] = []
        self.top: list[Anim] = []

    def add_board(self, anim: Anim) -> None:
        self.board.append(anim)

    def add_top(self, anim: Anim) -> None:
        self.top.append(anim)

    def clear(self) -> None:
        self.board.clear()
        self.top.clear()

    def update(self, dt: float) -> None:
        for a in self.board:
            a.update(dt)
        for a in self.top:
            a.update(dt)
        self.board = [a for a in self.board if not a.done]
        self.top = [a for a in self.top if not a.done]

    @property
    def busy(self) -> bool:
        """是否还有动画在播放 (用于延迟自动跳转下一关)。"""
        return bool(self.board or self.top)

    def draw_board_layer(self, surface) -> None:
        for a in self.board:
            a.draw(surface)

    def draw_top_layer(self, surface) -> None:
        for a in self.top:
            a.draw(surface)
