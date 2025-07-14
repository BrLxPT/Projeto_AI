document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("rule-form");
    const msgDiv = document.getElementById("msg");

    form.addEventListener("submit", async function (e) {
        e.preventDefault();

        const id = form.id.value.trim();
        const condition = form.condition.value.trim();
        let action;

        try {
            action = JSON.parse(form.action.value);
        } catch {
            msgDiv.innerText = "❌ JSON inválido.";
            return;
        }

        const res = await fetch("/rules", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ id, condition, action })
        });

        const result = await res.json();
        msgDiv.innerText = result.message;
        setTimeout(() => location.reload(), 1000);
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
