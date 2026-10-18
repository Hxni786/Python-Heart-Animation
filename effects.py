"""
effects.py - Visual Effects, Glow Cache, Lighting, and Heartbeat Engine
Provides cached radial glow textures with premultiplied alpha for flawless
additive blending, organic heartbeat pulsation, soft diffuse background halos,
and glowing romantic text rendering.
"""

import math
import numpy as np
import pygame

# Romantic Palette Constants
COLOR_NEON_PINK   = (255, 45, 130)
COLOR_DEEP_RED    = (225, 20, 65)
COLOR_MAGENTA     = (210, 0, 115)
COLOR_SOFT_ROSE   = (255, 160, 190)
COLOR_WHITE_PINK  = (255, 240, 248)
COLOR_WARM_WHITE  = (255, 250, 252)

PALETTE = [
    COLOR_NEON_PINK,
    COLOR_DEEP_RED,
    COLOR_MAGENTA,
    COLOR_SOFT_ROSE,
    COLOR_WHITE_PINK
]


class GlowCache:
    """
    High-performance pre-rendered radial glow textures with premultiplied alpha.
    Ensures that pygame.BLEND_ADD adds pure light with zero square tile artifacts.
    """

    def __init__(self):
        # Radii of precomputed delicate starlight glow discs
        self.radii = [2, 4, 7, 12, 20, 34, 52]
        self.cache = {}
        self._generate_cache()

    def _generate_cache(self):
        """Precompute smooth glow surfaces for each color and radius."""
        for color in PALETTE:
            self.cache[color] = {}
            for r in self.radii:
                self.cache[color][r] = self._create_radial_glow(color, r)

        # White highlight cache for particle cores
        white = (255, 255, 255)
        self.cache[white] = {}
        for r in [2, 4, 7, 12]:
            self.cache[white][r] = self._create_radial_glow(white, r, falloff=2.6, core_scale=3.5)

    def _create_radial_glow(self, color, radius, falloff=2.2, core_scale=2.8):
        """
        Creates a square pygame.Surface with a smooth cosine bell radial glow
        and PREMULTIPLIED RGB channels for authentic physical light addition.
        """
        size = radius * 2 + 1
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        
        y, x = np.ogrid[:size, :size]
        dist = np.sqrt((x - radius)**2 + (y - radius)**2) / max(radius, 1.0)
        
        # Zero derivative at boundary avoids harsh cutoff
        factor = np.clip(1.0 - dist, 0.0, 1.0)
        falloff_curve = 0.5 * (1.0 - np.cos(factor * np.pi))
        alpha_norm = falloff_curve ** falloff
        
        # White-hot pinpoint core
        core_norm = np.clip(1.0 - dist * core_scale, 0.0, 1.0) ** 2.2
        
        # Premultiply RGB by alpha_norm
        r = np.clip((color[0] + core_norm * 180.0) * alpha_norm, 0, 255).astype(np.uint8)
        g = np.clip((color[1] + core_norm * 180.0) * alpha_norm, 0, 255).astype(np.uint8)
        b = np.clip((color[2] + core_norm * 180.0) * alpha_norm, 0, 255).astype(np.uint8)
        a = (alpha_norm * 255.0).astype(np.uint8)
        
        pygame.surfarray.pixels_alpha(surf)[:] = a.T
        rgb = np.stack([r, g, b], axis=-1)
        pygame.surfarray.pixels3d(surf)[:] = rgb.transpose((1, 0, 2))
        return surf

    def get_glow(self, color, radius):
        """Finds closest pre-rendered glow surface for requested color and radius."""
        color_cache = self.cache.get(color, self.cache[COLOR_NEON_PINK])
        closest_r = min(self.radii, key=lambda r: abs(r - radius))
        return color_cache[closest_r]

    def get_core_glow(self, radius):
        """Returns intense white core glow."""
        white_cache = self.cache[(255, 255, 255)]
        closest_r = min(white_cache.keys(), key=lambda r: abs(r - radius))
        return white_cache[closest_r]


