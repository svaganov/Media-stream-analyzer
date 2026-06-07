"""Input Factory - registers all input plugins"""
from typing import Dict, Type
from .base import BaseInput

class InputFactory:
    _inputs: Dict[str, Type[BaseInput]] = {}

    @classmethod
    def register(cls, name: str, input_class: Type[BaseInput]):
        cls._inputs[name] = input_class

    @classmethod
    def create(cls, name: str, **kwargs):
        if name not in cls._inputs:
            raise ValueError(f"Unknown input: {name}")
        return cls._inputs[name](**kwargs)

    @classmethod
    def list_inputs(cls):
        return list(cls._inputs.keys())

# Register inputs
from .icecast.icecast_input import IcecastInput
from .srt.srt_input import SRTInput

InputFactory.register("icecast", IcecastInput)
InputFactory.register("srt", SRTInput)
