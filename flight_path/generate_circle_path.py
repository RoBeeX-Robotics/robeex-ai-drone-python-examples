import math
import pickle
import numpy as np

RADIUS = 1
mult = RADIUS / 2

ctx = []
a = -math.pi / 2
while a - (math.pi*(1.5)) < 0:
    a += 0.1
    print(a)
    x = (math.cos(a) * mult)
    y = (math.sin(a) * mult) + mult
    print(x, y)
    ctx.append((x,y))

ctx = np.array(ctx)

with open('circle_coordinates.pkl', 'wb') as f:
    pickle.dump(ctx[::-1], f)