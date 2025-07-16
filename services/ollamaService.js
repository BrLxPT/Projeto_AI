import axios from "axios";

class OllamaService {
  static async generateText(prompt, model = "llama3") {
    try {
      const response = await axios.post("http://localhost:11434/api/generate", {
        model,
        prompt,
        stream: false,
      });
      return response.data.response;
    } catch (error) {
      console.error("Erro ao chamar Ollama:", error);
      return null;
    }
  }
}

export default OllamaService;