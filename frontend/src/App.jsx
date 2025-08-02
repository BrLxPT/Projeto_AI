import React, { useState, useEffect } from 'react';
import './index.css'; // Importa o novo ficheiro CSS

// Componente principal da aplicação
function App() {
  const [messages, setMessages] = useState([]); // Armazena as mensagens do chat
  const [input, setInput] = useState(''); // Armazena o texto do input do usuário
  const [loading, setLoading] = useState(false); // Estado de carregamento
  const [showEmailConfig, setShowEmailConfig] = useState(false); // Controla a visibilidade do modal de email
  const [emailConfig, setEmailConfig] = useState({ // Dados de configuração de email
    smtp_server: '',
    smtp_port: '',
    email: '',
    password: ''
  });
  const [emailConfigStatus, setEmailConfigStatus] = useState(''); // Status da configuração de email
  const [isEmailConfigured, setIsEmailConfigured] = useState(false); // Se o email já foi configurado
  const [isListening, setIsListening] = useState(false); // Estado para o reconhecimento de voz

  // URL base do seu backend Flask
  const API_BASE_URL = 'http://localhost:5000';

  // Efeito para verificar o status da configuração do e-mail ao carregar a página
  useEffect(() => {
    const checkEmailStatus = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/email_status`);
        const data = await response.json();
        setIsEmailConfigured(data.email_configured);
        if (data.email_configured) {
          setEmailConfigStatus('Email configurado com sucesso.');
        }
      } catch (error) {
        console.error('Erro ao verificar status do email:', error);
        setEmailConfigStatus('Não foi possível verificar o status do email.');
      }
    };
    checkEmailStatus();
  }, []);

  // Função para enviar o comando para o backend
  const sendMessage = async (messageText) => {
    if (messageText.trim() === '') return;

    const userMessage = { sender: 'user', text: messageText };
    setMessages((prevMessages) => [...prevMessages, userMessage]);
    setInput(''); // Limpa o input de texto, mesmo se for de voz
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/command`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ user_input: userMessage.text }),
      });

      const data = await response.json();
      let botMessage;

      if (data.status === 'success' && data.result) {
        // Se a resposta é de uma ferramenta, exiba o resultado
        botMessage = { sender: 'bot', text: `Ação concluída: ${JSON.stringify(data.result)}` };
      } else if (data.status === 'text_response') {
        // Se a resposta é um texto direto do LLM
        botMessage = { sender: 'bot', text: data.message };
      } else if (data.status === 'error') {
        // Se houver um erro
        botMessage = { sender: 'bot', text: `Erro: ${data.message}` };
      } else {
        // Fallback para respostas inesperadas
        botMessage = { sender: 'bot', text: `Resposta inesperada: ${JSON.stringify(data)}` };
      }
      setMessages((prevMessages) => [...prevMessages, botMessage]);
    } catch (error) {
      console.error('Erro ao enviar mensagem:', error);
      setMessages((prevMessages) => [
        ...prevMessages,
        { sender: 'bot', text: `Erro de conexão: ${error.message}. Verifique se o backend está rodando.` },
      ]);
    } finally {
      setLoading(false);
    }
  };

  // Função para configurar o email
  const handleEmailConfigSubmit = async () => {
    setLoading(true);
    setEmailConfigStatus('Configurando...');
    try {
      const response = await fetch(`${API_BASE_URL}/configure_email`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(emailConfig),
      });

      const data = await response.json();
      setEmailConfigStatus(data.message);
      if (data.status === 'success') {
        setIsEmailConfigured(true);
        setShowEmailConfig(false); // Fecha o modal após sucesso
      }
    } catch (error) {
      console.error('Erro ao configurar email:', error);
      setEmailConfigStatus(`Erro de conexão: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Função para iniciar o reconhecimento de voz
  const startVoiceInput = () => {
    if (!('webkitSpeechRecognition' in window)) {
      alert('Seu navegador não suporta reconhecimento de voz. Por favor, use Chrome.');
      return;
    }

    const recognition = new window.webkitSpeechRecognition();
    recognition.lang = 'pt-PT'; // Define o idioma para Português (Portugal)
    recognition.interimResults = false; // Queremos apenas o resultado final
    recognition.maxAlternatives = 1; // Apenas a melhor alternativa

    recognition.onstart = () => {
      setIsListening(true);
      console.log('Ouvindo...');
      setMessages((prevMessages) => [...prevMessages, { sender: 'system', text: 'Estou a ouvir...' }]);
    };

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      console.log('Transcrição:', transcript);
      sendMessage(transcript); // Envia a transcrição para o backend
    };

    recognition.onerror = (event) => {
      setIsListening(false);
      console.error('Erro de reconhecimento de voz:', event.error);
      setMessages((prevMessages) => [...prevMessages, { sender: 'system', text: `Erro de voz: ${event.error}` }]);
    };

    recognition.onend = () => {
      setIsListening(false);
      console.log('Reconhecimento de voz terminou.');
    };

    recognition.start();
  };

  return (
    <div className="app-container">
      <div className="chat-window">
        {/* Header */}
        <div className="chat-header">
          <h1 className="header-title">Assistente de IA</h1>
          <button
            onClick={() => setShowEmailConfig(true)}
            className="header-button"
          >
            {isEmailConfigured ? 'Email Configurado' : 'Configurar Email'}
          </button>
        </div>

        {/* Área de Mensagens */}
        <div className="messages-area">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`message-bubble-wrapper ${
                msg.sender === 'user' ? 'user-message-wrapper' : 'bot-message-wrapper'
              }`}
            >
              <div
                className={`message-bubble ${
                  msg.sender === 'user'
                    ? 'user-message-bubble'
                    : 'bot-message-bubble'
                }`}
              >
                {msg.text}
              </div>
            </div>
          ))}
          {loading && (
            <div className="bot-message-wrapper">
              <div className="message-bubble bot-message-bubble">
                Digitando...
              </div>
            </div>
          )}
          {isListening && (
            <div className="bot-message-wrapper">
              <div className="message-bubble listening-message-bubble">
                A ouvir...
              </div>
            </div>
          )}
        </div>

        {/* Input da Mensagem */}
        <div className="input-area">
          <input
            type="text"
            className="message-input"
            placeholder="Digite sua mensagem..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                sendMessage(input); // Chama sendMessage com o input
              }
            }}
            disabled={loading || isListening}
          />
          <button
            onClick={() => sendMessage(input)} // Chama sendMessage com o input
            className="send-button"
            disabled={loading || isListening}
          >
            Enviar
          </button>
          <button
            onClick={startVoiceInput}
            className={`voice-button ${
              isListening ? 'listening' : 'not-listening'
            }`}
            disabled={loading}
          >
            {isListening ? 'A Ouvir...' : 'Voz'}
          </button>
        </div>
      </div>

      {/* Modal de Configuração de Email */}
      {showEmailConfig && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h2 className="modal-title">Configurar Email SMTP</h2>
            <div className="space-y-4">
              <div className="modal-form-group">
                <label className="modal-label">Servidor SMTP:</label>
                <input
                  type="text"
                  className="modal-input"
                  value={emailConfig.smtp_server}
                  onChange={(e) => setEmailConfig({ ...emailConfig, smtp_server: e.target.value })}
                  placeholder="ex: smtp.gmail.com"
                />
              </div>
              <div className="modal-form-group">
                <label className="modal-label">Porta SMTP:</label>
                <input
                  type="number"
                  className="modal-input"
                  value={emailConfig.smtp_port}
                  onChange={(e) => setEmailConfig({ ...emailConfig, smtp_port: e.target.value })}
                  placeholder="ex: 587 ou 465"
                />
              </div>
              <div className="modal-form-group">
                <label className="modal-label">Seu Email:</label>
                <input
                  type="email"
                  className="modal-input"
                  value={emailConfig.email}
                  onChange={(e) => setEmailConfig({ ...emailConfig, email: e.target.value })}
                  placeholder="seu.email@exemplo.com"
                />
              </div>
              <div className="modal-form-group">
                <label className="modal-label">Senha/App Password:</label>
                <input
                  type="password"
                  className="modal-input"
                  value={emailConfig.password}
                  onChange={(e) => setEmailConfig({ ...emailConfig, password: e.target.value })}
                  placeholder="Sua senha ou senha de aplicativo"
                />
              </div>
            </div>
            <p className="modal-status-text">{emailConfigStatus}</p>
            <div className="modal-buttons">
              <button
                onClick={() => setShowEmailConfig(false)}
                className="modal-button cancel"
                disabled={loading}
              >
                Cancelar
              </button>
              <button
                onClick={handleEmailConfigSubmit}
                className="modal-button save"
                disabled={loading}
              >
                Salvar Configuração
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
