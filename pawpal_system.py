"""PawPal+ system skeleton.

Class structure generated from the UML class diagram (see uml_draft.md):
    Pet, Scheduler, Task, Owner
"""

from dataclasses import dataclass, field


@dataclass
class Pet:
    name: str
    type: str
    weight: float


@dataclass
class Task:
    # collection of tasks this object manages
    tasks: list = field(default_factory=list)

    def view_tasks(self):
        pass

    def add_tasks(self, task):
        pass

    def remove_tasks(self, task):
        pass

    def sort_tasks(self):
        pass


class Scheduler:
    def walk(self):
        pass

    def meds(self):
        pass

    def feeding(self):
        pass

    def grooming(self):
        pass

    def enrichment(self):
        pass


class Owner:
    def __init__(self, availability=None):
        self.availability = availability
        self.scheduler = Scheduler()   # association: Owner "has a" Scheduler
        self.task = Task()             # association: Owner "has a" Task
        self.pets = []                 # association: Owner "owns" many Pets

    def add_pet(self, pet):
        pass

    def remove_pet(self, pet):
        pass
