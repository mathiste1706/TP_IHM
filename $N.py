
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OneNDollarAllInOne.py
---------------------
- $N Multistroke Recognizer (implémentation complète)
- UI pygame pour dessiner plusieurs traits
- RECO en live
- **AJOUT DYNAMIQUE DE TEMPLATES**: dessiner -> appuyer sur 't' -> saisir un nom -> Entrée -> sauvegarde JSON
- Chargement automatique des templates au démarrage (fichier JSON local)
- Publication Ivy optionnelle (si python-ivy est installé)
"""
from __future__ import annotations

import math
import json
import os
import argparse
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional

Point = Tuple[float, float]
Stroke = List[Point]
Multistroke = List[Stroke]

TEMPLATES_FILE = os.path.join(os.path.dirname(__file__), "ndollar_templates.json")

@dataclass
class UnistrokeTemplate:
    name: str
    points: List[Point]
    start_vector: Tuple[float, float]

@dataclass
class MultistrokeTemplate:
    name: str
    unistrokes: List[UnistrokeTemplate] = field(default_factory=list)

class NDollarRecognizer:
    def __init__(self,
                 n_points: int = 96,
                 size: float = 250.0,
                 rotate_range_degrees: float = 45.0,
                 rotate_precision_degrees: float = 2.0,
                 start_angle_tolerance_degrees: float = 30.0,
                 dimensional_invariance_threshold: float = 0.30,
                 start_index: int = 12,
                 use_bounded_rotation_invariance: bool = True,
                 max_unistroke_permutations: int = 4096):
        self.N = n_points
        self.size = size
        self.rotate_range = math.radians(rotate_range_degrees)
        self.rotate_precision = math.radians(rotate_precision_degrees)
        self.start_angle_tolerance = math.radians(start_angle_tolerance_degrees)
        self.delta = dimensional_invariance_threshold
        self.I = start_index
        self.use_bounded_rot_inv = use_bounded_rotation_invariance
        self.max_permutations = max_unistroke_permutations
        self.multistrokes: Dict[str, MultistrokeTemplate] = {}
        self._phi = 0.5 * (-1.0 + math.sqrt(5.0))

    def add_template(self, name: str, strokes: Multistroke):
        unistrokes_raw = self._generate_unistroke_permutations(strokes)
        processed_unistrokes: List[UnistrokeTemplate] = []
        for uni in unistrokes_raw:
            pts = self._resample(uni, self.N)
            omega = self._indicative_angle(pts)
            pts = self._rotate_by(pts, -omega)
            pts = self._scale_dim_to(pts, self.size, self.delta)
            if self.use_bounded_rot_inv:
                pts = self._rotate_by(pts, omega)
            pts = self._translate_to(pts, (0.0, 0.0))
            start_vec = self._calc_start_unit_vector(pts, self.I)
            processed_unistrokes.append(UnistrokeTemplate(name=name, points=pts, start_vector=start_vec))
        self.multistrokes.setdefault(name, MultistrokeTemplate(name=name)).unistrokes.extend(processed_unistrokes)

    def addTemplate(self, name: str, points_or_strokes):
        if len(points_or_strokes) == 0:
            return
        if isinstance(points_or_strokes[0], tuple):
            self.add_template(name, [points_or_strokes])
        else:
            self.add_template(name, points_or_strokes)

    def recognize(self, strokes: Multistroke) -> Tuple[Optional[str], float]:
        if not self.multistrokes:
            return None, 0.0

        candidate_points = self._combine_strokes(strokes)
        candidate_points = self._resample(candidate_points, self.N)
        omega = self._indicative_angle(candidate_points)
        candidate_points = self._rotate_by(candidate_points, -omega)
        candidate_points = self._scale_dim_to(candidate_points, self.size, self.delta)
        if self.use_bounded_rot_inv:
            candidate_points = self._rotate_by(candidate_points, omega)
        candidate_points = self._translate_to(candidate_points, (0.0, 0.0))
        v = self._calc_start_unit_vector(candidate_points, self.I)

        b = float('inf')
        mprime: Optional[str] = None
        for name, m in self.multistrokes.items():
            for u in m.unistrokes:
                if self._angle_between_vectors(v, u.start_vector) <= self.start_angle_tolerance:
                    d = self._distance_at_best_angle(candidate_points, u.points,
                                                    -self.rotate_range, self.rotate_range, self.rotate_precision)
                    if d < b:
                        b = d
                        mprime = name

        half_diag = 0.5 * math.sqrt(self.size * self.size + self.size * self.size)
        score = 1.0 - (b / half_diag if math.isfinite(b) else 1.0)
        score = max(0.0, min(1.0, score))
        return mprime, score

    def _generate_unistroke_permutations(self, strokes: Multistroke) -> List[List[Point]]:
        k = len(strokes)
        if k == 0:
            return [[]]
        order = list(range(k))
        orders: List[List[int]] = []
        self._heap_permute(len(order), order, orders)
        max_orders = max(1, self.max_permutations // max(1, (1 << k)))
        if len(orders) > max_orders:
            orders = orders[:max_orders]
        unistrokes: List[List[Point]] = []
        for R in orders:
            combinations = 1 << len(R)
            if combinations * len(unistrokes) > self.max_permutations:
                combinations = max(1, self.max_permutations - len(unistrokes))
            for b in range(combinations):
                uni: List[Point] = []
                for i, idx in enumerate(R):
                    s = strokes[idx]
                    if (b >> i) & 1:
                        uni.extend(reversed(s))
                    else:
                        uni.extend(s)
                unistrokes.append(uni)
                if len(unistrokes) >= self.max_permutations:
                    return unistrokes
        return unistrokes

    def _heap_permute(self, n: int, order: List[int], out_orders: List[List[int]]):
        if n == 1:
            out_orders.append(order.copy())
        else:
            for i in range(n):
                self._heap_permute(n - 1, order, out_orders)
                if n % 2 == 1:
                    order[0], order[n - 1] = order[n - 1], order[0]
                else:
                    order[i], order[n - 1] = order[n - 1], order[i]

    def _combine_strokes(self, strokes: Multistroke) -> List[Point]:
        pts: List[Point] = []
        for s in strokes:
            pts.extend(s)
        return pts

    def _resample(self, points: List[Point], n: int) -> List[Point]:
        if not points:
            return points
        path_len = self._path_length(points)
        if n <= 1 or path_len == 0:
            return [points[0]] * max(1, n)
        I = path_len / (n - 1)
        D = 0.0
        new_pts = [points[0]]
        i = 1
        pts = points.copy()

        def _dist(a: Point, b: Point) -> float:
            d = math.hypot(b[0]-a[0], b[1]-a[1])
            return d if d > 1e-12 else 0.0

        while i < len(pts):
            d = _dist(pts[i - 1], pts[i])
            if (D + d) >= I and d > 0.0:
                t = (I - D) / d
                qx = pts[i - 1][0] + t * (pts[i][0] - pts[i - 1][0])
                qy = pts[i - 1][1] + t * (pts[i][1] - pts[i - 1][1])
                q = (qx, qy)
                new_pts.append(q)
                pts.insert(i, q)
                D = 0.0
                i += 1
            else:
                D += d
                i += 1

        while len(new_pts) < n:
            new_pts.append(points[-1])
        return new_pts[:n]

    def _path_length(self, A: List[Point]) -> float:
        d = 0.0
        for i in range(1, len(A)):
            d += self._distance(A[i - 1], A[i])
        return d

    def _indicative_angle(self, points: List[Point]) -> float:
        cx, cy = self._centroid(points)
        px, py = points[0]
        return math.atan2(cy - py, cx - px)

    def _rotate_by(self, points: List[Point], omega: float) -> List[Point]:
        cx, cy = self._centroid(points)
        cosw = math.cos(omega)
        sinw = math.sin(omega)
        new_pts: List[Point] = []
        for (px, py) in points:
            qx = (px - cx) * cosw - (py - cy) * sinw + cx
            qy = (px - cx) * sinw + (py - cy) * cosw + cy
            new_pts.append((qx, qy))
        return new_pts

    def _scale_dim_to(self, points: List[Point], size: float, delta: float) -> List[Point]:
        minx = min(p[0] for p in points)
        maxx = max(p[0] for p in points)
        miny = min(p[1] for p in points)
        maxy = max(p[1] for p in points)
        w = maxx - minx
        h = maxy - miny

        new_pts: List[Point] = []
        if (max(w, h) == 0) or (min(w, h) / max(w, h)) <= delta:
            # uniform scaling
            denom = max(w, h) if max(w, h) != 0 else 1.0
            for (px, py) in points:
                qx = px * size / denom
                qy = py * size / denom
                new_pts.append((qx, qy))
        else:
            w = w if w != 0 else 1.0
            h = h if h != 0 else 1.0
            for (px, py) in points:
                qx = px * size / w
                qy = py * size / h
                new_pts.append((qx, qy))
        return new_pts

    def _translate_to(self, points: List[Point], k: Point) -> List[Point]:
        cx, cy = self._centroid(points)
        dx = k[0] - cx
        dy = k[1] - cy
        return [(px + dx, py + dy) for (px, py) in points]

    def _calc_start_unit_vector(self, points: List[Point], I: int) -> Tuple[float, float]:
        if len(points) <= I:
            I = max(1, len(points) - 1)
        qx = points[I][0] - points[0][0]
        qy = points[I][1] - points[0][1]
        mag = math.hypot(qx, qy)
        if mag == 0:
            return (0.0, 0.0)
        return (qx / mag, qy / mag)

    def _angle_between_vectors(self, A: Tuple[float, float], B: Tuple[float, float]) -> float:
        dot = A[0] * B[0] + A[1] * B[1]
        dot = max(-1.0, min(1.0, dot))
        return math.acos(dot)

    def _distance_at_best_angle(self, points: List[Point], T: List[Point],
                                theta_a: float, theta_b: float, theta_delta: float) -> float:
        x1 = self._phi * theta_a + (1.0 - self._phi) * theta_b
        f1 = self._distance_at_angle(points, T, x1)
        x2 = (1.0 - self._phi) * theta_a + self._phi * theta_b
        f2 = self._distance_at_angle(points, T, x2)
        while abs(theta_b - theta_a) > theta_delta:
            if f1 < f2:
                theta_b = x2
                x2 = x1
                f2 = f1
                x1 = self._phi * theta_a + (1.0 - self._phi) * theta_b
                f1 = self._distance_at_angle(points, T, x1)
            else:
                theta_a = x1
                x1 = x2
                f1 = f2
                x2 = (1.0 - self._phi) * theta_a + self._phi * theta_b
                f2 = self._distance_at_angle(points, T, x2)
        return min(f1, f2)

    def _distance_at_angle(self, points: List[Point], T: List[Point], theta: float) -> float:
        new_pts = self._rotate_by(points, theta)
        return self._path_distance(new_pts, T)

    def _path_distance(self, A: List[Point], B: List[Point]) -> float:
        n = min(len(A), len(B))
        if n == 0:
            return float('inf')
        d = 0.0
        for i in range(n):
            d += self._distance(A[i], B[i])
        return d / float(n)

    @staticmethod
    def _distance(p1: Point, p2: Point) -> float:
        return math.hypot(p2[0] - p1[0], p2[1] - p1[1])

    @staticmethod
    def _centroid(points: List[Point]) -> Point:
        if not points:
            return (0.0, 0.0)
        sx = sum(p[0] for p in points)
        sy = sum(p[1] for p in points)
        n = len(points)
        return (sx / n, sy / n)

# --- Persistence helpers ---

def load_templates_from_disk(recognizer: NDollarRecognizer, path: str = TEMPLATES_FILE) -> int:
    if not os.path.exists(path):
        return 0
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        cnt = 0
        for item in data.get("templates", []):
            name = item.get("name")
            strokes = item.get("strokes", [])
            conv = []
            for s in strokes:
                conv.append([tuple(map(float, p)) for p in s])
            recognizer.add_template(name, conv)
            cnt += 1
        return cnt
    except Exception as e:
        print("[WARN] load failed:", e)
        return 0

def save_template_to_disk(name: str, strokes: Multistroke, path: str = TEMPLATES_FILE) -> None:
    record = {"name": name, "strokes": [[[float(x), float(y)] for (x, y) in s] for s in strokes]}
    data = {"templates": []}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f) or {"templates": []}
        except Exception:
            data = {"templates": []}
    data.setdefault("templates", []).append(record)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# --- Pygame Demo with naming ---

def run_demo():
    try:
        import pygame
    except ImportError:
        print("pygame n'est pas installé. `pip install pygame`")
        return

    ivy_enabled = False
    ivy_app = None
    try:
        from ivy.std_api import IvyInit, IvyStart, IvyStop, IvySendMsg
        IvyInit("NDollar", "NDollar ready", 0)
        IvyStart("127.0.0.1:2010")
        ivy_enabled = True
        ivy_app = {"send": IvySendMsg, "stop": IvyStop}
        print("[Ivy] connecté 127.0.0.1:2010")
    except Exception as e:
        print("[Ivy] non utilisé:", e)

    WIDTH, HEIGHT = 1000, 650
    BG = (245, 245, 245); FG = (20, 20, 20)
    GREEN = (40, 160, 60); RED = (200, 60, 60); BLUE = (60, 60, 220); ORANGE = (240, 140, 40)

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("$N")
    clock = pygame.time.Clock()

    rec = NDollarRecognizer()

    loaded = load_templates_from_disk(rec)
    print(f"[INFO] Templates chargés: {loaded} depuis {TEMPLATES_FILE}")

    def draw_strokes(strokes, color=FG, radius=3):
        for s in strokes:
            if not s: continue
            for p in s:
                pygame.draw.circle(screen, color, (int(p[0]), int(p[1])), radius)
            if len(s) >= 2:
                pygame.draw.lines(screen, color, False, s, 2)

    def write(txt, x, y, color=FG, size=18):
        font = pygame.font.SysFont('consolas', size)
        surf = font.render(txt, True, color)
        screen.blit(surf, (x, y))

    def write_multiline(text, x, y, color=FG, size=16, max_width=WIDTH-20):
        font = pygame.font.SysFont('consolas', size)
        words = text.split(' ')
        lines = []
        cur = ""
        for w in words:
            test = (cur + " " + w).strip()
            if font.size(test)[0] > max_width and cur:
                lines.append(cur); cur = w
            else:
                cur = test
        if cur: lines.append(cur)
        for i, line in enumerate(lines):
            surf = font.render(line, True, color)
            screen.blit(surf, (x, y + i*(size+2)))

    strokes: List[Stroke] = []
    drawing = False
    cur: Stroke = []
    result = ("", 0.0)

    naming_mode = False
    name_buffer = ""

    show_help = True
    help_text = "Souris: dessiner | Entrée: reconnaître | Backspace/Espace: effacer | t: enregistrer template | Esc: quitter"

    info_flash = ""
    info_timer = 0
    flash_color = ORANGE
    def flash(msg, duration_frames=180, color=ORANGE):
        nonlocal info_flash, info_timer, flash_color
        info_flash = msg; info_timer = duration_frames; flash_color = color

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if naming_mode:
                    if event.key == pygame.K_RETURN:
                        if strokes and name_buffer.strip():
                            name = name_buffer.strip()
                            save_template_to_disk(name, strokes)
                            rec.add_template(name, strokes)
                            flash(f"Template '{name}' enregistré.", 180, GREEN)
                        else:
                            flash("Nom vide ou aucun trait", 180, RED)
                        name_buffer = ""; naming_mode = False
                    elif event.key == pygame.K_ESCAPE:
                        naming_mode = False; name_buffer = ""
                    elif event.key == pygame.K_BACKSPACE:
                        name_buffer = name_buffer[:-1]
                    else:
                        ch = event.unicode
                        if ch and ch.isprintable():
                            name_buffer += ch
                else:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_RETURN:
                        if strokes:
                            name, score = rec.recognize(strokes)
                            result = (name if name else "(none)", score)
                            if ivy_enabled and name:
                                ivy_app["send"](f"NDOLLAR_RECO name={name} score={score:.3f}")
                                print(f"[Ivy] NDOLLAR_RECO name={name} score={score:.3f}")
                    elif event.key == pygame.K_BACKSPACE or event.key == pygame.K_SPACE:
                        strokes.clear(); result = ("", 0.0)
                    elif event.key == pygame.K_F1:
                        show_help = not show_help
                    elif event.key == pygame.K_t:
                        if not strokes:
                            flash("Aucun trait à enregistrer", 180, RED)
                        else:
                            naming_mode = True; name_buffer = ""
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not naming_mode:
                drawing = True; cur = [pygame.mouse.get_pos()]
            elif event.type == pygame.MOUSEMOTION and drawing and not naming_mode:
                cur.append(pygame.mouse.get_pos())
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and drawing and not naming_mode:
                drawing = False
                if len(cur) >= 2:
                    strokes.append(cur)
                cur = []

        screen.fill(BG)
        draw_strokes(strokes, BLUE, 3)
        if drawing and len(cur) >= 1:
            draw_strokes([cur], (220, 80, 80), 3)

        write(help_text, 10, 10)
        if result[0] != "":
            write(f"Reconnu: {result[0]}  score={result[1]:.3f}", 10, 36, GREEN, 20)

        if info_timer > 0:
            write(info_flash, 10, 62, flash_color, 18)
            info_timer -= 1

        if naming_mode:
            overlay = pygame.Surface((1000, 140), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            screen.blit(overlay, (0, 650//2 - 70))
            write("Entrer un nom de template (Entrée pour valider, Échap pour annuler):", 20, 650//2 - 46, (255,255,255), 20)
            write(name_buffer + "▌", 20, 650//2 - 10, (255,255,255), 24)

        if show_help and not naming_mode:
            block = (
                ""
            )
            write_multiline(block, 10, 650-160, FG, 16)

        import pygame  # keep after Surface for type
        pygame.display.flip()
        clock.tick(120)

    if ivy_enabled:
        try: ivy_app["stop"]()
        except Exception: pass
    import pygame
    pygame.quit()

def headless_example():
    rec = NDollarRecognizer()
    load_templates_from_disk(rec)
    if not rec.multistrokes:
        rec.add_template("L", [[(0,0),(0,100)], [(0,100),(80,100)]])
    candidate = [[(80, 100), (0, 100)], [(0, 100), (0, 0)]]
    name, score = rec.recognize(candidate)
    print(f"Recognized: {name}, score={score:.3f}")

def main():
    parser = argparse.ArgumentParser(description="$N Multistroke Recognizer demo (+ save/load)")
    parser.add_argument("--headless", action="store_true", help="Exécuter un exemple sans UI")
    args = parser.parse_args()
    if args.headless:
        headless_example()
    else:
        run_demo()

if __name__ == "__main__":
    main()
