# Super Animal Fighting Explorer — Dev Log

## What is this?
A turn-based RPG built in Python/Pygame, being ported to Godot 4.
This log tracks technical decisions, problems encountered, and lessons learned.

---

## Entry 1 — March 2026
### Pygame/Web phase complete (v2 archived)

Built a full turn-based RPG in Python/Pygame with 4 playable characters,
4 biomes, boss battles, shop, NPC interactions, evolution system, and web deployment
via pygbag/GitHub Pages.

**Key technical challenges solved:**
- Responsive UI scaling across screen sizes using lh-relative spacing (screen_h / 54)
- Touch/swipe controls for mobile web: two-tap confirm pattern, 30px swipe threshold
- Web audio: pygame mixer pre_init at 24kHz mono per pygbag spec
- WebAssembly audio context unlock via SDL2.audioContext.resume() on user gesture

**Unresolved limitation:**
- iOS audio does not work in pygbag — confirmed upstream bug in pygame-web.
  WebKit's media engagement policy blocks SDL2's audio context on iOS Safari and
  Chrome (which also uses WebKit on iOS). The pygbag maintainer acknowledged this
  as an unfixed issue requiring Apple hardware to debug at the JS engine level.
  Decision: archive Pygame version, port to Godot 4 for proper cross-platform support.

**Decision to port:**
Godot 4 exports natively to Android, iOS, Web, Windows, Mac and Linux from one
codebase. GDScript syntax is close to Python. This removes the WebAssembly audio
layer entirely and opens a path to app store deployment.

---
