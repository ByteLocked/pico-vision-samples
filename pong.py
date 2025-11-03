import time, random
from picovision import PicoVision, PEN_RGB555
import machine
from pimoroni import Button
# === Display setup ===
WIDTH, HEIGHT = 720, 480
display = PicoVision(PEN_RGB555, WIDTH, HEIGHT)

# === Colors ===
bg_pen = display.create_pen(0, 0, 0)
paddle_pen = display.create_pen(255, 255, 255)
ball_pen = display.create_pen(255, 255, 255)
text_pen = display.create_pen(255, 255, 100)

# === Game settings ===
PADDLE_W = 8
PADDLE_H = 60
BALL_SIZE = 8
PLAYER_X = 20
CPU_X = WIDTH - 20 - PADDLE_W
PADDLE_SPEED = 6
CPU_SPEED = 4
BALL_SPEED = 5

# === State ===
player_y = HEIGHT // 2 - PADDLE_H // 2
cpu_y = HEIGHT // 2 - PADDLE_H // 2
ball_x = WIDTH // 2
ball_y = HEIGHT // 2
ball_dx = random.choice([-1, 1]) * BALL_SPEED
ball_dy = random.choice([-1, 1]) * BALL_SPEED
player_score = 0
cpu_score = 0

# === Input setup (use up/down buttons if available) ===
up_btn = Button(9, invert=True).read
down_btn = machine.Pin(14, machine.Pin.IN, machine.Pin.PULL_UP)

def draw():
    display.set_pen(bg_pen)
    display.clear()

    # Middle divider
    display.set_pen(paddle_pen)
    for y in range(0, HEIGHT, 20):
        display.rectangle(WIDTH//2 - 2, y, 4, 10)

    # Draw paddles
    display.rectangle(PLAYER_X, int(player_y), PADDLE_W, PADDLE_H)
    display.rectangle(CPU_X, int(cpu_y), PADDLE_W, PADDLE_H)

    # Draw ball
    display.set_pen(ball_pen)
    display.rectangle(int(ball_x), int(ball_y), BALL_SIZE, BALL_SIZE)

    # Scores
    display.set_pen(text_pen)
    display.text(str(player_score), WIDTH//2 - 60, 20, -1, 3)
    display.text(str(cpu_score), WIDTH//2 + 40, 20, -1, 3)

    display.update()

def reset_ball(direction):
    global ball_x, ball_y, ball_dx, ball_dy
    ball_x = WIDTH // 2
    ball_y = HEIGHT // 2
    ball_dx = direction * BALL_SPEED
    ball_dy = random.choice([-1, 1]) * BALL_SPEED

# === Game loop ===
while True:
    # --- Player input ---
    if display.is_button_a_pressed():
        player_y -= PADDLE_SPEED
    if display.is_button_x_pressed():
        player_y += PADDLE_SPEED

    # Clamp player paddle
    player_y = max(0, min(HEIGHT - PADDLE_H, player_y))

    # --- CPU AI ---
    if ball_y + BALL_SIZE/2 < cpu_y + PADDLE_H/2:
        cpu_y -= CPU_SPEED
    elif ball_y + BALL_SIZE/2 > cpu_y + PADDLE_H/2:
        cpu_y += CPU_SPEED
    cpu_y = max(0, min(HEIGHT - PADDLE_H, cpu_y))

    # --- Move ball ---
    ball_x += ball_dx
    ball_y += ball_dy

    # Bounce off top/bottom
    if ball_y <= 0 or ball_y + BALL_SIZE >= HEIGHT:
        ball_dy = -ball_dy

    # Paddle collisions
    if (PLAYER_X < ball_x < PLAYER_X + PADDLE_W and
        player_y < ball_y + BALL_SIZE and ball_y < player_y + PADDLE_H):
        ball_dx = abs(ball_dx)
    elif (CPU_X < ball_x + BALL_SIZE < CPU_X + PADDLE_W and
          cpu_y < ball_y + BALL_SIZE and ball_y < cpu_y + PADDLE_H):
        ball_dx = -abs(ball_dx)

    # Scoring
    if ball_x < 0:
        cpu_score += 1
        reset_ball(1)
    elif ball_x > WIDTH:
        player_score += 1
        reset_ball(-1)

    draw()
    time.sleep(0.02)

