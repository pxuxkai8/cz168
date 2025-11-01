#!/usr/bin/env python3
"""Simple terminal Snake game implemented with curses.

Use the arrow keys or WASD to move the snake. The game ends when the
snake collides with the wall or with itself. Food appears randomly on
the board and each piece eaten increases the score and the snake's
length. The game speeds up slightly as the snake grows to keep things
interesting. When ``curses`` is not available, the script falls back to
a slower text mode that accepts ``W/A/S/D`` commands followed by Enter.
"""
from __future__ import annotations

import os
import random
import sys
import time
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Union

try:
    import curses
except ImportError:  # pragma: no cover - platform dependent
    curses = None  # type: ignore[assignment]

# Dimensions of the playable area (without borders)
BOARD_HEIGHT = 20
BOARD_WIDTH = 40

# Initial delay between frames in milliseconds. The delay decreases as the
# snake grows, making the game progressively harder.
INITIAL_DELAY = 150
MIN_DELAY = 60
SPEEDUP_STEP = 2


@dataclass(frozen=True)
class Point:
    """Represents a coordinate on the board."""

    y: int
    x: int

    def __add__(self, other: "Point") -> "Point":
        return Point(self.y + other.y, self.x + other.x)


CURSES_DIRECTIONS: Dict[int, Point] = {}
if curses is not None:
    CURSES_DIRECTIONS = {
        curses.KEY_UP: Point(-1, 0),
        curses.KEY_DOWN: Point(1, 0),
        curses.KEY_LEFT: Point(0, -1),
        curses.KEY_RIGHT: Point(0, 1),
        ord("w"): Point(-1, 0),
        ord("s"): Point(1, 0),
        ord("a"): Point(0, -1),
        ord("d"): Point(0, 1),
    }

TEXT_DIRECTIONS: Dict[str, Point] = {
    "w": Point(-1, 0),
    "s": Point(1, 0),
    "a": Point(0, -1),
    "d": Point(0, 1),
}


def random_food(snake: Iterable[Point]) -> Point:
    """Return a random point that is not occupied by the snake."""

    snake_set = set(snake)
    while True:
        point = Point(random.randrange(1, BOARD_HEIGHT + 1), random.randrange(1, BOARD_WIDTH + 1))
        if point not in snake_set:
            return point


def draw_border(stdscr: "curses._CursesWindow") -> None:
    """Draw a rectangular border around the playing field."""

    for x in range(BOARD_WIDTH + 2):
        stdscr.addch(0, x, "#")
        stdscr.addch(BOARD_HEIGHT + 1, x, "#")
    for y in range(BOARD_HEIGHT + 2):
        stdscr.addch(y, 0, "#")
        stdscr.addch(y, BOARD_WIDTH + 1, "#")


def render_curses(stdscr: "curses._CursesWindow", snake: List[Point], food: Point, score: int) -> None:
    """Render the current game state."""

    stdscr.clear()
    draw_border(stdscr)
    stdscr.addstr(0, BOARD_WIDTH + 4, f"Score: {score}")
    stdscr.addstr(2, BOARD_WIDTH + 4, "Controls:")
    stdscr.addstr(3, BOARD_WIDTH + 4, "Arrows / WASD")

    # Draw food
    stdscr.addch(food.y, food.x, "*")

    # Draw snake head and body
    if snake:
        stdscr.addch(snake[0].y, snake[0].x, "@")
        for segment in snake[1:]:
            stdscr.addch(segment.y, segment.x, "o")

    stdscr.refresh()


def render_text(snake: List[Point], food: Point, score: int) -> None:
    """Render the current game state using plain text output."""

    if sys.stdout.isatty():
        os.system("cls" if os.name == "nt" else "clear")

    board = [[" "] * BOARD_WIDTH for _ in range(BOARD_HEIGHT)]
    board[food.y - 1][food.x - 1] = "*"

    if snake:
        head = snake[0]
        board[head.y - 1][head.x - 1] = "@"
        for segment in snake[1:]:
            board[segment.y - 1][segment.x - 1] = "o"

    horizontal_border = "#" * (BOARD_WIDTH + 2)
    print(horizontal_border)
    for row in board:
        print("#" + "".join(row) + "#")
    print(horizontal_border)
    print(f"得分: {score}")
    print("控制: 输入 W/A/S/D 后回车，直接回车保持方向，Q 退出")


