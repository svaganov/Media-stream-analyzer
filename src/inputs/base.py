
import asyncio
from abc import ABC, abstractmethod

class BaseInput(ABC):
    async def start(self):
        pass

    async def stop(self):
        pass

    @abstractmethod
    async def get_frame(self):
        pass
