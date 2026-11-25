# Sticker packs builder (GitHub Actions)

Telegram sticker packs (static + video + animated) -> WhatsApp-ready WebP, hosted free on GitHub Pages.
PC ekata kisima de install karanna ona naha.

## Setup (eka paara)
1. GitHub eke aluth repo ekak hadanna (eg: `novakey-stickers`), me folder eke files okkoma upload karanna (`.github` folder eka ekka).
2. Repo -> **Settings -> Pages -> Build and deployment -> Source = "GitHub Actions"**.
3. Repo -> **Settings -> Secrets and variables -> Actions -> New repository secret**
   Name: `TELEGRAM_BOT_TOKEN`   Value: oyage bot token eka (@BotFather).
4. `packs.txt` eke pack links danna (format eke top eke thiyenawa), commit karanna.
5. **Actions** tab eke "Build sticker packs" run wenawa balanna (1-5 min). Green unama ready.
6. App eke `StickerCatalog.kt` -> `StickerConfig.CATALOG_URL` ekata:
   `https://<github-username-lowercase>.github.io/<repo-name>/catalog.json`

## Aluth pack ekak add karanna
`packs.txt` ekata line ekak add karala commit karanna. Automatically run wenawa. App ekata app update ona naha.
Pack eke stickers wenas kala nam line eke version eka +1 karanna.

## Notes
- Token eka dan app eke APK ekata danna ona naha (GitHub secret ekata withrai).
- Animated (.tgs) convert eka test karala naha; fail unoth Actions log eke "skip" kiyala pennanawa.
- Sticker 500 KB wata adu (animated) / 100 KB (static) wenna auto adu karanawa.
