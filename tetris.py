# Tetris for PicoVision (MicroPython)
# Buttons (PicoVision helpers):
#   B = left, X = right, Y = rotate, A = soft drop, A+Y = hard drop
import time, random
from picovision import PicoVision, PEN_RGB555
from pimoroni import Button
# === Display setup ===
WIDTH, HEIGHT = 720, 480
display = PicoVision(PEN_RGB555, WIDTH, HEIGHT)
display.set_font("bitmap8")

# === Board geometry ===
COLS, ROWS = 10, 20
CELL = 20
BOARD_W = COLS * CELL              # 200
BOARD_H = ROWS * CELL              # 400
BOARD_X = (WIDTH - BOARD_W) // 2   # center horizontally
BOARD_Y = (HEIGHT - BOARD_H) // 2  # center vertically

# === Colors ===
bg_pen        = display.create_pen(0, 0, 0)
grid_pen      = display.create_pen(20, 30, 20)
border_pen    = display.create_pen(90, 140, 100)
text_pen      = display.create_pen(255, 255, 180)

# Tetromino colors (I, J, L, O, S, T, Z)
piece_pens = [
    display.create_pen( 50, 220, 220),  # I
    display.create_pen( 60,  80, 220),  # J
    display.create_pen(220, 140,  60),  # L
    display.create_pen(240, 230,  60),  # O
    display.create_pen( 60, 220,  80),  # S
    display.create_pen(200,  80, 220),  # T
    display.create_pen(220,  60,  60),  # Z
]

# === Tetromino shapes (4x4) ===
# Each shape is a list of rotations; each rotation is a list of (x, y) block coordinates.
TETROMINOES = {
    "I": [
        [(0,1),(1,1),(2,1),(3,1)],
        [(2,0),(2,1),(2,2),(2,3)],
        [(0,2),(1,2),(2,2),(3,2)],
        [(1,0),(1,1),(1,2),(1,3)],
    ],
    "J": [
        [(0,0),(0,1),(1,1),(2,1)],
        [(1,0),(2,0),(1,1),(1,2)],
        [(0,1),(1,1),(2,1),(2,2)],
        [(1,0),(1,1),(0,2),(1,2)],
    ],
    "L": [
        [(2,0),(0,1),(1,1),(2,1)],
        [(1,0),(1,1),(1,2),(2,2)],
        [(0,1),(1,1),(2,1),(0,2)],
        [(0,0),(1,0),(1,1),(1,2)],
    ],
    "O": [
        [(1,0),(2,0),(1,1),(2,1)],
        [(1,0),(2,0),(1,1),(2,1)],
        [(1,0),(2,0),(1,1),(2,1)],
        [(1,0),(2,0),(1,1),(2,1)],
    ],
    "S": [
        [(1,0),(2,0),(0,1),(1,1)],
        [(1,0),(1,1),(2,1),(2,2)],
        [(1,1),(2,1),(0,2),(1,2)],
        [(0,0),(0,1),(1,1),(1,2)],
    ],
    "T": [
        [(1,0),(0,1),(1,1),(2,1)],
        [(1,0),(1,1),(2,1),(1,2)],
        [(0,1),(1,1),(2,1),(1,2)],
        [(1,0),(0,1),(1,1),(1,2)],
    ],
    "Z": [
        [(0,0),(1,0),(1,1),(2,1)],
        [(2,0),(1,1),(2,1),(1,2)],
        [(0,1),(1,1),(1,2),(2,2)],
        [(1,0),(0,1),(1,1),(0,2)],
    ]
}
ORDER = ["I","J","L","O","S","T","Z"]

# === Game state ===
board = [[-1 for _ in range(COLS)] for _ in range(ROWS)]  # -1 = empty else index 0..6
score = 0
level = 1
lines_cleared = 0

