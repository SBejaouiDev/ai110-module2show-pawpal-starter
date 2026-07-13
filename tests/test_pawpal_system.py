import pytest

from pawpal_system import Owner, Pet, ScheduledTask


def test_scheduler_creates_task_for_pet():
    owner = Owner()
    pet = Pet("Mochi", "dog", 22.5)
    owner.add_pet(pet)

    task = owner.scheduler.walk(pet, "08:00", 3, duration_minutes=30)
    owner.add_task(task)

    assert task in owner.task.view_tasks()
    assert task.task_type == "walk"
    assert task.pet == pet


def test_owner_rejects_task_for_pet_it_does_not_own():
    owner = Owner()
    pet = Pet("Mochi", "dog", 22.5)
    task = owner.scheduler.feeding(pet, "09:00", 2, duration_minutes=10)

    with pytest.raises(ValueError):
        owner.add_task(task)


def test_scheduler_gets_only_tasks_for_owner_pets():
    owner = Owner()
    owned_pet = Pet("Mochi", "dog", 22.5)
    other_pet = Pet("Nori", "cat", 11.0)
    owner.add_pet(owned_pet)

    owned_task = owner.scheduler.walk(owned_pet, "08:00", 3, duration_minutes=30)
    other_task = ScheduledTask("feeding", other_pet, "09:00", 2, duration_minutes=10)
    owner.task.add_tasks(owned_task)
    owner.task.add_tasks(other_task)

    assert owner.scheduler.get_tasks_for_owner_pets(owner) == [owned_task]


def test_daily_plan_sorts_by_priority_then_time():
    owner = Owner()
    pet = Pet("Mochi", "dog", 22.5)
    owner.add_pet(pet)

    low_priority = owner.scheduler.feeding(pet, "08:00", 1, duration_minutes=10)
    later_high_priority = owner.scheduler.walk(pet, "10:00", 3, duration_minutes=30)
    earlier_high_priority = owner.scheduler.meds(pet, "09:00", 3, duration_minutes=5)
    owner.add_task(low_priority)
    owner.add_task(later_high_priority)
    owner.add_task(earlier_high_priority)

    assert owner.view_schedule() == [
        earlier_high_priority,
        later_high_priority,
        low_priority,
    ]


def test_daily_plan_respects_available_minutes():
    owner = Owner(availability=35)
    pet = Pet("Mochi", "dog", 22.5)
    owner.add_pet(pet)

    walk = owner.scheduler.walk(pet, "08:00", 3, duration_minutes=30)
    grooming = owner.scheduler.grooming(pet, "09:00", 2, duration_minutes=20)
    meds = owner.scheduler.meds(pet, "10:00", 1, duration_minutes=5)
    owner.add_task(walk)
    owner.add_task(grooming)
    owner.add_task(meds)

    assert owner.view_schedule() == [walk, meds]
