"""
OPERACIÓN NEPTUNO 2D  -  Mini-juego de estrategia naval en Python (pygame)

Objetivo: controlar 8 de las 11 regiones estratégicas durante 20 segundos.
Cada flota tiene 4 grupos de ataque que patrullan su región. Aparecen
contactos hostiles, tormentas y fallos mecánicos. Tú das órdenes a las flotas.

Controles
  Clic en un barco ... selecciona su flota
  Clic en el océano .. envía la flota seleccionada (ruta con A*)
  B ................. la flota seleccionada vuelve a su base
  TAB ............... cambia de flota          ESC ... deselecciona
  1-5 ............... nivel DEFCON             V ..... velocidad x0.5/1/2/5
  ESPACIO ........... pausa                   R ..... reiniciar
"""
import math
import os
import random
import sys
import heapq

TEST = "--test" in sys.argv
if TEST:
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame

# ------------------------------------------------------------------ constantes
MAP_W, MAP_H = 1000, 500
TOP = 50
WIN_W, WIN_H = 1000, 700
CELL = 8                       # tamaño de celda de la rejilla A*
PX_DEG = MAP_W / 360.0         # píxeles por grado
GRUPOS_POR_FLOTA = 4
OBJETIVO_REGIONES = 8
TIEMPO_SOSTENER = 20.0

# (código, nombre, región, lat, lon, radio en grados, color)
FLOTAS = [
    ("F1", "1ª Flota", "Pacífico Este", 33, -125, 16, (0, 229, 255)),
    ("F2", "2ª Flota", "Atlántico Norte", 35, -68, 14, (82, 255, 122)),
    ("F3", "3ª Flota", "Pacífico Central", 20, -152, 15, (255, 176, 0)),
    ("F4", "4ª Flota", "Caribe", 15, -74, 8, (255, 79, 216)),
    ("F5", "5ª Flota", "Golfo Pérsico", 27, 51.5, 2.6, (198, 255, 0)),
    ("F6", "6ª Flota", "Mediterráneo", 35.5, 19, 7, (255, 122, 26)),
    ("F7", "7ª Flota", "Pacífico Oeste", 31, 143, 14, (157, 123, 255)),
    ("F10", "10ª Flota", "Atlántico Sur", -18, -10, 16, (0, 255, 204)),
    ("FMN", "Flota Mar Negro", "Mar Negro", 43.4, 34, 2.8, (255, 107, 139)),
    ("FIN", "Flota Índico", "Océano Índico", -7, 72, 18, (77, 166, 255)),
    ("FAR", "Flota Ártica", "Ártico", 71, -8, 8, (255, 238, 51)),
]

# Polígonos de tierra [lon, lat, lon, lat, ...] (aproximados)
TIERRA = [
    [-168,66,-162,70,-141,70,-125,70,-95,72,-82,69,-78,62,-70,60,-64,60,-60,55,-56,52,-60,48,-66,45,-70,42,-76,38,-76,35,-81,31,-80,25,-83,29,-88,30,-94,29,-97,26,-97,21,-95,18,-91,19,-87,21,-88,16,-83,15,-83,10,-79,9,-83,8,-86,11,-90,13,-94,16,-100,17,-105,20,-106,23,-109,26,-112,30,-114,31.5,-113,28,-110,24,-110,23,-112,25,-115,28,-117,32,-121,35,-124,40,-124,47,-128,51,-133,56,-140,60,-148,60,-152,58,-158,56,-164,55,-158,59,-165,62],
    [-73,78,-60,82,-30,83,-20,80,-20,72,-30,68,-42,60,-50,64,-55,70,-68,76],
    [-77,8,-72,12,-62,10,-52,5,-50,0,-44,-2,-35,-5,-35,-9,-39,-15,-41,-22,-48,-26,-53,-34,-58,-38,-62,-40,-65,-45,-68,-50,-69,-54,-73,-52,-75,-46,-73,-37,-71,-30,-70,-18,-76,-14,-81,-6,-80,-1,-78,3],
    [-17,21,-10,30,-6,36,10,37,11,33,20,31,32,31,34,27,37,20,43,12,51,12,48,5,40,-3,40,-15,35,-24,32,-29,27,-34,20,-35,18,-32,12,-17,13,-8,9,-1,9,4,4,6,-8,4,-13,8,-17,14],
    [-9,37,-9,43,-1,43.5,-4,48,2,51,8,54,9,57,11,54,20,55,24,58,30,60,32,66,40,66,44,68,60,69,70,73,80,73,100,77,112,74,130,72,142,72,160,70,170,70,178,68,178,64,170,62,163,60,160,54,156,51,152,59,142,59,138,54,141,48,135,43,130,42,129,35,126,35,126,38,124,40,121,40,118,38,121,36,120,32,122,30,120,26,116,22,110,21,108,18,109,12,105,9,103,10,100,13,100,7,103,2,100,4,98,9,98,16,94,17,91,22,87,21,80,15,78,8,73,17,72,21,67,24,62,25,57,26,56,27,50,30,48,29,51,25,56,25,59,22,53,16,45,13,43,13,39,21,35,28,34,30,36,36,27,37,26,40,24,38,22,36,20,40,19,42,14,45,7,44,3,43,0,39,-2,37,-6,36],
    [5,58,5,62,12,66,18,70,26,71,31,70,29,66,25,65,22,63,19,60,17,57,13,55.5,11,58],
    [7,44,10,44.3,12.5,44.5,14,42,16,41.5,18.5,40.2,16.5,38,15.6,38,15.5,40,12,42,10,43.5],
    [114,-22,122,-18,130,-12,137,-12,136,-15,142,-11,146,-19,153,-25,153,-30,150,-37,141,-38,135,-34,130,-32,124,-34,115,-34,114,-26],
    [-5,50,1,51,2,53,-2,56,-3,58.5,-6,57,-3,54,-5,52], [-10,52,-6,52,-6,55,-10,54], [-24,64,-14,64,-14,66,-22,66],
    [44,-25,48,-24,50,-15,49,-12,44,-17], [95,5,98,4,104,-2,106,-6,102,-4,96,2], [109,2,117,7,119,1,116,-4,110,-3],
    [105,-6,114,-7,114,-8.5,106,-7.5], [131,-1,141,-3,150,-10,141,-9,138,-8,132,-3], [120,18,122,18,126,8,122,7,120,14],
    [130,33,135,34,140,35,142,40,141,41,139,38,136,36,132,35], [140,42,145,44,142,45], [142,46,144,50,143,54,142,52],
    [173,-35,178,-38,175,-41,173,-39], [172,-41,174,-42,170,-46,167,-45], [145,-41,148,-41,147,-43.5],
    [-85,22,-80,23,-74,20,-78,20], [-74,19,-69,19,-68,18,-72,18],
    [-80,73,-62,67,-65,62,-75,64], [-118,72,-100,73,-102,69,-118,69], [-90,80,-65,82,-75,78,-90,77],
]
AGUA = [  # mares interiores (se restan de la tierra)
    [-94,59,-88,64,-82,63,-78,62,-78,56,-80,52,-86,55,-92,57],
    [28,42,28,45,33,46,38,47,41,43,36,41.5,31,41],
    [47,43,53,46,54,40,53,37,49,37,49,40],
    [16,56,20,55,22,57,24,59,29,60,22,60.2,21,63,24,65.5,22,65.8,17,62,17.5,59],
]

