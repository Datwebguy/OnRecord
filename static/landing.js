/**
 * OnRecord Landing Page Interactive Canvas
 * "Two Rails / One Stamp" Motion System
 */

document.addEventListener("DOMContentLoaded", () => {
  initHeroCanvas();
});

function initHeroCanvas() {
  const canvas = document.getElementById("hero-canvas");
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  let width = (canvas.width = canvas.parentElement.clientWidth);
  let height = (canvas.height = canvas.parentElement.clientHeight);

  window.addEventListener("resize", () => {
    width = canvas.width = canvas.parentElement.clientWidth;
    height = canvas.height = canvas.parentElement.clientHeight;
  });

  // Particles (paper dust)
  const particleCount = prefersReduced ? 0 : 35;
  const particles = [];
  for (let i = 0; i < particleCount; i++) {
    particles.push({
      x: Math.random() * width,
      y: Math.random() * height,
      size: Math.random() * 1.5 + 0.5,
      speedY: Math.random() * 0.3 + 0.1,
      opacity: Math.random() * 0.4 + 0.1
    });
  }

  // Two rails offsets
  let scoutRailOffset = 0;
  let clerkRailOffset = 0;

  // Stamp state
  let stampScale = 1.6;
  let stampOpacity = 0;
  let stampPhase = "settling"; // settling, resting, fading
  let stampTimer = 0;

  function render() {
    const isDark = document.documentElement.dataset.theme === "dark";
    const canvasBg = isDark ? "#141210" : "#efe6d6";
    const grid = isDark ? "rgba(36, 32, 28, 0.8)" : "rgba(214, 201, 178, 0.75)";
    const scoutRail = isDark ? "rgba(92, 18, 18, 0.4)" : "rgba(156, 90, 60, 0.28)";
    const clerkRail = isDark ? "rgba(196, 163, 90, 0.3)" : "rgba(51, 80, 122, 0.3)";
    const ink = isDark ? "rgba(232, 224, 212, 0.5)" : "rgba(106, 96, 85, 0.6)";
    const dust = isDark ? "rgba(232, 224, 212, 0.3)" : "rgba(106, 96, 85, 0.25)";
    const stamp = isDark ? "rgba(200, 30, 30, " : "rgba(156, 90, 60, ";
    const stampAccent = isDark ? "rgba(196, 163, 90, " : "rgba(51, 80, 122, ";

    ctx.fillStyle = canvasBg;
    ctx.fillRect(0, 0, width, height);

    // 1. Draw Grid / Two Rails
    ctx.lineWidth = 1;

    // Rail 1: Scout (Left Lane)
    const rail1X = width * 0.32;
    ctx.strokeStyle = scoutRail;
    ctx.beginPath();
    ctx.moveTo(rail1X, 0);
    ctx.lineTo(rail1X, height);
    ctx.stroke();

    // Rail 2: Clerk (Right Lane)
    const rail2X = width * 0.68;
    ctx.strokeStyle = clerkRail;
    ctx.beginPath();
    ctx.moveTo(rail2X, 0);
    ctx.lineTo(rail2X, height);
    ctx.stroke();

    // Cross-ties moving downward
    if (!prefersReduced) {
      scoutRailOffset = (scoutRailOffset + 0.4) % 40;
      clerkRailOffset = (clerkRailOffset + 0.25) % 40;
    }

    ctx.strokeStyle = grid;
    for (let y = scoutRailOffset; y < height; y += 40) {
      ctx.beginPath();
      ctx.moveTo(rail1X - 30, y);
      ctx.lineTo(rail1X + 30, y);
      ctx.stroke();
    }

    ctx.strokeStyle = grid;
    for (let y = clerkRailOffset; y < height; y += 40) {
      ctx.beginPath();
      ctx.moveTo(rail2X - 30, y);
      ctx.lineTo(rail2X + 30, y);
      ctx.stroke();
    }

    // Rail Labels
    ctx.font = "10px 'JetBrains Mono', monospace";
    ctx.fillStyle = ink;
    ctx.fillText("TENANT_SCOUT [WRITE]", rail1X - 60, 30);
    ctx.fillText("TENANT_CLERK [READ]", rail2X - 60, 30);

    // 2. Paper dust particles
    ctx.fillStyle = dust;
    for (let p of particles) {
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
      ctx.fill();

      if (!prefersReduced) {
        p.y -= p.speedY;
        if (p.y < 0) {
          p.y = height;
          p.x = Math.random() * width;
        }
      }
    }

    // 3. The Red Stamp (Center-Right Bridge)
    const stampCenterX = width * 0.5;
    const stampCenterY = height * 0.52;

    if (!prefersReduced) {
      stampTimer++;
      if (stampPhase === "settling") {
        stampScale += (1.0 - stampScale) * 0.12;
        stampOpacity += (1.0 - stampOpacity) * 0.15;
        if (Math.abs(stampScale - 1.0) < 0.01) {
          stampScale = 1.0;
          stampOpacity = 1.0;
          stampPhase = "resting";
          stampTimer = 0;
        }
      } else if (stampPhase === "resting") {
        if (stampTimer > 160) {
          stampPhase = "fading";
        }
      } else if (stampPhase === "fading") {
        stampOpacity -= 0.03;
        if (stampOpacity <= 0) {
          stampOpacity = 0;
          stampScale = 1.8;
          stampPhase = "settling";
          stampTimer = 0;
        }
      }
    } else {
      stampScale = 1.0;
      stampOpacity = 1.0;
    }

    ctx.save();
    ctx.translate(stampCenterX, stampCenterY);
    ctx.scale(stampScale, stampScale);
    ctx.rotate(-0.06); // slight mechanical stamp tilt

    // Stamp box
    ctx.strokeStyle = `${stamp}${stampOpacity * 0.9})`;
    ctx.lineWidth = 3;
    ctx.strokeRect(-90, -32, 180, 64);

    // Stamp text
    ctx.font = "700 18px 'JetBrains Mono', monospace";
    ctx.fillStyle = `${stamp}${stampOpacity})`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText("ON RECORD", 0, -4);

    ctx.font = "500 9px 'JetBrains Mono', monospace";
    ctx.fillStyle = `${stampAccent}${stampOpacity * 0.8})`;
    ctx.fillText("COLD HANDOFF VERIFIED", 0, 16);

    ctx.restore();

    requestAnimationFrame(render);
  }

  render();
}
