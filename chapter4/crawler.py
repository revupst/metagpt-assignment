import asyncio
import os

import aiohttp
from bs4 import BeautifulSoup


async def fetch(session, url):
    http_proxy = os.getenv("http_proxy")
    async with session.get(url, proxy=http_proxy) as response:
        return await response.text()


async def parse(url):
    async with aiohttp.ClientSession() as session:
        html = await fetch(session, url)
        soup = BeautifulSoup(html, "html.parser")

        # 解析所需字段
        for article in soup.find_all("article", class_="Box-row"):
            repo_name = article.h2.a.text.strip()
            repo_url = "https://github.com" + article.h2.a["href"]
            description = article.p.text.strip() if article.p else "No Description"
            language_elements = article.find_all("span", class_="repo-language-color")
            language = (
                language_elements[0].next_sibling.strip()
                if language_elements
                else "Unknown"
            )

            star_fork_elements = article.find_all(
                "a", class_="Link--muted d-inline-block mr-3"
            )
            stars = (
                star_fork_elements[0].text.strip().replace(",", "")
                if len(star_fork_elements) > 0
                else "0"
            )
            forks = (
                star_fork_elements[1].text.strip().replace(",", "")
                if len(star_fork_elements) > 1
                else "0"
            )

            today_stars_element = article.find(
                "span", class_="d-inline-block float-sm-right"
            )
            today_stars = (
                today_stars_element.text.strip().split(" ")[0].replace(",", "")
                if today_stars_element
                else "0"
            )

            print(
                {
                    "Repository Name": repo_name,
                    "URL": repo_url,
                    "Description": description,
                    "Language": language,
                    "Stars": stars,
                    "Forks": forks,
                    "Stars Today": today_stars,
                }
            )


async def main():
    url = "https://github.com/trending"
    await parse(url)


if __name__ == "__main__":
    asyncio.run(main())
