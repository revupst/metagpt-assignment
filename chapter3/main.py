import re
import asyncio

from metagpt.actions import Action
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.logs import logger


class SimplePrint(Action):
    _count = 0

    def __init__(self, name="SimplePrint", context=None, llm=None):
        super().__init__(name=name, context=context, llm=llm)

    async def run(self, content: str) -> str:
        logger.info(f"SimplePrint({SimplePrint._count}): {content}")
        SimplePrint._count += 1
        return content


class SimplePrinter(Role):
    def __init__(
        self,
        name: str = "SimplePrinter",
        profile: str = "Simple Printer",
        goal: str = "Generate and print new random messages",
        constraints: str = "Result must be Chinese",
    ):
        super().__init__(name=name, profile=profile, goal=goal, constraints=constraints)
        self._init_actions([SimplePrint, SimplePrint, SimplePrint])
        self._rc.todo = None
        self._has_generated = False

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
            if self._has_generated == False:
                logger.info("generate new")
                await self._generate()
                self._has_generated = True
                self._rc.todo = None
                self._set_state(0)
            else:
                self._rc.todo = None

    async def _generate(self) -> None:
        if self._has_generated == False:
            self._has_generated = True
            self._init_actions([SimplePrint, SimplePrint, SimplePrint])

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: 准备 {self._rc.todo}")
        todo = self._rc.todo
        result = await todo.run(f"state {self._rc.state}")
        msg = Message(content=result, role=self.profile)
        self._rc.memory.add(msg)
        return msg

    async def _react(self) -> Message:
        while True:
            await self._think()
            if self._rc.todo is None:
                break
            await self._act()
        return Message(content="SimplePrinter is finished", role=self.profile)


async def main():
    msg = "assignment3"
    role = SimplePrinter()
    logger.info(msg)
    result = await role.run(msg)
    logger.info(result)


if __name__ == "__main__":
    asyncio.run(main())
