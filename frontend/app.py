import sys
import os
import tkinter as tk
from tkinter import scrolledtext, messagebox, BooleanVar
import requests
import json
import importlib

# Adicionar o diretório pai ao caminho para importar módulos
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Importar o ficheiro de configuração (config.py)
try:
    from backend import config
except ImportError:
    messagebox.showerror("Erro", "Não foi possível encontrar o ficheiro backend/config.py")
    sys.exit()

def display_response(text):
    """Insere o texto de resposta na área de saída e garante a exibição."""
    output_text_area.config(state=tk.NORMAL)
    output_text_area.insert(tk.END, text + "\n")
    output_text_area.config(state=tk.DISABLED)
    output_text_area.see(tk.END) # Rola para o fim para ver a mensagem mais recente

def run_ollama():
    """Função para enviar o comando do usuário para o servidor backend."""
    user_input = user_input_entry.get()
    if not user_input:
        return
    
    display_response(f"Você: {user_input}")

    try:
        url = "http://localhost:5000/api/ask" # Rota corrigida
        payload = {"query": user_input} # Chave do JSON corrigida
        
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            display_response(f"AI: {result.get('message', 'Sem resposta da IA.')}\n\n")
        else:
            display_response(f"AI: Erro ao conectar ao backend. Status: {response.status_code}\n\n")
            
    except requests.exceptions.ConnectionError:
        display_response("AI: Erro: Não foi possível conectar ao servidor backend. Por favor, verifique se o servidor está em execução.\n\n")
    except Exception as e:
        display_response(f"AI: Ocorreu um erro inesperado: {str(e)}\n\n")
        
    user_input_entry.delete(0, tk.END)

def get_available_plugins():
    """Procura todos os ficheiros .py na pasta de plugins, exceto os internos."""
    plugins_dir = os.path.join(parent_dir, "backend", "plugins")
    if not os.path.exists(plugins_dir):
        return []
    
    available = []
    for file in os.listdir(plugins_dir):
        if file.endswith(".py") and file not in ["__init__.py", "register.py"]:
            available.append(file[:-3])
    return available

def save_settings(new_settings, settings_window):
    """Guarda as configurações no ficheiro config.py."""
    try:
        config_path = os.path.join(parent_dir, "backend", "config.py")
        with open(config_path, "w") as f:
            f.write("# Ficheiro de configuração para o Ollie\n")
            f.write("ENABLED_PLUGINS = {\n")
            for name, enabled in new_settings.items():
                f.write(f"    \"{name}\": {enabled},\n")
            f.write("}\n")
        
        messagebox.showinfo("Sucesso", "Configurações guardadas com sucesso!\nPor favor, reinicie o servidor do Ollie para aplicar as mudanças.")
        settings_window.destroy()
    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro ao guardar as configurações: {str(e)}")

def open_settings_panel():
    """Cria e exibe a janela de configurações de plugins."""
    settings_window = tk.Toplevel(root)
    settings_window.title("Ollie - Configurações")
    settings_window.geometry("400x300")
    
    # Aceder aos plugins do ficheiro de configuração
    enabled_plugins = config.ENABLED_PLUGINS
    
    # Obter a lista de todos os plugins disponíveis
    all_plugins = get_available_plugins()
    
    plugin_vars = {} # Dicionário para guardar as variáveis das caixas de seleção
    
    title_label = tk.Label(settings_window, text="Ativar/Desativar Plugins", font=("Arial", 14, "bold"))
    title_label.pack(pady=10)
    
    frame = tk.Frame(settings_window)
    frame.pack(fill=tk.BOTH, expand=True)

    canvas = tk.Canvas(frame)
    scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL, command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    for plugin_name in all_plugins:
        var = BooleanVar(value=enabled_plugins.get(plugin_name, False))
        cb = tk.Checkbutton(scrollable_frame, text=plugin_name.replace("_", " ").title(), variable=var)
        cb.pack(anchor="w", padx=20, pady=2)
        plugin_vars[plugin_name] = var

    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    button_frame = tk.Frame(settings_window)
    button_frame.pack(pady=10)
    
    save_button = tk.Button(button_frame, text="Guardar Configurações", command=lambda: save_settings({name: var.get() for name, var in plugin_vars.items()}, settings_window))
    save_button.pack(side=tk.LEFT, padx=10)

    cancel_button = tk.Button(button_frame, text="Sair", command=settings_window.destroy)
    cancel_button.pack(side=tk.LEFT, padx=10)
# --- Configuração da janela Principal ---
root = tk.Tk()
root.title("Ollie - Seu Assistente de AI")
root.geometry("600x450")

# --- Widgets ---
title_label = tk.Label(root, text="Ollie: Seu Assistente AI", font=("Arial", 16))
title_label.pack(pady=10)

output_text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=15)
output_text_area.pack(pady=5)
output_text_area.config(state=tk.DISABLED)

input_frame = tk.Frame(root)
input_frame.pack(pady=10)

user_input_entry = tk.Entry(input_frame, width=50, font=("Arial", 12))
user_input_entry.pack(side=tk.LEFT, padx=5)
user_input_entry.bind("<Return>", lambda event: run_ollama())

execute_button = tk.Button(input_frame, text="Executar", command=run_ollama)
execute_button.pack(side=tk.LEFT, padx=5)

# Novo botão para abrir o painel de configurações
settings_button = tk.Button(root, text="Configurações", command=open_settings_panel)
settings_button.pack(pady=5)

root.mainloop()
