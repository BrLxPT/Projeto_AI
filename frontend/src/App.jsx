import React, { useState, useEffect } from 'react';

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
  const sendMessage = async () => {
    if (input.trim() === '') return;

    const userMessage = { sender: 'user', text: input };
    setMessages((prevMessages) => [...prevMessages, userMessage]);
    setInput('');
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

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center justify-center p-4 font-sans">
      <div className="bg-white shadow-lg rounded-lg w-full max-w-2xl flex flex-col h-[80vh]">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-500 to-purple-600 text-white p-4 rounded-t-lg flex justify-between items-center">
          <h1 className="text-2xl font-bold">Assistente de IA</h1>
          <button
            onClick={() => setShowEmailConfig(true)}
            className="px-4 py-2 bg-white text-blue-600 rounded-md shadow hover:bg-gray-100 transition duration-200"
          >
            {isEmailConfigured ? 'Email Configurado' : 'Configurar Email'}
          </button>
        </div>

        {/* Área de Mensagens */}
        <div className="flex-1 p-4 overflow-y-auto space-y-4">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[70%] p-3 rounded-lg shadow-md ${
                  msg.sender === 'user'
                    ? 'bg-blue-500 text-white rounded-br-none'
                    : 'bg-gray-200 text-gray-800 rounded-bl-none'
                }`}
              >
                {msg.text}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="max-w-[70%] p-3 rounded-lg shadow-md bg-gray-200 text-gray-800 rounded-bl-none">
                Digitando...
              </div>
            </div>
          )}
        </div>

        {/* Input da Mensagem */}
        <div className="p-4 border-t border-gray-200 flex items-center space-x-2">
          <input
            type="text"
            className="flex-1 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Digite sua mensagem..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                sendMessage();
              }
            }}
            disabled={loading}
          />
          <button
            onClick={sendMessage}
            className="px-5 py-3 bg-blue-600 text-white rounded-lg shadow hover:bg-blue-700 transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={loading}
          >
            Enviar
          </button>
        </div>
      </div>

      {/* Modal de Configuração de Email */}
      {showEmailConfig && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg p-6 shadow-xl w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">Configurar Email SMTP</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-gray-700 text-sm font-bold mb-2">Servidor SMTP:</label>
                <input
                  type="text"
                  className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                  value={emailConfig.smtp_server}
                  onChange={(e) => setEmailConfig({ ...emailConfig, smtp_server: e.target.value })}
                  placeholder="ex: smtp.gmail.com"
                />
              </div>
              <div>
                <label className="block text-gray-700 text-sm font-bold mb-2">Porta SMTP:</label>
                <input
                  type="number"
                  className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                  value={emailConfig.smtp_port}
                  onChange={(e) => setEmailConfig({ ...emailConfig, smtp_port: e.target.value })}
                  placeholder="ex: 587 ou 465"
                />
              </div>
              <div>
                <label className="block text-gray-700 text-sm font-bold mb-2">Seu Email:</label>
                <input
                  type="email"
                  className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                  value={emailConfig.email}
                  onChange={(e) => setEmailConfig({ ...emailConfig, email: e.target.value })}
                  placeholder="seu.email@exemplo.com"
                />
              </div>
              <div>
                <label className="block text-gray-700 text-sm font-bold mb-2">Senha/App Password:</label>
                <input
                  type="password"
                  className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                  value={emailConfig.password}
                  onChange={(e) => setEmailConfig({ ...emailConfig, password: e.target.value })}
                  placeholder="Sua senha ou senha de aplicativo"
                />
              </div>
            </div>
            <p className="text-sm text-gray-600 mt-2">{emailConfigStatus}</p>
            <div className="mt-6 flex justify-end space-x-3">
              <button
                onClick={() => setShowEmailConfig(false)}
                className="px-4 py-2 bg-gray-300 text-gray-800 rounded-md shadow hover:bg-gray-400 transition duration-200"
                disabled={loading}
              >
                Cancelar
              </button>
              <button
                onClick={handleEmailConfigSubmit}
                className="px-4 py-2 bg-blue-600 text-white rounded-md shadow hover:bg-blue-700 transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
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
