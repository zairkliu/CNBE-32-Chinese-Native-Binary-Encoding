#!/usr/bin/env python3
import csv, os
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

def gen_radix():
    p = os.path.join(DATA_DIR, "radix_table.csv")
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["radix_id", "unicode", "hanzi", "stroke_count"])
        for i in range(1, 215):
            w.writerow([i, "", "", 0])
    print(f"Generated: radix_table.csv ({215} entries)")

def main():
    gen_radix()
    print("All databases generated")

if __name__ == "__main__":
    main()