def next_direction(current_direction: Point, key: Union[int, str, None]) -> Point:
    """Return the next direction based on the pressed key."""

    if key is None:
        return current_direction

    proposed: Optional[Point] = None
    if isinstance(key, str):
        key = key.lower()
        if not key:
            return current_direction
        proposed = TEXT_DIRECTIONS.get(key[0])
    else:
        proposed = CURSES_DIRECTIONS.get(key)

    if proposed is None:
        return current_direction

    # Prevent reversing direction instantly
    if Point(-current_direction.y, -current_direction.x) == proposed:
        return current_direction
    return proposed


def play_curses(stdscr: "curses._CursesWindow") -> None:
    curses.curs_set(False)
    stdscr.nodelay(True)
    stdscr.keypad(True)

    snake: List[Point] = [Point(BOARD_HEIGHT // 2, BOARD_WIDTH // 2 + i) for i in range(2, -1, -1)]
    direction = Point(0, 1)
    food = random_food(snake)
    score = 0
    delay = INITIAL_DELAY

    while True:
        render_curses(stdscr, snake, food, score)
        key = stdscr.getch()
        direction = next_direction(direction, key)

        new_head = snake[0] + direction

        # Check collisions with walls
        if new_head.x <= 0 or new_head.x >= BOARD_WIDTH + 1 or new_head.y <= 0 or new_head.y >= BOARD_HEIGHT + 1:
            break

        # Check collisions with self
        if new_head in snake:
            break

        snake.insert(0, new_head)

        if new_head == food:
            score += 1
            food = random_food(snake)
            delay = max(MIN_DELAY, delay - SPEEDUP_STEP)
        else:
            snake.pop()

        curses.napms(delay)

    game_over(stdscr, score)


def play_text_mode() -> None:
    """Fallback text-mode implementation that works without curses."""

    snake: List[Point] = [Point(BOARD_HEIGHT // 2, BOARD_WIDTH // 2 + i) for i in range(2, -1, -1)]
    direction = Point(0, 1)
    food = random_food(snake)
    score = 0
    delay = INITIAL_DELAY

    print("当前环境不支持 curses，将使用简易文本模式运行。\n")

    while True:
        render_text(snake, food, score)
        try:
            user_input = input("方向 (W/A/S/D，回车保持，Q 退出): ").strip().lower()
        except EOFError:
            print()  # move to next line when Ctrl+D is pressed
            break
        except KeyboardInterrupt:
            print()
            break

        if user_input == "q":
            break

        direction = next_direction(direction, user_input or None)

        new_head = snake[0] + direction

        if new_head.x <= 0 or new_head.x >= BOARD_WIDTH + 1 or new_head.y <= 0 or new_head.y >= BOARD_HEIGHT + 1:
            break

        if new_head in snake:
            break

        snake.insert(0, new_head)

        if new_head == food:
            score += 1
            food = random_food(snake)
            delay = max(MIN_DELAY, delay - SPEEDUP_STEP)
        else:
            snake.pop()

        time.sleep(delay / 1000.0)

    render_text(snake, food, score)
    print(f"游戏结束！最终得分: {score}")


def game_over(stdscr: "curses._CursesWindow", score: int) -> None:
    """Display a game over message and wait for the user to exit."""

    stdscr.nodelay(False)
    msg = "Game Over!"
    stdscr.addstr(BOARD_HEIGHT // 2, (BOARD_WIDTH // 2) - len(msg) // 2, msg)
    stdscr.addstr(BOARD_HEIGHT // 2 + 1, (BOARD_WIDTH // 2) - 6, f"Score: {score}")
    stdscr.addstr(BOARD_HEIGHT // 2 + 3, (BOARD_WIDTH // 2) - 12, "Press any key to exit...")
    stdscr.refresh()
    stdscr.getch()


def main() -> None:
    if curses is not None and sys.stdin.isatty() and sys.stdout.isatty():
        curses.wrapper(play_curses)
    else:
        play_text_mode()


if __name__ == "__main__":
    main()
