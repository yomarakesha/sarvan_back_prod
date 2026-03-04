class DeliveryTimes:
    URGENT = 'urgent'                  # Срочно
    DURING_DAY = 'during_day'          # В течении дня
    SPECIFIC_TIME = 'specific_time'    # В конкретное время

    CHOICES = [
        URGENT,
        DURING_DAY,
        SPECIFIC_TIME,
    ]

    LABELS = {
        URGENT: {'ru': 'Срочно', 'tm': 'Çalt'},
        DURING_DAY: {'ru': 'В течении дня', 'tm': 'Gün içinde'},
        SPECIFIC_TIME: {'ru': 'В конкретное время', 'tm': 'Belli bir wagtda'},
    }
