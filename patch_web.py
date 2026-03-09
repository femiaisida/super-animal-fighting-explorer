content = open('build/web/index.html').read()

script = (
    '<script>\n'
    'function unlockSDL2Audio() {\n'
    '  try {\n'
    '    if (typeof SDL2 !== "undefined" && SDL2.audioContext) {\n'
    '      SDL2.audioContext.resume();\n'
    '    }\n'
    '  } catch(e) {}\n'
    '}\n'
    'document.addEventListener("touchstart", unlockSDL2Audio, {passive:true});\n'
    'document.addEventListener("touchend",   unlockSDL2Audio, {passive:true});\n'
    'document.addEventListener("click",      unlockSDL2Audio, {passive:true});\n'
    '</script>\n'
    '</body>'
)

content = content.replace('</body>', script)
open('build/web/index.html', 'w').write(content)
print('SDL2 audio unlock injected')
