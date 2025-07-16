import json
import os
import logging
from difflib import SequenceMatcher

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RulesEngine:
    """Motor de regras para correspondência de intenções"""
    
    def __init__(self, rules_file='rules_store.json'):
        """
        Inicializa o motor de regras com tratamento de caminhos
        :param rules_file: Nome do arquivo de regras (relativo ao diretório do módulo)
        """
        # Obtém o diretório do arquivo atual
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Constrói o caminho completo para o arquivo de regras
        self.rules_path = os.path.join(current_dir, rules_file)
        
        # Carrega as regras
        self.rules = self._load_rules()
        
        logger.info(f"Motor de regras inicializado com {len(self.rules)} regras")

    def _load_rules(self):
        """Carrega regras do arquivo JSON com tratamento de erro"""
        try:
            with open(self.rules_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Arquivo de regras não encontrado: {self.rules_path}")
            return []
        except json.JSONDecodeError:
            logger.error(f"Erro ao decodificar o arquivo de regras: {self.rules_path}")
            return []
    
    def match_rule(self, parsed_request):
        """
        Encontra a regra que melhor corresponde à solicitação
        :param parsed_request: solicitação parseada contendo 'intent'
        :return: regra correspondente ou None
        """
        if not self.rules:
            return None
            
        best_match = None
        highest_score = 0
        
        for rule in self.rules:
            score = self._calculate_similarity(
                parsed_request['intent'], 
                rule['intent']
            )
            
            if score > highest_score and score > 0.7:
                highest_score = score
                best_match = rule
                
        return best_match
    
    def _calculate_similarity(self, a, b):
        """
        Calcula similaridade entre strings
        :param a: primeira string
        :param b: segunda string
        :return: pontuação de similaridade (0.0 a 1.0)
        """
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()