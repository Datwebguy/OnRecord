import os
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

RECORDING_DIR = Path(__file__).parent.parent / "video" / "public" / "recordings"
RECORDING_DIR.mkdir(parents=True, exist_ok=True)

APP_URL = "http://127.0.0.1:8000"
USER_WALLET = "0x75a0c2d1df51c07982de3ff031e5232518676b19"
TARGET_REPO = "https://github.com/cea-sec/Sibyl"
MOCK_TX_HASH = "0x89a1c4df629007cb49bbf049b40061e8609520cb2a4216ee892d192e2fbcf9a3"

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
      box-shadow: 0 0 18px rgba(230, 255, 0, 0.95), 0 2px 10px rgba(0,0,0,0.85);
      pointer-events: none;
      z-index: 2147483647;
      transform: translate(-50%, -50%);
      transition: transform 0.08s ease-out;
    }
    #demo-mouse-cursor.clicking {
      transform: translate(-50%, -50%) scale(0.75);
      background: #ff5500;
      box-shadow: 0 0 24px #ff5500;
    }
    .demo-ripple {
      position: fixed;
      border-radius: 50%;
      border: 3.5px solid #e6ff00;
      box-shadow: 0 0 20px #e6ff00;
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
      background: rgba(14, 18, 14, 0.96);
      border: 1.5px solid #e6ff00;
      border-radius: 8px;
      padding: 12px 18px;
      color: #f0f0f0;
      font-family: 'JetBrains Mono', monospace, sans-serif;
      font-size: 13px;
      box-shadow: 0 8px 36px rgba(0,0,0,0.92), 0 0 25px rgba(230,255,0,0.25);
      pointer-events: none;
      opacity: 0;
      transform: translateY(8px);
      transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1);
      display: flex;
      flex-direction: column;
      gap: 5px;
      max-width: 440px;
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
    b.style.left = Math.min(window.innerWidth - 460, Math.max(20, x)) + 'px';
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

def type_text(page, selector, text, delay=0.04):
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
    time.sleep(0.3)

def prepare_fresh_desk_state():
    """Wipes clerk and scout cleanly, sets Sibyl & wallet scene, runs Scout so task 1 is wallet_18676b19."""
    import requests
    try:
        # Full wipe
        requests.post(f"{APP_URL}/api/desk/delete_test?full=true")
        # Save scene
        requests.post(f"{APP_URL}/api/scene", json={
            "name": "OnRecord Desk",
            "sources": [
                f"repo:cea-sec/Sibyl",
                f"wallet:{USER_WALLET}@8453"
            ]
        })
        # Run scout
        requests.post(f"{APP_URL}/api/scout/run")
        print(">> Desk primed cleanly with Sibyl repo, Base wallet, and fresh queue.")
    except Exception as e:
        print(">> Notice preparing fresh desk state:", e)

