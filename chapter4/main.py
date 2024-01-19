import asyncio
import json
from typing import Any

import aiohttp
from bs4 import BeautifulSoup
from metagpt.actions import Action
from metagpt.config import CONFIG
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message

from .callback import discord_callback


class HuggingfacePaperMainpageCrawl(Action):
    async def run(self, url: str = "https://huggingface.co/papers"):
        logger.info(f"Mainpage Crawl start!")
        async with aiohttp.ClientSession() as client:
            async with client.get(url, proxy=CONFIG.global_proxy) as response:
                response.raise_for_status()
                html = await response.text()

        soup = BeautifulSoup(html, "html.parser")
        papers = []

        for article in soup.find_all(
            "article", class_="flex flex-col overflow-hidden rounded-xl border"
        ):
            title_tag = article.find("h3")
            if title_tag and title_tag.a:
                title = title_tag.a.get_text(strip=True)
                paper_url = title_tag.a["href"]
                parts = paper_url.split("/")
                paper_id = parts[-1] if parts else None
                papers.append({"title": title, "id": paper_id})

        logger.info(f"papers: {papers}")
        return papers


class HuggingfacePaperContentCrawl(Action):
    def __init__(self, paper_id: str):
        super().__init__()
        self.paper_id = paper_id

    async def run(self):
        base_url = "https://huggingface.co/papers"
        url = base_url + "/" + self.paper_id
        async with aiohttp.ClientSession() as client:
            async with client.get(url, proxy=CONFIG.global_proxy) as response:
                response.raise_for_status()
                html = await response.text()

        soup = BeautifulSoup(html, "html.parser")
        # 找到包含论文信息的部分
        main_tag = soup.find("main", class_="flex flex-1 flex-col")
        paper_data = main_tag.find("div", {"data-target": "PaperContent"})["data-props"]
        paper_info = json.loads(paper_data)["paper"]

        # 提取所需信息
        paper_details = {
            "id": paper_info["id"],
            "title": paper_info["title"],
            "url": f"https://huggingface.co/papers/{paper_info['id']}",
            "authors": [author["name"] for author in paper_info["authors"]],
            "summary": paper_info["summary"],
            "publishedAt": paper_info["publishedAt"],
            "originLink": f"https://arxiv.org/abs/{paper_info['id']}",
        }

        return paper_details


PAPER_ANALYSIS_PROMPT = """Please act as a HuggingFace Paper Analyst, aiming to provide users with insightful and personalized recommendations based on the HuggingFace Daily Paper listings page. Based on the context, fill in the missing information, generate engaging and informative titles, ensuring users discover papers aligned with their interests. The output language is {language}.
---
# The title about Today's HuggingFace Daily Papers
## Daily Papers Insight: Uncover the Hottest HuggingFace Papers Today! Explore the hot papers and discover key domains capturing researchers' attention. From ** to **, witness the top papers like never before.
## Highlights of the List: Spotlight noteworthy projects on HuggingFace Paper, including new ideas, innovative framework, focusing on delivering distinctive and attention-grabbing content for users.
---
# Format Example

```
# [Title]

## Daily Papers Insight
Today, ** and ** continue to dominate as the most popular papers. Key areas of interest include **, ** and **.
The top popular papers are paper1 and paper2.

## The Trends Categories
1. Generative AI
    - [Paper1](https://huggingface.co/papers/1234.2222): [detail of the paper, such as summary, authors background, ...]
    - [Paper2](https://huggingface.co/papers/1234.2223): ...
...

## Highlights of the List
1. [Paper3](https://huggingface.co/papers/1234.2224): [provide specific reasons why this project is recommended].
...
```

---
# Popular Papers
{papers}
"""


class HuggingfacePaperContentAnalyze(Action):
    async def run(self, papers: Any, language: str = "Chinese") -> str:
        return await self._aask(
            PAPER_ANALYSIS_PROMPT.format(papers=papers, language=language)
        )


class HuggingfacePaperWatcher(Role):
    def __init__(
        self,
        name: str = "Codey",
        profile: str = "HuggingfacePaperWatcher",
        goal: str = "Generate an insightful HuggingFace Paper analysis report.",
        constraints: str = "Only analyze based on the provided HuggingFace Paper data.",
    ):
        super().__init__(name, profile, goal, constraints)
        self._init_actions([HuggingfacePaperMainpageCrawl])
        # self._set_react_mode(react_mode="by_order")
        self.total_content = ""

    async def _think(self) -> None:
        """Determine the next action to be taken by the role."""
        logger.info(self._rc.state)
        logger.info(
            self,
        )
        if self._rc.todo is None:
            self._set_state(0)
            return

        if self._rc.state + 1 < len(self._states):
            self._set_state(self._rc.state + 1)
        else:
            self._rc.todo = None

    async def _react(self) -> Message:
        """Execute the assistant's think and actions.

        Returns:
            A message containing the final result of the assistant's actions.
        """
        while True:
            await self._think()
            if self._rc.todo is None:
                logger.info(f"_react break!")
                break
            msg = await self._act()

        return msg

    async def _handle_papers(self, papers: list) -> Message:
        logger.info(f"_handle_papers: {papers}")
        actions = []
        for paper in papers:
            paper_id = paper["id"]
            actions.append(HuggingfacePaperContentCrawl(paper_id=paper_id))
        actions.append(HuggingfacePaperContentAnalyze)
        self._init_actions(actions)
        # self._set_react_mode(react_mode="by_order")
        self._rc.todo = None
        msg = Message(content="_handle_papers Done")
        self._rc.memory.add(msg)
        return msg

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: ready to {self._rc.todo}")
        todo = self._rc.todo
        if type(todo) is HuggingfacePaperMainpageCrawl:
            logger.info(
                f"HuggingfacePaperMainpageCrawl {self._setting}: ready to {self._rc.todo}"
            )
            resp = await todo.run(url="https://huggingface.co/papers")
            return await self._handle_papers(resp)
        elif type(todo) is HuggingfacePaperContentAnalyze:
            logger.info(
                f"HuggingfacePaperContentAnalyze {self._setting}: ready to {self._rc.todo}"
            )
            resp = await todo.run(self.total_content)
            msg = Message(content=resp, role=self.profile, cause_by=type(todo))
            return msg
        else:
            logger.info(f"else {self._setting}: ready to {self._rc.todo}")
            resp = await todo.run()
            self.total_content += str(resp)
            self.total_content = self.total_content[:8192]
            msg = Message(content="Done", role=self.profile, cause_by=type(todo))
            return msg


async def main():
    # action = HuggingfacePaperMainpageCrawl()
    # result = await action.run()
    # logger.info(result)

    # action2 = HuggingfacePaperContentCrawl(paper_id="2401.10020")
    # result2 = await action2.run()
    # logger.info(result2)

    role = HuggingfacePaperWatcher()
    result3 = await role.run(Message(content="start"))
    logger.info(result3)
    await discord_callback(result3)


if __name__ == "__main__":
    asyncio.run(main())
