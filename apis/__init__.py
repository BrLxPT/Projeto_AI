from .weather_api import WeatherAPI
from .crypto_api import CryptoAPI
from .calendar_api import CalendarAPI

# Versão do pacote
__version__ = '1.0.0'

# Exportações públicas
__all__ = [
    'WeatherAPI',
    'CryptoAPI',
    'CalendarAPI'
]

# Instâncias padrão para conveniência
weather_api = WeatherAPI()
crypto_api = CryptoAPI()
calendar_api = CalendarAPI()