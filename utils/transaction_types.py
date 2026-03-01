class TransactionTypes:
    INVENTORY_IN = 'incoming'      # Приход с завода
    COURIER_ISSUE = 'courier_issue'    # Выдача курьеру (Утро)
    COURIER_RETURN = 'courier_return'  # Прием от курьера (Вечер)
    COURIER_TRANSFER = 'courier_transfer' # Между курьерами
    WRITE_OFF = 'write_off'            # Списание (утиль/брак)

    # словарь для мультиязычных названий, ключи — коды операций
    LABELS = {
        INVENTORY_IN: {'ru': 'Приход с контрагента', 'tm': 'Kontragentdan gelýän'},
        COURIER_ISSUE: {'ru': 'Выдача курьеру', 'tm': 'Kurýere bermek'},
        COURIER_RETURN: {'ru': 'Прием от курьера', 'tm': 'Kurýerden kabul etmek'},
        COURIER_TRANSFER: {'ru': 'Перевод между курьерами', 'tm': 'Başga kurýere geçirmek'},
        WRITE_OFF: {'ru': 'Списание', 'tm': 'Hasapdan çykarmak'},
    }