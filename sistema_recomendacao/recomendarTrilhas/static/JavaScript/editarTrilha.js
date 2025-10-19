document.addEventListener('DOMContentLoaded', function () {
  console.log("Script carregado");

  // Função utilitária: normaliza campos clonados (name, id e label)
  function normalizeFields(container, topicoIndex, capIndex) {
    container.querySelectorAll('input, textarea, select').forEach(input => {
      if (!input.name) return;

      // remove __prefix__-
      let fieldName = input.name.replace('__prefix__-', '').split('-').pop();

      input.name = `capitulo_${topicoIndex}-${capIndex}-${fieldName}`;
      input.id = `id_capitulo_${topicoIndex}-${capIndex}-${fieldName}`;
      input.value = '';
      input.removeAttribute('disabled');
      if (input.tagName === 'SELECT') input.selectedIndex = 0;
    });

    // Corrige labels associadas
    container.querySelectorAll('label').forEach(label => {
      if (label.htmlFor) {
        let fieldName = label.htmlFor.replace('__prefix__-', '').split('-').pop();
        label.htmlFor = `id_capitulo_${topicoIndex}-${capIndex}-${fieldName}`;
      }
    });

    // 🔥 Remove campo DELETE se existir
    container.querySelectorAll('input[name$="-DELETE"]').forEach(el => el.remove());
  }

  // Função utilitária: garante management_form para cada capitulo_X
  function ensureCapituloManagement(container, idx) {
    const ids = {
      total: `id_capitulo_${idx}-TOTAL_FORMS`,
      initial: `id_capitulo_${idx}-INITIAL_FORMS`,
      min: `id_capitulo_${idx}-MIN_NUM_FORMS`,
      max: `id_capitulo_${idx}-MAX_NUM_FORMS`,
    };

    let totalForms = container.querySelector(`#${ids.total}`);
    if (!totalForms) {
      totalForms = document.createElement('input');
      totalForms.type = 'hidden';
      totalForms.name = `capitulo_${idx}-TOTAL_FORMS`;
      totalForms.id = ids.total;
      totalForms.value = '0';
      container.appendChild(totalForms);

      const initialForms = document.createElement('input');
      initialForms.type = 'hidden';
      initialForms.name = `capitulo_${idx}-INITIAL_FORMS`;
      initialForms.id = ids.initial;
      initialForms.value = '0';
      container.appendChild(initialForms);

      const minForms = document.createElement('input');
      minForms.type = 'hidden';
      minForms.name = `capitulo_${idx}-MIN_NUM_FORMS`;
      minForms.id = ids.min;
      minForms.value = '0';
      container.appendChild(minForms);

      const maxForms = document.createElement('input');
      maxForms.type = 'hidden';
      maxForms.name = `capitulo_${idx}-MAX_NUM_FORMS`;
      maxForms.id = ids.max;
      maxForms.value = '1000';
      container.appendChild(maxForms);
    }
    return totalForms;
  }

  // Adicionar tópico
  const botaoTopico = document.getElementById('add-topico');
  botaoTopico.addEventListener('click', function () {
    const container = document.getElementById('topico-formset-container');
    const totalForms = document.querySelector('#id_topico_set-TOTAL_FORMS');
    const formCount = parseInt(totalForms.value, 10);
    const firstForm = document.getElementById('topico-empty-form');
    const newForm = firstForm.cloneNode(true);

    newForm.setAttribute('data-topico-index', formCount);
    newForm.removeAttribute('id');

    // 🔥 Remove campo DELETE se existir
    newForm.querySelectorAll('input[name$="-DELETE"]').forEach(el => el.remove());

    // Atualiza campos do novo tópico
    newForm.querySelectorAll('input, textarea, select').forEach(input => {
      if (!input.name) return;
      const fieldName = input.name.split('-').pop();
      input.name = `topico_set-${formCount}-${fieldName}`;
      input.id = `id_topico_set-${formCount}-${fieldName}`;
      input.value = '';
      input.removeAttribute('disabled');
      if (input.tagName === 'SELECT') input.selectedIndex = 0;
    });

    // Atualiza container de capítulos do novo tópico
    const capituloContainer = newForm.querySelector('.capitulo-formset');
    capituloContainer.innerHTML = '';
    capituloContainer.setAttribute('data-topico-index', formCount);

    // Garante management_form
    const totalCapsInput = ensureCapituloManagement(capituloContainer, formCount);

    // Clona modelo oculto
    const modelo = document.querySelector('#capitulo-modelo .capitulo-form');
    const capituloForm = modelo.cloneNode(true);

    // Normaliza campos do capítulo inicial (índice 0)
    normalizeFields(capituloForm, formCount, 0);
    capituloContainer.appendChild(capituloForm);

    // Atualiza TOTAL_FORMS dos capítulos para 1
    totalCapsInput.value = '1';

    // Incrementa TOTAL_FORMS dos tópicos e adiciona ao DOM
    totalForms.value = formCount + 1;
    container.appendChild(newForm);
  });

  // Adicionar capítulo em tópico existente
  document.addEventListener('click', function (e) {
    if (!e.target.classList.contains('add-capitulo')) return;

    const topicoForm = e.target.closest('.topico-form');
    const topicoIndex = topicoForm.getAttribute('data-topico-index');
    const container = topicoForm.querySelector('.capitulo-formset');

    // Garante management_form do capitulo_{topicoIndex}
    const totalFormsInput = ensureCapituloManagement(container, topicoIndex);
    const formCount = parseInt(totalFormsInput.value, 10);

    // Clona modelo oculto
    const modelo = document.querySelector('#capitulo-modelo .capitulo-form');
    const newForm = modelo.cloneNode(true);

    // 🔥 Remove campo DELETE se existir
    newForm.querySelectorAll('input[name$="-DELETE"]').forEach(el => el.remove());

    // Normaliza campos do novo capítulo
    normalizeFields(newForm, topicoIndex, formCount);

    // Incrementa TOTAL_FORMS e adiciona o capítulo
    totalFormsInput.value = (formCount + 1).toString();
    container.appendChild(newForm);
  });
});
