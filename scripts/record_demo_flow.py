import os
import sys
import time
import math
from pathlib import Path
from playwright.sync_api import sync_playwright

RECORDING_DIR = Path(__file__).parent.parent / "video" / "public" / "recordings"
RECORDING_DIR.mkdir(parents=True, exist_ok=True)

APP_URL = "http://127.0.0.1:8000"
USER_WALLET = "0x75a0c2d1df51c07982de3ff031e5232518676b19"
TARGET_REPO = "https://github.com/cea-sec/Sibyl"

CURSOR_JS = """
(() => {
  if (window.__demoCursorInjected) return;
  window.__demoCursorInjected = true;

  const style = document.createElement('style');
  style.textContent = `
    #demo-mouse-cursor {
      position: fixed;
      top: 0; left: 0;
      width: 24px; height: 24px;
      border-radius: 50%;
      background: radial-gradient(circle at 35% 35%, #ffffff 0%, #e6ff00 65%, #94b300 100%);
      border: 2.5px solid #000000;
      box-shadow: 0 0 16px rgba(230, 255, 0, 0.95), 0 2px 10px rgba(0,0,0,0.85);
      pointer-events: none;
      z-index: 2147483647;
      transform: translate(-50%, -50%);
      transition: transform 0.08s ease-out;
    }
    #demo-mouse-cursor.clicking {
      transform: translate(-50%, -50%) scale(0.75);
      background: #ff5500;
      box-shadow: 0 0 22px #ff5500;
    }
    .demo-ripple {
      position: fixed;
      border-radius: 50%;
      border: 3.5px solid #e6ff00;
      box-shadow: 0 0 18px #e6ff00;
      pointer-events: none;
      z-index: 2147483646;
      transform: translate(-50%, -50%) scale(0.2);
      opacity: 1;
      animation: demo-ripple-anim 0.65s cubic-bezier(0.1, 0.8, 0.25, 1) forwards;
    }
    @keyframes demo-ripple-anim {
      0% { transform: translate(-50%, -50%) scale(0.2); opacity: 1; }
      100% { transform: translate(-50%, -50%) scale(5.5); opacity: 0; }
    }
    .demo-callout-bubble {
      position: fixed;
      z-index: 2147483640;
      background: rgba(14, 18, 14, 0.95);
      border: 1.5px solid #e6ff00;
      border-radius: 8px;
      padding: 12px 18px;
      color: #f0f0f0;
      font-family: 'JetBrains Mono', monospace, sans-serif;
      font-size: 13px;
      box-shadow: 0 8px 32px rgba(0,0,0,0.9), 0 0 20px rgba(230,255,0,0.25);
      pointer-events: none;
      opacity: 0;
      transform: translateY(8px);
      transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1);
      display: flex;
      flex-direction: column;
      gap: 5px;
      max-width: 420px;
    }
    .demo-callout-bubble.visible {
      opacity: 1;
      transform: translateY(0);
    }
    .demo-callout-tag {
      font-size: 10.5px;
      letter-spacing: 0.12em;
      color: #e6ff00;
      text-transform: uppercase;
      font-weight: 700;
    }
    .demo-callout-text {
      font-size: 13px;
      line-height: 1.45;
      color: #d8ded8;
    }
    .demo-arrow-pointer {
      position: fixed;
      z-index: 2147483645;
      pointer-events: none;
      opacity: 0;
      transition: opacity 0.3s ease;
      filter: drop-shadow(0 0 10px rgba(230,255,0,0.9));
      animation: pulse-bounce 1.2s infinite ease-in-out;
    }
    .demo-arrow-pointer.visible {
      opacity: 1;
    }
    @keyframes pulse-bounce {
      0%, 100% { transform: translateY(0) scale(1); }
      50% { transform: translateY(-8px) scale(1.12); }
    }
  `;
  document.head.appendChild(style);

  const cursor = document.createElement('div');
  cursor.id = 'demo-mouse-cursor';
  document.body.appendChild(cursor);

  window.__cursorEl = cursor;
  window.__calloutEl = null;
  window.__arrowEl = null;

  window.moveCursorTo = (x, y) => {
    cursor.style.left = x + 'px';
    cursor.style.top = y + 'px';
  };

  window.showClickEffect = (x, y) => {
    cursor.classList.add('clicking');
    setTimeout(() => cursor.classList.remove('clicking'), 150);

    const rip = document.createElement('div');
    rip.className = 'demo-ripple';
    rip.style.left = x + 'px';
    rip.style.top = y + 'px';
    rip.style.width = '18px';
    rip.style.height = '18px';
    document.body.appendChild(rip);
    setTimeout(() => rip.remove(), 700);
  };

  window.showCallout = (x, y, tag, text) => {
    if (window.__calloutEl) window.__calloutEl.remove();
    const b = document.createElement('div');
    b.className = 'demo-callout-bubble';
    b.innerHTML = `<span class="demo-callout-tag">${tag}</span><span class="demo-callout-text">${text}</span>`;
    b.style.left = Math.min(window.innerWidth - 450, Math.max(20, x)) + 'px';
    b.style.top = Math.max(20, y) + 'px';
    document.body.appendChild(b);
    window.__calloutEl = b;
    requestAnimationFrame(() => b.classList.add('visible'));
  };

  window.hideCallout = () => {
    if (window.__calloutEl) {
      window.__calloutEl.classList.remove('visible');
      setTimeout(() => { if (window.__calloutEl) window.__calloutEl.remove(); window.__calloutEl = null; }, 350);
    }
  };

  window.showArrow = (x, y, rotation = 0) => {
    if (window.__arrowEl) window.__arrowEl.remove();
    const svg = document.createElement('div');
    svg.className = 'demo-arrow-pointer';
    svg.innerHTML = `
      <svg width="52" height="52" viewBox="0 0 24 24" fill="none" stroke="#e6ff00" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
        <line x1="12" y1="19" x2="12" y2="5"></line>
        <polyline points="5 12 12 5 19 12"></polyline>
      </svg>
    `;
    svg.style.left = (x - 26) + 'px';
    svg.style.top = (y - 26) + 'px';
    svg.style.transformOrigin = 'center center';
    svg.style.transform = `rotate(${rotation}deg)`;
    document.body.appendChild(svg);
    window.__arrowEl = svg;
    requestAnimationFrame(() => svg.classList.add('visible'));
  };

  window.hideArrow = () => {
    if (window.__arrowEl) {
      window.__arrowEl.classList.remove('visible');
      setTimeout(() => { if (window.__arrowEl) window.__arrowEl.remove(); window.__arrowEl = null; }, 300);
    }
  };
})();
"""

