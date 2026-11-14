import math, re, pathlib

tris = []  # (a, b, c, center)

def add(a, b, c, center):
    tris.append((a, b, c, center))

def box(x0, y0, z0, x1, y1, z1):
    v = [(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),
         (x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
    c = ((x0+x1)/2, (y0+y1)/2, (z0+z1)/2)
    for q in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(2,3,7,6),(1,2,6,5),(3,0,4,7)]:
        a, b, d, e = (v[i] for i in q)
        add(a, b, d, c); add(a, d, e, c)

def wheel(cx, cz, r, y0, y1, n=16):
    c = (cx, (y0+y1)/2, cz)
    ring = [(cx + r*math.cos(2*math.pi*i/n), cz + r*math.sin(2*math.pi*i/n)) for i in range(n)]
    for i in range(n):
        (ax, az), (bx, bz) = ring[i], ring[(i+1) % n]
        add((ax,y0,az), (bx,y0,bz), (bx,y1,bz), c)
        add((ax,y0,az), (bx,y1,bz), (ax,y1,az), c)
        add((cx,y0,cz), (bx,y0,bz), (ax,y0,az), c)
        add((cx,y1,cz), (ax,y1,az), (bx,y1,bz), c)

# --- the bus ---
box(0, 0, 1.0, 12, 4, 5)            # body
box(0.8, -0.08, 3.1, 11.2, 4.08, 4.4)  # window band
box(11.95, 0.4, 2.6, 12.1, 3.6, 4.6)   # windshield
box(4, 1, 5, 8, 3, 5.5)             # roof A/C
box(-0.25, 0.2, 1.0, 12.25, 3.8, 1.5)  # bumpers
for x in (2.5, 9.5):
    wheel(x, 1.0, 1.0, -0.35, 0.65)
    wheel(x, 1.0, 1.0, 3.35, 4.35)

def sub(p, q): return tuple(p[i]-q[i] for i in range(3))
def cross(u, v): return (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
def dot(u, v): return sum(u[i]*v[i] for i in range(3))
f = lambda p: " ".join(f"{x:.4f}" for x in p)

lines = ["solid edward_bus"]
for a, b, c, ctr in tris:
    n = cross(sub(b, a), sub(c, a))
    mid = tuple((a[i]+b[i]+c[i])/3 for i in range(3))
    if dot(n, sub(mid, ctr)) < 0:
        b, c = c, b
        n = tuple(-x for x in n)
    l = math.sqrt(dot(n, n)) or 1
    n = tuple(x/l for x in n)
    lines += [f"  facet normal {f(n)}", "    outer loop",
              f"      vertex {f(a)}", f"      vertex {f(b)}", f"      vertex {f(c)}",
              "    endloop", "  endfacet"]
lines.append("endsolid edward_bus")

readme = pathlib.Path("README.md")
block = "```stl\n" + "\n".join(lines) + "\n```"
text = re.sub(r"<!-- BUS:START -->.*?<!-- BUS:END -->",
              lambda m: f"<!-- BUS:START -->\n{block}\n<!-- BUS:END -->",
              readme.read_text(encoding="utf-8"), flags=re.S)
readme.write_text(text, encoding="utf-8")
print(f"Bus inserted: {len(tris)} facets")