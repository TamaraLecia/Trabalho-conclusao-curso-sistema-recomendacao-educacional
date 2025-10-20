// ---------------- CAPÍTULOS ----------------
// ⚠️ Este trecho só deve existir na tela de capítulos (editar_topico.html)
document.addEventListener("DOMContentLoaded", function() {
  console.log("✅ capitulos.js carregado!");

  const container = document.getElementById("capitulos");
  const addButton = document.getElementById("add-capitulo");
  const totalForms = document.getElementById("id_capitulos-TOTAL_FORMS"); // prefixo correto!
  const emptyTpl = document.getElementById("empty-capitulo-form");

  if (!container || !addButton || !totalForms || !emptyTpl) {
    // Se não estiver na tela de capítulos, simplesmente não faz nada
    return;
  }

  // Adicionar novo capítulo
  addButton.addEventListener("click", function() {
    const formCount = parseInt(totalForms.value, 10);
    const html = emptyTpl.innerHTML.replace(/__prefix__/g, String(formCount));
    const wrapper = document.createElement("div");
    wrapper.className = "capitulo-form";
    wrapper.innerHTML = html;

    // 🔥 Remove campo DELETE se existir
    wrapper.querySelectorAll('input[name$="-DELETE"]').forEach(el => el.remove());

    container.appendChild(wrapper);
    totalForms.value = formCount + 1;
  });

  // ❌ Não há mais listener para remover-capitulo
});
