"""Generate the README banner for i-have-autism.

Design follows the repo's own rules: no decoration that carries no meaning.
The banner shows the one idea — literal output plus exacting code — in the
skill's own voice, and uses the before/after contrast the README already makes.
"""
from PIL import Image, ImageDraw, ImageFont

W, H = 1280, 400
BG = (13, 17, 23)            # near-black, GitHub dark
FG = (230, 237, 243)
MUTED = (139, 148, 158)
ACCENT = (88, 166, 255)      # GitHub blue
RULE = (48, 54, 61)
STRIKE = (248, 81, 73)       # the removed line

MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
MONO_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

f_title = ImageFont.truetype(MONO_B, 60)
f_sub = ImageFont.truetype(SANS, 23)
f_line = ImageFont.truetype(MONO, 21)
f_tag = ImageFont.truetype(MONO, 18)

M = 64
d.text((M, 52), "i-have-autism", font=f_title, fill=FG)

# accent rule under the title
d.rectangle([M, 128, M + 232, 132], fill=ACCENT)

d.text((M, 148), "Literal. Explicit. Direct. And exacting about the code.", font=f_sub, fill=FG)

# the before / after micro-example, the repo's central contrast
y = 205
before = 'Great question!  Hope this helps!'
d.text((M, y), before, font=f_line, fill=MUTED)
# strike it through — it is the thing the skill removes
bw = d.textlength(before, font=f_line)
d.line([(M, y + 16), (M + bw, y + 16)], fill=STRIKE, width=2)

after = 'Edit src/auth.ts:42.  Run npm test -- auth.spec.ts.'
d.text((M, y + 40), after, font=f_line, fill=FG)

# bottom tag line
d.line([(M, 300), (W - M, 300)], fill=RULE, width=1)
d.text((M, 318), "readability   maintainability   correctness", font=f_tag, fill=ACCENT)
d.text((M, 348), "no compromise on quality", font=f_tag, fill=MUTED)

img.save("/root/i-have-autism/assets/banner.png", "PNG")
print("saved /root/i-have-autism/assets/banner.png", img.size)
