import asyncio
import config

import aiofiles
from loguru import logger as lg

import lolzteam


async def load_known_posts(file_path: str):
    async with aiofiles.open(file_path, 'r') as file:
        known_posts = await file.readlines()
    return known_posts


class ReportProcessor:
    def __init__(self, api_key: str):
        self.lz = lolzteam.Lolzteam(api_key)
        self.complaint_queue = asyncio.Queue()

    async def add_to_queue(self, value):
        await self.complaint_queue.put(value)

    async def process_report(self):
        while True:
            report = await self.complaint_queue.get()
            lg.info("Кидаю жалобу: ", report)
            await self.lz.report_post(report, 'Флуд | Оффтоп')
            await asyncio.sleep(5)

    async def fetch_threads_and_posts(self, limit: int, forum_ids: list, known_posts: list):
        for forum_id in forum_ids:
            thread_list = await self.lz.get_threads_list(limit=limit, forum_id=forum_id)
            for thread in thread_list["threads"]:
                thread_posts = await self.lz.get_thread_posts(limit=limit, thread_id=thread["thread_id"])

                for post in thread_posts:
                    if post["post_body_plain_text"] in known_posts:
                        await self.add_to_queue(post["post_id"])

    async def start(self, file_path: str, limit: int, forum_ids: list):
        known_posts = await load_known_posts(file_path)
        await self.fetch_threads_and_posts(limit, forum_ids, known_posts)
        await self.process_report()


if __name__ == "__main__":
    processor = ReportProcessor(config.api_key)
    asyncio.run(processor.start('base.txt', 15, config.ls))