NIVELES_DEFCON = {1: (2.4, 1.5), 2: (1.6, 1.3), 3: (1.0, 1.0), 4: (0.7, 0.85), 5: (0.45, 0.7)}
COLOR_DEFCON = {1: (255, 46, 46), 2: (255, 122, 26), 3: (255, 176, 0), 4: (154, 205, 50), 5: (0, 255, 204)}
CIAN = (0, 255, 204)


def proyectar(lon, lat):
    """lon/lat (grados) -> píxeles del mapa."""
    return (lon + 180) / 360 * MAP_W, (90 - lat) / 180 * MAP_H


def poly_px(flat):
    return [proyectar(flat[i], flat[i + 1]) for i in range(0, len(flat), 2)]


# ------------------------------------------------------------------ el mundo
class Mundo:
    """Mapa de tierra/agua + rejilla de navegación + A*."""

    def __init__(self):
        mask = pygame.Surface((MAP_W, MAP_H))
        mask.fill((0, 0, 0))
        for p in TIERRA:
            pygame.draw.polygon(mask, (255, 255, 255), poly_px(p))
        for p in AGUA:
            pygame.draw.polygon(mask, (0, 0, 0), poly_px(p))
        pygame.draw.rect(mask, (255, 255, 255), (0, proyectar(0, -70)[1], MAP_W, MAP_H))  # Antártida
        self.mask = mask
        self.pix = pygame.image.tostring(mask, "RGB")
        self.gw, self.gh = MAP_W // CELL, MAP_H // CELL
        self.nav = [[self.agua((cx + .5) * CELL, (cy + .5) * CELL) for cy in range(self.gh)] for cx in range(self.gw)]
        self.fondo = self._dibujar_fondo()

    def agua(self, x, y):
        xi, yi = int(x), int(y)
        if not (0 <= xi < MAP_W and 10 <= yi < MAP_H):
            return False
        return self.pix[(yi * MAP_W + xi) * 3] == 0

    def linea_libre(self, a, b):
        d = math.dist(a, b)
        n = max(1, int(d / 3))
        for i in range(1, n + 1):
            t = i / n
            if not self.agua(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t):
                return False
        return True

    def agua_cercana(self, x, y, maxr=60):
        if self.agua(x, y):
            return (x, y)
        for r in range(2, maxr, 2):
            for k in range(16):
                a = k * math.pi / 8
                px, py = x + r * math.cos(a), y + r * math.sin(a)
                if self.agua(px, py):
                    return (px, py)
        return None

    # --- A* sobre la rejilla ---
    def _celda_nav(self, p):
        cx, cy = int(p[0] // CELL), int(p[1] // CELL)
        for r in range(0, 8):
            mejor, md = None, 1e9
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    if max(abs(dx), abs(dy)) != r:
                        continue
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < self.gw and 0 <= ny < self.gh and self.nav[nx][ny] and dx * dx + dy * dy < md:
                        mejor, md = (nx, ny), dx * dx + dy * dy
            if mejor:
                return mejor
        return None

    def ruta(self, a, b):
        """Devuelve lista de puntos (px) de a hasta b evitando tierra, o None."""
        s, g = self._celda_nav(a), self._celda_nav(b)
        if s is None or g is None:
            return None
        h = lambda c: max(abs(c[0] - g[0]), abs(c[1] - g[1])) + 0.414 * min(abs(c[0] - g[0]), abs(c[1] - g[1]))
        abierto = [(h(s), 0.0, s)]
        padre, costo = {s: None}, {s: 0.0}
        while abierto:
            _, c, cur = heapq.heappop(abierto)
            if cur == g:
                break
            if c > costo[cur]:
                continue
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if not dx and not dy:
                        continue
                    n = (cur[0] + dx, cur[1] + dy)
                    if not (0 <= n[0] < self.gw and 0 <= n[1] < self.gh) or not self.nav[n[0]][n[1]]:
                        continue
                    if dx and dy and not (self.nav[cur[0] + dx][cur[1]] and self.nav[cur[0]][cur[1] + dy]):
                        continue  # no cortar esquinas de tierra
                    nc = c + (1.414 if dx and dy else 1.0)
                    if nc < costo.get(n, 1e9):
                        costo[n] = nc
                        padre[n] = cur
                        heapq.heappush(abierto, (nc + h(n), nc, n))
        if g not in padre:
            return None
        celdas = []
        c = g
        while c:
            celdas.append(c)
            c = padre[c]
        celdas.reverse()
        pts = [((cx + .5) * CELL, (cy + .5) * CELL) for cx, cy in celdas]
        pts[0], pts[-1] = tuple(a), tuple(b)
        # suavizado por línea de visión
        out, i = [pts[0]], 0
        while i < len(pts) - 1:
            j = len(pts) - 1
            while j > i + 1 and not self.linea_libre(pts[i], pts[j]):
                j -= 1
            out.append(pts[j])
            i = j
        return out

    def _dibujar_fondo(self):
        s = pygame.Surface((MAP_W, MAP_H))
        for y in range(MAP_H):
            k = y / MAP_H
            pygame.draw.line(s, (6 + int(6 * k), 24 + int(12 * (1 - abs(k - .5) * 2)), 52), (0, y), (MAP_W, y))
        for lon in range(-180, 181, 30):
            x = proyectar(lon, 0)[0]
            pygame.draw.line(s, (12, 48, 80), (x, 0), (x, MAP_H))
        for lat in range(-90, 91, 30):
            y = proyectar(0, lat)[1]
            pygame.draw.line(s, (12, 48, 80), (0, y), (MAP_W, y))
        for p in TIERRA:
            pts = poly_px(p)
            pygame.draw.polygon(s, (52, 78, 44), pts)
            pygame.draw.polygon(s, (92, 130, 70), pts, 1)
        for p in AGUA:
            pts = poly_px(p)
            pygame.draw.polygon(s, (8, 30, 62), pts)
            pygame.draw.polygon(s, (30, 70, 110), pts, 1)
        pygame.draw.rect(s, (205, 225, 238), (0, proyectar(0, -70)[1], MAP_W, MAP_H))
        return s


# ------------------------------------------------------------------ entidades
class Grupo:
    VEL = 22.0

    def __init__(self, fi, n, x, y, radio_patrulla):
        self.fi, self.n = fi, n
        self.nombre = f"{FLOTAS[fi][0]}-G{n + 1:02d}"
        self.x, self.y = x, y
        self.anchor = (x, y)
        self.anchor0 = (x, y)
        self.off = (0.0, 0.0)
        self.path = []
        self.ordenado = False
        self.falla = 0.0
        self.rumbo = random.random() * 6.28
        self.radio_p = radio_patrulla
        self.estela = []
        self.t_estela = 0.0
        self.en_tormenta = False

    def actualizar(self, dt, mundo, tormentas):
        if self.falla > 0:
            self.falla -= dt
            return "reparado" if self.falla <= 0 else None
        self.en_tormenta = any(math.dist((self.x, self.y), (t["x"], t["y"])) < t["r"] for t in tormentas)
        if not self.path:
            self._nueva_patrulla(mundo)
        evento = None
        if self.path:
            tx, ty = self.path[0]
            dx, dy = tx - self.x, ty - self.y
            d = math.hypot(dx, dy)
            paso = self.VEL * (0.5 if self.en_tormenta else 1.0) * dt * (1.6 if self.ordenado else 1.0)
            if d <= paso:
                self.x, self.y = tx, ty
                self.path.pop(0)
                if not self.path and self.ordenado:
                    self.ordenado = False
                    evento = "llegada"
            else:
                self.x += dx / d * paso
                self.y += dy / d * paso
                self.rumbo = math.atan2(dy, dx)
        self.t_estela += dt
        if self.t_estela > 0.5:
            self.t_estela = 0
            self.estela.append((self.x, self.y))
            self.estela = self.estela[-14:]
        return evento

    def _nueva_patrulla(self, mundo):
        for _ in range(12):
            a, r = random.random() * 6.283, self.radio_p * math.sqrt(random.random())
            p = (self.anchor[0] + r * math.cos(a), self.anchor[1] + r * math.sin(a))
            if mundo.agua(*p) and mundo.linea_libre((self.x, self.y), p):
                self.path = [p]
                return


class Enemigo:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.vida = 60.0
        self.eng = 0.0
        self.aviso = False

    def actualizar(self, dt, mundo, grupos):
        objetivo = min(grupos, key=lambda g: math.dist((self.x, self.y), (g.x, g.y)))
        dx, dy = objetivo.x - self.x, objetivo.y - self.y
        d = math.hypot(dx, dy) or 1
        if d < 16:
            self.eng += dt
            return objetivo
        self.eng = max(0, self.eng - dt)
        base = math.atan2(dy, dx)
        for rot in (0, .5, -.5, 1.0, -1.0, 1.6, -1.6, 2.4, -2.4):
            a = base + rot
            nx, ny = self.x + math.cos(a) * 6, self.y + math.sin(a) * 6
            if mundo.agua(nx, ny):
                self.x += math.cos(a) * 15 * dt
                self.y += math.sin(a) * 15 * dt
                break
        return None


# ------------------------------------------------------------------ el juego
class Juego:
    def __init__(self):
        pygame.init()
        self.pantalla = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption("Operación Neptuno 2D")
        self.f_chica = pygame.font.SysFont("consolas,dejavusansmono,couriernew", 13)
        self.f_med = pygame.font.SysFont("consolas,dejavusansmono,couriernew", 16, bold=True)
        self.f_grande = pygame.font.SysFont("consolas,dejavusansmono,couriernew", 40, bold=True)
        self.mundo = Mundo()
        self.reloj = pygame.time.Clock()
        self.reiniciar()

    # ---- estado
    def reiniciar(self):
        self.t = 0.0
        self.pausa = False
        self.vel_i = 1
        self.defcon = 3
        self.sel = None
        self.grupos = []
        self.enemigos = []
        self.tormentas = []
        self.explosiones = []
        self.ondas = []        # ondas expansivas de las explosiones [x, y, vida]
        self.flotantes = []    # textos "+100" que suben y se desvanecen [x, y, vida, texto, color]
        self.flash_puntaje = 0.0
        self.pings = []
        self.logs = []
        self.hold = 0.0
        self.victoria = False
        self.t_evento = 6.0
        self.stats = {"neutralizados": 0, "tormentas": 0, "fallas": 0, "puntaje": 0}
        self.control = [0.0] * len(FLOTAS)
        self.controlada = [False] * len(FLOTAS)
        self.ops = [0] * len(FLOTAS)
        self.ordenes = [False] * len(FLOTAS)
        for fi, f in enumerate(FLOTAS):
            bx, by = proyectar(f[4], f[3])
            rad = f[5] * PX_DEG
            for n in range(GRUPOS_POR_FLOTA):
                p = None
                for _ in range(80):
                    a, r = random.random() * 6.283, rad * 0.7 * math.sqrt(random.random())
                    q = (bx + r * math.cos(a), by + r * math.sin(a))
                    if self.mundo.agua(*q):
                        p = q
                        break
                p = p or self.mundo.agua_cercana(bx, by) or (bx, by)
                g = Grupo(fi, n, p[0], p[1], max(8, min(30, rad * 0.6)))
                g.off = (p[0] - bx, p[1] - by)
                self.grupos.append(g)
        self.log("info", "Sistema iniciado: 11 flotas y %d grupos en patrulla." % len(self.grupos))
        for _ in range(2):
            self.spawn_enemigo()

    def log(self, tipo, msg):
        h, m, s = int(self.t // 3600), int(self.t % 3600 // 60), int(self.t % 60)
        self.logs.insert(0, (f"{h:02d}:{m:02d}:{s:02d}", msg, tipo))
        del self.logs[8:]

    @property
    def velocidad(self):
        return (0.5, 1, 2, 5)[self.vel_i]

    def radio_region(self, fi):
        return max(24, (FLOTAS[fi][5] + 2) * PX_DEG)

    def centro(self, fi):
        return proyectar(FLOTAS[fi][4], FLOTAS[fi][3])

    # ---- eventos
    def spawn_enemigo(self):
        if len(self.enemigos) >= 14:
            return False
        fi = random.randrange(len(FLOTAS))
        bx, by = self.centro(fi)
        for _ in range(60):
            a, d = random.random() * 6.283, random.uniform(40, 75)
            p = (bx + d * math.cos(a), by + d * math.sin(a))
            if self.mundo.agua(*p):
                self.enemigos.append(Enemigo(*p))
                self.log("conflicto", f"Contacto hostil detectado cerca de {FLOTAS[fi][2]}.")
                return True
        return False

    def evento_aleatorio(self):
        r = random.random()
        if r < 0.25:
            fi = random.randrange(len(FLOTAS))
            bx, by = self.centro(fi)
            p = self.mundo.agua_cercana(bx + random.uniform(-40, 40), by + random.uniform(-30, 30))
            if p:
                self.tormentas.append({"x": p[0], "y": p[1], "r": random.uniform(30, 45), "t": 22.0})
                self.stats["tormentas"] += 1
                self.log("alerta", f"Tormenta en {FLOTAS[fi][2]}: velocidad reducida al 50 %.")
        elif r < 0.70:
            self.spawn_enemigo()
        else:
            libres = [g for g in self.grupos if g.falla <= 0]
            if libres:
                g = random.choice(libres)
                g.falla = 10.0
                self.stats["fallas"] += 1
                self.log("alerta", f"Fallo mecánico en {g.nombre}: el grupo se detiene.")

    # ---- órdenes
    def ordenar_flota(self, fi, destino):
        ok = 0
        for g in self.grupos:
            if g.fi != fi:
                continue
            d = self.mundo.agua_cercana(destino[0] + g.off[0] * 0.5, destino[1] + g.off[1] * 0.5)
            if not d:
                continue
            r = self.mundo.ruta((g.x, g.y), d)
            if r and len(r) > 1:
                g.path, g.ordenado, g.anchor = r[1:], True, d
                ok += 1
        if ok:
            self.ordenes[fi] = True
            self.log("info", f"{FLOTAS[fi][1]} se despliega hacia el destino ({ok} grupos).")
        else:
            self.log("alerta", f"Destino no alcanzable para la {FLOTAS[fi][1]}.")

    def volver_base(self, fi):
        bx, by = self.centro(fi)
        ok = 0
        for g in self.grupos:
            if g.fi == fi:
                r = self.mundo.ruta((g.x, g.y), g.anchor0)
                if r and len(r) > 1:
                    g.path, g.ordenado, g.anchor = r[1:], True, g.anchor0
                    ok += 1
                else:
                    g.anchor = g.anchor0
        self.ordenes[fi] = True
        self.log("info", f"{FLOTAS[fi][1]} regresa a su base.")

    # ---- simulación
    def simular(self, dt):
        self.t += dt
        for g in self.grupos:
            ev = g.actualizar(dt, self.mundo, self.tormentas)
            if ev == "reparado":
                self.log("info", f"{g.nombre}: unidad reparada.")
            elif ev == "llegada" and self.ordenes[g.fi] and all(not x.ordenado for x in self.grupos if x.fi == g.fi):
                self.ordenes[g.fi] = False
                self.log("info", f"{FLOTAS[g.fi][1]} completó el despliegue.")
        for s in self.tormentas[:]:
            s["t"] -= dt
            if s["t"] <= 0:
                self.tormentas.remove(s)
        for e in self.enemigos[:]:
            e.vida -= dt
            g = e.actualizar(dt, self.mundo, self.grupos)
            if g and not e.aviso:
                e.aviso = True
                self.log("conflicto", f"{g.nombre} entra en combate con un contacto hostil.")
            if e.eng > 5:
                self.explosion(e.x, e.y)
                self.stats["neutralizados"] += 1
                self.sumar_puntos(100, e.x, e.y, (255, 220, 90))
                self.log("info", f"Contacto hostil neutralizado por {g.nombre}.")
                if random.random() < 0.25 and g.falla <= 0:
                    g.falla = 10.0
                    self.stats["fallas"] += 1
                    self.log("alerta", f"Daños leves en {g.nombre}.")
                self.enemigos.remove(e)
            elif e.vida <= 0:
                self.log("alerta", "Contacto hostil perdido: salió del alcance.")
                self.enemigos.remove(e)
        self.t_evento -= dt
        if self.t_evento <= 0:
            self.evento_aleatorio()
            self.t_evento = random.uniform(7, 15) / NIVELES_DEFCON[self.defcon][0]
        self.actualizar_regiones(dt)

    def actualizar_regiones(self, dt):
        cr = NIVELES_DEFCON[self.defcon][1]
        for i in range(len(FLOTAS)):
            cx, cy = self.centro(i)
            rad = self.radio_region(i)
            ops = sum(1 for g in self.grupos if g.fi == i and g.falla <= 0 and math.dist((g.x, g.y), (cx, cy)) <= rad)
            hostiles = sum(1 for e in self.enemigos if math.dist((e.x, e.y), (cx, cy)) < rad + 25)
            self.ops[i] = ops
            d = 0.0
            if ops >= 3 and hostiles == 0:
                d += 2.5 * cr
            if hostiles:
                d -= 8.0 * hostiles
            if ops < 3:
                d -= 2.0
            self.control[i] = max(0.0, min(100.0, self.control[i] + d * dt))
            if not self.controlada[i] and self.control[i] >= 100:
                self.controlada[i] = True
                self.sumar_puntos(250, cx, cy - self.radio_region(i), FLOTAS[i][6])
                self.log("info", f"Región {FLOTAS[i][2]} bajo control.")
            elif self.controlada[i] and self.control[i] < 85:
                self.controlada[i] = False
                self.log("conflicto", f"Se pierde el control de {FLOTAS[i][2]}.")
        if not self.victoria:
            if sum(self.controlada) >= OBJETIVO_REGIONES:
                self.hold += dt
                if self.hold >= TIEMPO_SOSTENER:
                    self.victoria = True
                    self.log("info", "MISIÓN CUMPLIDA.")
            else:
                self.hold = max(0.0, self.hold - dt * 0.5)

    def explosion(self, x, y):
        """Explosión con chispas de varios tamaños/colores y una onda expansiva."""
        for _ in range(40):
            a, v = random.random() * 6.283, random.uniform(15, 90)
            col = random.choice([(255, 240, 160), (255, 170, 40), (255, 90, 30)])
            self.explosiones.append([x, y, math.cos(a) * v, math.sin(a) * v, 1.0, random.uniform(1.5, 3.5), col])
        self.ondas.append([x, y, 1.0])

    def sumar_puntos(self, puntos, x, y, color):
        """Suma puntaje, muestra un texto flotante y hace brillar el marcador del HUD."""
        self.stats["puntaje"] += puntos
        self.flotantes.append([x, y, 1.0, f"+{puntos}", color])
        self.flash_puntaje = 1.0

    # ---- entrada
    def grupo_en(self, pos, umbral=12):
        mejor, md = None, umbral
        for g in self.grupos:
            d = math.dist((g.x, g.y), pos)
            if d < md:
                mejor, md = g, d
        return mejor

    def clic(self, mx, my):
        if not (TOP <= my < TOP + MAP_H):
            return
        p = (mx, my - TOP)
        g = self.grupo_en(p)
        if g:
            self.sel = g.fi
            return
        if self.sel is not None:
            if not self.mundo.agua(*p):
                self.log("alerta", "Destino no navegable: elige un punto de océano.")
                return
            self.pings.append([p[0], p[1], 1.0])
            self.ordenar_flota(self.sel, p)

    def tecla(self, k):
        if k == pygame.K_SPACE:
            self.pausa = not self.pausa
        elif k == pygame.K_r:
            self.reiniciar()
        elif k == pygame.K_v:
            self.vel_i = (self.vel_i + 1) % 4
        elif k == pygame.K_ESCAPE:
            self.sel = None
        elif k == pygame.K_TAB:
            self.sel = 0 if self.sel is None else (self.sel + 1) % len(FLOTAS)
        elif k == pygame.K_b and self.sel is not None:
            self.volver_base(self.sel)
        elif pygame.K_1 <= k <= pygame.K_5:
            self.defcon = k - pygame.K_0
            self.log("conflicto" if self.defcon <= 2 else "alerta", f"Nivel DEFCON {self.defcon}.")

    # ---- dibujo
    def texto(self, s, pos, fuente=None, color=(207, 238, 230)):
        self.pantalla.blit((fuente or self.f_chica).render(s, True, color), pos)

    def dibujar(self):
        p = self.pantalla
        p.fill((4, 7, 11))
        p.blit(self.mundo.fondo, (0, TOP))
        # regiones
        for i, f in enumerate(FLOTAS):
            cx, cy = self.centro(i)
            cy += TOP
            r = int(self.radio_region(i))
            col = f[6]
            pygame.draw.circle(p, col if self.controlada[i] else (90, 110, 120), (int(cx), int(cy)), r, 2 if self.controlada[i] else 1)
            if 0 < self.control[i] < 100:
                pygame.draw.arc(p, col, (cx - r - 3, cy - r - 3, 2 * r + 6, 2 * r + 6), -1.57, -1.57 + 6.283 * self.control[i] / 100, 3)
        # tormentas
        for s in self.tormentas:
            surf = pygame.Surface((int(s["r"] * 2), int(s["r"] * 2)), pygame.SRCALPHA)
            pygame.draw.circle(surf, (200, 220, 255, 55), (int(s["r"]), int(s["r"])), int(s["r"]))
            pygame.draw.circle(surf, (225, 240, 255, 130), (int(s["r"]), int(s["r"])), int(s["r"]), 2)
            p.blit(surf, (s["x"] - s["r"], s["y"] - s["r"] + TOP))
        # rutas y estelas
        for g in self.grupos:
            col = FLOTAS[g.fi][6]
            if len(g.estela) > 1:
                for a, b in zip(g.estela, g.estela[1:]):
                    pygame.draw.line(p, tuple(c // 2 for c in col), (a[0], a[1] + TOP), (b[0], b[1] + TOP), 1)
            if g.ordenado and g.path:
                pts = [(g.x, g.y + TOP)] + [(x, y + TOP) for x, y in g.path]
                for a, b in zip(pts, pts[1:]):
                    n = max(1, int(math.dist(a, b) / 8))
                    for k in range(0, n, 2):
                        q = (a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n)
                        pygame.draw.circle(p, col, (int(q[0]), int(q[1])), 1)
        # grupos
        for g in self.grupos:
            col = FLOTAS[g.fi][6]
            sel = self.sel == g.fi
            x, y = g.x, g.y + TOP
            c, s_ = math.cos(g.rumbo), math.sin(g.rumbo)
            tam = 6 if sel else 4.5
            pts = [(x + c * tam * 1.5, y + s_ * tam * 1.5), (x - c * tam - s_ * tam * .8, y - s_ * tam + c * tam * .8),
                   (x - c * tam + s_ * tam * .8, y - s_ * tam - c * tam * .8)]
            if g.falla > 0:
                col = (255, 176, 0) if int(self.t * 4) % 2 == 0 else (90, 60, 0)
            pygame.draw.polygon(p, col, pts)
            if sel:
                pygame.draw.circle(p, (255, 255, 255), (int(x), int(y)), 11, 1)
        # enemigos
        for e in self.enemigos:
            x, y = e.x, e.y + TOP
            k = 4 + int(1.5 * math.sin(self.t * 6))
            pygame.draw.polygon(p, (255, 46, 46), [(x, y - k), (x + k, y), (x, y + k), (x - k, y)])
            pygame.draw.circle(p, (255, 46, 46), (int(x), int(y)), 14, 1)
        # efectos
        for o in self.ondas[:]:
            o[2] -= 0.016 * 1.5
            if o[2] <= 0:
                self.ondas.remove(o)
                continue
            r = int(6 + (1 - o[2]) * 34)
            surf = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
            if o[2] > 0.75:  # destello inicial
                pygame.draw.circle(surf, (255, 250, 220, int(255 * (o[2] - 0.75) * 4)), (r + 2, r + 2), max(3, r // 2))
            pygame.draw.circle(surf, (255, 200, 80, int(220 * o[2])), (r + 2, r + 2), r, 2)
            p.blit(surf, (o[0] - r - 2, o[1] + TOP - r - 2))
        for e in self.explosiones[:]:
            e[2] *= 0.96  # las chispas frenan
            e[3] *= 0.96
            e[0] += e[2] * 0.016
            e[1] += e[3] * 0.016
            e[4] -= 0.016 * 1.1
            if e[4] <= 0:
                self.explosiones.remove(e)
            else:
                col = tuple(int(c * (0.4 + 0.6 * e[4])) for c in e[6])
                pygame.draw.circle(p, col, (int(e[0]), int(e[1] + TOP)), max(1, int(e[5] * e[4] + 0.5)))
        for ft in self.flotantes[:]:
            ft[1] -= 0.016 * 30  # sube
            ft[2] -= 0.016 * 0.8
            if ft[2] <= 0:
                self.flotantes.remove(ft)
                continue
            img = self.f_med.render(ft[3], True, ft[4])
            img.set_alpha(int(255 * min(1.0, ft[2] * 1.5)))
            p.blit(img, (ft[0] - img.get_width() // 2, ft[1] + TOP - 18))
        for pg in self.pings[:]:
            pg[2] -= 0.02
            if pg[2] <= 0:
                self.pings.remove(pg)
            else:
                pygame.draw.circle(p, (255, 176, 0), (int(pg[0]), int(pg[1] + TOP)), int(4 + (1 - pg[2]) * 26), 1)
        self.dibujar_hud()
        if self.victoria:
            vel = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
            vel.fill((30, 20, 0, 170))
            p.blit(vel, (0, 0))
            t = self.f_grande.render("MISIÓN CUMPLIDA", True, (245, 197, 66))
            p.blit(t, (WIN_W // 2 - t.get_width() // 2, 240))
            s = self.stats
            m = f"Tiempo {int(self.t // 60)} min {int(self.t % 60)} s · Neutralizados {s['neutralizados']} · Tormentas {s['tormentas']} · Fallos {s['fallas']}"
            t2 = self.f_med.render(m, True, (255, 255, 255))
            p.blit(t2, (WIN_W // 2 - t2.get_width() // 2, 300))
            tp = self.f_med.render(f"PUNTAJE FINAL: {s['puntaje']}", True, (255, 220, 90))
            p.blit(tp, (WIN_W // 2 - tp.get_width() // 2, 328))
            t3 = self.f_chica.render("R: nueva partida", True, (217, 195, 131))
            p.blit(t3, (WIN_W // 2 - t3.get_width() // 2, 360))
        elif self.pausa:
            t = self.f_grande.render("PAUSA", True, (255, 255, 255))
            p.blit(t, (WIN_W // 2 - t.get_width() // 2, 100 + TOP))
        pygame.display.flip()

    def dibujar_hud(self):
        p = self.pantalla
        col = COLOR_DEFCON[self.defcon]
        pygame.draw.rect(p, (2, 8, 12), (0, 0, WIN_W, TOP))
        pygame.draw.line(p, col, (0, TOP - 1), (WIN_W, TOP - 1), 2)
        self.texto("OPERACIÓN NEPTUNO", (14, 8), self.f_med, CIAN)
        self.texto(f"Misión {int(self.t // 60):02d}:{int(self.t % 60):02d}   x{self.velocidad}", (14, 29), self.f_chica, (127, 163, 154))
        self.texto(f"DEFCON {self.defcon}", (260, 8), self.f_med, col)
        self.texto("teclas 1-5", (260, 29), self.f_chica, (127, 163, 154))
        nc = sum(self.controlada)
        self.texto(f"Regiones {nc}/{len(FLOTAS)}  (meta {OBJETIVO_REGIONES})", (400, 8), self.f_med)
        pygame.draw.rect(p, (40, 50, 55), (400, 32, 260, 8))
        pygame.draw.rect(p, CIAN, (400, 32, int(260 * nc / len(FLOTAS)), 8))
        pygame.draw.rect(p, (255, 255, 255), (400 + int(260 * OBJETIVO_REGIONES / len(FLOTAS)), 30, 2, 12))
        self.texto(f"Sostener {int(self.hold)}/{int(TIEMPO_SOSTENER)} s", (690, 8), self.f_med, (255, 176, 0))
        pygame.draw.rect(p, (40, 50, 55), (690, 32, 160, 8))
        pygame.draw.rect(p, (255, 176, 0), (690, 32, int(160 * self.hold / TIEMPO_SOSTENER), 8))
        # marcador de puntaje: brilla en blanco al sumar puntos y vuelve a dorado
        self.flash_puntaje = max(0.0, self.flash_puntaje - 0.016 * 2)
        k = self.flash_puntaje
        col_p = (255, int(220 + 35 * k), int(90 + 165 * k))
        self.texto("PUNTAJE", (875, 6), self.f_chica, (127, 163, 154))
        self.texto(f"{self.stats['puntaje']:05d}", (875, 22), self.f_med, col_p)
        if k > 0:
            pygame.draw.rect(p, col_p, (870, 20, 70, 22), 1)
        # consola inferior
        y0 = TOP + MAP_H
        pygame.draw.rect(p, (3, 9, 13), (0, y0, WIN_W, WIN_H - y0))
        pygame.draw.line(p, CIAN, (0, y0), (WIN_W, y0), 1)
        if self.sel is not None:
            f = FLOTAS[self.sel]
            self.texto(f"FLOTA: {f[1]} · {f[2]} · ops {self.ops[self.sel]}/{GRUPOS_POR_FLOTA} · control {int(self.control[self.sel])} %", (14, y0 + 6), self.f_med, f[6])
            self.texto("Clic en el océano: mover · B: volver a base · ESC: deseleccionar", (14, y0 + 26), self.f_chica, (127, 163, 154))
        else:
            self.texto("Clic en un barco para seleccionar su flota · TAB cambia de flota · ESPACIO pausa · V velocidad · R reinicia", (14, y0 + 8), self.f_chica, (127, 163, 154))
        self.texto(f"{int(self.reloj.get_fps())} FPS", (WIN_W - 60, WIN_H - 18), self.f_chica, (60, 90, 85))
        colores = {"info": (93, 255, 160), "alerta": (255, 176, 0), "conflicto": (255, 70, 70)}
        for i, (h, m, tipo) in enumerate(self.logs[:6]):
            self.texto(h + "  " + m, (14, y0 + 50 + i * 16), self.f_chica, colores[tipo])

    # ---- bucle
    def correr(self, frames=None):
        n = 0
        while True:
            dt_real = self.reloj.tick(60) / 1000.0
            if frames is not None:
                dt_real = 1 / 30
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    return
                if ev.type == pygame.KEYDOWN:
                    self.tecla(ev.key)
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    self.clic(*ev.pos)
            if not self.pausa and not self.victoria:
                self.simular(min(dt_real, 0.05) * self.velocidad)
            self.dibujar()
            n += 1
            if frames is not None:
                yield n
                if n >= frames:
                    return


def prueba():
    """Modo prueba sin ventana: simula, da órdenes y guarda una captura."""
    random.seed(7)
    j = Juego()
    j.vel_i = 3
    for _ in j.correr(600):
        pass
    # órdenes: mover flota 0 al Pacífico, flota 3 al Atlántico, una inalcanzable
    j.clic(*[int(proyectar(-140, 15)[0]), int(proyectar(-140, 15)[1]) + TOP])  # selecciona nada / orden
    j.sel = 0
    j.clic(int(proyectar(-150, 0)[0]), int(proyectar(-150, 0)[1]) + TOP)
    j.sel = 3
    j.clic(int(proyectar(-40, 20)[0]), int(proyectar(-40, 20)[1]) + TOP)
    j.sel = 6
    j.clic(int(proyectar(20, 5)[0]), int(proyectar(20, 5)[1]) + TOP)  # tierra (África): debe rechazarse
    for _ in j.correr(900):
        pass
    pygame.image.save(j.pantalla, "captura.png")
    esperado = 100 * j.stats["neutralizados"]
    assert j.stats["puntaje"] >= esperado, "el puntaje no cuenta los neutralizados"
    print("PRUEBA OK · t=%.0fs · regiones=%d · neutralizados=%d · puntaje=%d · logs=%d" % (j.t, sum(j.controlada), j.stats["neutralizados"], j.stats["puntaje"], len(j.logs)))
    for l in j.logs[:4]:
        print("  ", l)


if __name__ == "__main__":
    if TEST:
        prueba()
    else:
        for _ in Juego().correr():
            pass
        pygame.quit()
