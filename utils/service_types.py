class ServiceTypes:
    INCOMING = 'incoming'      # Забираю от клиента
    OUTCOMING = 'outcoming'    # Выдача клиенту
    TRANSFORMATION = 'transformation'  # Списание у клиента 

    # словарь для мультиязычных названий, ключи — коды операций
    LABELS = {
        INCOMING: {'ru': 'Забираем от клиента', 'tm': 'Klientden almak'},
        OUTCOMING: {'ru': 'ВВыдаем клиенту', 'tm': 'Kliente bermek'},
        TRANSFORMATION: {'ru': 'Списываем у клиента', 'tm': 'Klientden hasapdan çykarmak'},
    }