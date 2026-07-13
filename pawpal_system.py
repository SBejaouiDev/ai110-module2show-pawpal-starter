"""Core PawPal+ domain classes.

Class structure generated from the UML class diagram:
    Pet, ScheduledTask, Scheduler, Task, Owner
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


def _time_sort_key(time: str):
    try:
        return datetime.strptime(time, "%H:%M").time()
    except ValueError:
        return datetime.max.time()


@dataclass
class Pet:
    name: str
    type: str
    weight: float
    tasks: list[ScheduledTask] = field(default_factory=list, compare=False, repr=False)

    def __post_init__(self):
        """Validate pet details after creation."""
        if not self.name:
            raise ValueError("Pet name is required.")
        if not self.type:
            raise ValueError("Pet type is required.")
        if self.weight <= 0:
            raise ValueError("Pet weight must be greater than zero.")

    def add_task(self, task: ScheduledTask):
        """Add a scheduled task that belongs to this pet."""
        if not isinstance(task, ScheduledTask):
            raise TypeError("Only ScheduledTask objects can be added.")
        if task.pet != self:
            raise ValueError("Task pet must match this pet.")
        self.tasks.append(task)
        return task


@dataclass
class ScheduledTask:
    task_type: str
    pet: Pet
    time: str
    priority: int
    duration_minutes: int = 0
    reason: str = ""
    status: str = "pending"

    def __post_init__(self):
        """Validate scheduled task details after creation."""
        if not self.task_type:
            raise ValueError("Task type is required.")
        if not isinstance(self.pet, Pet):
            raise TypeError("ScheduledTask pet must be a Pet.")
        if not self.time:
            raise ValueError("Task time is required.")
        if self.priority < 1:
            raise ValueError("Task priority must be 1 or higher.")
        if self.duration_minutes < 0:
            raise ValueError("Task duration cannot be negative.")

    def mark_complete(self):
        """Mark this scheduled task as complete."""
        self.status = "complete"
        return self


@dataclass
class Task:
    # collection of tasks this object manages
    tasks: list[ScheduledTask] = field(default_factory=list)

    def view_tasks(self):
        """Return a copy of all scheduled tasks."""
        return list(self.tasks)

    def add_tasks(self, task: ScheduledTask):
        """Add a scheduled task to the collection."""
        if not isinstance(task, ScheduledTask):
            raise TypeError("Only ScheduledTask objects can be added.")
        self.tasks.append(task)
        return task

    def remove_tasks(self, task: ScheduledTask):
        """Remove a scheduled task from the collection."""
        self.tasks.remove(task)
        return task

    def sort_tasks(self):
        """Sort tasks by priority first, then scheduled time."""
        self.tasks.sort(key=lambda task: (-task.priority, _time_sort_key(task.time)))
        return self.view_tasks()

    def tasks_for_pet(self, pet: Pet):
        """Return all scheduled tasks assigned to one pet."""
        return [task for task in self.tasks if task.pet == pet]

    def tasks_for_pets(self, pets: list[Pet]):
        """Return all scheduled tasks assigned to the given pets."""
        return [task for task in self.tasks if task.pet in pets]


class Scheduler:
    def _create_task(
        self,
        task_type: str,
        pet: Pet,
        time: str,
        priority: int,
        duration_minutes: int = 0,
        reason: str = "",
    ):
        """Create a scheduled task with the given task type."""
        return ScheduledTask(task_type, pet, time, priority, duration_minutes, reason)

    def walk(
        self,
        pet: Pet,
        time: str,
        priority: int,
        duration_minutes: int = 0,
        reason: str = "",
    ):
        """Create a walking task for a pet."""
        return self._create_task("walk", pet, time, priority, duration_minutes, reason)

    def meds(
        self,
        pet: Pet,
        time: str,
        priority: int,
        duration_minutes: int = 0,
        reason: str = "",
    ):
        """Create a medication task for a pet."""
        return self._create_task("meds", pet, time, priority, duration_minutes, reason)

    def feeding(
        self,
        pet: Pet,
        time: str,
        priority: int,
        duration_minutes: int = 0,
        reason: str = "",
    ):
        """Create a feeding task for a pet."""
        return self._create_task("feeding", pet, time, priority, duration_minutes, reason)

    def grooming(
        self,
        pet: Pet,
        time: str,
        priority: int,
        duration_minutes: int = 0,
        reason: str = "",
    ):
        """Create a grooming task for a pet."""
        return self._create_task("grooming", pet, time, priority, duration_minutes, reason)

    def enrichment(
        self,
        pet: Pet,
        time: str,
        priority: int,
        duration_minutes: int = 0,
        reason: str = "",
    ):
        """Create an enrichment task for a pet."""
        return self._create_task("enrichment", pet, time, priority, duration_minutes, reason)

    def get_all_tasks(self, owner: Owner):
        """Return every task stored by an owner."""
        return owner.task.view_tasks()

    def get_tasks_for_owner_pets(self, owner: Owner):
        """Return tasks assigned only to pets owned by the owner."""
        return owner.task.tasks_for_pets(owner.pets)

    def build_daily_plan(self, owner: Owner, available_minutes: int | None = None):
        """Build a sorted daily plan within the available minutes."""
        scheduled_tasks = self.get_tasks_for_owner_pets(owner)
        scheduled_tasks.sort(key=lambda task: (-task.priority, _time_sort_key(task.time)))

        if available_minutes is None:
            return scheduled_tasks

        if available_minutes < 0:
            raise ValueError("Available minutes cannot be negative.")

        plan = []
        used_minutes = 0
        for task in scheduled_tasks:
            if used_minutes + task.duration_minutes <= available_minutes:
                plan.append(task)
                used_minutes += task.duration_minutes
        return plan


class Owner:
    def __init__(self, availability=None):
        """Create an owner with optional available care minutes."""
        if availability is not None and availability < 0:
            raise ValueError("Owner availability cannot be negative.")

        self.availability = availability
        self.scheduler = Scheduler()   # association: Owner "has a" Scheduler
        self.task = Task()             # association: Owner "has a" Task
        self.pets: list[Pet] = []      # association: Owner "owns" many Pets

    def add_pet(self, pet: Pet):
        """Add a pet to this owner's pet list."""
        if not isinstance(pet, Pet):
            raise TypeError("Only Pet objects can be added.")
        if pet not in self.pets:
            self.pets.append(pet)
        return pet

    def remove_pet(self, pet: Pet):
        """Remove a pet and its scheduled tasks from this owner."""
        self.pets.remove(pet)
        self.task.tasks = [task for task in self.task.tasks if task.pet != pet]
        return pet

    def add_task(self, task: ScheduledTask):
        """Add a task for one of this owner's pets."""
        if task.pet not in self.pets:
            raise ValueError("Task pet must belong to the owner.")
        return self.task.add_tasks(task)

    def view_schedule(self):
        """Return this owner's generated care schedule."""
        return self.scheduler.build_daily_plan(self, self.availability)