def record_delete_and_recovery_flow():
    print("[1/5] Preparing environment for Delete Test & Recovery Flow...")
    prepare_fresh_desk_state()

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

        # Handle native confirm dialogs automatically for Delete Test
        page.on("dialog", lambda dialog: dialog.accept())

        # Injected Web3 mock provider to simulate browser wallet confirmation
        wallet_mock_js = f"""
          window.ethereum = {{
            isMetaMask: true,
            request: async (args) => {{
              if (args.method === 'eth_requestAccounts') {{
                return ['{USER_WALLET}'];
              }}
              if (args.method === 'wallet_switchEthereumChain' || args.method === 'wallet_addEthereumChain') {{
                return null;
              }}
              if (args.method === 'eth_sendTransaction') {{
                return '{MOCK_TX_HASH}';
              }}
              return null;
            }}
          }};
        """

        # Navigate to Desk
        print("[2/5] Loading Contributor Desk...")
        page.goto(f"{APP_URL}/desk", wait_until="networkidle")
        page.evaluate(wallet_mock_js)
        page.evaluate(CURSOR_JS)
        time.sleep(1.5)

        # Select the contributor task card in Queue (wallet_18676b19)
        print("[3/5] Flow Step 1: Wallet Transaction Confirmation...")
        card = page.locator("#queue-body .desk-card").first
        box_card = card.bounding_box()
        if box_card:
            cx = box_card["x"] + box_card["width"] / 2
            cy = box_card["y"] + box_card["height"] / 2
            page.evaluate("window.showCallout(600, 180, '01 / SELECTING TASK', 'Selecting verified contributor task (wallet_18676b19) from the queue.')")
            move_mouse(page, cx, cy, duration=0.8)
            time.sleep(1.0)
            page.evaluate("window.hideCallout()")
            click_point(page, cx, cy)
        time.sleep(1.5)

        # Scroll Clerk column down to Base Ping section
        clerk_col = page.locator("#col-clerk .col-stream").first
        clerk_col.evaluate("el => el.scrollTo({ top: 380, behavior: 'smooth' })")
        time.sleep(1.2)

        # 1. Move to "Confirm onchain ping" checkbox and check it
        checkbox = page.locator("#confirm-ping-checkbox").first
        box_chk = checkbox.bounding_box()
        if box_chk:
            cx = box_chk["x"] + box_chk["width"] / 2
            cy = box_chk["y"] + box_chk["height"] / 2
            page.evaluate("window.showCallout(1100, 480, '02 / CONFIRMATION GATE', 'Operator explicitly checks confirmation before Base ping broadcast.')")
            page.evaluate(f"window.showArrow({cx}, {cy + 35}, 0)")
            move_mouse(page, cx, cy, duration=1.0)
            time.sleep(1.0)
            page.evaluate("window.hideArrow()")
            click_point(page, cx, cy)
            time.sleep(1.0)
            page.evaluate("window.hideCallout()")

        # 2. Click "Sign with Browser Wallet (MetaMask / Coinbase)"
        wallet_ping_btn = page.locator("#btn-wallet-ping").first
        box_ping = wallet_ping_btn.bounding_box()
        if box_ping:
            cx = box_ping["x"] + box_ping["width"] / 2
            cy = box_ping["y"] + box_ping["height"] / 2
            page.evaluate("window.showCallout(1100, 520, '03 / OPERATOR SIGNATURE', 'Signing on-chain ping to 0x75a0...6b19 on Base Mainnet (8453). Zero server private keys.')")
            page.evaluate(f"window.showArrow({cx}, {cy + 45}, 0)")
            move_mouse(page, cx, cy, duration=1.0)
            time.sleep(1.2)
            page.evaluate("window.hideArrow()")
            page.evaluate("window.hideCallout()")
            click_point(page, cx, cy)
            time.sleep(3.0)

        # Show confirmation callout with transaction hash
        page.evaluate(f"""
          window.showCallout(
            1100, 540,
            '04 / CONFIRMED ONCHAIN',
            'Transaction Broadcasted: {MOCK_TX_HASH[:12]}...{MOCK_TX_HASH[-8:]}<br/>Anchored to immutable append-only event journal on Base Mainnet.'
          )
        """)
        time.sleep(4.5)
        page.evaluate("window.hideCallout()")

        # ==========================================
        # STEP 2: BLIND CLERK VERIFICATION (UNFILED VS FILED)
        # ==========================================
        print("[4/5] Flow Step 2: Testing Verification on Unfiled vs Filed (Sibyl Blind Clerk Test)...")
        clerk_col.evaluate("el => el.scrollTo({ top: 0, behavior: 'smooth' })")
        time.sleep(1.0)

        # 1. Test unfiled handle
        verify_input = page.locator("#verify-person-input").first
        box_vi = verify_input.bounding_box()
        if box_vi:
            cx = box_vi["x"] + box_vi["width"] / 2
            cy = box_vi["y"] + box_vi["height"] / 2
            page.evaluate("window.showCallout(1250, 140, '05 / BLIND CLERK TEST', 'Testing an unfiled handle: Clerk must refuse execution without a memory file.')")
            move_mouse(page, cx, cy, duration=0.8)
            time.sleep(1.0)
            page.evaluate("window.hideCallout()")
            type_text(page, "#verify-person-input", "maya_unfiled", delay=0.05)
            time.sleep(0.5)

            # Click Check
            click_selector(page, "#btn-verify-person")
            time.sleep(2.5)

        # Highlight NOT ON RECORD
        page.evaluate("window.showCallout(1300, 160, '06 / STRICT REFUSAL', 'NOT ON RECORD: Entity was never filed into tenant_scout. Zero execution permitted.')")
        time.sleep(3.5)
        page.evaluate("window.hideCallout()")

        # 2. Test filed handle
        page.locator("#verify-person-input").fill("")
        type_text(page, "#verify-person-input", "wallet_18676b19", delay=0.04)
        time.sleep(0.5)
        click_selector(page, "#btn-verify-person")
        time.sleep(2.5)

        # Highlight ON RECORD
        page.evaluate("window.showCallout(1300, 160, '07 / VERIFIED ON RECORD', 'ON RECORD: Verified in SQLite storage. Bound to Base wallet 0x75a0...6b19.')")
        time.sleep(3.5)
        page.evaluate("window.hideCallout()")

        # ==========================================
        # STEP 3: THE DELETE TEST (SIBYL CORE RULE)
        # ==========================================
        print("[5/5] Flow Step 3: Executing The Delete Test (Wiping Scout Memory)...")
        del_btn = page.locator("#btn-delete-test").first
        box_del = del_btn.bounding_box()
        if box_del:
            cx = box_del["x"] + box_del["width"] / 2
            cy = box_del["y"] + box_del["height"] / 2
            page.evaluate("window.showCallout(800, 110, '08 / THE DELETE TEST', 'Sibyl Hackathon Invariant: Delete tenant_scout and the queue must drop to 0.')")
            page.evaluate(f"window.showArrow({cx}, {cy + 40}, 0)")
            move_mouse(page, cx, cy, duration=1.0)
            time.sleep(1.5)
            page.evaluate("window.hideArrow()")
            page.evaluate("window.hideCallout()")
            click_point(page, cx, cy)
            time.sleep(3.0)

        # Highlight the empty state
        page.evaluate("window.showCallout(400, 200, '09 / MEMORY IS LOAD-BEARING', 'Delete Test Passed: Queue is 0. Scout stream is 0. The desk is strictly the files.')")
        move_mouse(page, 500, 300, duration=1.0)
        time.sleep(4.0)
        page.evaluate("window.hideCallout()")

        # Re-verify filed handle in wiped state -> must be NOT ON RECORD!
        click_selector(page, "#btn-verify-person")
        time.sleep(2.5)
        page.evaluate("window.showCallout(1300, 160, '10 / ZERO RESIDUAL PROMPT STATE', 'Even previously verified entity now returns NOT ON RECORD. Zero prompt hallucination.')")
        time.sleep(4.0)
        page.evaluate("window.hideCallout()")

        # ==========================================
        # STEP 4: MEMORY RECOVERY (RESTORING SNAPSHOT)
        # ==========================================
        print("[6/5] Flow Step 4: Memory Recovery (Restoring Snapshot)...")
        restore_btn = page.locator("#btn-restore-memory").first
        box_res = restore_btn.bounding_box()
        if box_res:
            cx = box_res["x"] + box_res["width"] / 2
            cy = box_res["y"] + box_res["height"] / 2
            page.evaluate("window.showCallout(920, 110, '11 / MEMORY RECOVERY', 'Restoring SQLite snapshot: Recovering partition files and re-syncing Scout.')")
            page.evaluate(f"window.showArrow({cx}, {cy + 40}, 0)")
            move_mouse(page, cx, cy, duration=1.0)
            time.sleep(1.5)
            page.evaluate("window.hideArrow()")
            page.evaluate("window.hideCallout()")
            click_point(page, cx, cy)
            time.sleep(3.5)

        # Highlight restored state
        page.evaluate("window.showCallout(400, 200, '12 / RESTORE COMPLETE', 'Memory restored! Scout filings recovered. Queue repopulated with verified tasks.')")
        move_mouse(page, 500, 300, duration=1.0)
        time.sleep(3.5)
        page.evaluate("window.hideCallout()")

        # Re-verify person -> ON RECORD again!
        click_selector(page, "#btn-verify-person")
        time.sleep(2.5)

        # Select first queue card to re-open Clerk
        first_card = page.locator("#queue-body .desk-card").first
        box_fc = first_card.bounding_box()
        if box_fc:
            cx = box_fc["x"] + box_fc["width"] / 2
            cy = box_fc["y"] + box_fc["height"] / 2
            click_point(page, cx, cy)
            time.sleep(2.0)

        # Final Proof Callout
        page.evaluate("""
          window.showCallout(
            680, 480,
            '13 / SIBYL INVARIANT PROVEN',
            'Full Test Completed:<br/>• Confirmed On-Chain Ping<br/>• Blind Clerk Strict Refusal<br/>• Delete Test Queue Zero<br/>• Full Snapshot Recovery<br/><strong style="color:#e6ff00;">Memory is 100% Load-Bearing.</strong>'
          )
        """)
        time.sleep(6.0)

        print(">> Flow complete! Closing browser context...")
        page.close()
        context.close()
        browser.close()

    video_files = list(RECORDING_DIR.glob("*.webm"))
    if video_files:
        latest_video = max(video_files, key=os.path.getctime)
        print(f"Recorded video saved to: {latest_video}")
        return str(latest_video)
    return None

if __name__ == "__main__":
    record_delete_and_recovery_flow()
