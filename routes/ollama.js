import express from "express";
import OllamaService from "../services/ollamaService";

const router = express.Router();

router.post("/generate", async (requestAnimationFrame, res) =>{
    const {prompt, model} = req.body;
    const response = await OllamaService.generateText(prompt, model);
    res.json({response});
});

export default router;