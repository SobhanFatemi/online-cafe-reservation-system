from datetime import datetime, timedelta
from seating.models import TimeSlot, CafeTable, WorkingHour, DayofWeek
from dashboard.models import CafeSetting


def generate_time_ranges(start_time, end_time):
    slots = []
    current = datetime.combine(datetime.today(), start_time)
    end = datetime.combine(datetime.today(), end_time)
    settings = CafeSetting.load()


    while current + timedelta(hours=settings.slot_duration_minutes/60) <= end:
        

        slot_end = current + timedelta(
            minutes=settings.slot_duration_minutes
        )

        slots.append((current.time(), slot_end.time()))
        current = slot_end

    return slots

def ensure_slots_exist_for_date(selected_date):
    if TimeSlot.objects.filter(date=selected_date).exists():
        return

    weekday_number = selected_date.weekday()

    weekday_map = {
        0: DayofWeek.MONDAY,
        1: DayofWeek.TUESDAY,
        2: DayofWeek.WEDNESDAY,
        3: DayofWeek.THURSDAY,
        4: DayofWeek.FRIDAY,
        5: DayofWeek.SATURDAY,
        6: DayofWeek.SUNDAY,
    }

    weekday_code = weekday_map[weekday_number]
    try:
        working_hours = WorkingHour.objects.get(day_of_week=weekday_code)
    except WorkingHour.DoesNotExist:
        return

    ranges = generate_time_ranges(
        working_hours.start_time,
        working_hours.end_time
    )

    for table in CafeTable.objects.filter(is_active=True):
        for start, end in ranges:
            TimeSlot.objects.create(
                date=selected_date,
                table=table,
                start_time=start,
                end_time=end
            )