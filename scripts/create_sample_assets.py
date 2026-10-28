"""Generate high-quality aesthetic sample property images for Property Studio AI.

Creates 5 sample images matching the Green Valley Residency specification:
1. 01_exterior.jpg (Modern residential building exterior)
2. 02_living_room.jpg (Contemporary living lounge with warm sunlight)
3. 03_modular_kitchen.jpg (Modern modular kitchen with granite and wood finishes)
4. 04_bedroom.jpg (Spacious bedroom suite)
5. 05_balcony_view.jpg (Scenic balcony with panoramic garden view)
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "assets" / "sample_images"
WIDTH = 1280
HEIGHT = 720


def generate_exterior_image() -> Image.Image:
    """Aesthetic modern luxury residential facade with sky and greenery."""
    img = Image.new("RGB", (WIDTH, HEIGHT), (200, 225, 245))
    draw = ImageDraw.Draw(img)

    # Sky gradient
    for y in range(HEIGHT // 2):
        r = int(120 + 85 * (y / (HEIGHT // 2)))
        g = int(170 + 60 * (y / (HEIGHT // 2)))
        b = int(220 + 25 * (y / (HEIGHT // 2)))
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))

    # Sun glow
    draw.ellipse([(850, 60), (1000, 210)], fill=(255, 248, 220, 180))

    # Main Building Structure (Modern geometric architecture)
    draw.rectangle([(250, 160), (980, 650)], fill=(235, 238, 242))
    
    # Wooden accent panels
    for i in range(4):
        y_top = 220 + i * 100
        draw.rectangle([(300, y_top), (480, y_top + 75)], fill=(160, 105, 60))
        # Glass balconies
        draw.rectangle([(520, y_top + 10), (940, y_top + 75)], fill=(180, 215, 235))
        draw.rectangle([(520, y_top + 10), (940, y_top + 15)], fill=(80, 95, 110))

    # Architectural columns
    draw.rectangle([(280, 150), (300, 650)], fill=(100, 110, 125))
    draw.rectangle([(960, 150), (980, 650)], fill=(100, 110, 125))

    # Foreground landscaped lawn
    draw.rectangle([(0, 580), (WIDTH, HEIGHT)], fill=(55, 125, 60))
    for x in range(0, WIDTH, 35):
        h = 50 + (x % 3) * 20
        draw.ellipse([(x - 20, 560 - h), (x + 30, 620)], fill=(40, 105, 45))

    # Paved driveway
    draw.polygon([(450, 720), (580, 580), (700, 580), (830, 720)], fill=(185, 190, 195))
    
    return img.filter(ImageFilter.SMOOTH_MORE)


def generate_living_room_image() -> Image.Image:
    """Spacious contemporary living room with large glass windows and modern sofa."""
    img = Image.new("RGB", (WIDTH, HEIGHT), (245, 243, 238))
    draw = ImageDraw.Draw(img)

    # Warm hardwood flooring
    for y in range(430, HEIGHT):
        shade = 110 + int(30 * ((y - 430) / (HEIGHT - 430)))
        draw.line([(0, y), (WIDTH, y)], fill=(shade + 30, shade, shade - 30))

    # Floor plank lines
    for x in range(-200, WIDTH + 400, 90):
        draw.line([(x, 430), (x + 120, HEIGHT)], fill=(115, 80, 50), width=2)

    # Feature accent wall (Nordic teal/slate)
    draw.rectangle([(0, 0), (750, 430)], fill=(238, 236, 230))
    draw.rectangle([(100, 60), (700, 390)], fill=(52, 73, 94))

    # Minimalist abstract artwork on wall
    draw.rectangle([(220, 110), (420, 290)], fill=(220, 180, 110))
    draw.ellipse([(260, 140), (360, 240)], fill=(180, 80, 60))
    draw.line([(220, 250), (420, 150)], fill=(30, 30, 30), width=4)

    # Modern Sectional Sofa
    draw.rounded_rectangle([(180, 380), (780, 560)], radius=25, fill=(210, 215, 220))
    draw.rounded_rectangle([(180, 460), (780, 580)], radius=15, fill=(180, 185, 190))
    # Cushions
    draw.rounded_rectangle([(230, 410), (330, 480)], radius=10, fill=(218, 165, 32))
    draw.rounded_rectangle([(360, 410), (460, 480)], radius=10, fill=(70, 90, 105))

    # Large floor-to-ceiling balcony glass doors (Right side)
    draw.rectangle([(800, 40), (1220, 500)], fill=(195, 225, 245))
    draw.line([(1010, 40), (1010, 500)], fill=(80, 90, 100), width=8)
    draw.rectangle([(795, 35), (1225, 505)], outline=(60, 70, 80), width=6)

    # Lush greenery visible through glass window
    for x in range(820, 1200, 45):
        draw.ellipse([(x, 320), (x + 80, 490)], fill=(45, 120, 55))

    # Designer Coffee Table
    draw.ellipse([(450, 550), (750, 640)], fill=(40, 42, 45))
    draw.ellipse([(465, 560), (735, 630)], fill=(65, 68, 72))

    return img.filter(ImageFilter.SMOOTH)


def generate_modular_kitchen_image() -> Image.Image:
    """Modern modular kitchen with cabinets, island, and quartz countertops."""
    img = Image.new("RGB", (WIDTH, HEIGHT), (242, 242, 244))
    draw = ImageDraw.Draw(img)

    # Floor (Large format ceramic grey tiles)
    draw.rectangle([(0, 460), (WIDTH, HEIGHT)], fill=(215, 215, 218))
    for x in range(0, WIDTH, 160):
        draw.line([(x, 460), (x, HEIGHT)], fill=(180, 180, 185), width=2)
    for y in range(460, HEIGHT, 80):
        draw.line([(0, y), (WIDTH, y)], fill=(180, 180, 185), width=2)

    # Upper overhead cabinets (Matte White & Warm Oak)
    draw.rectangle([(150, 60), (1130, 220)], fill=(255, 255, 255))
    for x in range(150, 1130, 163):
        draw.line([(x, 60), (x, 220)], fill=(210, 210, 215), width=2)
        draw.line([(x + 20, 205), (x + 70, 205)], fill=(160, 160, 165), width=3)

    # Subway tile backsplash
    draw.rectangle([(150, 220), (1130, 360)], fill=(245, 246, 248))
    for y in range(220, 360, 25):
        draw.line([(150, y), (1130, y)], fill=(225, 228, 232), width=1)
        offset = 30 if (y // 25) % 2 else 0
        for x in range(150 + offset, 1130, 60):
            draw.line([(x, y), (x, y + 25)], fill=(225, 228, 232), width=1)

    # Granite countertop
    draw.rectangle([(120, 360), (1160, 395)], fill=(45, 48, 52))

    # Base cabinets (Rich Charcoal / Navy)
    draw.rectangle([(150, 395), (1130, 560)], fill=(35, 45, 60))
    for x in range(150, 1130, 196):
        draw.line([(x, 395), (x, 560)], fill=(25, 32, 45), width=3)
        # Stainless steel handles
        draw.line([(x + 30, 420), (x + 130, 420)], fill=(220, 225, 230), width=4)

    # Kitchen Island Bar in foreground
    draw.polygon([(350, 510), (930, 510), (980, 660), (300, 660)], fill=(250, 250, 252))
    draw.polygon([(300, 660), (980, 660), (960, 720), (320, 720)], fill=(160, 105, 60))

    return img.filter(ImageFilter.SMOOTH)


def generate_bedroom_image() -> Image.Image:
    """Inviting modern bedroom with king bed, accent wall, and ambient lighting."""
    img = Image.new("RGB", (WIDTH, HEIGHT), (240, 238, 235))
    draw = ImageDraw.Draw(img)

    # Dark Oak Wood flooring
    draw.rectangle([(0, 450), (WIDTH, HEIGHT)], fill=(125, 85, 55))
    for x in range(0, WIDTH, 120):
        draw.line([(x, 450), (x + 50, HEIGHT)], fill=(100, 65, 40), width=2)

    # Headboard Feature Wall with geometric vertical slats
    draw.rectangle([(150, 80), (1130, 450)], fill=(60, 68, 78))
    for x in range(170, 1110, 28):
        draw.line([(x, 80), (x, 450)], fill=(180, 130, 85), width=4)

    # Modern King Bed Headboard
    draw.rounded_rectangle([(300, 280), (980, 470)], radius=20, fill=(210, 205, 195))

    # Bed Mattress & Pillows
    draw.rounded_rectangle([(280, 410), (1000, 640)], radius=25, fill=(250, 250, 252))
    # Pillows
    draw.rounded_rectangle([(340, 360), (510, 430)], radius=12, fill=(240, 240, 245))
    draw.rounded_rectangle([(550, 360), (720, 430)], radius=12, fill=(240, 240, 245))
    draw.rounded_rectangle([(760, 360), (930, 430)], radius=12, fill=(218, 165, 32))

    # Duvet / Comforter
    draw.rounded_rectangle([(280, 460), (1000, 640)], radius=15, fill=(180, 190, 200))
    # Gold decorative runner
    draw.rectangle([(280, 540), (1000, 580)], fill=(218, 165, 32))

    # Nightstands & warm lamps
    draw.rectangle([(160, 390), (280, 490)], fill=(45, 45, 48))
    draw.rectangle([(1000, 390), (1120, 490)], fill=(45, 45, 48))
    # Lamp glow
    draw.ellipse([(190, 320), (250, 380)], fill=(255, 230, 150))
    draw.ellipse([(1030, 320), (1090, 380)], fill=(255, 230, 150))

    return img.filter(ImageFilter.SMOOTH)


def generate_balcony_image() -> Image.Image:
    """Spacious scenic balcony overlooking lush Chandigarh tree canopy and distant hills."""
    img = Image.new("RGB", (WIDTH, HEIGHT), (160, 205, 240))
    draw = ImageDraw.Draw(img)

    # Blue sky with soft clouds
    for y in range(300):
        b = int(210 + 35 * (1 - y / 300))
        draw.line([(0, y), (WIDTH, y)], fill=(130, 185, b))
    
    # Soft clouds
    for cx, cy, rad in [(300, 100, 80), (420, 80, 110), (850, 130, 95)]:
        draw.ellipse([(cx - rad, cy - rad // 2), (cx + rad, cy + rad // 2)], fill=(250, 252, 255, 200))

    # Distant scenic green hills
    draw.ellipse([(50, 240), (750, 460)], fill=(75, 120, 85))
    draw.ellipse([(600, 220), (1350, 470)], fill=(65, 110, 75))

    # Lush tree canopy in midground
    for x in range(-50, WIDTH + 50, 40):
        h = 80 + (x * 7 % 60)
        draw.ellipse([(x - 30, 360 - h), (x + 50, 450)], fill=(35, 95, 40))

    # Balcony Glass Railing
    draw.rectangle([(80, 400), (WIDTH - 80, 570)], fill=(215, 235, 245))
    draw.rectangle([(70, 390), (WIDTH - 70, 410)], fill=(65, 75, 85))  # Top rail
    draw.rectangle([(70, 560), (WIDTH - 70, 580)], fill=(65, 75, 85))  # Bottom rail

    # Balcony Timber Deck Flooring
    draw.polygon([(0, 570), (WIDTH, 570), (WIDTH, HEIGHT), (0, HEIGHT)], fill=(145, 95, 55))
    for y in range(570, HEIGHT, 25):
        draw.line([(0, y), (WIDTH, y)], fill=(110, 70, 40), width=2)

    # Elegant outdoor patio lounge chairs and coffee table
    draw.rounded_rectangle([(250, 480), (380, 620)], radius=15, fill=(50, 55, 60))
    draw.rounded_rectangle([(880, 480), (1010, 620)], radius=15, fill=(50, 55, 60))
    draw.ellipse([(560, 550), (720, 630)], fill=(230, 235, 240))
    # Plant pot on table
    draw.rectangle([(625, 530), (655, 560)], fill=(175, 90, 60))
    draw.ellipse([(615, 495), (665, 535)], fill=(40, 130, 50))

    return img.filter(ImageFilter.SMOOTH)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    images = [
        ("01_exterior.jpg", generate_exterior_image()),
        ("02_living_room.jpg", generate_living_room_image()),
        ("03_modular_kitchen.jpg", generate_modular_kitchen_image()),
        ("04_bedroom.jpg", generate_bedroom_image()),
        ("05_balcony_view.jpg", generate_balcony_image()),
    ]
    for filename, img in images:
        out_path = OUTPUT_DIR / filename
        img.save(out_path, "JPEG", quality=95)
        print(f"Generated {out_path.name} ({img.size[0]}x{img.size[1]})")


if __name__ == "__main__":
    main()

