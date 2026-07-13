from datetime import date, timedelta

import pytest

import pawpal_system
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


def test_chronological_sort_uses_date_time_pet_and_task_type_tiebreakers():
    owner = Owner()
    zelda = Pet("Zelda", "dog", 18.0)
    bella = Pet("Bella", "cat", 9.0)
    owner.add_pet(zelda)
    owner.add_pet(bella)

    later_date = owner.scheduler.walk(
        bella, "07:30", 3, duration_minutes=20, date="2026-07-13"
    )
    later_time = owner.scheduler.feeding(
        bella, "09:00", 3, duration_minutes=10, date="2026-07-12"
    )
    same_time_later_pet = owner.scheduler.walk(
        zelda, "08:00", 3, duration_minutes=20, date="2026-07-12"
    )
    same_time_earlier_pet_later_type = owner.scheduler.meds(
        bella, "08:00", 3, duration_minutes=5, date="2026-07-12"
    )
    same_time_earlier_pet_earlier_type = owner.scheduler.feeding(
        bella, "08:00", 3, duration_minutes=10, date="2026-07-12"
    )

    for task in [
        later_date,
        later_time,
        same_time_later_pet,
        same_time_earlier_pet_later_type,
        same_time_earlier_pet_earlier_type,
    ]:
        owner.add_task(task)

    assert owner.task.sort_tasks_by_time() == [
        same_time_earlier_pet_earlier_type,
        same_time_earlier_pet_later_type,
        same_time_later_pet,
        later_time,
        later_date,
    ]


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


def test_weekly_recurring_tasks_expand_from_today_and_reset_recurrence(monkeypatch):
    class FixedDate(date):
        @classmethod
        def today(cls):
            return cls(2026, 7, 12)

    monkeypatch.setattr(pawpal_system, "date_cls", FixedDate)

    owner = Owner()
    pet = Pet("Mochi", "dog", 22.5)
    owner.add_pet(pet)
    task = owner.scheduler.meds(
        pet,
        "08:00",
        3,
        duration_minutes=5,
        reason="Heartworm prevention",
        date="2026-07-12",
        recurrence="weekly",
        repeat_count=2,
    )

    tasks = owner.add_task_series(task)

    assert [scheduled_task.date for scheduled_task in tasks] == [
        "2026-07-12",
        "2026-07-19",
        "2026-07-26",
    ]
    assert [scheduled_task.recurrence for scheduled_task in tasks] == [
        "weekly",
        "none",
        "none",
    ]
    assert [scheduled_task.repeat_count for scheduled_task in tasks] == [2, 0, 0]
    assert all(scheduled_task.task_type == "meds" for scheduled_task in tasks)
    assert all(scheduled_task.pet == pet for scheduled_task in tasks)
    assert all(scheduled_task.duration_minutes == 5 for scheduled_task in tasks)


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


def test_conflict_detection_ignores_non_conflicts_and_non_pending_tasks():
    owner = Owner()
    pet = Pet("Mochi", "dog", 22.5)
    owner.add_pet(pet)

    walk = owner.scheduler.walk(
        pet, "08:00", 3, duration_minutes=30, date="2026-07-12"
    )
    adjacent_feeding = owner.scheduler.feeding(
        pet, "08:30", 2, duration_minutes=10, date="2026-07-12"
    )
    overlapping_meds = owner.scheduler.meds(
        pet, "08:15", 3, duration_minutes=5, date="2026-07-12"
    )
    completed_overlap = owner.scheduler.grooming(
        pet, "08:10", 2, duration_minutes=20, date="2026-07-12"
    )
    completed_overlap.mark_complete()
    different_day_overlap = owner.scheduler.enrichment(
        pet, "08:10", 2, duration_minutes=20, date="2026-07-13"
    )
    zero_minute_same_start = owner.scheduler.feeding(
        pet, "09:00", 1, duration_minutes=0, date="2026-07-12"
    )
    zero_minute_collision = owner.scheduler.meds(
        pet, "09:00", 1, duration_minutes=0, date="2026-07-12"
    )

    tasks = [
        walk,
        adjacent_feeding,
        overlapping_meds,
        completed_overlap,
        different_day_overlap,
        zero_minute_same_start,
        zero_minute_collision,
    ]

    assert owner.scheduler.find_conflicts(tasks) == [
        (walk, overlapping_meds),
        (zero_minute_same_start, zero_minute_collision),
    ]


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
