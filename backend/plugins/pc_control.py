import platform
import subprocess
import logging
from typing import Dict, Any

# Configura o logging para este módulo
logger = logging.getLogger(__name__)

class PCControl:
    """
    Uma classe para controlar operações básicas do PC, como desligar e reiniciar.
    """
    def __init__(self):
        """
        Inicializa a classe PCControl.
        """
        pass # Nenhuma configuração inicial necessária por enquanto

    def _execute_command(self, command: list[str]) -> Dict[str, str]:
        """
        Executa um comando de sistema e captura a saída/erros.
        Utilizado internamente pelos métodos de controlo do PC.
        """
        try:
            # Executa o comando e espera que termine
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            logger.info(f"Comando executado: {' '.join(command)}")
            logger.info(f"Saída: {result.stdout.strip()}")
            return {"status": "success", "message": result.stdout.strip()}
        except subprocess.CalledProcessError as e:
            logger.error(f"Erro ao executar comando: {' '.join(command)}. Erro: {e.stderr.strip()}")
            return {"status": "error", "message": f"Erro ao executar comando: {e.stderr.strip()}"}
        except FileNotFoundError:
            logger.error(f"Comando não encontrado: {command[0]}. Verifique se está no PATH.")
            return {"status": "error", "message": f"Comando '{command[0]}' não encontrado. Verifique a instalação do sistema operacional."}
        except Exception as e:
            logger.error(f"Erro inesperado ao executar comando: {str(e)}")
            return {"status": "error", "message": f"Erro inesperado: {str(e)}"}

    def shutdown(self, params: Dict[str, Any]) -> Dict[str, str]:
        """
        Desliga o computador.
        Requer confirmação para evitar desligamentos acidentais.

        Args:
            params (Dict[str, Any]): Um dicionário que pode conter:
                - 'confirm' (bool, opcional): Se True, executa o desligamento sem pedir confirmação interativa.
                                                (Para uso em ambientes controlados, não interativos)

        Returns:
            Dict[str, str]: Um dicionário com 'status' ('success' ou 'error') e uma 'message'.
        """
        confirmation = params.get('confirm', False)

        if not confirmation:
            # Em um ambiente real de assistente de voz/texto, você faria uma pergunta
            # e esperaria por uma resposta do usuário para confirmar.
            # Para este exemplo de plugin, simulamos a necessidade de confirmação.
            return {"status": "info", "message": "Comando de desligamento requer confirmação. Por favor, confirme."}

        system = platform.system()
        if system == "Windows":
            command = ["shutdown", "/s", "/t", "0"] # /s para desligar, /t 0 para imediato
        elif system == "Linux" or system == "Darwin": # Darwin é macOS
            command = ["sudo", "shutdown", "-h", "now"] # -h para halt (desligar)
        else:
            return {"status": "error", "message": f"Sistema operacional '{system}' não suportado para desligamento."}
        
        logger.warning(f"Tentando desligar o sistema: {' '.join(command)}")
        return self._execute_command(command)

    def restart(self, params: Dict[str, Any]) -> Dict[str, str]:
        """
        Reinicia o computador.
        Requer confirmação para evitar reinicializações acidentais.

        Args:
            params (Dict[str, Any]): Um dicionário que pode conter:
                - 'confirm' (bool, opcional): Se True, executa o reinício sem pedir confirmação interativa.

        Returns:
            Dict[str, str]: Um dicionário com 'status' ('success' ou 'error') e uma 'message'.
        """
        confirmation = params.get('confirm', False)

        if not confirmation:
            return {"status": "info", "message": "Comando de reinício requer confirmação. Por favor, confirme."}

        system = platform.system()
        if system == "Windows":
            command = ["shutdown", "/r", "/t", "0"] # /r para reiniciar, /t 0 para imediato
        elif system == "Linux" or system == "Darwin": # Darwin é macOS
            command = ["sudo", "reboot"]
        else:
            return {"status": "error", "message": f"Sistema operacional '{system}' não suportado para reinício."}
        
        logger.warning(f"Tentando reiniciar o sistema: {' '.join(command)}")
        return self._execute_command(command)

def register() -> Dict[str, Any]:
    """
    Registra a classe PCControl como uma ferramenta para o TaskEngine.
    Define as ações 'shutdown_pc' e 'restart_pc'.

    Returns:
        Dict[str, Any]: Um dicionário que descreve a ferramenta e suas ações.
    """
    pc_control_instance = PCControl()
    return {
        "name": "pc_control",
        "description": "Ferramenta para controlar operações básicas do PC (desligar, reiniciar).",
        "actions": {
            "shutdown_pc": {
                "description": "Desliga o computador. Requer confirmação.",
                "parameters": {
                    "confirm": "boolean (true para confirmar o desligamento)"
                },
                "execute": pc_control_instance.shutdown
            },
            "restart_pc": {
                "description": "Reinicia o computador. Requer confirmação.",
                "parameters": {
                    "confirm": "boolean (true para confirmar o reinício)"
                },
                "execute": pc_control_instance.restart
            }
        }
    }

# Exemplo de uso interativo (para testes diretos do plugin)
if __name__ == "__main__":
    tool_info = register()
    pc_controller = tool_info["actions"]["shutdown_pc"]["execute"].__self__ # Acessa a instância

    print("--- Teste de PC Control ---")
    
    # Exemplo de desligamento (não vai desligar sem confirmação)
    print("\nTentando desligar sem confirmação:")
    result = pc_controller.shutdown({"confirm": False})
    print(result) # Deve retornar {"status": "info", "message": "Comando de desligamento requer confirmação. Por favor, confirme."}

    # Exemplo de desligamento (com confirmação - CUIDADO!)
    # print("\nTentando desligar com confirmação (CUIDADO!):")
    # result = pc_controller.shutdown({"confirm": True})
    # print(result)

    # Exemplo de reinício (não vai reiniciar sem confirmação)
    print("\nTentando reiniciar sem confirmação:")
    result = pc_controller.restart({"confirm": False})
    print(result) # Deve retornar {"status": "info", "message": "Comando de reinício requer confirmação. Por favor, confirme."}

    # Exemplo de reinício (com confirmação - CUIDADO!)
    # print("\nTentando reiniciar com confirmação (CUIDADO!):")
    # result = pc_controller.restart({"confirm": True})
    # print(result)
