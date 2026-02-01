import subprocess
import sys
import os
import json
import time

def check_backend():
    print("🔍 [Backend] Running automated test suite...")
    try:
        result = subprocess.run(["python3", "-m", "pytest", "tests/test_api.py"], 
                              env={**os.environ, "PYTHONPATH": os.getcwd()},
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Backend: All API tests passed.")
            return True
        else:
            print(f"❌ Backend: API tests failed!\n{result.stdout}")
            return False
    except Exception as e:
        print(f"❌ Backend: Critical error: {e}")
        return False

def check_frontend(url):
    print(f"🔍 [Frontend] Scanning {url} via Headless Browser...")
    js_code = """
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const logs = [];
  page.on('console', msg => logs.push('[' + msg.type().toUpperCase() + '] ' + msg.text()));
  page.on('pageerror', err => logs.push('[RUNTIME] ' + err.message));
  try {
    await page.goto('""" + url + """', { waitUntil: 'networkidle', timeout: 30000 });
    await new Promise(r => setTimeout(r, 5000));
    console.log(JSON.stringify(logs));
  } catch (e) {
    console.log(JSON.stringify(["ERROR: " + e.message]));
  } finally {
    await browser.close();
  }
})();
"""
    try:
        with open("diag_tmp.js", "w") as f: f.write(js_code)
        
        # 增加重试逻辑，等待部署生效
        for i in range(5):
            print(f"   (Attempt {i+1}/5) Checking console logs...")
            result = subprocess.run(["node", "diag_tmp.js"], capture_output=True, text=True)
            if not result.stdout.strip(): continue
            
            logs = json.loads(result.stdout)
            # 排除掉不可避免的 WebGL 性能警告以及 Cesium 内部的资源加载警告
            errors = [l for l in logs if ("ERROR" in l or "RUNTIME" in l or "401" in l or "500" in l) 
                      and "GPU stall" not in l 
                      and "NaturalEarthII" not in l]
            
            if not errors:
                print("✅ Frontend: No critical console errors found.")
                os.remove("diag_tmp.js")
                return True
            
            # 如果发现老错误，可能部署还没完
            if any("TypeError" in e for e in errors) and i < 4:
                print("   ⚠️ Found old error, waiting for Render deployment to finish...")
                time.sleep(30)
                continue
            
            print(f"❌ Frontend: Detected {len(errors)} critical errors:")
            for e in errors: print(f"   - {e}")
            os.remove("diag_tmp.js")
            return False
            
    except Exception as e:
        print(f"❌ Frontend: Diagnostic failed: {e}")
        return False

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "https://dcs-web-tac.onrender.com/"
    b_ok = check_backend()
    f_ok = check_frontend(target)
    if b_ok and f_ok:
        print("\n✨ FULL CHAIN STATUS: HEALTHY")
        sys.exit(0)
    else:
        print("\n🚨 FULL CHAIN STATUS: UNHEALTHY")
        sys.exit(1)
