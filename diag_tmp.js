
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
    await page.goto('https://dcs-web-tac.onrender.com/', { waitUntil: 'networkidle', timeout: 30000 });
    // 等待 Cesium 彻底完成初始化
    await new Promise(r => setTimeout(r, 8000));
    
    // 检查核心对象
    const viewerStatus = await page.evaluate(() => {
        return {
            cesiumReady: typeof Cesium !== 'undefined',
            viewerReady: typeof viewer !== 'undefined' && viewer !== null,
            hudReady: !!document.getElementById('hud-lat')
        };
    });
    
    if (!viewerStatus.viewerReady) logs.push('[SYSTEM_ERROR] Cesium Viewer 未能正确初始化');
    if (!viewerStatus.hudReady) logs.push('[SYSTEM_ERROR] 遥测 HUD 元素缺失');
    
    console.log(JSON.stringify(logs));
  } catch (e) {
    console.log(JSON.stringify(["[CONNECTION_ERROR] 访问失败: " + e.message]));
  } finally {
    await browser.close();
  }
})();
