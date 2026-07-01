import freetype
import numpy as np
import cv2

# Global container for curve data
curve_data = []

precision = 0.1

# Callback functions for outline decomposition
def move_to(a, ctx):
    print(len(ctx), "move_to", a.x, a.y)
    ctx.append((a.x, a.y))
    # ctx.append("M {} {}".format(a.x, a.y))

def line_to(a, ctx):
    # ctx.append((a.x, a.y))
    p0 = np.array(ctx[-1])
    p1 = np.array([a.x, a.y])
    t = 0.0
    while t - 1 < 0:
        pt = p0 + (t*(p1-p0))
        t += precision 
        q = map(int,[*pt])
        q = list(q)
        ctx.append(q)
    # ctx.append("L {} {}".format(a.x, a.y))

def conic_to(a, b, ctx):
    p0 = np.array(ctx[-1])
    p1 = np.array([a.x, a.y])
    p2 = np.array([b.x, b.y])

    t = 0.0
    while t - 1 < 0:
        pt = ((1-t)**2)*p0 + (2*(1 - t)*t*p1) + ((t**2)*p2)
        t += precision * 3
        q = map(int,[*pt])
        q = list(q)
        ctx.append(q)
        # ctx.append("L {},{}".format(*q))

def cubic_to(a, b, c, ctx):
    ctx.append("C {},{} {},{} {},{}".format(a.x, a.y, b.x, b.y, c.x, c.y))


# Load the font with a 4x scale (instead of 64x) and avoid bitmap glyphs.
face = freetype.Face("./JetBrainsMonoNerdFontMono-Regular.ttf")
# Use FT_LOAD_NO_HINTING and FT_LOAD_NO_BITMAP to force outline data.
face.set_char_size(50 * 4)
char = "S"  # Try "A" if "S" still returns no outline.
face.load_char(char, freetype.FT_LOAD_DEFAULT | freetype.FT_LOAD_NO_BITMAP)

ctx = []
class Pos:
    def __init__(self, x, y):
        self.x = x
        self.y = y

# move_to(Pos(0, 0), ctx)
# conic_to(Pos(50, 0), Pos(50, 50), ctx)
# line_to(Pos(100, 100), ctx)
# b = face.glyph.outline.get_outside_border()
# print('n:', b)
face.glyph.outline.decompose(ctx, move_to=move_to, line_to=line_to, conic_to=conic_to, cubic_to=cubic_to)
# 
ctx = np.array(ctx)
print('Point count', len(ctx))

char_w = max(ctx[:, 0])
char_h = max(ctx[:, 1])

offset_char_x = min(ctx[:, 0])
offset_char_y = min(ctx[:, 1])
print(offset_char_y, offset_char_x)


ctx = np.array([((x - offset_char_x) / char_w, (y - offset_char_y) / char_h) for x, y in ctx])
ctx *= 0.75

print(min(ctx[:, 0]), min(ctx[:, 1]), max(ctx[:, 0]), max(ctx[:, 1]))

import pickle
pickle.dump(ctx, open("text-cords.pkl", "wb"))

# print(ctx, (ctx.shape))
# svg_content = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
# <svg xmlns="http://www.w3.org/2000/svg">
#     <g>
#         <path
#             style="fill:none;stroke:#000000;stroke-width:2;stroke-linecap:butt;stroke-linejoin:miter;stroke-miterlimit:4;stroke-opacity:1;stroke-dasharray:none;stroke-dashoffset:0"
#             d="{}"
#         />
#   <path d="M 10 80 Q 95 10 180 80" stroke="black" fill="transparent"/>

#     </g>
# </svg>
# """.format(" ".join(ctx))

# with open("output.svg", "w") as f:
#     f.write(svg_content)
#     f.close()


# cv2.polylines(img, [ctx], isClosed=False, color=0, thickness=1)

# char_h = max(ctx[:, 1])
# for x, y in ctx:
#     cv2.circle(img, (x, char_h - y), 1, (0), -1)

# cv2.imshow(f"X", img)