# Bag randomizer
def new_bag():
    bag = ORDER[:]
    # Simple Fisher–Yates shuffle for MicroPython
    for i in range(len(bag) - 1, 0, -1):
        j = random.randint(0, i)
        bag[i], bag[j] = bag[j], bag[i]
    return bag


bag = new_bag()

def spawn_piece():
    global current, cur_shape, cur_rot, cur_x, cur_y, cur_color
    if not bag:
        refill_bag()
    cur_shape = bag.pop()
    current = TETROMINOES[cur_shape]
    cur_rot = 0
    cur_x = COLS//2 - 2
    cur_y = 0
    cur_color = piece_pens[ORDER.index(cur_shape)]
    if collides(cur_x, cur_y, cur_rot):
        return False
    return True

def refill_bag():
    global bag
    bag = new_bag()

def collides(nx, ny, nrot):
    shape = current[nrot]
    for (bx, by) in shape:
        x = nx + bx
        y = ny + by
        if x < 0 or x >= COLS or y < 0 or y >= ROWS:
            return True
        if board[y][x] != -1:
            return True
    return False

def lock_piece():
    shape = current[cur_rot]
    color_idx = ORDER.index(cur_shape)
    for (bx, by) in shape:
        x = cur_x + bx
        y = cur_y + by
        if 0 <= x < COLS and 0 <= y < ROWS:
            board[y][x] = color_idx

def clear_lines():
    global board, score, lines_cleared, level
    new_rows = []
    cleared = 0
    for row in board:
        if all(cell != -1 for cell in row):
            cleared += 1
        else:
            new_rows.append(row)
    while len(new_rows) < ROWS:
        new_rows.insert(0, [-1]*COLS)
    board = new_rows
    if cleared:
        lines_cleared += cleared
        # Simple scoring: 100/300/500/800 per 1/2/3/4 lines
        add = [0,100,300,500,800][cleared]
        score += add * level
        level = 1 + lines_cleared // 10

def rotate():
    global cur_rot
    nrot = (cur_rot + 1) % 4
    # Try simple wall kicks: right, left, up
    for dx, dy in [(0,0),(1,0),(-1,0),(0,-1)]:
        if not collides(cur_x+dx, cur_y+dy, nrot):
            cur_rot = nrot
            return

def move(dx):
    global cur_x
    if not collides(cur_x + dx, cur_y, cur_rot):
        cur_x += dx

def soft_drop():
    global cur_y
    if not collides(cur_x, cur_y + 1, cur_rot):
        cur_y += 1
        return True
    return False

def hard_drop():
    while soft_drop():
        pass
    lock_piece()
    clear_lines()
    return spawn_piece()

# === Input handling with simple edge/hold repeat ===
prev_left = prev_right = prev_rot = prev_soft = False
left_repeat_t = right_repeat_t = 0
REPEAT_DELAY = 180   # ms before auto-repeat
REPEAT_RATE  = 45    # ms between repeats

def btn(what):
    # Safely call PicoVision helpers if present; else False
    try:
        return getattr(display, what)()
    except:
        return False

def get_input():
    global prev_left, prev_right, prev_rot, prev_soft
    global left_repeat_t, right_repeat_t

    now = time.ticks_ms()

    b_left  = btn("is_button_a_pressed")   # B -> left
    b_right = btn("is_button_x_pressed")   # X -> right
    b_rot   = Button(9, invert=True).read()
    

    # Left with auto-repeat
    moved_left = False
    if b_left and not prev_left:
        move(-1)
        left_repeat_t = now + REPEAT_DELAY
        moved_left = True
    elif b_left and prev_left and time.ticks_diff(now, left_repeat_t) >= 0:
        move(-1)
        left_repeat_t = now + REPEAT_RATE
        moved_left = True
    prev_left = b_left

    # Right with auto-repeat
    moved_right = False
    if b_right and not prev_right:
        move(+1)
        right_repeat_t = now + REPEAT_DELAY
        moved_right = True
    elif b_right and prev_right and time.ticks_diff(now, right_repeat_t) >= 0:
        move(+1)
        right_repeat_t = now + REPEAT_RATE
        moved_right = True
    prev_right = b_right

    # Rotate (edge)
    if b_rot and not prev_rot:
        rotate()
    prev_rot = b_rot

    # Soft drop (held speeds gravity)
    soft = b_soft

    # Optional: Hard drop if A+Y together
    hard = b_soft and b_rot

    return soft, hard, moved_left or moved_right

