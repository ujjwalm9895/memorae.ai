from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.start()

def send_notification(user_id, text):
    print(f"⏰ MEMORAE REMINDER for {user_id}: {text}")

def schedule_reminder(reminder):
    scheduler.add_job(
        send_notification,
        "date",
        run_date=reminder.remind_at,
        args=[reminder.user_id, reminder.text],
        id=str(reminder.id)
    )
