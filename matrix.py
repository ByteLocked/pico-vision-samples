import random, time
from picovision import PicoVision, PEN_RGB555


# === Display setup ===
WIDTH, HEIGHT = 320, 240

display = PicoVision(PEN_RGB555, WIDTH, HEIGHT)
display.set_font("bitmap8")

# === Colors ===
bg_pen = display.create_pen(0, 0, 0)
dim_green = display.create_pen(0, 80, 0)
bright_green = display.create_pen(100, 255, 100)
fade_green = display.create_pen(0, 30, 0)

# === Matrix parameters ===
FONT_W = 8
FONT_H = 8
COLS = WIDTH // FONT_W
ROWS = HEIGHT // FONT_H

# Each column has a y position (the head of the falling text)
drops = [random.randint(0, ROWS - 1) for _ in range(COLS)]
chars = [chr(i) for i in range(33, 127)]  # printable ASCII set

# === Animation loop ===
while True:
    display.set_pen(bg_pen)
    display.clear()

    for i in range(COLS):
        y = drops[i] * FONT_H

        # Draw bright leading character
        c = random.choice(chars)
        display.set_pen(bright_green)
        display.text(c, i * FONT_W, y, -1, 1)

        # Draw trailing faded characters for that column
        for trail in range(1, 6):
            yy = y - trail * FONT_H
            if yy < 0:
                break
            display.set_pen(dim_green if trail < 3 else fade_green)
            display.text(random.choice(chars), i * FONT_W, yy, -1, 1)

        # Move drop downward
        drops[i] += 1

        # Reset to top randomly to create varied lengths
        if drops[i] * FONT_H > HEIGHT or random.random() > 0.98:
            drops[i] = 0

    display.update()
    time.sleep(0.05)

