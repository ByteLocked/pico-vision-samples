import time, random
from picovision import PicoVision, PEN_RGB555
from pimoroni import Button
# === Display setup ===
WIDTH, HEIGHT = 720, 480
display = PicoVision(PEN_RGB555, WIDTH, HEIGHT)
display.set_font("bitmap8")

# === Colors ===
bg_pen        = display.create_pen(0, 0, 10)
player_pen    = display.create_pen(100, 255, 100)
bullet_pen    = display.create_pen(255, 255, 255)
enemy_pen     = display.create_pen(255, 100, 100)
text_pen      = display.create_pen(255, 255, 180)
explosion_pen = display.create_pen(255, 255, 0)

# === Game constants ===
PLAYER_W, PLAYER_H = 32, 12
PLAYER_SPEED = 6
BULLET_SPEED = 10
ENEMY_W, ENEMY_H = 24, 16
ENEMY_COLS = 8
ENEMY_ROWS = 4
ENEMY_X_SPACING = 60
ENEMY_Y_SPACING = 40
ENEMY_SPEED = 2
ENEMY_DROP = 20

# === Game state ===
player_x = WIDTH//2 - PLAYER_W//2
player_y = HEIGHT - 60
bullets = []  # list of (x,y)
enemies = []
enemy_dx = ENEMY_SPEED
score = 0
game_over = False

# === Create enemy formation ===
for row in range(ENEMY_ROWS):
    for col in range(ENEMY_COLS):
        x = 100 + col * ENEMY_X_SPACING
        y = 60 + row * ENEMY_Y_SPACING
        enemies.append([x, y, True])  # [x, y, alive]

# === Input helper ===
def btn(name):
    try:
        return getattr(display, name)()
    except:
        return False

# === Drawing ===
def draw():
    display.set_pen(bg_pen)
    display.clear()

    # Player
    display.set_pen(player_pen)
    display.rectangle(int(player_x), int(player_y), PLAYER_W, PLAYER_H)

    # Bullets
    display.set_pen(bullet_pen)
    for (bx, by) in bullets:
        display.rectangle(int(bx), int(by), 3, 10)

    # Enemies
    display.set_pen(enemy_pen)
    for e in enemies:
        if e[2]:
            display.rectangle(int(e[0]), int(e[1]), ENEMY_W, ENEMY_H)

    # UI
    display.set_pen(text_pen)
    display.text(f"Score: {score}", 20, 10, -1, 2)

    if game_over:
        display.set_pen(explosion_pen)
        display.text("GAME OVER", WIDTH//2 - 80, HEIGHT//2 - 20, -1, 3)
        display.text("Press A to Restart", WIDTH//2 - 100, HEIGHT//2 + 20, -1, 2)

    display.update()

# === Reset function ===
def reset_game():
    global player_x, bullets, enemies, enemy_dx, score, game_over
    player_x = WIDTH//2 - PLAYER_W//2
    bullets = []
    enemies.clear()
    for row in range(ENEMY_ROWS):
        for col in range(ENEMY_COLS):
            x = 100 + col * ENEMY_X_SPACING
            y = 60 + row * ENEMY_Y_SPACING
            enemies.append([x, y, True])
    enemy_dx = ENEMY_SPEED
    score = 0
    game_over = False

# === Main loop ===
last_fire = 0
while True:
    if game_over:
        draw()
        if btn("is_button_a_pressed"):
            reset_game()
        time.sleep(0.05)
        continue

    # --- Input ---
    if btn("is_button_x_pressed"):     # move left
        player_x -= PLAYER_SPEED
    if Button(9, invert=True).read():     # move right
        player_x += PLAYER_SPEED
    player_x = max(10, min(WIDTH - PLAYER_W - 10, player_x))

    # Fire bullet
    if btn("is_button_a_pressed"):
        now = time.ticks_ms()
        if time.ticks_diff(now, last_fire) > 300:  # rate limit
            bullets.append([player_x + PLAYER_W//2 - 1, player_y - 12])
            last_fire = now

    # --- Update bullets ---
    new_bullets = []
    for (bx, by) in bullets:
        by -= BULLET_SPEED
        if by > 0:
            new_bullets.append([bx, by])
    bullets = new_bullets

    # --- Move enemies ---
    hit_edge = False
    for e in enemies:
        if e[2]:
            e[0] += enemy_dx
            if e[0] <= 10 or e[0] + ENEMY_W >= WIDTH - 10:
                hit_edge = True
    if hit_edge:
        enemy_dx = -enemy_dx
        for e in enemies:
            e[1] += ENEMY_DROP

    # --- Bullet collisions ---
    for b in bullets[:]:
        bx, by = b
        for e in enemies:
            if not e[2]:
                continue
            ex, ey = e[0], e[1]
            if (ex < bx < ex + ENEMY_W) and (ey < by < ey + ENEMY_H):
                e[2] = False
                score += 10
                bullets.remove(b)
                break

    # --- Check lose condition ---
    for e in enemies:
        if e[2] and e[1] + ENEMY_H >= player_y:
            game_over = True
            break

    # --- Check win condition ---
    if all(not e[2] for e in enemies):
        game_over = True

    draw()
    time.sleep(0.02)

