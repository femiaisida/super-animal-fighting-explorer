content = open('build/web/index.html').read()

# Fix body background and canvas fullscreen
content = content.replace('background-color:powderblue;', 'background-color:#000;')

# SDL2 audio unlock — polls until SDL2 audioContext exists then resumes it
# Injected before </html> since there is no </body> in pygbag output
unlock_script = """
<script>
(function(){
  function tryUnlock() {
    try {
      if (typeof SDL2 !== "undefined" && SDL2.audioContext) {
        if (SDL2.audioContext.state === "suspended") {
          SDL2.audioContext.resume().then(function(){
            console.log("SDL2 audio context resumed");
          });
        }
        return true;
      }
    } catch(e) { console.warn("audio unlock error", e); }
    return false;
  }

  var unlocked = false;
  function onGesture() {
    if (unlocked) return;
    if (tryUnlock()) {
      unlocked = true;
      document.removeEventListener("touchstart", onGesture);
      document.removeEventListener("touchend",   onGesture);
      document.removeEventListener("click",      onGesture);
    }
  }

  // Also poll every 500ms in case SDL2 loads after first gesture
  var pollInterval = setInterval(function(){
    if (tryUnlock()) {
      unlocked = true;
      clearInterval(pollInterval);
    }
  }, 500);

  document.addEventListener("touchstart", onGesture, {passive:true});
  document.addEventListener("touchend",   onGesture, {passive:true});
  document.addEventListener("click",      onGesture, {passive:true});
})();
</script>
</html>"""

content = content.replace('</html>', unlock_script)
open('build/web/index.html', 'w').write(content)
print('patch_web done')
