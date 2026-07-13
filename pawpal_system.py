"""Core PawPal+ domain classes.

Class structure generated from the UML class diagram:
    Pet, ScheduledTask, Scheduler, Task, Owner
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date as date_cls
from datetime import datetime, timedelta


VALID_STATUSES = {"pending", "complete", "skipped"}
VALID_RECURRENCES = {"none", "daily", "weekly"}
CARE_CRITICAL_TASK_TYPES = {"meds"}


def _today_iso():
    return date_cls.today().isoformat()


def _time_sort_key(time: str):
    try:
        return datetime.strptime(time, "%H:%M").time()
    except ValueError:
        return datetime.max.time()


def _parse_date(task_date: str):
    return date_cls.fromisoformat(task_date)


def _date_sort_key(task_date: str):
    try:
        return _parse_date(task_date)
    except ValueError:
        return date_cls.max


def _time_to_minutes(time: str):
    parsed_time = datetime.strptime(time, "%H:%M").time()
    return parsed_time.hour * 60 + parsed_time.minute


def _effective_priority(task: ScheduledTask):
    """Return the priority used by scheduling algorithms.

    Medication tasks receive a large priority boost so constrained schedules try
    to keep them before lower-risk care tasks.
    """
    if task.task_type in CARE_CRITICAL_TASK_TYPES:
        return task.priority + 100
    return task.priority


def _priority_sort_key(task: ScheduledTask):
    """Return a stable key for priority-based schedule ordering.

    Higher effective priority comes first, then earlier date/time, then pet name
    and task type so equal-priority tasks stay predictable in tables and tests.
    """
    return (
        -_effective_priority(task),
        _date_sort_key(task.date),
        _time_sort_key(task.time),
        task.pet.name.lower(),
        task.task_type,
    )


def _chronological_sort_key(task: ScheduledTask):
    """Return a stable key for chronological task ordering.

    Tasks are ordered by date, time, pet name, and task type without considering
    priority.
    """
    return (
        _date_sort_key(task.date),
        _time_sort_key(task.time),
        task.pet.name.lower(),
        task.task_type,
    )


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
    date: str = field(default_factory=_today_iso)
    recurrence: str = "none"
    repeat_count: int = 0

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
        try:
            datetime.strptime(self.time, "%H:%M")
        except ValueError as error:
            raise ValueError("Task time must use HH:MM format.") from error
        try:
            _parse_date(self.date)
        except ValueError as error:
            raise ValueError("Task date must use YYYY-MM-DD format.") from error
        if self.status not in VALID_STATUSES:
            raise ValueError(f"Task status must be one of {sorted(VALID_STATUSES)}.")
        if self.recurrence not in VALID_RECURRENCES:
            raise ValueError(
                f"Task recurrence must be one of {sorted(VALID_RECURRENCES)}."
            )
        if self.repeat_count < 0:
            raise ValueError("Task repeat count cannot be negative.")

    def mark_complete(self):
        """Mark this scheduled task as complete."""
        self.status = "complete"
        return self

    def mark_skipped(self):
        """Mark this scheduled task as skipped."""
        self.status = "skipped"
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
        self.tasks.sort(key=_priority_sort_key)
        return self.view_tasks()

    def sort_tasks_by_time(self):
        """Sort managed tasks chronologically in place.

        Ordering ignores priority and uses date, time, pet name, and task type
        so repeated calls produce consistent output.
        """
        self.tasks.sort(key=_chronological_sort_key)
        return self.view_tasks()

    def tasks_for_pet(self, pet: Pet):
        """Return all scheduled tasks assigned to one pet."""
        return [task for task in self.tasks if task.pet == pet]

    def tasks_for_pets(self, pets: list[Pet]):
        """Return all scheduled tasks assigned to the given pets."""
        return [task for task in self.tasks if task.pet in pets]

    def filter_tasks(
        self,
        pet: Pet | None = None,
        status: str | None = None,
        sort_by: str | None = None,
    ):
        """Return tasks matching the requested pet and/or status.

        The original collection is not mutated. When ``sort_by`` is ``"time"``
        or ``"priority"``, the returned copy is ordered with the matching
        scheduling sort key.
        """
        if status is not None and status not in VALID_STATUSES:
            raise ValueError(f"Task status must be one of {sorted(VALID_STATUSES)}.")

        filtered_tasks = self.view_tasks()
        if pet is not None:
            filtered_tasks = [task for task in filtered_tasks if task.pet == pet]
        if status is not None:
            filtered_tasks = [task for task in filtered_tasks if task.status == status]

        if sort_by == "time":
            filtered_tasks.sort(key=_chronological_sort_key)
        elif sort_by == "priority":
            filtered_tasks.sort(key=_priority_sort_key)
        elif sort_by is not None:
            raise ValueError("Sort option must be 'time', 'priority', or None.")

        return filtered_tasks


class Scheduler:
    def _create_task(
        self,
        task_type: str,
        pet: Pet,
        time: str,
        priority: int,
        duration_minutes: int = 0,
        reason: str = "",
        date: str | None = None,
        recurrence: str = "none",
        repeat_count: int = 0,
    ):
        """Create a scheduled task with the given task type."""
        return ScheduledTask(
            task_type,
            pet,
            time,
            priority,
            duration_minutes,
            reason,
            date=date or _today_iso(),
            recurrence=recurrence,
            repeat_count=repeat_count,
        )

    def walk(
        self,
        pet: Pet,
        time: str,
        priority: int,
        duration_minutes: int = 0,
        reason: str = "",
        date: str | None = None,
        recurrence: str = "none",
        repeat_count: int = 0,
    ):
        """Create a walking task for a pet."""
        return self._create_task(
            "walk", pet, time, priority, duration_minutes, reason, date, recurrence, repeat_count
        )

    def meds(
        self,
        pet: Pet,
        time: str,
        priority: int,
        duration_minutes: int = 0,
        reason: str = "",
        date: str | None = None,
        recurrence: str = "none",
        repeat_count: int = 0,
    ):
        """Create a medication task for a pet."""
        return self._create_task(
            "meds", pet, time, priority, duration_minutes, reason, date, recurrence, repeat_count
        )

    def feeding(
        self,
        pet: Pet,
        time: str,
        priority: int,
        duration_minutes: int = 0,
        reason: str = "",
        date: str | None = None,
        recurrence: str = "none",
        repeat_count: int = 0,
    ):
        """Create a feeding task for a pet."""
        return self._create_task(
            "feeding",
            pet,
            time,
            priority,
            duration_minutes,
            reason,
            date,
            recurrence,
            repeat_count,
        )

    def grooming(
        self,
        pet: Pet,
        time: str,
        priority: int,
        duration_minutes: int = 0,
        reason: str = "",
        date: str | None = None,
        recurrence: str = "none",
        repeat_count: int = 0,
    ):
        """Create a grooming task for a pet."""
        return self._create_task(
            "grooming",
            pet,
            time,
            priority,
            duration_minutes,
            reason,
            date,
            recurrence,
            repeat_count,
        )

    def enrichment(
        self,
        pet: Pet,
        time: str,
        priority: int,
        duration_minutes: int = 0,
        reason: str = "",
        date: str | None = None,
        recurrence: str = "none",
        repeat_count: int = 0,
    ):
        """Create an enrichment task for a pet."""
        return self._create_task(
            "enrichment",
            pet,
            time,
            priority,
            duration_minutes,
            reason,
            date,
            recurrence,
            repeat_count,
        )

    def get_all_tasks(self, owner: Owner):
        """Return every task stored by an owner."""
        return owner.task.view_tasks()

    def get_tasks_for_owner_pets(self, owner: Owner):
        """Return tasks assigned only to pets owned by the owner."""
        return owner.task.tasks_for_pets(owner.pets)

    def get_filtered_tasks(
        self,
        owner: Owner,
        pet: Pet | None = None,
        status: str | None = None,
        sort_by: str | None = None,
    ):
        """Return an owner's tasks after pet/status filtering and optional sorting.

        Only tasks for pets currently owned by ``owner`` are considered, so
        orphaned or unrelated tasks cannot appear in the filtered result.
        """
        tasks = Task(self.get_tasks_for_owner_pets(owner))
        return tasks.filter_tasks(pet=pet, status=status, sort_by=sort_by)

    def create_recurring_tasks(self, task: ScheduledTask):
        """Expand one recurring task into dated task instances.

        The original task is returned first. Additional daily or weekly
        occurrences are generated from today's date with ``timedelta``:
        daily tasks use today + 1 day for the next due date, and weekly tasks
        use today + 7 days.
        """
        tasks = [task]
        if task.recurrence == "none" or task.repeat_count == 0:
            return tasks

        interval = 1 if task.recurrence == "daily" else 7
        start_date = date_cls.today()
        for index in range(1, task.repeat_count + 1):
            task_date = start_date + timedelta(days=interval * index)
            tasks.append(
                ScheduledTask(
                    task.task_type,
                    task.pet,
                    task.time,
                    task.priority,
                    duration_minutes=task.duration_minutes,
                    reason=task.reason,
                    status=task.status,
                    date=task_date.isoformat(),
                    recurrence="none",
                    repeat_count=0,
                )
            )
        return tasks

    def find_conflicts(self, tasks: list[ScheduledTask]):
        """Return pairs of pending tasks whose scheduled time ranges overlap.

        Completed or skipped tasks are ignored. A zero-minute task is treated as
        a one-minute block so exact-time collisions are still detected.
        """
        conflicts = []
        pending_tasks = [task for task in tasks if task.status == "pending"]
        pending_tasks.sort(key=_chronological_sort_key)

        for index, first_task in enumerate(pending_tasks):
            first_start = _time_to_minutes(first_task.time)
            first_end = first_start + max(first_task.duration_minutes, 1)

            for second_task in pending_tasks[index + 1 :]:
                if first_task.date != second_task.date:
                    continue

                second_start = _time_to_minutes(second_task.time)
                second_end = second_start + max(second_task.duration_minutes, 1)
                if first_start < second_end and second_start < first_end:
                    conflicts.append((first_task, second_task))

        return conflicts

    def conflicts_for_task(
        self,
        task: ScheduledTask,
        existing_tasks: list[ScheduledTask],
    ):
        """Return existing pending tasks that conflict with a candidate task.

        This is used before adding a task in the UI. It compares date plus
        start/end minutes and returns conflicts in chronological order.
        """
        if task.status != "pending":
            return []

        task_start = _time_to_minutes(task.time)
        task_end = task_start + max(task.duration_minutes, 1)
        conflicts = []

        for existing_task in existing_tasks:
            if existing_task is task or existing_task.status != "pending":
                continue
            if existing_task.date != task.date:
                continue

            existing_start = _time_to_minutes(existing_task.time)
            existing_end = existing_start + max(existing_task.duration_minutes, 1)
            if task_start < existing_end and existing_start < task_end:
                conflicts.append(existing_task)

        return sorted(conflicts, key=_chronological_sort_key)

    def build_daily_plan(self, owner: Owner, available_minutes: int | None = None):
        """Build a priority-ordered plan of pending tasks for an owner.

        Tasks for pets not owned by ``owner`` are excluded. If
        ``available_minutes`` is provided, tasks are greedily included until the
        time budget is full; tasks that do not fit are omitted from this compact
        result.
        """
        scheduled_tasks = [
            task for task in self.get_tasks_for_owner_pets(owner) if task.status == "pending"
        ]
        scheduled_tasks.sort(key=_priority_sort_key)

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

    def build_daily_plan_details(
        self, owner: Owner, available_minutes: int | None = None
    ):
        """Build a daily plan plus tasks skipped by availability limits.

        The plan uses the same priority ordering as ``build_daily_plan``. The
        returned tuple is ``(planned_tasks, skipped_tasks)``, where skipped
        entries include a short reason string for display.
        """
        scheduled_tasks = [
            task for task in self.get_tasks_for_owner_pets(owner) if task.status == "pending"
        ]
        scheduled_tasks.sort(key=_priority_sort_key)

        if available_minutes is None:
            return scheduled_tasks, []

        if available_minutes < 0:
            raise ValueError("Available minutes cannot be negative.")

        plan = []
        skipped = []
        used_minutes = 0
        for task in scheduled_tasks:
            if used_minutes + task.duration_minutes <= available_minutes:
                plan.append(task)
                used_minutes += task.duration_minutes
            else:
                skipped.append((task, "Not enough available care time."))

        return plan, skipped


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
        if task not in task.pet.tasks:
            task.pet.add_task(task)
        if task not in self.task.tasks:
            self.task.add_tasks(task)
        return task

    def add_task_series(self, task: ScheduledTask):
        """Add a task and any generated recurring occurrences."""
        tasks = self.scheduler.create_recurring_tasks(task)
        for scheduled_task in tasks:
            self.add_task(scheduled_task)
        return tasks

    def view_schedule(self):
        """Return this owner's generated care schedule."""
        return self.scheduler.build_daily_plan(self, self.availability)

    def view_schedule_details(self):
        """Return this owner's generated care schedule plus skipped tasks."""
        return self.scheduler.build_daily_plan_details(self, self.availability)