class HeartEffects:
    """
    Manages atmospheric halos, heartbeat pulsation, and visual timing.
    """

    def __init__(self, glow_cache, heart_path):
        self.glow = glow_cache
        self.path = heart_path
        self.halo_glow = self.glow.get_glow(COLOR_MAGENTA, 34)
        self.halo_w, self.halo_h = self.halo_glow.get_size()

    def get_heartbeat(self, t):
        """
        Natural, romantic double-beat heartbeat pulse ("lub-dub").
        Active primarily from 6.5s onward.
        Returns:
            scale_multiplier (float): e.g. 1.0 to 1.045
            glow_multiplier (float): e.g. 1.0 to 1.30
        """
        if t < 6.5:
            return 1.0, 1.0
            
        # Resting romantic pulse: ~52 bpm (cycle = 1.15 seconds)
        cycle_time = 1.15
        elapsed_in_pulse = t - 6.5
        phase = (elapsed_in_pulse % cycle_time) / cycle_time
        
        # Double-pulse wave
        # Beat 1 (Systole - primary expansion): 0.0 to 0.16
        if phase < 0.16:
            p = math.sin(phase / 0.16 * math.pi)
            scale = 1.0 + 0.045 * (p ** 1.8)
            glow = 1.0 + 0.28 * p
        # Beat 2 (Secondary gentle rebound): 0.20 to 0.34
        elif 0.20 <= phase < 0.34:
            p = math.sin((phase - 0.20) / 0.14 * math.pi)
            scale = 1.0 + 0.022 * (p ** 1.8)
            glow = 1.0 + 0.16 * p
        else:
            scale = 1.0
            glow = 1.0
            
        return scale, glow

    def render_halo(self, surface, t, scale, glow_boost):
        """
        Draws the soft background heart aura, modulated by timeline phase and heartbeat.
        """
        if t < 4.5:
            return  # Halo emerges in Phase 3
            
        # Phase 3 fade-in: 4.5s to 6.5s
        if 4.5 <= t < 6.5:
            alpha_factor = (t - 4.5) / 2.0
        else:
            alpha_factor = 1.0
            
        if alpha_factor <= 0.05:
            return
            
        # Sample points along the heart path to cast a soft diffuse aura
        step = 30
        for i in range(0, 1200, step):
            u = i / 1200.0
            x, y = self.path.get_screen_point(u, scale_factor=scale)
            surface.blit(
                self.halo_glow,
                (x - self.halo_w // 2, y - self.halo_h // 2),
                special_flags=pygame.BLEND_ADD
            )


class TextRenderer:
    """
    Renders the romantic message with smooth fade-in and subtle glow:
    '“Every little thing reminds me of you.”'
    """

    def __init__(self, font_path=None, font_size=36):
        self.font = self._load_font(font_path, font_size)
        self.message = "“Every little thing reminds me of you.”"

    def _load_font(self, font_path, font_size):
        if font_path:
            try:
                return pygame.font.Font(font_path, font_size)
            except Exception:
                pass
                
        fallbacks = ['georgia', 'segoeui', 'palatino', 'garamond', 'serif']
        for name in fallbacks:
            try:
                f = pygame.font.SysFont(name, font_size)
                if f:
                    return f
            except Exception:
                continue
                
        return pygame.font.Font(None, font_size)

    def _make_premultiplied_text(self, text, color):
        """Renders text with premultiplied alpha for clean additive blending."""
        surf = self.font.render(text, True, color)
        a = pygame.surfarray.pixels_alpha(surf).astype(np.float32) / 255.0
        rgb = pygame.surfarray.pixels3d(surf)
        for i in range(3):
            rgb[..., i] = (rgb[..., i] * a).astype(np.uint8)
        return surf

    def render(self, surface, current_time, target_y=925):
        """
        Fades in the message starting at 8.0s through 9.6s.
        Target Y is centered horizontally beneath the heart.
        """
        if current_time < 8.0:
            return
            
        # Smooth smoothstep fade-in over [8.0, 9.6] seconds
        raw_u = np.clip((current_time - 8.0) / 1.6, 0.0, 1.0)
        smooth_u = raw_u * raw_u * (3.0 - 2.0 * raw_u)
        
        if smooth_u <= 0.01:
            return
            
        # Fade colors
        fg_col = (
            int(255 * smooth_u),
            int(246 * smooth_u),
            int(250 * smooth_u)
        )
        glow_col = (
            int(190 * smooth_u),
            int(45 * smooth_u),
            int(95 * smooth_u)
        )
        
        fg_surf = self._make_premultiplied_text(self.message, fg_col)
        glow_surf = self._make_premultiplied_text(self.message, glow_col)
        
        tw, th = fg_surf.get_size()
        tx = 1920 // 2 - tw // 2
        ty = target_y
        
        # Render delicate glowing contour
        for ox, oy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1)]:
            surface.blit(glow_surf, (tx + ox, ty + oy), special_flags=pygame.BLEND_ADD)
            
        # Render crisp foreground text
        surface.blit(fg_surf, (tx, ty), special_flags=pygame.BLEND_ADD)
