import OllamaService from "./ollamaService.js";

class ActionService {
  // ... (outras ações)

  static async generateAIText(actionConfig) {
    const { prompt, model } = actionConfig;
    const aiResponse = await OllamaService.generateText(prompt, model);
    console.log("Resposta da IA:", aiResponse);
    return aiResponse;
  }
}