// Tela de intake. Valida no cliente apenas o que evita ida desnecessária ao
// servidor; a validação que conta é a do workflow, no nó Sanitizar Entrada.

const formulario = document.getElementById('formulario');
const botao = document.getElementById('enviar');
const saida = document.getElementById('saida');
const campoCpf = document.getElementById('cpf');
const campoDescricao = document.getElementById('descricao');
const contagem = document.getElementById('contagem');

campoDescricao.addEventListener('input', () => {
  contagem.textContent = campoDescricao.value.length;
});

// Máscara de CPF conforme digita, sem impedir colar o valor já formatado.
campoCpf.addEventListener('input', () => {
  const d = campoCpf.value.replace(/\D/g, '').slice(0, 11);
  campoCpf.value = d
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})\.(\d{3})(\d)/, '$1.$2.$3')
    .replace(/(\d{3})\.(\d{3})\.(\d{3})(\d)/, '$1.$2.$3-$4');
});

function cpfValido(valor) {
  const d = valor.replace(/\D/g, '');
  if (d.length !== 11 || /^(\d)\1{10}$/.test(d)) return false;
  // Dígitos verificadores: recusa número inventado antes de gastar uma chamada
  // de LLM, e evita que dado inválido entre na trilha de auditoria.
  for (const [inicio, posicao] of [[9, 10], [10, 11]]) {
    let soma = 0;
    for (let i = 0; i < inicio; i++) soma += Number(d[i]) * (posicao - i);
    let resto = (soma * 10) % 11;
    if (resto === 10) resto = 0;
    if (resto !== Number(d[inicio])) return false;
  }
  return true;
}

function mostrarErro(mensagem) {
  saida.innerHTML = '';
  const div = document.createElement('div');
  div.className = 'erro';
  div.textContent = mensagem;
  saida.appendChild(div);
}

function mostrarResultado(dados) {
  const urgencia = (dados.urgencia || 'media').toLowerCase();
  const rotuloUrgencia = { alta: 'Alta', media: 'Média', baixa: 'Baixa' }[urgencia] || dados.urgencia;

  saida.innerHTML = '';
  const bloco = document.createElement('div');
  bloco.className = 'resultado';

  const topo = document.createElement('div');
  topo.className = 'protocolo';
  const rotulo = document.createElement('div');
  rotulo.className = 'rotulo';
  rotulo.textContent = 'Protocolo do seu caso';
  const numero = document.createElement('div');
  numero.className = 'numero';
  numero.textContent = dados.protocolo || '—';
  topo.append(rotulo, numero);

  const detalhes = document.createElement('div');
  detalhes.className = 'detalhes';

  const area = document.createElement('div');
  area.className = 'detalhe';
  area.innerHTML = '<div class="rotulo">Área</div>';
  const valorArea = document.createElement('div');
  valorArea.className = 'valor';
  valorArea.textContent = dados.revisao_manual ? 'Em triagem manual' : (dados.area || '—');
  area.appendChild(valorArea);

  const urg = document.createElement('div');
  urg.className = 'detalhe';
  urg.innerHTML = '<div class="rotulo">Urgência</div>';
  const etiqueta = document.createElement('span');
  etiqueta.className = 'etiqueta ' + urgencia;
  etiqueta.textContent = rotuloUrgencia;
  urg.appendChild(etiqueta);

  detalhes.append(area, urg);
  bloco.append(topo, detalhes);

  const nota = document.createElement('p');
  nota.className = 'rodape';
  nota.textContent = dados.revisao_manual
    ? 'O seu caso foi recebido e será encaminhado por uma pessoa da equipe, porque a classificação automática não teve certeza da área. Guarde o protocolo.'
    : 'O seu caso já está com a equipe da área indicada. Guarde o protocolo para acompanhar.';
  bloco.appendChild(nota);

  saida.appendChild(bloco);
  bloco.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

formulario.addEventListener('submit', async (evento) => {
  evento.preventDefault();

  const nome = document.getElementById('nome').value.trim();
  const cpf = campoCpf.value.trim();
  const descricao = campoDescricao.value.trim();

  if (nome.split(/\s+/).length < 2) {
    return mostrarErro('Informe o nome completo, com ao menos um sobrenome.');
  }
  if (!cpfValido(cpf)) {
    return mostrarErro('O CPF informado não é válido. Confira os números.');
  }
  if (descricao.length < 20) {
    return mostrarErro('Descreva o caso com um pouco mais de detalhe, ao menos 20 caracteres.');
  }

  botao.disabled = true;
  botao.innerHTML = '<span class="girando"></span>Classificando o seu caso…';
  saida.innerHTML = '';

  try {
    const resposta = await fetch('/api/intake', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nome_cliente: nome, cpf, descricao_caso: descricao }),
    });

    const corpo = await resposta.json().catch(() => ({}));

    if (!resposta.ok) {
      return mostrarErro(corpo.detail || 'Não foi possível enviar o seu caso. Tente novamente.');
    }

    mostrarResultado(corpo);
    formulario.reset();
    contagem.textContent = '0';
  } catch {
    mostrarErro('Falha de conexão. Verifique a sua internet e tente novamente.');
  } finally {
    botao.disabled = false;
    botao.textContent = 'Enviar meu caso';
  }
});
