document.addEventListener("DOMContentLoaded", () => {
    const formAI = document.getElementById("form_ai");
    const msgDiv = document.getElementById("msg");

    formAI.addEventListener("submit", async (e) => {
        e.preventDefault();

        const instrucao = document.getElementById("instrucao_input").value;

        const formData = new FormData();
        formData.append("instrucao", instrucao);

        try {
            const response = await fetch("/rules/generate/json", {
                method: "POST",
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                msgDiv.innerHTML = `<p style="color:green;">✅ ${result.message}</p><pre>${JSON.stringify(result.rule, null, 2)}</pre>`;
            } else {
                msgDiv.innerHTML = `<p style="color:red;">❌ ${result.message}</p>`;
            }

        } catch (err) {
            msgDiv.innerHTML = `<p style="color:red;">Erro ao comunicar com o servidor.</p>`;
            console.error(err);
        }
    });
});

async function apagarRegra(id) {
    if (!confirm(`Tens a certeza que queres apagar a regra "${id}"?`)) return;

    const res = await fetch(`/rules/${id}`, { method: "DELETE" });
    const result = await res.json();
    alert(result.message);
    location.reload();
}

async function avaliarRegras() {
    const res = await fetch("/rules/evaluate", { method: "POST" });
    const result = await res.json();
    alert(result.message);
}

async function carregarNotificacoes() {
  const res = await fetch("/notifications");
  const data = await res.json();
  const ul = document.getElementById("notificacoes");
  ul.innerHTML = "";
  data.notificacoes.forEach(msg => {
    const li = document.createElement("li");
    li.textContent = msg;
    ul.appendChild(li);
  });
}

setInterval(carregarNotificacoes, 3000);
carregarNotificacoes();
