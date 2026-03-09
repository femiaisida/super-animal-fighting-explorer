import sys

content = open('build/web/index.html').read()

script = (
    '<script>\n'
    '(function(){\n'
    '  var unlocked=false;\n'
    '  function unlock(){\n'
    '    if(unlocked)return;\n'
    '    unlocked=true;\n'
    '    var AC=window.AudioContext||window.webkitAudioContext;\n'
    '    if(!AC)return;\n'
    '    var ctx=new AC();\n'
    '    var buf=ctx.createBuffer(1,1,22050);\n'
    '    var src=ctx.createBufferSource();\n'
    '    src.buffer=buf;\n'
    '    src.connect(ctx.destination);\n'
    '    src.start(0);\n'
    '    if(ctx.state==="suspended")ctx.resume();\n'
    '    document.removeEventListener("touchstart",unlock);\n'
    '    document.removeEventListener("touchend",unlock);\n'
    '    document.removeEventListener("click",unlock);\n'
    '  }\n'
    '  document.addEventListener("touchstart",unlock,{passive:true});\n'
    '  document.addEventListener("touchend",unlock,{passive:true});\n'
    '  document.addEventListener("click",unlock,{passive:true});\n'
    '})();\n'
    '</script>\n'
    '</body>'
)

content = content.replace('</body>', script)
open('build/web/index.html', 'w').write(content)
print('audio unlock injected')
