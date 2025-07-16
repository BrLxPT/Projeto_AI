// Aguarda o carregamento completo do DOM
document.addEventListener('DOMContentLoaded', function() {
    // Elementos da interface
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const messagesDiv = document.getElementById('messages');
    
    // Função para adicionar mensagem ao chat
    function addMessage(content, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = isUser ? 'user-message' : 'ai-message';
        messageDiv.textContent = content;
        messagesDiv.appendChild(messageDiv);
        messagesDiv.scrollTop = messagesDiv.scrollHeight; // Auto-scroll
    }
    
    // Envia mensagem quando botão é clicado
    sendBtn.addEventListener('click', async function() {
        const text = userInput.value.trim();
        if (text) {
            addMessage(text, true); // Adiciona mensagem do usuário
            userInput.value = ''; // Limpa campo
            
            try {
                // Faz requisição para o backend
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message: text })
                });
                
                const data = await response.json();
                addMessage(data.response); // Adiciona resposta da AI
            } catch (error) {
                addMessage("Erro ao conectar com o servidor.");
            }
        }
    });
    
    // Permite enviar com Enter
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendBtn.click();
        }
    });
});