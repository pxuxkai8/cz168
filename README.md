# cz168

贪吃蛇小游戏，使用 Python `curses` 编写。

## 运行

确保安装了 Python 3，并且在支持 `curses` 的终端中运行：

```bash
python snake.py
```

使用方向键或 WASD 控制蛇移动，碰到墙壁或自己的身体时游戏结束。

如果当前环境不支持 `curses`（如在 Windows 未安装 `windows-curses`、或在简单的在线终端中），脚本会自动退回到文本模式，使用 `W/A/S/D` 加回车即可缓步体验游戏。
