class OrderStatuses:
    """Статусы заказов"""
    PENDING = 'pending'                # В ожидании
    IN_PROGRESS = 'in_progress'        # В пути
    DELIVERED = 'delivered'            # Доставлено
    CANCELLED = 'cancelled'            # Отменено

    CHOICES = [
        PENDING,
        IN_PROGRESS,
        DELIVERED,
        CANCELLED,
    ]

    LABELS = {
        PENDING: {'ru': 'В ожидании', 'tm': 'Garaşylýar'},
        IN_PROGRESS: {'ru': 'В пути', 'tm': 'Ýolda'},
        DELIVERED: {'ru': 'Доставлено', 'tm': 'Eltildi'},
        CANCELLED: {'ru': 'Отменено', 'tm': 'Ýatyryldy'},
    }
