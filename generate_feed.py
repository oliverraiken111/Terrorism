import requests
from bs4 import BeautifulSoup
import datetime
import xml.etree.ElementTree as ET

# FT Syria section
url = "https://www.ft.com/syria"
headers = {"User-Agent": "Mozilla/5.0"}

response = requests.get(url, headers=headers)
response.raise_for_status()
soup = BeautifulSoup(response.text, "html.parser")

# Set up RSS feed
ET.register_namespace('media', 'http://search.yahoo.com/mrss/')
rss = ET.Element('rss', {"version": "2.0", "xmlns:media": "http://search.yahoo.com/mrss/"})
channel = ET.SubElement(rss, 'channel')
ET.SubElement(channel, 'title').text = "FT.com Syria News"
ET.SubElement(channel, 'link').text = url
ET.SubElement(channel, 'description').text = "Latest news on Syria from the Financial Times"
ET.SubElement(channel, 'lastBuildDate').text = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

# Extract Syria-specific articles
articles_found = 0
seen_titles = set()

for teaser in soup.select('a.js-teaser-heading-link[href^="/content/"]'):
    title = teaser.get_text(strip=True)
    href = teaser["href"]

    if not title or title in seen_titles:
        continue

    seen_titles.add(title)
    full_url = "https://www.ft.com" + href

    # Try to get actual pubDate from the article page
    try:
        article_resp = requests.get(full_url, headers=headers)
        article_resp.raise_for_status()
        article_soup = BeautifulSoup(article_resp.text, "html.parser")

        # FT meta tag for published time
        meta_tag = article_soup.find("meta", attrs={"property": "article:published_time"})
        if meta_tag and meta_tag.get("content"):
            pub_date_iso = meta_tag["content"]
            pub_date = datetime.datetime.fromisoformat(pub_date_iso.rstrip("Z"))
            pub_date_str = pub_date.strftime("%a, %d %b %Y %H:%M:%S GMT")
        else:
            pub_date_str = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

    except Exception as e:
        print(f"⚠️ Failed to fetch pubDate for {full_url}: {e}")
        pub_date_str = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

    item = ET.SubElement(channel, "item")
    ET.SubElement(item, "title").text = title
    ET.SubElement(item, "link").text = full_url
    ET.SubElement(item, "description").text = f"FT article on Syria: {title}"
    ET.SubElement(item, "pubDate").text = pub_date_str

    articles_found += 1
    if articles_found >= 10:
        break

# Write output
with open("syria_fixed.xml", "wb") as f:
    ET.ElementTree(rss).write(f, encoding="utf-8", xml_declaration=True)

print(f"✅ RSS feed created with {articles_found} Syria-specific articles.")
