import requests

class CryptoAPI:
    """Classe para obtenção de cotações de criptomoedas"""
    
    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3"
    
    def get_price(self, coin_id):
        """
        Obtém preço atual de uma criptomoeda
        :param coin_id: ID da moeda (ex: 'bitcoin')
        :return: Dicionário com informações de preço
        """
        try:
            endpoint = f"{self.base_url}/simple/price?ids={coin_id}&vs_currencies=usd"
            response = requests.get(endpoint)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": f"Falha ao obter preço: {str(e)}"}