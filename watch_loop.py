"""
Continuous local background watcher for H&M Hoodie on Myntra.
Checks every 10 minutes and sends a Telegram alert as soon as Size S is in stock.
"""
import time
import sys
from datetime import datetime
import check_stock

INTERVAL_SECONDS = 600  # 10 minutes


def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Myntra Hoodie Watcher started.")
    print(f"Target: H&M Loose Fit Zip-Through Hoodie | Size: {check_stock.TARGET_SIZE}")
    print(f"Checking every {INTERVAL_SECONDS // 60} minutes...\n")

    while True:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] Checking stock...", end=" ", flush=True)
        try:
            try:
                pdp = check_stock.fetch_product_json()
            except Exception:
                pdp = check_stock.fetch_from_html()

            sizes = check_stock.extract_sizes(pdp)
            target = next((a for (lab, a) in sizes if lab == check_stock.TARGET_SIZE), None)

            if target is True:
                print("SIZE S IS IN STOCK! Sending alert!")
                check_stock.main()
                print("Notification sent to your Telegram! Exiting watcher.")
                break
            elif target is False:
                print("Size S still out of stock.")
            else:
                print("Size S not listed in options.")
        except Exception as e:
            print(f"Error during check: {e}")

        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nWatcher stopped by user.")
        sys.exit(0)
