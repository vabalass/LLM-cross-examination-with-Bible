#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://biblija.lt/index.aspx?cmp=reading&doc=BiblijaRKK1998_Jn_"
OUTPUT_DIR = "Jono_evangelija"
NAMING_CONVENTION = "Jn_{chapter}.txt"
START_CHAPTER = 1
END_CHAPTER = 21  # inclusive


def fetch_html(chapter):
    url = BASE_URL + str(chapter)
    print(f"Fetching chapter {chapter}: {url}")
    r = requests.get(url)
    r.raise_for_status()
    r.encoding = "utf-8"
    return r.text


def extract_chapter_text(html):
    soup = BeautifulSoup(html, "html.parser")

    # chapter label: Mk 1, Mk 2, ...
    chapter_label = soup.find("td", class_="bibl_kn")
    chapter_name = chapter_label.get_text(strip=True) if chapter_label else "Unknown Chapter"

    # the text is in the second <td> of the same <tr>
    tr = chapter_label.find_parent("tr")
    content_td = tr.find_all("td")[1]

    paragraphs = content_td.find_all("p")

    out_lines = [chapter_name]   # FIRST LINE = chapter name

    for p in paragraphs:
        # Remove footnote hyperlinks (<a>) but keep verse numbers
        for a in p.find_all("a"):
            a.decompose()

        # DO NOT remove <sup> -> keeps verse numbers
        text = p.get_text(strip=True)

        if text:
            out_lines.append(text)

    return "\n".join(out_lines)


def save_chapter(chapter, text):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filename = os.path.join(OUTPUT_DIR, NAMING_CONVENTION.format(chapter=chapter))
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Saved: {filename}")


def main():
    for chapter in range(START_CHAPTER, END_CHAPTER + 1):
        try:
            html = fetch_html(chapter)
            text = extract_chapter_text(html)
            save_chapter(chapter, text)
            time.sleep(0.3)
        except Exception as e:
            print(f"Error on chapter {chapter}: {e}")


if __name__ == "__main__":
    main()
