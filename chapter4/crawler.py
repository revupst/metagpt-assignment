import asyncio

import aiohttp
from bs4 import BeautifulSoup
from metagpt.actions.action import Action
from metagpt.config import CONFIG
from metagpt.logs import logger


class CrawlOSSTrending(Action):
    async def run(self, url: str = "https://github.com/trending"):
        async with aiohttp.ClientSession() as client:
            async with client.get(url, proxy=CONFIG.global_proxy) as response:
                response.raise_for_status()
                html = await response.text()

        soup = BeautifulSoup(html, "html.parser")

        repositories = []

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

            repo_info = {
                "name": repo_name,
                "url": repo_url,
                "description": description,
                "language": language,
                "stars": stars,
                "forks": forks,
                "today_stars": today_stars,
            }
            repositories.append(repo_info)

        return repositories


async def main():
    action = CrawlOSSTrending()
    result = await action.run()
    logger.info(result)


if __name__ == "__main__":
    asyncio.run(main())
