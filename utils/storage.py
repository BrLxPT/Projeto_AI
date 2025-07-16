import json
import os

class Storage:
    """Gerencia armazenamento persistente de dados"""
    
    def __init__(self, storage_dir="data"):
        """
        Inicializa sistema de armazenamento
        :param storage_dir: Diretório para armazenar arquivos
        """
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
    
    def save(self, filename, data):
        """
        Salva dados em arquivo JSON
        :param filename: Nome do arquivo (sem extensão)
        :param data: Dados a serem salvos
        """
        path = os.path.join(self.storage_dir, f"{filename}.json")
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load(self, filename):
        """
        Carrega dados de arquivo JSON
        :param filename: Nome do arquivo (sem extensão)
        :return: Dados carregados ou None se erro
        """
        path = os.path.join(self.storage_dir, f"{filename}.json")
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None