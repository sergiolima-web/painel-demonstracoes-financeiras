import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { KpiCard } from './components/KpiCard';
import { BalancoView } from './components/BalancoView';
import { DreView } from './components/DreView';
import { DreMatrizView } from './components/DreMatrizView';
import { EnsinoJevView } from './components/EnsinoJevView';
import { IndicesView } from './components/IndicesView';
import { AcionistasReport } from './components/AcionistasReport';
import { getDadosPadrao, getStatusJev, uploadDemonstracao } from './services/api';
import { DemonstracaoData, TipoPeriodo } from './types/financeiro';
import { 
  Building2, 
  TrendingUp, 
  DollarSign, 
  Percent, 
  PieChart, 
  FileSpreadsheet, 
  Award,
  Sparkles,
  Loader2,
  Calendar,
  Layers,
  Brain
} from 'lucide-react';

export const App: React.FC = () => {
  const [data, setData] = useState<DemonstracaoData | null>(null);
  const [activeTab, setActiveTab] = useState<'matriz' | 'ensino_jev' | 'acionistas' | 'balanco' | 'dre' | 'indices'>('matriz');
  const [periodoAtivo, setPeriodoAtivo] = useState<TipoPeriodo>('todos_trimestres');
  const [isLoading, setIsLoading] = useState(false);
  const [processandoModal, setProcessandoModal] = useState(false);
  const [etapaAtual, setEtapaAtual] = useState(1);
  const [progresso, setProgresso] = useState(15);
  const [nomeArquivoProcessando, setNomeArquivoProcessando] = useState('');
  const [mensagemSucesso, setMensagemSucesso] = useState('');
  const [jevStatus, setJevStatus] = useState<{ jev_habilitado?: boolean; badge?: string; icone?: string }>({
    jev_habilitado: true,
    badge: '⚡🧠 JEV Management Engine'
  });

  const carregarDados = async () => {
    setIsLoading(true);
    try {
      const [statusRes, dadosRes] = await Promise.all([
        getStatusJev().catch(() => ({ jev_habilitado: true, badge: '⚡🧠 JEV Engine' })),
        getDadosPadrao()
      ]);
      setJevStatus(statusRes);
      setData(dadosRes);
    } catch (err) {
      console.error('Erro ao carregar dados:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    carregarDados();
  }, []);

  const handleUpload = async (file: File) => {
    setNomeArquivoProcessando(file.name);
    setProcessandoModal(true);
    setEtapaAtual(1);
    setProgresso(20);
    setIsLoading(true);

    const timer1 = setTimeout(() => { setEtapaAtual(2); setProgresso(50); }, 350);
    const timer2 = setTimeout(() => { setEtapaAtual(3); setProgresso(75); }, 750);

    try {
      const resultado = await uploadDemonstracao(file);
      setEtapaAtual(4);
      setProgresso(100);

      setTimeout(() => {
        setData(resultado);
        setActiveTab('matriz');
        setProcessandoModal(false);
        const total = resultado.total_linhas_lidas || (resultado.itens_dre?.length || 0) + (resultado.contas_detalhadas?.length || 0);
        setMensagemSucesso(`Documento "${file.name}" processado e conglutinado na Matriz da Empresa com sucesso! ${total} contas identificadas.`);
        setTimeout(() => setMensagemSucesso(''), 6000);
      }, 500);
    } catch (err) {
      clearTimeout(timer1);
      clearTimeout(timer2);
      setProcessandoModal(false);
      alert('Erro ao processar o arquivo. Certifique-se de que o documento contém dados contábeis legíveis.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const formatarMoeda = (val: number) => {
    return val.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  };

  const indicesExibicao = (data?.indicadores_por_periodo && periodoAtivo !== 'todos_trimestres')
    ? (data.indicadores_por_periodo[periodoAtivo] || data.indices_financeiros)
    : (data?.indices_financeiros || {
        estrutura: { ativo_total: 0, passivo_exigivel: 0, patrimonio_liquido: 0 },
        liquidez: { liquidez_corrente: 0, liquidez_seca: 0, liquidez_imediata: 0, liquidez_geral: 0 },
        rentabilidade: { margem_bruta_pct: 0, margem_operacional_pct: 0, margem_ebitda_pct: 0, margem_liquida_pct: 0, roe_pct: 0, roa_pct: 0 },
        endividamento: { endividamento_geral_pct: 0, composicao_divida_curto_prazo_pct: 0, imobilizacao_pl_pct: 0 }
      });

  const fatorPeriodo = periodoAtivo === '1T' ? 0.22 : (periodoAtivo === '2T' ? 0.24 : (periodoAtivo === '3T' ? 0.26 : (periodoAtivo === '4T' ? 0.28 : 1.0)));
  const receitaPeriodo = (data?.totais_dre.receita_bruta || 0) * (periodoAtivo === 'todos_trimestres' || periodoAtivo === 'anual' ? 1 : fatorPeriodo);
  const lucroPeriodo = (data?.totais_dre.lucro_liquido || 0) * (periodoAtivo === 'todos_trimestres' || periodoAtivo === 'anual' ? 1 : fatorPeriodo);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-white">
      
      {/* Cabeçalho com Seletor de Trimestres */}
      <Header 
        onUpload={handleUpload} 
        isLoading={isLoading} 
        jevStatus={jevStatus}
        periodoAtivo={periodoAtivo}
        onSelecionarPeriodo={setPeriodoAtivo}
        onAbrirEnsinoJev={() => setActiveTab('ensino_jev')}
      />

      {/* Conteúdo Principal */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        
        {mensagemSucesso && (
          <div className="flex items-center justify-between p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs shadow-lg animate-fade-in">
            <div className="flex items-center gap-2 font-medium">
              <span className="text-base">✅</span>
              <span>{mensagemSucesso}</span>
            </div>
            <button 
              onClick={() => setMensagemSucesso('')}
              className="text-emerald-400 hover:text-white font-bold ml-4"
            >
              ✕
            </button>
          </div>
        )}

        {/* Modal de Processamento em Tempo Real */}
        {processandoModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/85 backdrop-blur-md p-4">
            <div className="max-w-lg w-full bg-slate-900 border border-amber-500/40 rounded-2xl p-6 sm:p-8 shadow-2xl space-y-6">
              
              <div className="flex items-center space-x-4">
                <div className="h-14 w-14 rounded-2xl bg-gradient-to-tr from-amber-500 via-yellow-500 to-amber-600 flex items-center justify-center text-slate-950 font-bold text-2xl shadow-lg shadow-amber-500/30 animate-pulse">
                  ⚡🧠
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white flex items-center gap-2">
                    Conglutinação & Reconhecimento JEV
                  </h3>
                  <p className="text-xs text-slate-400 truncate max-w-xs">
                    Mapeando na Matriz da Empresa: <span className="text-amber-400 font-mono font-medium">{nomeArquivoProcessando}</span>
                  </p>
                </div>
              </div>

              {/* Barra de Progresso */}
              <div className="space-y-2">
                <div className="flex justify-between text-xs font-semibold">
                  <span className="text-slate-300">Progresso do Reconhecimento:</span>
                  <span className="text-amber-400 font-mono">{progresso}%</span>
                </div>
                <div className="h-2.5 w-full bg-slate-800 rounded-full overflow-hidden p-0.5 border border-slate-700">
                  <div 
                    className="h-full bg-gradient-to-r from-amber-500 via-yellow-500 to-emerald-500 rounded-full transition-all duration-500"
                    style={{ width: `${progresso}%` }}
                  ></div>
                </div>
              </div>

              {/* Etapas de Processamento */}
              <div className="space-y-3 bg-slate-950/60 p-4 rounded-xl border border-slate-800 text-xs">
                <div className={`flex items-center gap-3 transition-colors ${etapaAtual >= 1 ? 'text-amber-300 font-semibold' : 'text-slate-500'}`}>
                  <span>{etapaAtual > 1 ? '✅' : (etapaAtual === 1 ? '⏳' : '⚪')}</span>
                  <span>1. Recepção do documento e identificação de rubricas contábeis</span>
                </div>
                <div className={`flex items-center gap-3 transition-colors ${etapaAtual >= 2 ? 'text-amber-300 font-semibold' : 'text-slate-500'}`}>
                  <span>{etapaAtual > 2 ? '✅' : (etapaAtual === 2 ? '⏳' : '⚪')}</span>
                  <span>2. Mapeamento dos 4 trimestres (3º Trim, 4º Trim e Total)</span>
                </div>
                <div className={`flex items-center gap-3 transition-colors ${etapaAtual >= 3 ? 'text-amber-300 font-semibold' : 'text-slate-500'}`}>
                  <span>{etapaAtual > 3 ? '✅' : (etapaAtual === 3 ? '⏳' : '⚪')}</span>
                  <span>3. Conglutinação semântica na Matriz DRE Oficial da Empresa</span>
                </div>
                <div className={`flex items-center gap-3 transition-colors ${etapaAtual >= 4 ? 'text-amber-300 font-semibold' : 'text-slate-500'}`}>
                  <span>{etapaAtual >= 4 ? '✅' : '⚪'}</span>
                  <span>4. Consolidação de subtotais, Análise Vertical (% AV) e tendências</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {isLoading && !data && (
          <div className="flex flex-col items-center justify-center h-96 space-y-4">
            <Loader2 className="h-10 w-10 text-amber-400 animate-spin" />
            <p className="text-sm font-semibold text-slate-300 flex items-center gap-2">
              <span>⚡🧠</span> Conglutinando DRE na Matriz Corporativa com TypeSafe JEV...
            </p>
          </div>
        )}

        {data && (
          <>
            {/* KPI Cards de Topo */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <KpiCard
                titulo="Receita Bruta"
                valor={formatarMoeda(receitaPeriodo)}
                subtitulo={periodoAtivo === 'todos_trimestres' ? 'Exercício Completo' : `Faturamento no ${periodoAtivo}`}
                variacao={21.5}
                tipoVariacao="positivo"
                badge="DRE"
                icone={<TrendingUp className="h-5 w-5" />}
              />
              <KpiCard
                titulo="Lucro Líquido"
                valor={formatarMoeda(lucroPeriodo)}
                subtitulo={periodoAtivo === 'todos_trimestres' ? 'Exercício Completo' : `Resultado no ${periodoAtivo}`}
                variacao={18.2}
                tipoVariacao="positivo"
                badge="Lucro"
                icone={<DollarSign className="h-5 w-5" />}
              />
              <KpiCard
                titulo={data.somente_dre ? "Margem Líquida" : "Ativo Total"}
                valor={data.somente_dre ? `${indicesExibicao.rentabilidade.margem_liquida_pct}%` : formatarMoeda(data.totais_balanco.ativo_total)}
                subtitulo={data.somente_dre ? "Eficiência operacional" : "Patrimônio sob gestão"}
                variacao={12.8}
                tipoVariacao="positivo"
                badge={data.somente_dre ? "Rentabilidade" : "Balanço"}
                icone={<Building2 className="h-5 w-5" />}
              />
              <KpiCard
                titulo={data.somente_dre ? "Margem EBITDA" : "Retorno s/ PL (ROE)"}
                valor={data.somente_dre ? `${indicesExibicao.rentabilidade.margem_ebitda_pct}%` : `${indicesExibicao.rentabilidade.roe_pct}% a.a.`}
                subtitulo={data.somente_dre ? "Geração de Caixa" : "Remuneração dos acionistas"}
                badge="⚡🧠 JEV"
                icone={<Percent className="h-5 w-5" />}
              />
            </div>

            {/* Navegação por Abas Principais */}
            <div className="flex items-center space-x-2 border-b border-slate-800 pb-2 overflow-x-auto">
              <button
                onClick={() => setActiveTab('matriz')}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all shrink-0 ${
                  activeTab === 'matriz'
                    ? 'bg-gradient-to-r from-amber-500 via-amber-600 to-yellow-600 text-slate-950 font-black shadow-lg shadow-amber-500/25'
                    : 'bg-slate-900/50 hover:bg-slate-800 text-slate-400 hover:text-white'
                }`}
              >
                <span>🏢 Matriz DRE da Empresa</span>
              </button>

              <button
                onClick={() => setActiveTab('ensino_jev')}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all shrink-0 ${
                  activeTab === 'ensino_jev'
                    ? 'bg-gradient-to-r from-cyan-500 via-blue-600 to-indigo-600 text-white font-black shadow-lg shadow-cyan-500/30 ring-2 ring-cyan-400/40'
                    : 'bg-cyan-950/30 hover:bg-cyan-900/40 text-cyan-300 border border-cyan-500/30 hover:text-white'
                }`}
              >
                <Brain className="h-4 w-4" />
                <span>Módulo de Ensino JEV (De-Para)</span>
              </button>

              <button
                onClick={() => setActiveTab('acionistas')}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all shrink-0 ${
                  activeTab === 'acionistas'
                    ? 'bg-gradient-to-r from-cyan-600 via-indigo-600 to-blue-600 text-white shadow-lg shadow-cyan-500/25'
                    : 'bg-slate-900/50 hover:bg-slate-800 text-slate-400 hover:text-white'
                }`}
              >
                <Award className="h-4 w-4" />
                <span>Parecer de Gestão & Acionistas</span>
              </button>

              <button
                onClick={() => setActiveTab('balanco')}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all shrink-0 ${
                  activeTab === 'balanco'
                    ? 'bg-gradient-to-r from-cyan-600 via-indigo-600 to-blue-600 text-white shadow-lg shadow-cyan-500/25'
                    : 'bg-slate-900/50 hover:bg-slate-800 text-slate-400 hover:text-white'
                }`}
              >
                <Building2 className="h-4 w-4" />
                <span>Balanço Patrimonial</span>
              </button>

              <button
                onClick={() => setActiveTab('dre')}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all shrink-0 ${
                  activeTab === 'dre'
                    ? 'bg-gradient-to-r from-cyan-600 via-indigo-600 to-blue-600 text-white shadow-lg shadow-cyan-500/25'
                    : 'bg-slate-900/50 hover:bg-slate-800 text-slate-400 hover:text-white'
                }`}
              >
                <FileSpreadsheet className="h-4 w-4" />
                <span>DRE Tradicional</span>
              </button>

              <button
                onClick={() => setActiveTab('indices')}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all shrink-0 ${
                  activeTab === 'indices'
                    ? 'bg-gradient-to-r from-cyan-600 via-indigo-600 to-blue-600 text-white shadow-lg shadow-cyan-500/25'
                    : 'bg-slate-900/50 hover:bg-slate-800 text-slate-400 hover:text-white'
                }`}
              >
                <PieChart className="h-4 w-4" />
                <span>Indicadores Financeiros</span>
              </button>
            </div>

            {/* Conteúdo da Aba Ativa */}
            <div className="transition-all duration-300">
              {activeTab === 'matriz' && (
                <DreMatrizView
                  matriz={data.dre_matriz_empresa}
                />
              )}

              {activeTab === 'ensino_jev' && (
                <EnsinoJevView />
              )}

              {activeTab === 'acionistas' && (
                <AcionistasReport
                  destaques={data.destaques_acionistas}
                  indices={indicesExibicao}
                  parecerGestao={data.parecer_gestao_jev}
                  totais={{
                    receita_bruta: receitaPeriodo,
                    lucro_liquido: lucroPeriodo,
                    ativo_total: data.totais_balanco.ativo_total,
                    patrimonio_liquido: data.totais_balanco.patrimonio_liquido
                  }}
                />
              )}

              {activeTab === 'balanco' && (
                <BalancoView
                  contas={data.contas_detalhadas}
                  periodoAtivo={periodoAtivo}
                  totais={data.totais_balanco}
                />
              )}

              {activeTab === 'dre' && (
                <DreView
                  itens={data.itens_dre}
                  periodoAtivo={periodoAtivo}
                  totais={{
                    receita_bruta: receitaPeriodo,
                    lucro_liquido: lucroPeriodo
                  }}
                />
              )}

              {activeTab === 'indices' && (
                <IndicesView
                  indices={indicesExibicao}
                  periodoAtivo={periodoAtivo}
                  indicadoresPorPeriodo={data.indicadores_por_periodo}
                />
              )}
            </div>
          </>
        )}

      </main>

      {/* Rodapé Executivo */}
      <footer className="border-t border-slate-800/80 bg-slate-950/60 py-6 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row justify-between items-center gap-4 text-xs text-slate-500">
          <div className="flex items-center gap-2">
            <span>⚡🧠 Sistema de Demonstrações Financeiras & Acionistas</span>
            <span>•</span>
            <span className="text-cyan-400 font-medium">TypeSafe JEV Engine</span>
          </div>
          <div>
            <span>Gestão Contábil Confiável, Matriz Corporativa Conglutinada & Padrão Zero Trust</span>
          </div>
        </div>
      </footer>

    </div>
  );
};

export default App;

