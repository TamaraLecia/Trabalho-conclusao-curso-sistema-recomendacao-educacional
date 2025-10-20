// ---------------- TÓPICOS ----------------
document.addEventListener("DOMContentLoaded", function() {
    console.log("✅ script.js carregado!");

    const container = document.getElementById("topicos");
    const addButton = document.getElementById("add-topico");
    const totalForms = document.getElementById("id_topicos-TOTAL_FORMS"); // prefixo correto
    const emptyTpl = document.getElementById("empty-topico-form");

    console.log("container:", container);
    console.log("addButton:", addButton);
    console.log("totalForms:", totalForms);
    console.log("emptyTpl:", emptyTpl);

    if (!container || !addButton || !totalForms || !emptyTpl) {
        console.warn("⚠️ Algum elemento não foi encontrado");
        return;
    }

    addButton.addEventListener("click", function() {
        console.log("Botão clicado!");
        const formCount = parseInt(totalForms.value, 10);
        const html = emptyTpl.innerHTML.replace(/__prefix__/g, String(formCount));
        const wrapper = document.createElement("div");
        wrapper.className = "topico-form";
        wrapper.innerHTML = html;

        // 🔥 Remove o campo DELETE se existir
        wrapper.querySelectorAll('input[name$="-DELETE"]').forEach(el => el.remove());

        container.appendChild(wrapper);
        totalForms.value = formCount + 1;
    });
});
