class PaymentTypes:
    CASH = 'cash'                      # Наличные
    CARD = 'card'                      # Карта
    CASH_AND_CARD = 'cash_and_card'   # Наличные и карта
    CREDIT = 'credit'                  # Кредит
    FREE = 'free'                      # Бесплатно

    CHOICES = [
        CASH,
        CARD,
        CASH_AND_CARD,
        CREDIT,
        FREE,
    ]

    LABELS = {
        CASH: {'ru': 'Наличные', 'tm': 'Nagt'},
        CARD: {'ru': 'Карта', 'tm': 'Karta'},
        CASH_AND_CARD: {'ru': 'Наличные и карта', 'tm': 'Nagt we karta'},
        CREDIT: {'ru': 'Кредит', 'tm': 'Kredit'},
        FREE: {'ru': 'Бесплатно', 'tm': 'Mugt'},
    }
