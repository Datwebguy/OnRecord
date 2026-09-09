from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "static" / "brand" / "onrecord_x_article_cover.png"
LOGO = ROOT / "static" / "brand" / "onrecord_logo_dark.png"
WIDTH, HEIGHT = 1600, 900


def font(size, bold=False):
    candidates = [
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def rounded_panel(draw, box, fill, outline=None, width=1, radius=22):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def main():
    image = Image.new("RGB", (WIDTH, HEIGHT), (9, 11, 10))
    pixels = image.load()
    for y in range(HEIGHT):
        for x in range(WIDTH):
            glow = max(0, 1 - (((x - 1200) / 900) ** 2 + ((y - 120) / 520) ** 2))
            pixels[x, y] = (9 + int(10 * glow), 11 + int(17 * glow), 10 + int(8 * glow))

    glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse((980, -180, 1740, 580), fill=(213, 255, 0, 34))
    glow_draw.ellipse((-300, 500, 700, 1300), fill=(204, 41, 34, 20))
    glow = glow.filter(ImageFilter.GaussianBlur(90))
    image = Image.alpha_composite(image.convert("RGBA"), glow)
    draw = ImageDraw.Draw(image)

    # Fine archival grid.
    for x in range(0, WIDTH, 80):
        draw.line((x, 0, x, HEIGHT), fill=(255, 255, 255, 10), width=1)
    for y in range(0, HEIGHT, 80):
        draw.line((0, y, WIDTH, y), fill=(255, 255, 255, 10), width=1)

    # Brand mark.
    logo = Image.open(LOGO).convert("RGBA")
    logo.thumbnail((310, 75), Image.Resampling.LANCZOS)
    image.alpha_composite(logo, (92, 68))
    draw.text((98, 158), "DURABLE MEMORY FOR OPERATIONS", font=font(17, True), fill=(213, 255, 0, 225))

    # Main copy with mobile-safe margins.
    draw.text((92, 275), "NO RECORD.", font=font(94, True), fill=(239, 236, 225, 255))
    draw.text((92, 382), "NO ACTION.", font=font(94, True), fill=(213, 255, 0, 255))
    draw.text((98, 515), "Scout files evidence. Clerk verifies it.\nDelete memory — and the queue disappears.", font=font(27), fill=(204, 211, 200, 255), spacing=12)

    # Right-side visual: memory pipeline and deletion proof.
    panel_x, panel_y, panel_w, panel_h = 930, 215, 560, 455
    rounded_panel(draw, (panel_x, panel_y, panel_x + panel_w, panel_y + panel_h), (17, 22, 19, 220), (91, 105, 89, 180), 2)
    draw.text((975, 250), "LOAD-BEARING MEMORY", font=font(20, True), fill=(239, 236, 225, 255))

    cards = [(975, 320, "SCOUT", "writes evidence", (213, 255, 0)), (1190, 320, "SIBYL", "persists records", (239, 236, 225)), (975, 475, "CLERK", "recalls queue", (239, 236, 225))]
    for x, y, title, subtitle, color in cards:
        rounded_panel(draw, (x, y, x + 180, y + 92), (25, 31, 26, 245), color + (185,), 2, 16)
        draw.text((x + 18, y + 17), title, font=font(20, True), fill=color + (255,))
        draw.text((x + 18, y + 52), subtitle, font=font(15), fill=(191, 201, 188, 255))
    draw.line((1155, 366, 1180, 366), fill=(213, 255, 0, 230), width=4)
    draw.polygon([(1180, 366), (1168, 358), (1168, 374)], fill=(213, 255, 0, 230))
    draw.line((1280, 415, 1280, 462), fill=(213, 255, 0, 230), width=4)
    draw.polygon([(1280, 462), (1272, 450), (1288, 450)], fill=(213, 255, 0, 230))

    # Deletion receipt.
    rounded_panel(draw, (1190, 475, 1435, 567), (50, 19, 18, 245), (204, 41, 34, 220), 2, 16)
    draw.text((1210, 490), "DELETE MEMORY", font=font(18, True), fill=(255, 116, 90, 255))
    draw.text((1210, 523), "QUEUE 0  ·  NOT ON RECORD", font=font(13, True), fill=(239, 236, 225, 255))

    draw.text((92, 812), "SIBYL LABS HACKATHON  ·  BASE MAINNET 8453  ·  ONRECORD", font=font(16, True), fill=(157, 168, 151, 255))
    draw.line((92, 780, 1508, 780), fill=(213, 255, 0, 150), width=2)

    image.convert("RGB").save(OUT, quality=95, optimize=True)
    print(OUT)


if __name__ == "__main__":
    main()
