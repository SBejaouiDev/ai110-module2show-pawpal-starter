from datetime import date, timedelta

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

    assert owner.view_schedule() == [meds, walk]


def test_tasks_can_be_sorted_chronologically():
    owner = Owner()
    pet = Pet("Mochi", "dog", 22.5)
    owner.add_pet(pet)

    later = owner.scheduler.walk(pet, "18:00", 3, duration_minutes=30)
    earlier = owner.scheduler.feeding(pet, "07:30", 1, duration_minutes=10)
    owner.add_task(later)
    owner.add_task(earlier)

    assert owner.task.sort_tasks_by_time() == [earlier, later]


def test_tasks_can_be_filtered_by_pet_and_status():
    owner = Owner()
    dog = Pet("Mochi", "dog", 22.5)
    cat = Pet("Nori", "cat", 11.0)
    owner.add_pet(dog)
    owner.add_pet(cat)

    dog_task = owner.scheduler.walk(dog, "08:00", 3, duration_minutes=30)
    complete_cat_task = owner.scheduler.feeding(cat, "09:00", 2, duration_minutes=10)
    complete_cat_task.mark_complete()
    owner.add_task(dog_task)
    owner.add_task(complete_cat_task)

    assert owner.scheduler.get_filtered_tasks(owner, pet=dog) == [dog_task]
    assert owner.scheduler.get_filtered_tasks(owner, status="complete") == [
        complete_cat_task
    ]


def test_recurring_tasks_expand_into_future_dates():
    owner = Owner()
    pet = Pet("Mochi", "dog", 22.5)
    owner.add_pet(pet)
    tomorrow = date.today() + timedelta(days=1)
    day_after_tomorrow = date.today() + timedelta(days=2)

    task = owner.scheduler.feeding(
        pet,
        "08:00",
        2,
        duration_minutes=10,
        date="2026-07-12",
        recurrence="daily",
        repeat_count=2,
    )

    tasks = owner.add_task_series(task)

    assert [scheduled_task.date for scheduled_task in tasks] == [
        "2026-07-12",
        tomorrow.isoformat(),
        day_after_tomorrow.isoformat(),
    ]
    assert len(owner.task.view_tasks()) == 3


def test_conflict_detection_finds_overlapping_pending_tasks():
    owner = Owner()
    pet = Pet("Mochi", "dog", 22.5)
    owner.add_pet(pet)

    walk = owner.scheduler.walk(
        pet, "08:00", 3, duration_minutes=30, date="2026-07-12"
    )
    meds = owner.scheduler.meds(
        pet, "08:15", 3, duration_minutes=5, date="2026-07-12"
    )
    later_feeding = owner.scheduler.feeding(
        pet, "09:00", 1, duration_minutes=10, date="2026-07-12"
    )
    owner.add_task(walk)
    owner.add_task(meds)
    owner.add_task(later_feeding)

    assert owner.scheduler.find_conflicts(owner.task.view_tasks()) == [(walk, meds)]


def test_schedule_details_reports_tasks_skipped_by_availability():
    owner = Owner(availability=10)
    pet = Pet("Mochi", "dog", 22.5)
    owner.add_pet(pet)

    walk = owner.scheduler.walk(pet, "08:00", 3, duration_minutes=30)
    meds = owner.scheduler.meds(pet, "09:00", 1, duration_minutes=5)
    owner.add_task(walk)
    owner.add_task(meds)

    plan, skipped = owner.view_schedule_details()

    assert plan == [meds]
    assert skipped == [(walk, "Not enough available care time.")]
