"""
SEO Listing Generator
----------------------
Reads products.csv, generates an SEO-optimized title + description for each
row, and writes results to output.csv.

Two modes:
  1. AI mode (default) - calls the Anthropic API. Requires ANTHROPIC_API_KEY.
  2. Offline mode (--offline) - rule-based generator, no API key needed.
     Use this if you don't have an API key yet. It still produces a real,
     working automation you can demo.

Usage:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY="your-key-here"     # skip this line for --offline
    python seo_generator.py                       # AI mode
    python seo_generator.py --offline              # offline/rule-based mode
"""

import csv
import os
import sys
import time
import argparse


def build_prompt(product_name: str, specs: str, category: str) -> str:
    return (
        f"Write an SEO-optimized e-commerce listing for this product.\n"
        f"Product name: {product_name}\n"
        f"Specs: {specs}\n"
        f"Category: {category}\n\n"
        f"Return exactly two lines, no labels, no markdown:\n"
        f"Line 1: an SEO title, under 60 characters, keyword-rich.\n"
        f"Line 2: a 2-sentence product description highlighting benefits."
    )


def generate_ai(product_name: str, specs: str, category: str) -> tuple[str, str]:
    import anthropic

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
    prompt = build_prompt(product_name, specs, category)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    title = lines[0] if len(lines) > 0 else product_name
    description = lines[1] if len(lines) > 1 else specs
    return title, description


def generate_offline(product_name: str, specs: str, category: str) -> tuple[str, str]:
    """No API needed. Simple template + keyword combination."""
    first_spec = specs.split(",")[0].strip() if specs else ""
    title = f"{product_name} - {first_spec} | {category}"
    title = title[:60]

    description = (
        f"Upgrade your routine with the {product_name}, built with {specs.strip().lower()}. "
        f"A reliable choice in {category.lower()} designed for everyday use."
    )
    return title, description


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="products.csv")
    parser.add_argument("--output", default="output.csv")
    parser.add_argument("--offline", action="store_true", help="Run without calling any API")
    args = parser.parse_args()

    if not args.offline and not os.environ.get("ANTHROPIC_API_KEY"):
        print("No ANTHROPIC_API_KEY found. Run again with --offline, or set the key.")
        sys.exit(1)

    with open(args.input, newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        rows = list(reader)

    results = []
    for i, row in enumerate(rows, start=1):
        name, specs, category = row["product_name"], row["specs"], row["category"]
        print(f"[{i}/{len(rows)}] Processing: {name}")

        try:
            if args.offline:
                title, description = generate_offline(name, specs, category)
            else:
                title, description = generate_ai(name, specs, category)
                time.sleep(0.5)  # basic rate-limit courtesy
        except Exception as e:
            print(f"  Error on '{name}': {e}. Falling back to offline mode for this row.")
            title, description = generate_offline(name, specs, category)

        results.append({
            "product_name": name,
            "specs": specs,
            "category": category,
            "new_title": title,
            "new_description": description,
        })

    with open(args.output, "w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(
            outfile,
            fieldnames=["product_name", "specs", "category", "new_title", "new_description"],
        )
        writer.writeheader()
        writer.writerows(results)

    print(f"\nDone. Wrote {len(results)} rows to {args.output}")


if __name__ == "__main__":
    main()
