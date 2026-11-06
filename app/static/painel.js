// Painel de operação. Lê /api/metricas, que é a ponte para a mesma view que o
// relatório cita. A rubrica exige que os números batam; a forma de garantir
// isso é não ter duas fontes.

const THRESHOLDS = { p95_ms: 60000, pct_erro: 1, pct_revisao_manual: 15 };

const fmt = {
  inteiro: (v) => v == null ? '—' : Number(v).toLocaleString('pt-BR'),
  ms: (v) => v == null ? '—' : Number(v) >= 1000
    ? (Number(v) / 1000).toLocaleString('pt-BR', { maximumFractionDigits: 2 }) + ' s'
    : Math.round(Number(v)) + ' ms',
  pct: (v) => v == null ? '—' : Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 2 }) + ' %',
  usd: (v) => v == null ? '—' : 'US$ ' + Number(v).toLocaleString('pt-BR', { minimumFractionDigits: 4, maximumFractionDigits: 4 }),
};

function placa(rotulo, valor, nota, estado) {
  const d = document.createElement('div');
  d.className = 'placa' + (estado ? ' ' + estado : '');
  const r = document.createElement('div'); r.className = 'rotulo'; r.textContent = rotulo;
  const v = document.createElement('div'); v.className = 'valor'; v.textContent = valor;
  const n = document.createElement('div'); n.className = 'nota'; n.textContent = nota;
  d.append(r, v, n);
  return d;
}

function barras(destino, linhas, unidade) {
  destino.innerHTML = '';
  if (!linhas.length) {
    destino.innerHTML = '<p class="nota">Sem dados na janela.</p>';
    return;
  }
  const maior = Math.max(...linhas.map((l) => l.valor)) || 1;
  for (const l of linhas) {
    const bloco = document.createElement('div');
    bloco.className = 'barra-linha';

    const topo = document.createElement('div');
    topo.className = 'barra-topo';
    const nome = document.createElement('span'); nome.className = 'nome'; nome.textContent = l.nome;
    const num = document.createElement('span'); num.className = 'num'; num.textContent = l.rotulo;
    topo.append(nome, num);

    const trilho = document.createElement('div');
    trilho.className = 'barra-trilho';
    const preenche = document.createElement('div');
    preenche.className = 'barra-preenche' + (l.destaque ? ' destaque' : '');
    preenche.style.width = Math.max(2, (l.valor / maior) * 100) + '%';
    trilho.appendChild(preenche);

    bloco.append(topo, trilho);
    destino.appendChild(bloco);
  }
  if (unidade) {
    const nota = document.createElement('p');
    nota.className = 'nota';
    nota.textContent = unidade;
    destino.appendChild(nota);
  }
}

function tabela(destino, colunas, linhas) {
  destino.innerHTML = '';
  if (!linhas.length) {
    destino.innerHTML = '<p class="nota">Nenhum registro.</p>';
    return;
  }
  const t = document.createElement('table');
  const thead = document.createElement('thead');
  const tr = document.createElement('tr');
  for (const c of colunas) { const th = document.createElement('th'); th.textContent = c; tr.appendChild(th); }
  thead.appendChild(tr); t.appendChild(thead);
  const tbody = document.createElement('tbody');
  for (const linha of linhas) {
    const tr = document.createElement('tr');
    for (const celula of linha) { const td = document.createElement('td'); td.textContent = celula; tr.appendChild(td); }
    tbody.appendChild(tr);
  }
  t.appendChild(tbody);
  destino.appendChild(t);
}

async function carregar() {
  let dados;
  try {
    const r = await fetch('/api/metricas');
    if (!r.ok) throw new Error();
    dados = await r.json();
  } catch {
    document.getElementById('placas').innerHTML =
      '<div class="erro">Não foi possível carregar as métricas. O serviço de triagem pode estar indisponível.</div>';
    return;
  }

  const p = dados.painel || {};

  const estadoP95 = p.p95_ms == null ? '' : (p.p95_ms <= THRESHOLDS.p95_ms ? 'bom' : 'atencao');
  const estadoErro = p.pct_erro == null ? '' : (p.pct_erro <= THRESHOLDS.pct_erro ? 'bom' : 'atencao');
  const estadoRev = p.pct_revisao_manual == null ? '' : (p.pct_revisao_manual <= THRESHOLDS.pct_revisao_manual ? 'bom' : 'atencao');

  const placas = document.getElementById('placas');
  placas.innerHTML = '';
  placas.append(
    placa('Volume', fmt.inteiro(p.volume), 'intakes em 24 h'),
    placa('Latência p95', fmt.ms(p.p95_ms), 'SLA de 60 s', estadoP95),
    placa('Taxa de erro', fmt.pct(p.pct_erro), 'limite de 1 %', estadoErro),
    placa('Revisão manual', fmt.pct(p.pct_revisao_manual), 'limite de 15 %', estadoRev),
    placa('Custo', fmt.usd(p.usd), 'em 24 h'),
  );

  const spans = (dados.latencia_por_span || []).map((s) => ({
    nome: s.span,
    valor: Number(s.p50_ms) || 0,
    rotulo: `p50 ${fmt.ms(s.p50_ms)} · p95 ${fmt.ms(s.p95_ms)}`,
    destaque: s.span === 'classificacao_llm',
  }));
  barras(document.getElementById('spans'), spans, 'Mediana por etapa. A chamada ao modelo domina o caminho.');

  const areas = (dados.por_area || []).map((a) => ({
    nome: a.area,
    valor: Number(a.intakes) || 0,
    rotulo: fmt.inteiro(a.intakes),
  }));
  barras(document.getElementById('areas'), areas, 'Intakes por área na janela.');

  tabela(
    document.getElementById('purgas'),
    ['Alvo', 'Prazo', 'Removidas', 'Executada em'],
    (dados.purgas_recentes || []).map((x) => [
      x.alvo,
      x.prazo,
      fmt.inteiro(x.linhas_removidas),
      new Date(x.executado_em).toLocaleString('pt-BR'),
    ]),
  );

  const rodape = document.getElementById('rodape');
  rodape.textContent =
    `Trilha com ${fmt.inteiro(dados.total_trilha)} registros e ${fmt.inteiro(dados.total_spans)} spans. ` +
    `Atualizado em ${new Date(dados.gerado_em).toLocaleString('pt-BR')}.`;
}

carregar();
setInterval(carregar, 30000);
