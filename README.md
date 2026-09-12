# XOIO 麻將 · 免費試玩 App

以 **Capacitor** 打包的「免費試玩 台灣 16 張麻將」Android / iOS App。

## 內容來源

`www/` = 官網的純免費頁面(已去博弈化,零下注/加密元素):

- `free.html` — 入口(免費試玩)
- `play.html` — AI 對局(乾淨版)
- `about.html` — 關於 XOIO(中性介紹)
- `favicon.svg` / `pwa/*` / `mj/*` — 圖標與牌面

## 建置(雲端 CI,免本機 SDK)

- **Android**:push 到 `main` → GitHub Actions 自動產 **debug APK** 並上傳為 artifact(`mahjong-debug-apk`)→ 下載即可安裝測試。
- **iOS**:GitHub Actions(macOS runner)產**模擬器用** app(未簽章)。要裝到實機/上架需 Apple 簽章。

## 本機建置(需 Android SDK / Xcode)

```bash
npm install
npx cap sync
npx cap open android   # 或 npx cap open ios
```

## 上架

- Google Play:需 Gradle `bundleRelease` 產 AAB + 簽章金鑰。
- App Store:需 Apple Developer 簽章 + Xcode archive。

> 提醒:本 App 刻意不含任何博弈/下注/加密元素;請勿加入連往博弈頁的連結,以免違反商店政策。
