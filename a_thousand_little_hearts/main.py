"""
main.py - PROJECT 11: A THOUSAND LITTLE HEARTS ✨
A Cinematic, Romantic, Live Particle Drawing in Python.

Rendered in real-time using Pygame, NumPy, and custom particle physics.
Thousands of glowing particles draw a heart live on a pure black 16:9 canvas.

Controls:
  Space : Restart the 10-second animation from the beginning
  R     : Restart immediately
  F     : Toggle Fullscreen / Windowed mode
  Esc   : Exit cleanly
"""

import os
import sys
import pygame

from heart_path import HeartPath, CANVAS_WIDTH, CANVAS_HEIGHT
from effects import GlowCache, HeartEffects, TextRenderer
from particle import ParticleSystem


def get_font_path():
    """Locate local romantic font asset if available."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(script_dir, "assets", "fonts", "romantic_serif.ttf"),
        os.path.join(script_dir, "assets", "fonts", "romantic_light.ttf"),
        os.path.join(script_dir, "..", "assets", "fonts", "romantic_serif.ttf"),
        os.path.join("assets", "fonts", "romantic_serif.ttf"),
    ]
    for p in candidates:
        if os.path.isfile(p):
            return p
    return None


def main():
    # Initialize Pygame display and font systems
    try:
        pygame.init()
        pygame.font.init()
    except Exception as e:
        print(f"Error initializing Pygame: {e}", file=sys.stderr)
        sys.exit(1)

    # Window title and configuration
    pygame.display.set_caption("A Thousand Little Hearts ✨")
    
    # 1920x1080 canvas with hardware scaling support
    # pygame.SCALED automatically scales the 16:9 canvas to any screen size
    try:
        screen = pygame.display.set_mode((CANVAS_WIDTH, CANVAS_HEIGHT), pygame.SCALED | pygame.RESIZABLE)
    except Exception:
        screen = pygame.display.set_mode((CANVAS_WIDTH, CANVAS_HEIGHT))

    # Hide cursor for pure cinematic immersion
    pygame.mouse.set_visible(False)

    clock = pygame.time.Clock()
    target_fps = 60

    # Initialize mathematical curve, glow cache, particle system, and typography
    heart_path = HeartPath()
    glow_cache = GlowCache()
    effects = HeartEffects(glow_cache, heart_path)
    font_path = get_font_path()
    text_renderer = TextRenderer(font_path=font_path, font_size=36)
    particle_system = ParticleSystem(heart_path, glow_cache)

    current_time = 0.0
    running = True
    is_fullscreen = False

    while running:
        # High-precision delta time (clamped to prevent physics explosion on window movement)
        raw_dt = clock.tick(target_fps) / 1000.0
        dt = min(raw_dt, 0.05)

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key in (pygame.K_SPACE, pygame.K_r):
                    # Restart animation cleanly from t=0.0
                    current_time = 0.0
                    particle_system.reset()
                elif event.key == pygame.K_f:
                    # Toggle fullscreen mode safely
                    try:
                        pygame.display.toggle_fullscreen()
                        is_fullscreen = not is_fullscreen
                    except Exception:
                        pass

        # Advance timeline
        current_time += dt

        # Calculate physiological heartbeat expansion and glow boost (active from 6.5s onward)
        pulse_scale, glow_boost = effects.get_heartbeat(current_time)

        # Update particle physics (damped spring dynamics, trails, shimmer, stardust)
        particle_system.update(current_time, dt, pulse_scale)

        # --- RENDERING PIPELINE ---
        # 1. Pure black background
        screen.fill((0, 0, 0))

        # 2. Ambient soft romantic halo (fades in Phase 3, pulses in Phase 4 & 5)
        effects.render_halo(screen, current_time, pulse_scale, glow_boost)

        # 3. Particle system (stars, volumetric depth, perimeter, lead spark, and stardust trails)
        particle_system.render(screen, current_time, glow_boost)

        # 4. Romantic message text (smooth fade-in at 8.0s - 10.0s, remains visible thereafter)
        text_renderer.render(screen, current_time, target_y=925)

        # Present frame
        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
