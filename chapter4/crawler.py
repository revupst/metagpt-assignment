import asyncio
import aiohttp
from bs4 import BeautifulSoup


async def fetch(session, url):
    async with session.get(url, proxy="http://127.0.0.1:8888") as response:
        return await response.text()


async def parse(url):
    # proxydict = {"http": "http://127.0.0.1:8888", "https": "http://127.0.0.1:8888"}
    async with aiohttp.ClientSession() as session:
        html = await fetch(session, url)
        soup = BeautifulSoup(html, "html.parser")

        # 解析所需字段
        for article in soup.find_all("article", class_="Box-row"):
            repo_name = article.h2.a.text.strip()
            repo_url = "https://github.com" + article.h2.a["href"]
            description = article.p.text.strip() if article.p else "No Description"
            language = article.find(
                "span", class_="repo-language-color"
            ).next_sibling.strip()
            stars = (
                article.find_all("a", class_="Link--muted d-inline-block mr-3")[0]
                .text.strip()
                .replace(",", "")
            )
            forks = (
                article.find_all("a", class_="Link--muted d-inline-block mr-3")[1]
                .text.strip()
                .replace(",", "")
            )
            today_stars = (
                article.find("span", class_="d-inline-block float-sm-right")
                .text.strip()
                .split(" ")[0]
                .replace(",", "")
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
