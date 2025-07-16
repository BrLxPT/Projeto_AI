import requests  # Para requisições HTTP

class WeatherAPI:
    """Classe para integração com serviços de previsão do tempo"""
    
    def __init__(self, api_key=None):
        """
        Inicializa a API com chave de autenticação
        :param api_key: Chave da API (opcional)
        """
        self.base_url = "https://api.weatherapi.com/v1"
        self.api_key = api_key
    
    def get_weather(self, location):
        """
        Obtém dados meteorológicos para uma localização
        :param location: Cidade/coordenadas para consulta
        :return: Dados meteorológicos em formato JSON
        """
        try:
            # Monta URL da requisição
            endpoint = f"{self.base_url}/current.json?key={self.api_key}&q={location}"
            
            # Faz requisição GET
            response = requests.get(endpoint)
            response.raise_for_status()  # Verifica erros
            
            return response.json()  # Retorna dados em JSON
        except Exception as e:
            return {"error": str(e)}