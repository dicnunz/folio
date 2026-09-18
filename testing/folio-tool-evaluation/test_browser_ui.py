import socket
import subprocess
import sys
import time
from urllib.request import urlopen

from playwright.sync_api import sync_playwright


APP_URL = "http://127.0.0.1:8501"


def wait_for_server(url: str, timeout: float = 30.0):
   deadline = time.time() + timeout
   while time.time() < deadline:
      try:
            with urlopen(url) as response:
               if response.status < 500:
                  return
      except Exception:
            time.sleep(0.5)
   raise RuntimeError(f"Streamlit app did not become ready at {url}")


def run_playwright_flow():
   repo_root = __file__.rsplit("/", 1)[0]
   proc = subprocess.Popen(
      [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "tinyfolio.py",
            "--server.headless",
            "true",
            "--server.address",
            "127.0.0.1",
            "--server.port",
            "8501",
      ],
      cwd=repo_root,
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL,
   )
   try:
      wait_for_server(APP_URL)
      with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            page.goto(APP_URL)
            page.wait_for_selector("text=Folio Prototype", timeout=30000)
            assignment_input = page.get_by_label("Assignment Name")
            assignment_input.wait_for(state="visible", timeout=30000)
            assignment_input.fill("Design Review")
            page.get_by_role("button", name="Add Assignment").click()
            page.wait_for_selector("text=Assignment added.", timeout=30000)
            assert page.get_by_text("Assignment added.").is_visible()
            browser.close()
   finally:
      proc.terminate()
      try:
            proc.wait(timeout=10)
      except subprocess.TimeoutExpired:
            proc.kill()


def test_playwright_ui_smoke():
   run_playwright_flow()
