import asyncio

from metagpt.actions import Action
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.logs import logger
from metagpt.utils.common import OutputParser


class SimplePrint(Action):
    _count = 0

    def __init__(self, name="SimplePrint", context=None, llm=None):
        super().__init__(name=name, context=context, llm=llm)

    async def run(self, content: str, need_generate: bool) -> list:
        logger.info(f"SimplePrint({SimplePrint._count}): {content}")
        SimplePrint._count += 1
        if need_generate:
            return await self._generate_actions()
        return []

    async def _generate_actions(self) -> list:
        PROMPT = """
        Please generate a new action list for MetaGPT, strictly following the following requirements:
        - The result must be a json object, and the result list is the value ,the key is 'actions'.
        - Each action is named SimplePrint.
        - The length of the list is 3.
        - Don't need to write python code, just return the json object.
        Example:
        {'actions': ['SimplePrint', 'SimplePrint']}
        """
        resp = await self._aask(prompt=PROMPT)
        ret = OutputParser.extract_struct(resp, "dict")
        actions_strs = ret["actions"]
        logger.info(actions_strs)
        actions = [globals()[s] for s in actions_strs]
        logger.info(actions)
        return actions


class SimplePrinter(Role):
    def __init__(
        self,
        name: str = "SimplePrinter",
        profile: str = "Simple Printer",
    ):
        super().__init__(name=name, profile=profile)
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
            self._rc.todo = None

    async def _act(self):
        logger.info(f"{self._setting}: 准备 {self._rc.todo}")
        todo = self._rc.todo

        logger.info(f"state len: {self._rc.state}:{len(self._states)}")

        if self._rc.state + 1 == len(self._states) and self._has_generated == False:
            self._has_generated = True
            actions = await todo.run(f"state {self._rc.state}", need_generate=True)
            self._init_actions(actions)
            self._rc.todo = None
        else:
            result = await todo.run(f"state {self._rc.state}", need_generate=False)

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
