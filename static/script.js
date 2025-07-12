document.getElementById("rule-form").addEventListener("submit", async function (e) {
    e.preventDefault();

    const form = e.target;
    const id = form.id.value;
    const condition = form.condition.value;
    let action;

    try {
        action = JSON.parse(form.action.value);
    } catch {
        document.getElementById("msg").innerText = "❌ Ação não é JSON válido!";
        return;
    }

    const response = await fetch("/rules", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id, condition, action })
    });

    const result = await response.json();
    document.getElementById("msg").innerText = result.message || "Erro";

    // Reload page to see new rule
    location.reload();
});
