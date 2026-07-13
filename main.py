from pawpal_system import Owner, Pet


def print_schedule(owner):
    print("Today's Schedule")
    print("================")

    for task in owner.view_schedule():
        print(
            f"{task.time} - {task.pet.name}: {task.task_type.title()} "
            f"({task.duration_minutes} min, priority {task.priority})"
        )


def main():
    owner = Owner()

    mochi = Pet("Mochi", "dog", 22.5)
    luna = Pet("Luna", "cat", 10.0)

    owner.add_pet(mochi)
    owner.add_pet(luna)

    owner.add_task(owner.scheduler.feeding(mochi, "08:00", 3, duration_minutes=10))
    owner.add_task(owner.scheduler.walk(mochi, "12:30", 2, duration_minutes=30))
    owner.add_task(owner.scheduler.meds(luna, "09:15", 3, duration_minutes=5))
    owner.add_task(owner.scheduler.enrichment(luna, "17:00", 1, duration_minutes=20))

    print_schedule(owner)


if __name__ == "__main__":
    main()
