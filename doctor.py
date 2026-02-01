import subprocess
import sys
import os
import json
import time

def check_backend():
    print("🔍 [后端检查] 运行自动化测试...")
    try:
        result = subprocess.run(["python3", "-m", "pytest", "tests/test_api.py"], 
                              env={**os.environ, "PYTHONPATH": os.getcwd()},
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ 后端: API 测试全部通过。")
            return True
        else:
            print(f"❌ 后端: API 测试失败!\n{result.stdout}")
            return False
    except Exception as e:
        print(f"❌ 后端: 发生严重错误: {e}")
        return False

def check_frontend(url):
    print(f"🔍 [前端检查] 使用 Playwright 扫描 {url} ...")
    js_code = """
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const logs = [];
  page.on('console', msg => {
    const txt = msg.text();
    // 忽略一些由于外部库(Cesium)引起的非致命性资源加载警告或特定报错
    if (msg.type() === 'error' && !txt.includes('NaturalEarthII') && !txt.includes('GPU stall')) {
        logs.push('[CONSOLE_ERROR] ' + txt);
    }
  });
  page.on('pageerror', err => logs.push('[RUNTIME_ERROR] ' + err.message));
  
  try {
    await page.goto('""" + url + """', { waitUntil: 'networkidle', timeout: 30000 });
    // 等待 Cesium 彻底完成初始化
    await new Promise(r => setTimeout(r, 8000));
    
    // 检查核心对象（Vue 版本不暴露全局 viewer）
    const viewerStatus = await page.evaluate(() => {
        const cesiumReady = typeof Cesium !== 'undefined';
        const container = document.getElementById('cesiumContainer');
        const hasCanvas = !!(container && container.querySelector('canvas'));
        const hasHudText = !!document.querySelector('header h1');
        return { cesiumReady, hasCanvas, hasHudText };
    });
    
    if (!viewerStatus.cesiumReady) logs.push('[SYSTEM_ERROR] Cesium 未加载');
    if (!viewerStatus.hasCanvas) logs.push('[SYSTEM_ERROR] Cesium Canvas 未渲染');
    if (!viewerStatus.hasHudText) logs.push('[SYSTEM_ERROR] HUD/顶部栏缺失');
    
    console.log(JSON.stringify(logs));
  } catch (e) {
    console.log(JSON.stringify(["[CONNECTION_ERROR] 访问失败: " + e.message]));
  } finally {
    await browser.close();
  }
})();
"""
    try:
        with open("diag_tmp.js", "w") as f: f.write(js_code)
        
        # 针对 Render 部署延迟，进行多轮探测
        for i in range(10):
            print(f"   (尝试 {i+1}/10) 探测浏览器控制台日志...")
            result = subprocess.run(["node", "diag_tmp.js"], capture_output=True, text=True)
            if not result.stdout.strip(): continue
            
            try:
                logs = json.loads(result.stdout)
            except:
                continue

            # 过滤掉 401 报错（这是残留的旧版本特征）
            is_old_version = any("401" in l for l in logs)
            
            if is_old_version:
                print("   ⚠️ 检测到 401 报错，这说明 Render 还在运行旧代码，等待部署更新...")
                time.sleep(30)
                continue

            if not logs:
                print("✅ 前端: 未发现任何报错，页面加载完美。")
                os.remove("diag_tmp.js")
                return True
            else:
                print(f"❌ 前端: 发现 {len(logs)} 个致命错误:")
                for e in logs: print(f"   - {e}")
                os.remove("diag_tmp.js")
                return False
                
        print("❌ 前端: 探测超时，代码可能未生效或持续报错。")
        return False
    except Exception as e:
        print(f"❌ 前端: 诊断脚本执行失败: {e}")
        return False

if __name__ == "__main__":
    target = "https://dcs-web-tac.onrender.com/"
    b_ok = check_backend()
    f_ok = check_frontend(target)
    if b_ok and f_ok:
        print("\n✨ 全链路验证结果: 完美健康 (HEALTHY)")
        sys.exit(0)
    else:
        print("\n🚨 全链路验证结果: 存在缺陷 (UNHEALTHY)")
        sys.exit(1)