current_mouse = {"x": 960, "y": 540}

def move_mouse(page, target_x, target_y, duration=0.8, steps=30):
    start_x = current_mouse["x"]
    start_y = current_mouse["y"]
    
    for i in range(1, steps + 1):
        t = i / steps
        ease = t * t * (3.0 - 2.0 * t)
        cx = start_x + (target_x - start_x) * ease
        cy = start_y + (target_y - start_y) * ease
        page.evaluate(f"window.moveCursorTo({cx}, {cy})")
        time.sleep(duration / steps)
    
    current_mouse["x"] = target_x
    current_mouse["y"] = target_y

def click_point(page, x, y):
    move_mouse(page, x, y, duration=0.6)
    page.evaluate(f"window.showClickEffect({x}, {y})")
    time.sleep(0.12)
    page.mouse.click(x, y)
    time.sleep(0.3)

def click_selector(page, selector):
    box = page.locator(selector).first.bounding_box()
    if box:
        cx = box["x"] + box["width"] / 2
        cy = box["y"] + box["height"] / 2
        click_point(page, cx, cy)
    else:
        page.click(selector)

def type_text(page, selector, text, delay=0.05):
    box = page.locator(selector).first.bounding_box()
    if box:
        cx = box["x"] + box["width"] / 2
        cy = box["y"] + box["height"] / 2
        click_point(page, cx, cy)
    else:
        page.click(selector)
    time.sleep(0.2)
    for char in text:
        page.keyboard.type(char)
        time.sleep(delay)
    time.sleep(0.4)

