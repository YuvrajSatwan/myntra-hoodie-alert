# Myntra Hoodie Stock Watcher

Watches the **H&M Loose Fit Zip-Through Hoodie (size S)** on Myntra and pings Telegram the moment it's back in stock. Runs on GitHub Actions every 30 minutes.

Product: https://www.myntra.com/mailers/sweatshirts/h%26m/h%26m-loose-fit-zip-through-hoodie/35714533/buy

## 1. Create a Telegram bot

1. Open Telegram → search **@BotFather** → `/newbot` → follow prompts.
2. Save the **bot token** it gives you (looks like `123456:ABC-DEF...`).
3. Open your bot's chat and send it any message (`hi`).
4. Visit `https://api.telegram.org/bot<TOKEN>/getUpdates` in a browser — copy the `chat.id` number from the JSON.

## 2. Push this folder to a new GitHub repo

```bash
cd myntra_hoodie_alert
git init
git add .
git commit -m "init: myntra hoodie stock watcher"
git branch -M main
git remote add origin https://github.com/<you>/myntra-hoodie-alert.git
git push -u origin main
```

## 3. Add the secrets on GitHub

Repo → **Settings → Secrets and variables → Actions → New repository secret**

| Name | Value |
|---|---|
| `TELEGRAM_BOT_TOKEN` | the token from BotFather |
| `TELEGRAM_CHAT_ID`   | the chat id from step 1 |

## 4. Turn Actions on

Repo → **Actions** tab → enable workflows. The cron fires every 30 min; you can also hit **Run workflow** manually to test.

## Local test

```bash
set TELEGRAM_BOT_TOKEN=xxxxx
set TELEGRAM_CHAT_ID=yyyyy
python check_stock.py
```

With no creds, it just prints what it would have sent.

## Notes

- Script uses only the Python stdlib (no `pip install`) — Actions stays fast and free.
- It tries Myntra's PDP gateway first, falls back to HTML scrape if that 403s.
- To watch a different size, change `TARGET_SIZE` at the top of `check_stock.py`.
- To watch a different product, change `STYLE_ID` and `PRODUCT_URL` (the styleId is the number in the URL — here `35714533`).
- Message text rotates through hype lines so you don't get bored of the alert.
