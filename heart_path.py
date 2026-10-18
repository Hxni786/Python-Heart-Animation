"""
heart_path.py - Mathematical Heart Curve and Trajectory Engine
Defines the parametric heart curve with arc-length parameterization,
drawing progression, anchor point distribution, and volumetric depth.
"""

import math
import numpy as np

# Canvas reference geometry
CANVAS_WIDTH = 1920
CANVAS_HEIGHT = 1080
CENTER_X = 960.0
CENTER_Y = 445.0  # Elegantly positioned to leave balanced space for message below
BASE_SCALE = 22.0  # Produces a ~704px wide by ~638px high majestic heart


class HeartPath:
    """
    Mathematical parametric heart model.
    x(t) = -16 * sin^3(t)
    y(t) = -(13*cos(t) - 5*cos(2t) - 2*cos(3t) - cos(4t))
    Arc-length reparameterized so drawing speed is silky smooth and uniform.
    """

    def __init__(self, center_x=CENTER_X, center_y=CENTER_Y, scale=BASE_SCALE, resolution=4000):
        self.center_x = center_x
        self.center_y = center_y
        self.scale = scale
        self.resolution = resolution
        
        self._build_arc_length_tables()

    def _build_arc_length_tables(self):
        """
        Precompute dense parametric points and build arc-length lookup table.
        Tracing t from 0 to 2*pi:
        t=0: Top center notch
        0 -> pi/2: Upper-left arch
        pi/2 -> pi: Left outer curve down to bottom sharp tip
        pi -> 3pi/2: Right outer curve up from bottom tip
        3pi/2 -> 2pi: Upper-right arch curving down into top notch
        """
        t = np.linspace(0, 2.0 * np.pi, self.resolution)
        
        # Smooth parametric heart equations
        # Note: -16 * sin^3(t) ensures stroke goes to left first (negative X)
        raw_x = -16.0 * (np.sin(t) ** 3)
        raw_y = -(13.0 * np.cos(t) - 5.0 * np.cos(2.0 * t) - 2.0 * np.cos(3.0 * t) - np.cos(4.0 * t))
        
        # Calculate arc lengths along the curve
        dx = np.diff(raw_x)
        dy = np.diff(raw_y)
        segment_lengths = np.sqrt(dx ** 2 + dy ** 2)
        
        cumulative_s = np.zeros(self.resolution)
        cumulative_s[1:] = np.cumsum(segment_lengths)
        self.total_length = cumulative_s[-1]
        
        # Normalized cumulative arc-length u in [0, 1]
        self.u_table = cumulative_s / self.total_length
        self.x_table = raw_x
        self.y_table = raw_y

    def get_raw_point_at_u(self, u):
        """
        Returns (raw_x, raw_y) normalized by arc length u in [0, 1].
        Uniform linear speed along the perimeter.
        """
        u_clamped = np.clip(u, 0.0, 1.0)
        rx = float(np.interp(u_clamped, self.u_table, self.x_table))
        ry = float(np.interp(u_clamped, self.u_table, self.y_table))
        return rx, ry

    def get_screen_point(self, u, scale_factor=1.0, offset_normal=(0.0, 0.0)):
        """
        Returns screen coordinates (x, y) at progress u in [0, 1].
        """
        rx, ry = self.get_raw_point_at_u(u)
        s = self.scale * scale_factor
        x = self.center_x + rx * s + offset_normal[0]
        y = self.center_y + ry * s + offset_normal[1]
        return x, y

    def get_tangent_and_normal(self, u, delta=0.002):
        """
        Returns unit tangent (tx, ty) and outward normal (nx, ny) at progress u.
        """
        u0 = max(0.0, u - delta)
        u1 = min(1.0, u + delta)
        x0, y0 = self.get_screen_point(u0)
        x1, y1 = self.get_screen_point(u1)
        
        dx = x1 - x0
        dy = y1 - y0
        dist = math.hypot(dx, dy)
        if dist < 1e-6:
            return (1.0, 0.0), (0.0, -1.0)
        
        tx = dx / dist
        ty = dy / dist
        # Normal pointing outward
        nx = -ty
        ny = tx
        return (tx, ty), (nx, ny)

    def generate_perimeter_anchors(self, count=1500, rng=None):
        """
        Distributes particles along the heart boundary across multiple subtle layers:
        - Primary outline curve
        - Subtle inner rim (depth)
        - Subtle outer halo (luminescence)
        Returns a list of dicts with anchor details.
        """
        if rng is None:
            rng = np.random.default_rng(42)
            
        anchors = []
        
        # Layer 1: Core primary stroke (~60% of perimeter particles)
        n_core = int(count * 0.60)
        u_core = np.linspace(0.001, 0.999, n_core)
        # Add slight natural jitter to avoid robotic line
        u_core += rng.normal(0, 0.0015, n_core)
        u_core = np.clip(u_core, 0.0005, 0.9995)
        
        for u in u_core:
            # Subtle radial scatter (-1.5 to +1.5 px)
            jitter_scale = 1.0 + float(rng.normal(0, 0.008))
            rx, ry = self.get_raw_point_at_u(u)
            base_x = self.center_x + rx * self.scale * jitter_scale
            base_y = self.center_y + ry * self.scale * jitter_scale
            anchors.append({
                "u": float(u),
                "base_x": base_x,
                "base_y": base_y,
                "rel_x": base_x - self.center_x,
                "rel_y": base_y - self.center_y,
                "layer": "core",
                "scale_factor": jitter_scale
            })

        # Layer 2: Inner rim particles (~20% of perimeter)
        n_inner = int(count * 0.20)
        u_inner = rng.uniform(0.002, 0.998, n_inner)
        for u in u_inner:
            inner_scale = float(rng.uniform(0.95, 0.985))
            rx, ry = self.get_raw_point_at_u(u)
            base_x = self.center_x + rx * self.scale * inner_scale
            base_y = self.center_y + ry * self.scale * inner_scale
            anchors.append({
                "u": float(u),
                "base_x": base_x,
                "base_y": base_y,
                "rel_x": base_x - self.center_x,
                "rel_y": base_y - self.center_y,
                "layer": "inner",
                "scale_factor": inner_scale
            })

        # Layer 3: Outer halo particles (~20% of perimeter)
        n_outer = count - n_core - n_inner
        u_outer = rng.uniform(0.002, 0.998, n_outer)
        for u in u_outer:
            outer_scale = float(rng.uniform(1.015, 1.05))
            rx, ry = self.get_raw_point_at_u(u)
            base_x = self.center_x + rx * self.scale * outer_scale
            base_y = self.center_y + ry * self.scale * outer_scale
            anchors.append({
                "u": float(u),
                "base_x": base_x,
                "base_y": base_y,
                "rel_x": base_x - self.center_x,
                "rel_y": base_y - self.center_y,
                "layer": "outer",
                "scale_factor": outer_scale
            })

        # Sort primarily by u for sequential drawing coherence
        anchors.sort(key=lambda a: a["u"])
        return anchors

    def generate_interior_points(self, count=450, rng=None):
        """
        Generates volumetric depth particles inside the heart.
        Awakened in Phase 3 (4.5s - 6.5s) to give the heart rich warmth.
        """
        if rng is None:
            rng = np.random.default_rng(108)

        interior = []
        for _ in range(count):
            u = float(rng.uniform(0.01, 0.99))
            rx, ry = self.get_raw_point_at_u(u)
            
            # Radial contraction factor r: biased towards perimeter for elegance
            # (power law puts more particles near edge, fewer in dead center)
            r = float(rng.power(2.5) * 0.88 + 0.08)
            
            base_x = self.center_x + rx * self.scale * r
            base_y = self.center_y + ry * self.scale * r
            
            # Awakening time smoothly distributed during Phase 3 (4.5s to 6.2s)
            awaken_time = float(rng.uniform(4.55, 6.25))
            
            interior.append({
                "base_x": base_x,
                "base_y": base_y,
                "rel_x": base_x - self.center_x,
                "rel_y": base_y - self.center_y,
                "awaken_time": awaken_time,
                "r": r,
                "u": u
            })
            
        interior.sort(key=lambda p: p["awaken_time"])
        return interior

    def generate_ambient_stars(self, count=160, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, rng=None):
        """
        Generates subtle floating stardust particles drifting in the surrounding darkness.
        """
        if rng is None:
            rng = np.random.default_rng(777)
            
        stars = []
        for _ in range(count):
            # Pick positions across the screen
            x = float(rng.uniform(40, width - 40))
            y = float(rng.uniform(40, height - 40))
            
            # Avoid placing too many directly inside the heart core
            dist_to_center = math.hypot(x - self.center_x, y - self.center_y)
            if dist_to_center < 180 and rng.random() > 0.15:
                # Push outwards
                angle = rng.uniform(0, 2 * math.pi)
                x = self.center_x + math.cos(angle) * rng.uniform(360, 800)
                y = self.center_y + math.sin(angle) * rng.uniform(320, 520)
                x = np.clip(x, 40, width - 40)
                y = np.clip(y, 40, height - 40)
                
            stars.append({
                "x": float(x),
                "y": float(y),
                "vx": float(rng.uniform(-12.0, 12.0)),
                "vy": float(rng.uniform(-8.0, 8.0)),
                "base_radius": float(rng.uniform(1.2, 2.8)),
                "twinkle_speed": float(rng.uniform(1.5, 4.0)),
                "phase": float(rng.uniform(0, 2 * math.pi)),
                "color_idx": int(rng.integers(0, 4))
            })
        return stars
