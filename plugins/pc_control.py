import wakeonlan
import os
import subprocess

def wake_pc(mac):
    wakeonlan.send_magic_packet(mac)
    return f"Wake-on-LAN enviado para {mac}"

def run_script(path):
    result = subprocess.run(["python", path], capture_output=True, text=True)
    return result.stdout

def register():
    return {
        "name": "pc_control",
        "description": "Controle remoto de computadores",
        "actions": {
            "pc_wake": {
                "description": "Ligar computador via Wake-on-LAN",
                "parameters": {"mac": "string"},
                "execute": wake_pc
            },
            "script_run": {
                "description": "Executar script local",
                "parameters": {"path": "string"},
                "execute": run_script
            }
        }
    }