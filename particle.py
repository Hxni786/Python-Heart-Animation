"""
particle.py - Particle Dynamics and Drawing System
Defines the lead drawing spark, perimeter particles, interior volumetric depth,
ambient floating stardust, and drifting dissolution particles.
Tuned for delicate starlight radiance and cinematic elegance.
"""

import math
import random
import numpy as np
import pygame

from effects import (
    COLOR_NEON_PINK,
    COLOR_DEEP_RED,
    COLOR_MAGENTA,
    COLOR_SOFT_ROSE,
    COLOR_WHITE_PINK,
    COLOR_WARM_WHITE,
    PALETTE
)


class LeadSpark:
    """
    The luminous 'artist brush' that draws the heart curve from 1.0s to 4.5s.
    Leaves a silky decaying light trail and emits flying micro-sparks.
    """

    def __init__(self, heart_path, glow_cache):
        self.path = heart_path
        self.glow = glow_cache
        self.x, self.y = self.path.get_screen_point(0.0)
        self.trail = []  # stores (x, y, birth_time, color, radius)
        self.micro_sparks = []
        self.is_finished = False

    def update(self, t, dt):
        """Updates position along the heart path and handles trail/sparks."""
        # Clean expired micro-sparks
        self.micro_sparks = [s for s in self.micro_sparks if t - s['birth'] < s['life']]
        for s in self.micro_sparks:
            s['x'] += s['vx'] * dt
            s['y'] += s['vy'] * dt
            s['vx'] *= (0.92 ** (dt * 60))
            s['vy'] *= (0.92 ** (dt * 60))

        # Clean expired trail points (trail lasts ~0.28s)
        self.trail = [p for p in self.trail if t - p['birth'] < 0.28]

        # Phase 1: 0.0s to 1.0s (First spark awakening)
        if t < 1.0:
            self.x, self.y = self.path.get_screen_point(0.0)
            if t >= 0.3:
                # Add subtle trail pulse at the spark
                if random.random() < 0.4:
                    self.trail.append({
                        'x': self.x + random.uniform(-1.5, 1.5),
                        'y': self.y + random.uniform(-1.5, 1.5),
                        'birth': t,
                        'color': COLOR_NEON_PINK,
                        'radius': 4
                    })
            return

        # Phase 2: 1.0s to 4.5s (Drawing the curve)
        if 1.0 <= t <= 4.5:
            # Normalized progression u from 0.0 to 1.0
            u = (t - 1.0) / 3.5
            new_x, new_y = self.path.get_screen_point(u)
            
            # Emit trail points along the movement vector for continuous glow ribbon
            dist = math.hypot(new_x - self.x, new_y - self.y)
            steps = max(1, int(dist / 4.0))
            for i in range(steps):
                frac = (i + 1) / float(steps)
                ix = self.x + (new_x - self.x) * frac
                iy = self.y + (new_y - self.y) * frac
                self.trail.append({
                    'x': ix,
                    'y': iy,
                    'birth': t,
                    'color': COLOR_WHITE_PINK if random.random() < 0.35 else COLOR_NEON_PINK,
                    'radius': random.choice([4, 7])
                })

            # Emit flying energetic micro-sparks
            if random.random() < 0.7:
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(20.0, 75.0)
                self.micro_sparks.append({
                    'x': new_x,
                    'y': new_y,
                    'vx': math.cos(angle) * speed,
                    'vy': math.sin(angle) * speed,
                    'birth': t,
                    'life': random.uniform(0.15, 0.38),
                    'color': random.choice([COLOR_WHITE_PINK, COLOR_SOFT_ROSE, COLOR_NEON_PINK])
                })

            self.x = new_x
            self.y = new_y
        else:
            self.is_finished = True

    def render(self, surface, t):
        """Renders lead spark, silky trail, and micro-sparks."""
        if t < 0.3:
            return  # Darkness before spark

        # Render trailing ribbon
        for p in self.trail:
            age = t - p['birth']
            fade = max(0.0, 1.0 - (age / 0.28))
            if fade <= 0.05:
                continue
            glow_surf = self.glow.get_glow(p['color'], p['radius'])
            gw, gh = glow_surf.get_size()
            surface.blit(glow_surf, (p['x'] - gw // 2, p['y'] - gh // 2), special_flags=pygame.BLEND_ADD)

        # Render micro-sparks
        for s in self.micro_sparks:
            age = t - s['birth']
            fade = max(0.0, 1.0 - (age / s['life']))
            if fade <= 0.05:
                continue
            glow_surf = self.glow.get_glow(s['color'], 2)
            gw, gh = glow_surf.get_size()
            surface.blit(glow_surf, (s['x'] - gw // 2, s['y'] - gh // 2), special_flags=pygame.BLEND_ADD)

        # Render lead head if drawing is active
        if t <= 4.5:
            if t < 1.0:
                pulse = 1.0 + 0.25 * math.sin(t * 12.0)
                rad_outer = int(12 * pulse)
                rad_inner = int(4 * pulse)
            else:
                rad_outer = 20
                rad_inner = 7

            # Outer soft aura
            outer_glow = self.glow.get_glow(COLOR_NEON_PINK, rad_outer)
            ow, oh = outer_glow.get_size()
            surface.blit(outer_glow, (self.x - ow // 2, self.y - oh // 2), special_flags=pygame.BLEND_ADD)

            # Bright core
            mid_glow = self.glow.get_glow(COLOR_WHITE_PINK, rad_inner)
            mw, mh = mid_glow.get_size()
            surface.blit(mid_glow, (self.x - mw // 2, self.y - mh // 2), special_flags=pygame.BLEND_ADD)

            # Pinpoint white core
            core = self.glow.get_core_glow(4)
            cw, ch = core.get_size()
            surface.blit(core, (self.x - cw // 2, self.y - ch // 2), special_flags=pygame.BLEND_ADD)


class PerimeterParticle:
    """
    Individual particle outlining the heart curve.
    Awakens when the lead spark passes its u position, sweeps into place
    with smooth damped spring dynamics, and continuously shimmers and pulses.
    """

    def __init__(self, anchor, heart_path, glow_cache, rng):
        self.anchor = anchor
        self.path = heart_path
        self.glow = glow_cache
        
        # When this particle is born: mapped from u to [1.0, 4.5]s
        self.draw_time = 1.0 + anchor['u'] * 3.5
        self.is_active = False
        
        # Base coordinates
        self.base_x = anchor['base_x']
        self.base_y = anchor['base_y']
        self.rel_x = anchor['rel_x']
        self.rel_y = anchor['rel_y']
        
        # Current physical state
        self.x = self.base_x
        self.y = self.base_y
        self.vx = 0.0
        self.vy = 0.0
        
        # Visual attributes
        # Romantic color distribution
        palette_weights = [COLOR_NEON_PINK] * 8 + [COLOR_MAGENTA] * 4 + \
                          [COLOR_SOFT_ROSE] * 3 + [COLOR_DEEP_RED] * 2 + [COLOR_WHITE_PINK] * 2
        self.color = rng.choice(palette_weights)
        
        # Delicate starlight radius
        if anchor['layer'] == 'core':
            self.radius = rng.choice([4, 4, 7, 7, 12])
        elif anchor['layer'] == 'inner':
            self.radius = rng.choice([2, 4, 4])
        else:  # outer halo
            self.radius = rng.choice([4, 7, 12])
            
        # Shimmer and micro-oscillation parameters
        self.twinkle_speed = float(rng.uniform(2.5, 6.0))
        self.twinkle_phase = float(rng.uniform(0, 2 * math.pi))
        self.micro_freq = float(rng.uniform(1.2, 3.0))
        self.micro_phase_x = float(rng.uniform(0, 2 * math.pi))
        self.micro_phase_y = float(rng.uniform(0, 2 * math.pi))
        self.micro_amp = float(rng.uniform(0.4, 1.2))
        
        self.flight_trail = []

    def awaken(self, spawn_x, spawn_y, rng):
        """Activates particle with a slight kinetic burst near spawn point."""
        self.is_active = True
        offset_dist = rng.uniform(3.0, 16.0)
        angle = rng.uniform(0, 2 * math.pi)
        self.x = spawn_x + math.cos(angle) * offset_dist
        self.y = spawn_y + math.sin(angle) * offset_dist
        
        burst_speed = rng.uniform(30.0, 95.0)
        self.vx = math.cos(angle) * burst_speed
        self.vy = math.sin(angle) * burst_speed

    def update(self, t, dt, pulse_scale, lead_x, lead_y, rng):
        """Damped spring physics to target position + breathing micro-motion."""
        if not self.is_active:
            if t >= self.draw_time:
                self.awaken(lead_x, lead_y, rng)
            else:
                return

        cx = self.path.center_x
        cy = self.path.center_y
        target_x = cx + self.rel_x * pulse_scale
        target_y = cy + self.rel_y * pulse_scale
        
        # Subtle organic micro-floating
        target_x += math.sin(t * self.micro_freq + self.micro_phase_x) * self.micro_amp
        target_y += math.cos(t * self.micro_freq + self.micro_phase_y) * self.micro_amp
        
        # Damped spring attraction to target
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.hypot(dx, dy)
        
        k_spring = 55.0
        c_damping = 10.0
        
        ax = k_spring * dx - c_damping * self.vx
        ay = k_spring * dy - c_damping * self.vy
        
        self.vx += ax * dt
        self.vy += ay * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        
        if dist > 6.0:
            self.flight_trail.append((self.x, self.y, t))
            if len(self.flight_trail) > 3:
                self.flight_trail.pop(0)
        else:
            if self.flight_trail:
                self.flight_trail.pop(0)

    def render(self, surface, t, glow_boost):
        """Renders particle with independent twinkling and additive glow."""
        if not self.is_active:
            return

        # Flight trail
        for tx, ty, tb in self.flight_trail:
            fade = max(0.0, 1.0 - (t - tb) / 0.12)
            if fade > 0.1:
                trail_glow = self.glow.get_glow(self.color, 2)
                tw, th = trail_glow.get_size()
                surface.blit(trail_glow, (tx - tw // 2, ty - th // 2), special_flags=pygame.BLEND_ADD)

        # Twinkle modulation
        twinkle = 0.75 + 0.25 * math.sin(t * self.twinkle_speed + self.twinkle_phase)
        
        glow_surf = self.glow.get_glow(self.color, self.radius)
        gw, gh = glow_surf.get_size()
        surface.blit(glow_surf, (self.x - gw // 2, self.y - gh // 2), special_flags=pygame.BLEND_ADD)
        
        # Highlight sparkle for diamonds
        if self.radius >= 7 and twinkle > 0.90:
            core = self.glow.get_core_glow(2)
            cw, ch = core.get_size()
            surface.blit(core, (self.x - cw // 2, self.y - ch // 2), special_flags=pygame.BLEND_ADD)


class InteriorParticle:
    """
    Volumetric depth particle inside the heart.
    Awakens during Phase 3 (4.5s - 6.5s) to add gentle stardust within the heart.
    """

    def __init__(self, data, heart_path, glow_cache, rng):
        self.data = data
        self.path = heart_path
        self.glow = glow_cache
        self.awaken_time = data['awaken_time']
        self.is_active = False
        
        self.base_x = data['base_x']
        self.base_y = data['base_y']
        self.rel_x = data['rel_x']
        self.rel_y = data['rel_y']
        
        self.x = self.base_x
        self.y = self.base_y
        self.vx = 0.0
        self.vy = 0.0
        
        self.color = rng.choice([COLOR_SOFT_ROSE, COLOR_WHITE_PINK, COLOR_MAGENTA])
        self.radius = 2  # Delicate stardust pinpoints
        
        self.twinkle_speed = float(rng.uniform(1.8, 3.5))
        self.twinkle_phase = float(rng.uniform(0, 2 * math.pi))
        self.micro_freq = float(rng.uniform(0.8, 2.0))
        self.micro_phase = float(rng.uniform(0, 2 * math.pi))

    def update(self, t, dt, pulse_scale, rng):
        if not self.is_active:
            if t >= self.awaken_time:
                self.is_active = True
                angle = rng.uniform(0, 2 * math.pi)
                self.x = self.base_x + math.cos(angle) * rng.uniform(10.0, 30.0)
                self.y = self.base_y + math.sin(angle) * rng.uniform(10.0, 30.0)
            else:
                return

        cx = self.path.center_x
        cy = self.path.center_y
        target_x = cx + self.rel_x * pulse_scale + math.sin(t * self.micro_freq + self.micro_phase) * 1.2
        target_y = cy + self.rel_y * pulse_scale + math.cos(t * self.micro_freq + self.micro_phase) * 1.2
        
        dx = target_x - self.x
        dy = target_y - self.y
        
        k_spring = 26.0
        c_damping = 8.0
        
        self.vx += (k_spring * dx - c_damping * self.vx) * dt
        self.vy += (k_spring * dy - c_damping * self.vy) * dt
        self.x += self.vx * dt
        self.y += self.vy * dt

    def render(self, surface, t, glow_boost):
        if not self.is_active:
            return
            
        glow_surf = self.glow.get_glow(self.color, self.radius)
        gw, gh = glow_surf.get_size()
        surface.blit(glow_surf, (self.x - gw // 2, self.y - gh // 2), special_flags=pygame.BLEND_ADD)


class AmbientStar:
    """
    Subtle drifting stardust particle in the surrounding darkness.
    """

    def __init__(self, star_data, glow_cache):
        self.x = star_data['x']
        self.y = star_data['y']
        self.vx = star_data['vx']
        self.vy = star_data['vy']
        self.twinkle_speed = star_data['twinkle_speed']
        self.phase = star_data['phase']
        self.color = [COLOR_SOFT_ROSE, COLOR_WHITE_PINK, COLOR_MAGENTA, COLOR_NEON_PINK][star_data['color_idx']]
        self.radius = 2
        self.glow = glow_cache

    def update(self, t, dt):
        self.x += (self.vx + math.sin(t * 0.8 + self.phase) * 3.0) * dt
        self.y += (self.vy + math.cos(t * 0.7 + self.phase) * 2.0) * dt
        
        if self.x < 10:
            self.x = 1910
        elif self.x > 1910:
            self.x = 10
            
        if self.y < 10:
            self.y = 1070
        elif self.y > 1070:
            self.y = 10

    def render(self, surface, t):
        twinkle = 0.5 + 0.5 * math.sin(t * self.twinkle_speed + self.phase)
        if twinkle < 0.2:
            return
        glow_surf = self.glow.get_glow(self.color, self.radius)
        gw, gh = glow_surf.get_size()
        surface.blit(glow_surf, (self.x - gw // 2, self.y - gh // 2), special_flags=pygame.BLEND_ADD)


class DriftDissolveParticle:
    """
    Drifting stardust particle detached from heart perimeter in Phase 4 & 5.
    Fades gracefully into darkness.
    """

    def __init__(self, x, y, vx, vy, color, glow_cache, birth_time):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.glow = glow_cache
        self.birth = birth_time
        self.lifespan = random.uniform(1.2, 2.2)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vx *= 0.96
        self.vy *= 0.96

    def is_alive(self, t):
        return (t - self.birth) < self.lifespan

    def render(self, surface, t):
        age = t - self.birth
        fade = max(0.0, 1.0 - (age / self.lifespan))
        if fade <= 0.05:
            return
        glow_surf = self.glow.get_glow(self.color, 2)
        gw, gh = glow_surf.get_size()
        surface.blit(glow_surf, (self.x - gw // 2, self.y - gh // 2), special_flags=pygame.BLEND_ADD)


class ParticleSystem:
    """
    Unified manager orchestrating all particles and visual components.
    """

    def __init__(self, heart_path, glow_cache):
        self.path = heart_path
        self.glow = glow_cache
        self.rng = random.Random(42)
        self.np_rng = np.random.default_rng(42)
        
        self.lead_spark = LeadSpark(self.path, self.glow)
        
        anchors = self.path.generate_perimeter_anchors(count=1400, rng=self.np_rng)
        self.perimeter_particles = [
            PerimeterParticle(a, self.path, self.glow, self.rng) for a in anchors
        ]
        
        interior_pts = self.path.generate_interior_points(count=120, rng=self.np_rng)
        self.interior_particles = [
            InteriorParticle(p, self.path, self.glow, self.rng) for p in interior_pts
        ]
        
        stars = self.path.generate_ambient_stars(count=160, rng=self.np_rng)
        self.ambient_stars = [
            AmbientStar(s, self.glow) for s in stars
        ]
        
        self.dissolve_particles = []
        self.last_dissolve_time = 0.0

    def reset(self):
        """Resets the entire particle simulation to state at t=0.0."""
        self.lead_spark = LeadSpark(self.path, self.glow)
        for p in self.perimeter_particles:
            p.is_active = False
            p.x = p.base_x
            p.y = p.base_y
            p.vx = 0.0
            p.vy = 0.0
            p.flight_trail.clear()
            
        for ip in self.interior_particles:
            ip.is_active = False
            ip.x = ip.base_x
            ip.y = ip.base_y
            ip.vx = 0.0
            ip.vy = 0.0
            
        self.dissolve_particles.clear()
        self.last_dissolve_time = 0.0

    def update(self, t, dt, pulse_scale):
        """Advances physics for all particles."""
        self.lead_spark.update(t, dt)
        
        lx = self.lead_spark.x
        ly = self.lead_spark.y
        for p in self.perimeter_particles:
            p.update(t, dt, pulse_scale, lx, ly, self.rng)
            
        if t >= 4.5:
            for ip in self.interior_particles:
                ip.update(t, dt, pulse_scale, self.rng)
                
        for star in self.ambient_stars:
            star.update(t, dt)
            
        if t >= 6.5 and (t - self.last_dissolve_time) > 0.09:
            self.last_dissolve_time = t
            chosen = self.rng.choice(self.perimeter_particles)
            if chosen.is_active:
                angle = math.atan2(chosen.y - self.path.center_y, chosen.x - self.path.center_x)
                drift_speed = random.uniform(18.0, 48.0)
                vx = math.cos(angle) * drift_speed + random.uniform(-8, 8)
                vy = math.sin(angle) * drift_speed + random.uniform(-8, 8)
                self.dissolve_particles.append(
                    DriftDissolveParticle(chosen.x, chosen.y, vx, vy, chosen.color, self.glow, t)
                )

        self.dissolve_particles = [dp for dp in self.dissolve_particles if dp.is_alive(t)]
        for dp in self.dissolve_particles:
            dp.update(dt)

    def render(self, surface, t, glow_boost):
        """Renders all particles onto target surface with additive blending."""
        # 1. Ambient background stars
        for star in self.ambient_stars:
            star.render(surface, t)
            
        # 2. Interior volumetric stardust (Phase 3+)
        if t >= 4.5:
            for ip in self.interior_particles:
                ip.render(surface, t, glow_boost)
                
        # 3. Drifting dissolve stardust
        for dp in self.dissolve_particles:
            dp.render(surface, t)
            
        # 4. Perimeter particles & trails
        for p in self.perimeter_particles:
            p.render(surface, t, glow_boost)
            
        # 5. Lead spark & artist drawing ribbon
        self.lead_spark.render(surface, t)
