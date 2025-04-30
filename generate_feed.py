import requests
from bs4 import BeautifulSoup
import datetime
import xml.etree.ElementTree as ET
import json

# Set up RSS structure
ET.register_namespace('media', 'http://search.yahoo.com/mrss/')
rss = ET.Element('rss', {"version": "2.0", "xmlns:media": "http://search.yahoo.com/mrss/"})
channel = ET.SubElement(rss, 'channel')
ET.SubElement(channel, 'title').text = "Terrorism News from FT and NYT"
ET.SubElement(channel, 'link').text = "https://www.ft.com/terrorism"
ET.SubElement(channel, 'description').text = "Latest news on terrorism from the Financial Times and The New York Times"
ET.SubElement(channel, 'lastBuildDate').text = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

seen_titles = set()
articles_found = 0
headers = {"User-Agent": "Mozilla/5.0"}

### FT Articles
ft_url = "https://www.ft.com/terrorism"
try:
    response = requests.get(ft_url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    for teaser in soup.select('a.js-teaser-heading-link[href^="/content/"]'):
        title = teaser.get_text(strip=True)
        href = teaser["href"]
        if not title or title in seen_titles:
            continue

        seen_titles.add(title)
        full_url = "https://www.ft.com" + href

        # Try to extract actual publication date
        try:
            article_resp = requests.get(full_url, headers=headers)
            article_resp.raise_for_status()
            article_soup = BeautifulSoup(article_resp.text, "html.parser")

            pub_date_str = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
            json_ld = article_soup.find("script", type="application/ld+json")
            if json_ld:
                json_data = json.loads(json_ld.string.strip())
                if isinstance(json_data, list):
                    json_data = json_data[0]
                if "datePublished" in json_data:
                    pub_date = datetime.datetime.fromisoformat(json_data["datePublished"].replace("Z", "+00:00"))
                    pub_date_str = pub_date.strftime("%a, %d %b %Y %H:%M:%S GMT")
        except Exception as e:
            print(f"⚠️ Failed to fetch pubDate from FT article: {full_url} ({e})")
            pub_date_str = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = title
        ET.SubElement(item, "link").text = full_url
        ET.SubElement(item, "description").text = f"FT article on terrorism: {title}"
        ET.SubElement(item, "pubDate").text = pub_date_str

        articles_found += 1
        if articles_found >= 10:
            break
except Exception as e:
    print(f"❌ Could not fetch FT content: {e}")

### NYT Articles
nyt_url = "https://www.nytimes.com/topic/subject/terrorism"
try:
    response = requests.get(nyt_url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    for article in soup.select('ol li div.css-1l4spti a[href^="/"]'):
        title = article.get_text(strip=True)
        href = article.get("href")
        if not title or title in seen_titles:
            continue

        seen_titles.add(title)
        full_url = "https://www.nytimes.com" + href

        # Try to extract actual publication date
        try:
            article_resp = requests.get(full_url, headers=headers)
            article_resp.raise_for_status()
            article_soup = BeautifulSoup(article_resp.text, "html.parser")

            pub_date_str = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
            meta = article_soup.find("meta", attrs={"name": "ptime"}) or \
                   article_soup.find("meta", attrs={"property": "article:published"})

            if meta and meta.get("content"):
                pub_date = datetime.datetime.fromisoformat(meta["content"].replace("Z", "+00:00"))
                pub_date_str = pub_date.strftime("%a, %d %b %Y %H:%M:%S GMT")
        except Exception as e:
            print(f"⚠️ Failed to fetch pubDate from NYT article: {full_url} ({e})")
            pub_date_str = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = title
        ET.SubElement(item, "link").text = full_url
        ET.SubElement(item, "description").text = f"NYT article on terrorism: {title}"
        ET.SubElement(item, "pubDate").text = pub_date_str

        articles_found += 1
        if articles_found >= 20:
            break
except Exception as e:
    print(f"❌ Could not fetch NYT content: {e}")

# Write output
with open("terrorism.xml", "wb") as f:
    ET.ElementTree(rss).write(f, encoding="utf-8", xml_declaration=True)

print(f"✅ RSS feed created with {articles_found} terrorism-specific articles.")
