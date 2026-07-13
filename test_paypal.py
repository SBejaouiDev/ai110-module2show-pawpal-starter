from pawpal_system import Pet, ScheduledTask


def test_mark_complete_changes_task_status():
    pet = Pet("Mochi", "dog", 22.5)
    task = ScheduledTask("feeding", pet, "08:00", 3)

    task.mark_complete()

    assert task.status == "complete"


def test_adding_task_to_pet_increases_task_count():
    pet = Pet("Luna", "cat", 10.0)
    task = ScheduledTask("meds", pet, "09:15", 2)
    starting_count = len(pet.tasks)

    pet.add_task(task)

    assert len(pet.tasks) == starting_count + 1
