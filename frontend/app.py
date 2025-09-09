import sys
import os
import tkinter as tk
from tkinter import scrolledtext
import requests

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

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
    
    # Exibir a entrada do usuário na área de saída
    display_response(f"Você: {user_input}")

    try:
        url = "http://localhost:5000/api/ask" # Rota corrigida
        payload = {"query": user_input} # Chave do JSON corrigida
        
        # Enviar o comando para o backend via HTTP POST
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

root.mainloop()
