"""Painter's-algorithm box renderer for R6 storyboards (Pillow + numpy)."""

import math

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import rig

SS = 2  # supersampling factor

FONT_DIR = "/usr/share/fonts/truetype/dejavu/"


def font(size, bold=False):
    return ImageFont.truetype(FONT_DIR + ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"), size)


COLORS = {
    "Torso": (86, 98, 122),
    "Head": (236, 196, 150),
    "RightArm": (222, 92, 62),
    "RightLeg": (176, 66, 48),
    "LeftArm": (70, 140, 224),
    "LeftLeg": (48, 104, 176),
}
DUMMY = (150, 150, 150)

# (eye direction from target toward camera, camera up, label)
VIEWS = {
    "side": ((1.0, 0.22, 0.0), (0, 1, 0), "SIDE (from character's right)"),
    "front": ((0.50, 0.24, -0.83), (0, 1, 0), "FRONT 3/4 (from target's side)"),
    "top": ((0.0, 1.0, 0.0), (0, 0, -1), "TOP-DOWN (forward = up)"),
}
LIGHT = np.array([0.35, 0.85, -0.4])
LIGHT = LIGHT / np.linalg.norm(LIGHT)


def camera(view):
    eye, up, _ = VIEWS[view]
    eye = np.array(eye, dtype=float)
    eye /= np.linalg.norm(eye)
    up = np.array(up, dtype=float)
    look = -eye
    right = np.cross(look, up)
    right /= np.linalg.norm(right)
    cam_up = np.cross(right, look)
    return right, cam_up, eye


FACES = [
    ((0, 0, 1), [(1, 1, 1), (-1, 1, 1), (-1, -1, 1), (1, -1, 1)]),
    ((0, 0, -1), [(-1, 1, -1), (1, 1, -1), (1, -1, -1), (-1, -1, -1)]),
    ((1, 0, 0), [(1, 1, -1), (1, 1, 1), (1, -1, 1), (1, -1, -1)]),
    ((-1, 0, 0), [(-1, 1, 1), (-1, 1, -1), (-1, -1, -1), (-1, -1, 1)]),
    ((0, 1, 0), [(-1, 1, 1), (1, 1, 1), (1, 1, -1), (-1, 1, -1)]),
    ((0, -1, 0), [(-1, -1, -1), (1, -1, -1), (1, -1, 1), (-1, -1, 1)]),
]


def collect_faces(parts, colors, alpha, right, cam_up, eye):
    out = []
    for name, (center, r, size) in parts.items():
        half = size / 2
        base = colors[name]
        for normal, verts in FACES:
            n = r @ np.array(normal, dtype=float)
            if float(np.dot(n, eye)) <= 1e-4:
                continue
            pts = [center + r @ (np.array(v, dtype=float) * half) for v in verts]
            depth = float(np.dot(np.mean(pts, axis=0), eye))
            shade = 0.50 + 0.50 * max(0.0, float(np.dot(n, LIGHT)))
            col = tuple(int(c * shade) for c in base)
            out.append((depth, pts, col, alpha, name, normal))
    return out


class View:
    def __init__(self, view, w, h, scale, center):
        self.view, self.w, self.h = view, w, h
        self.scale = scale
        self.center = np.array(center, dtype=float)
        self.right, self.cam_up, self.eye = camera(view)

    def project(self, p):
        d = np.asarray(p, dtype=float) - self.center
        x = float(np.dot(d, self.right)) * self.scale * SS + self.w * SS / 2
        y = -float(np.dot(d, self.cam_up)) * self.scale * SS + self.h * SS / 2
        return (x, y)


def draw_ground(d, v):
    y = rig.GROUND_Y
    pts = [(-5, y, -9), (5, y, -9), (5, y, 4), (-5, y, 4)]
    d.polygon([v.project(p) for p in pts], fill=(226, 222, 212, 255))
    for i in range(-5, 6):
        col = (190, 184, 170, 255) if i else (150, 144, 130, 255)
        d.line([v.project((i, y, -9)), v.project((i, y, 4))], fill=col, width=SS)
    for k in range(-9, 5):
        col = (190, 184, 170, 255) if k else (150, 144, 130, 255)
        d.line([v.project((-5, y, k)), v.project((5, y, k))], fill=col, width=SS)


def dummy_parts(front_z):
    """A pale training-dummy R6 whose chest front face sits at z = front_z."""
    c = np.array([0.0, 0.0, front_z - 0.5])
    I = np.eye(3)
    parts = {
        "Torso": (c.copy(), I, np.array([2.0, 2.0, 1.0])),
        "Head": (c + [0, 1.5, 0], I, np.array([2.0, 1.0, 1.0])),
        "RightArm": (c + [1.5, 0, 0], I, np.array([1.0, 2.0, 1.0])),
        "LeftArm": (c + [-1.5, 0, 0], I, np.array([1.0, 2.0, 1.0])),
        "RightLeg": (c + [0.5, -2, 0], I, np.array([1.0, 2.0, 1.0])),
        "LeftLeg": (c + [-0.5, -2, 0], I, np.array([1.0, 2.0, 1.0])),
    }
    return parts


def fill(d, pts, col, alpha, outline=(20, 20, 26, 255)):
    d.polygon(pts, fill=col + (alpha,), outline=outline if alpha == 255 else (90, 90, 96, 150))


def draw_face_marks(d, v, parts):
    """Eyes on the head's front (-Z) face so head turn / facing is readable."""
    center, r, size = parts["Head"]
    n = r @ np.array([0, 0, -1.0])
    if float(np.dot(n, v.eye)) <= 0.05:
        return
    for sx in (-0.45, 0.45):
        p = center + r @ np.array([sx, 0.12, -0.5])
        x, y = v.project(p)
        rad = 2.4 * SS
        d.ellipse([x - rad, y - rad, x + rad, y + rad], fill=(30, 30, 36, 255))
    p = center + r @ np.array([0, -0.22, -0.5])
    x, y = v.project(p)
    p2 = center + r @ np.array([0.0, -0.22, -0.5]) + r @ np.array([0.38, 0, 0])
    p3 = center + r @ np.array([0.0, -0.22, -0.5]) - r @ np.array([0.38, 0, 0])
    d.line([v.project(p3), v.project(p2)], fill=(30, 30, 36, 255), width=SS)


def starburst(d, v, p, radius=0.95, col=(255, 214, 64, 255), edge=(214, 60, 36, 255)):
    x, y = v.project(p)
    pts = []
    for i in range(16):
        a = i * math.pi / 8
        rr = radius * v.scale * SS * (1.0 if i % 2 == 0 else 0.45)
        pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
    d.polygon(pts, fill=col, outline=edge)


def render_cell(fk, view, w, h, scale, center, front_z, show_dummy=True, trail=None, tip_name=None, contact=False, ghost=None):
    v = View(view, w, h, scale, center)
    img = Image.new("RGBA", (w * SS, h * SS), (244, 241, 233, 255))
    d = ImageDraw.Draw(img, "RGBA")
    draw_ground(d, v)

    faces = []
    if show_dummy:
        faces += collect_faces(dummy_parts(front_z), {k: DUMMY for k in COLORS}, 52, v.right, v.cam_up, v.eye)
    if ghost is not None:
        faces += collect_faces(ghost["parts"], {k: (120, 120, 130) for k in COLORS}, 60, v.right, v.cam_up, v.eye)
    faces += collect_faces(fk["parts"], COLORS, 255, v.right, v.cam_up, v.eye)
    faces.sort(key=lambda f: f[0])
    for depth, pts, col, alpha, name, normal in faces:
        proj = [v.project(p) for p in pts]
        if alpha == 255:
            fill(d, proj, col, 255)
        else:
            layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
            ImageDraw.Draw(layer).polygon(proj, fill=col + (alpha,), outline=(70, 70, 80, 120))
            img = Image.alpha_composite(img, layer)
            d = ImageDraw.Draw(img, "RGBA")

    draw_face_marks(d, v, fk["parts"])

    if trail:
        pts = [v.project(p) for p in trail]
        for a, b in zip(pts, pts[1:]):
            d.line([a, b], fill=(236, 70, 40, 255), width=2 * SS)
        for p in pts[::3]:
            r = 1.6 * SS
            d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=(236, 70, 40, 255))
    if contact and tip_name:
        starburst(d, v, fk["tips"][tip_name])

    return img.resize((w, h), Image.LANCZOS).convert("RGB")


def view_geometry(view):
    """(scale px/stud, world center to look at) per view."""
    if view == "top":
        return 36, (0.0, -3.0, -2.2)
    if view == "side":
        return 31, (0.0, -0.3, -1.8)
    return 33, (0.0, -0.3, -1.4)