# === Drawing ===
def draw_cell(px, py, pen):
    display.set_pen(pen)
    display.rectangle(BOARD_X + px*CELL, BOARD_Y + py*CELL, CELL-1, CELL-1)

def draw_board():
    # Background
    display.set_pen(bg_pen)
    display.clear()

    # Border
    display.set_pen(border_pen)
    display.rectangle(BOARD_X-2, BOARD_Y-2, BOARD_W+4, BOARD_H+4)

    # Grid
    display.set_pen(grid_pen)
    for r in range(ROWS):
        for c in range(COLS):
            display.rectangle(BOARD_X + c*CELL, BOARD_Y + r*CELL, CELL-1, CELL-1)

    # Locked cells
    for r in range(ROWS):
        for c in range(COLS):
            idx = board[r][c]
            if idx != -1:
                draw_cell(c, r, piece_pens[idx])

    # Active piece
    shape = current[cur_rot]
    for (bx, by) in shape:
        x = cur_x + bx
        y = cur_y + by
        if 0 <= x < COLS and 0 <= y < ROWS:
            draw_cell(x, y, cur_color)

    # UI text
    display.set_pen(text_pen)
    display.text(f"Score: {score}", BOARD_X + BOARD_W + 16, BOARD_Y + 10, -1, 2)
    display.text(f"Level: {level}", BOARD_X + BOARD_W + 16, BOARD_Y + 40, -1, 2)
    display.text("B/L  X/R  Y=Rot  A=Drop", BOARD_X, BOARD_Y + BOARD_H + 8, -1, 1)

    display.update()

# === Game init ===
if not spawn_piece():
    # immediate game over if spawn blocked
    pass

# Gravity timing (speeds up with level)
def gravity_interval_ms():
    # Classic-ish curve: faster with level. Tweak as desired.
    # Starts ~700ms, speeds up to ~90ms by level ~10
    base = max(90, 700 - (level-1)*60)
    return base

fall_next = time.ticks_ms() + gravity_interval_ms()

# === Main loop ===
while True:
    soft, hard, _ = get_input()

    if hard:
        if not hard_drop():
            # Game over
            display.set_pen(bg_pen)
            display.clear()
            display.set_pen(text_pen)
            display.text("GAME OVER", BOARD_X + 24, BOARD_Y + BOARD_H//2 - 10, -1, 3)
            display.text(f"Score: {score}", BOARD_X + 48, BOARD_Y + BOARD_H//2 + 30, -1, 2)
            display.update()
            while True:
                time.sleep(0.05)

        fall_next = time.ticks_ms() + gravity_interval_ms()

    # Gravity tick (faster while holding soft drop)
    now = time.ticks_ms()
    interval = gravity_interval_ms()
    if soft:
        interval //= 8  # accelerate when A held

    if time.ticks_diff(now, fall_next) >= 0:
        if not soft_drop():
            # could not move down -> lock and spawn
            lock_piece()
            clear_lines()
            if not spawn_piece():
                display.set_pen(bg_pen)
                display.clear()
                display.set_pen(text_pen)
                display.text("GAME OVER", BOARD_X + 24, BOARD_Y + BOARD_H//2 - 10, -1, 3)
                display.text(f"Score: {score}", BOARD_X + 48, BOARD_Y + BOARD_H//2 + 30, -1, 2)
                display.update()
                while True:
                    time.sleep(0.05)
        fall_next = now + interval

    draw_board()
    time.sleep(0.01)

