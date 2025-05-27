import abc
import ast
from abc import abstractmethod
from typing import Self
from dataclasses import dataclass

from src.explotest.generated_test import GeneratedTest


class TestGenerator(abc.ABC):
    @abstractmethod
    def __init__(self, function_name: str):
        ...

    @abstractmethod
    def generate(self) -> GeneratedTest:
        ...