def smooth_scroll(page, target_y, duration=1.5, steps=40):
    start_y = page.evaluate("window.scrollY || window.pageYOffset")
    for i in range(1, steps + 1):
        t = i / steps
        ease = t * t * (3.0 - 2.0 * t)
        cy = start_y + (target_y - start_y) * ease
        page.evaluate(f"window.scrollTo(0, {cy})")
        time.sleep(duration / steps)
    time.sleep(0.3)

def record_full_demo():
    print("[1/6] Preparing recording environment...")
    import urllib.request
    import json
    try:
        req = urllib.request.Request(
            f"{APP_URL}/api/scene",
            data=json.dumps({"name": "OnRecord Desk", "sources": []}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        urllib.request.urlopen(req)
        req_del = urllib.request.Request(f"{APP_URL}/api/desk/delete_test", method="POST")
        urllib.request.urlopen(req_del)
        print(">> Workspace scene & memory cleanly cleared.")
    except Exception as e:
        print(">> Notice: reset endpoint note:", e)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--force-device-scale-factor=1",
                "--window-size=1920,1080"
            ]
        )

        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir=str(RECORDING_DIR),
            record_video_size={"width": 1920, "height": 1080}
        )

        page = context.new_page()

        # ==========================================
        # ACT 1: LANDING PAGE TOUR (approx 42 seconds)
        # ==========================================
        print("[2/6] Recording Act 1: Landing Page Architecture Tour...")
        page.goto(f"{APP_URL}/", wait_until="networkidle")
        page.evaluate(CURSOR_JS)
        page.evaluate("window.moveCursorTo(960, 540)")
        time.sleep(1.5)

        # Hero badge highlight
        page.evaluate("window.showCallout(600, 160, '01 / SYSTEM IDENTITY', 'OnRecord: The safe air-gapped execution layer for AI contributor agents.')")
        move_mouse(page, 960, 240, duration=1.0)
        time.sleep(3.5)
        page.evaluate("window.hideCallout()")

        # Subtitle inspection
        move_mouse(page, 720, 360, duration=0.8)
        time.sleep(2.0)

        # Smooth scroll down to Problem Section
        page.evaluate("window.showCallout(200, 200, '02 / ARCHITECTURAL PRINCIPLE', 'The Problem: Unstructured prompt memory causes context drift and security leakage.')")
        smooth_scroll(page, 750, duration=2.2)
        page.evaluate(CURSOR_JS)
        time.sleep(3.5)
        page.evaluate("window.hideCallout()")

        # Smooth scroll down to 3-Column Desk Interface
        page.evaluate("window.showCallout(150, 180, '03 / ROLE SEPARATION', 'Three-Column Desk: Scout files. Verifiable Queue stages. Clerk acts only on record.')")
        smooth_scroll(page, 1450, duration=2.5)
        move_mouse(page, 450, 480, duration=0.8)
        time.sleep(2.5)
        move_mouse(page, 960, 480, duration=0.8)
        time.sleep(2.5)
        move_mouse(page, 1470, 480, duration=0.8)
        time.sleep(2.5)
        page.evaluate("window.hideCallout()")

        # Smooth scroll down to Workflow
        page.evaluate("window.showCallout(200, 200, '04 / PIPELINE', 'Step 1: Configure · Step 2: File · Step 3: Verify · Step 4: Confirmed Onchain Action.')")
        smooth_scroll(page, 2250, duration=2.2)
        time.sleep(4.0)
        page.evaluate("window.hideCallout()")

        # Smooth scroll down to Invariants & FAQ
        smooth_scroll(page, 3100, duration=2.0)
        time.sleep(3.0)

        # Scroll to bottom CTA section
        smooth_scroll(page, 3800, duration=2.0)
        time.sleep(2.5)

        # Scroll smoothly back to Top Nav to launch desk
        page.evaluate("window.showCallout(650, 300, '05 / PLATFORM LAUNCH', 'Navigating to the Contributor Desk to configure live repository & wallet.')")
        smooth_scroll(page, 0, duration=2.5)
        time.sleep(1.5)

        # Target "Open desk" button in navigation
        open_desk_btn = page.locator("header.landing-nav a.btn-primary").first
        box = open_desk_btn.bounding_box()
        if box:
            cx = box["x"] + box["width"] / 2
            cy = box["y"] + box["height"] / 2
            page.evaluate(f"window.showArrow({cx}, {cy + 45}, 0)")
            move_mouse(page, cx, cy, duration=1.2)
            time.sleep(1.8)
            page.evaluate("window.hideArrow()")
            page.evaluate("window.hideCallout()")
            click_point(page, cx, cy)
        else:
            page.click("a.btn-primary")

        # ==========================================
        # ACT 2 & 3: CONTRIBUTOR DESK & SCENE CONFIG
        # ==========================================
        print("[3/6] Recording Act 2 & 3: Desk Initialization & Scene Setup...")
        page.wait_for_url("**/desk", timeout=10000)
        time.sleep(1.5)
        page.evaluate(CURSOR_JS)
        page.evaluate("window.moveCursorTo(960, 400)")

        # Callout on Scene Context
        page.evaluate("window.showCallout(120, 160, '06 / SCENE ALLOWLIST', 'The Scene defines the runtime operational scope. Zero unconfigured inputs are accepted.')")
        move_mouse(page, 400, 75, duration=1.0)
        time.sleep(3.0)
        page.evaluate("window.hideCallout()")

        # Target Repository Input
        page.evaluate(f"window.showArrow(250, 115, 0)")
        page.evaluate("window.showCallout(60, 150, '07 / REPOSITORY INPUT', 'Entering live Sibyl repository to monitor public pull requests & issues.')")
        time.sleep(1.5)
        page.evaluate("window.hideArrow()")
        type_text(page, "#scene-repo", TARGET_REPO, delay=0.04)
        time.sleep(1.5)
        page.evaluate("window.hideCallout()")

        # Contributor Wallet Input
        page.evaluate(f"window.showArrow(680, 115, 0)")
        page.evaluate("window.showCallout(450, 150, '08 / CONTRIBUTOR WALLET', 'Binding operator Base Mainnet wallet address to receive verified attribution.')")
        time.sleep(1.5)
        page.evaluate("window.hideArrow()")
        type_text(page, "#scene-wallet", USER_WALLET, delay=0.04)
        time.sleep(1.5)
        page.evaluate("window.hideCallout()")

        # Click "Save Scene"
        save_btn = page.locator("#btn-save-scene").first
        box_save = save_btn.bounding_box()
        if box_save:
            cx = box_save["x"] + box_save["width"] / 2
            cy = box_save["y"] + box_save["height"] / 2
            page.evaluate(f"window.showArrow({cx}, {cy + 40}, 0)")
            move_mouse(page, cx, cy, duration=0.8)
            time.sleep(1.0)
            page.evaluate("window.hideArrow()")
            click_point(page, cx, cy)
        else:
            page.click("#btn-save-scene")

        page.evaluate("window.showCallout(980, 120, '09 / CONTEXT LOCKED', 'Scene saved to SQLite. Runtime state locked for Scout ingestion.')")
        time.sleep(3.5)
        page.evaluate("window.hideCallout()")

        # ==========================================
        # ACT 4: RUNNING SCOUT ENGINE
        # ==========================================
        print("[4/6] Recording Act 4: Running Scout Engine...")
        run_scout_btn = page.locator("#btn-run-scout").first
        box_scout = run_scout_btn.bounding_box()
        if box_scout:
            cx = box_scout["x"] + box_scout["width"] / 2
            cy = box_scout["y"] + box_scout["height"] / 2
            page.evaluate(f"window.showArrow({cx}, {cy + 40}, 0)")
            page.evaluate("window.showCallout(850, 120, '10 / SCOUT INGESTION', 'Triggering Scout to scan repository & watched wallet with ZERO private keys.')")
            move_mouse(page, cx, cy, duration=0.8)
            time.sleep(1.5)
            page.evaluate("window.hideArrow()")
            page.evaluate("window.hideCallout()")
            click_point(page, cx, cy)
        else:
            page.click("#btn-run-scout")

        # Wait for Scout to file and populate
        time.sleep(3.5)
        page.evaluate("window.showCallout(80, 180, '11 / FILINGS ON RECORD', 'Scout discovered inbound activity and filed structured records into partition.')")
        move_mouse(page, 200, 320, duration=1.0)
        time.sleep(4.0)
        page.evaluate("window.hideCallout()")

        # ==========================================
        # ACT 5: VERIFIABLE QUEUE INSPECTION
        # ==========================================
        print("[5/6] Recording Act 5: Verifiable Queue Inspection...")
        page.evaluate("window.showCallout(550, 180, '12 / VERIFIABLE QUEUE', 'Queue projects directly from persistent events. No secondary mutable state.')")
        move_mouse(page, 640, 260, duration=1.0)
        time.sleep(3.0)
        page.evaluate("window.hideCallout()")

        # Target the queue card and click it
        first_queue_card = page.locator("#queue-body .desk-card").first
        box_card = first_queue_card.bounding_box()
        if box_card:
            cx = box_card["x"] + box_card["width"] / 2
            cy = box_card["y"] + box_card["height"] / 2
            page.evaluate(f"window.showArrow({cx}, {cy + 45}, 0)")
            move_mouse(page, cx, cy, duration=1.0)
            time.sleep(1.8)
            page.evaluate("window.hideArrow()")
            click_point(page, cx, cy)
        else:
            print("Queue card click fallback")
            page.click("#queue-body .desk-card")

        time.sleep(2.5)

        # ==========================================
        # ACT 6: CLERK VERIFICATION & STOP AT CONNECT WALLET
        # ==========================================
        print("[6/6] Recording Act 6: Clerk Verification & Stopping at Connect Wallet...")
        page.evaluate("window.showCallout(1200, 140, '13 / CLERK DESK', 'Clerk validates entity against load-bearing memory files (person.json & ask.json).')")
        move_mouse(page, 1450, 260, duration=1.0)
        time.sleep(3.5)

        # Click ask.json tab
        ask_tab = page.locator("#tab-btn-ask").first
        if ask_tab.is_visible():
            click_selector(page, "#tab-btn-ask")
            time.sleep(2.0)
            click_selector(page, "#tab-btn-person")
            time.sleep(2.0)

        page.evaluate("window.hideCallout()")

        # Scroll Clerk column down to Base Ping section
        clerk_col = page.locator("#col-clerk .col-stream").first
        clerk_col.evaluate("el => el.scrollTo({ top: 380, behavior: 'smooth' })")
        time.sleep(2.0)

        # Move mouse to "Sign with Browser Wallet (MetaMask / Coinbase)" button
        wallet_ping_btn = page.locator("#btn-wallet-ping").first
        box_ping = wallet_ping_btn.bounding_box()
        if box_ping:
            cx = box_ping["x"] + box_ping["width"] / 2
            cy = box_ping["y"] + box_ping["height"] / 2

            page.evaluate(f"window.showArrow({cx}, {cy + 55}, 0)")
            move_mouse(page, cx, cy, duration=1.2)

            # Prominent Stop Point Safety Callout
            page.evaluate(f"""
              window.showCallout(
                {max(100, int(cx - 360))},
                {max(50, int(cy - 120))},
                'OPERATOR SAFETY GATE · STOP POINT',
                'Connect your Web3 wallet (0x75a0...6b19) to confirm and sign the Base on-chain ping.<br/><br/><strong style="color:#e6ff00;">Handoff Point: Stopped here for human operator execution.</strong>'
              )
            """)

            print(">> Holding at Connect Wallet step for operator handoff (15s)...")
            time.sleep(15.0)

        print(">> Recording complete! Closing browser context...")
        page.close()
        context.close()
        browser.close()

    video_files = list(RECORDING_DIR.glob("*.webm"))
    if video_files:
        latest_video = max(video_files, key=os.path.getctime)
        print(f"Recorded video saved to: {latest_video}")
        return str(latest_video)
    else:
        print("Error: No video file found in recording directory.")
        return None

if __name__ == "__main__":
    record_full_demo()
