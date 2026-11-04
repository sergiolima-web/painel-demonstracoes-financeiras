import React from 'react';
import { ContaContabil, IndicesFinanceiros, SolucoesGestaoJev } from '../types/financeiro';
import { 
  Award, 
  Zap, 
  TrendingUp, 
  ShieldCheck, 
  FileText, 
  CheckCircle, 
  Wallet, 
  ArrowRight,
  Target,
  Sparkles
} from 'lucide-react';

interface AcionistasReportProps {
  destaques: ContaContabil[];
  indices: IndicesFinanceiros;
  parecerGestao?: SolucoesGestaoJev;
  totais: {
    receita_bruta: number;
    lucro_liquido: number;
    ativo_total: number;
    patrimonio_liquido: number;
  };
}

export const AcionistasReport: React.FC<AcionistasReportProps> = ({
  destaques,
  indices,
  parecerGestao,
  totais
}) => {
  const formatarMoeda = (val: number) => {
    return val.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  };

  const score = parecerGestao?.score_saude || 88;
  const rating = parecerGestao?.rating || 'AAA - Excelente Solvência';
  const parecerTexto = parecerGestao?.parecer_sintese || 
    'A empresa apresenta saúde financeira de alto padrão, robusta geração de caixa operacional e estrutura de capital amplamente protegida.';

  return (
    <div className="space-y-8 animate-fade-in">
      
      {/* Banner Principal com Score de Saúde e Rating Executivo JEV */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-900/95 to-slate-950 border border-cyan-500/30 rounded-3xl p-6 md:p-8 shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 p-8 opacity-10 pointer-events-none">
          <Award className="w-72 h-72 text-cyan-400" />
        </div>

        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/15 border border-cyan-400/30 text-cyan-300 text-xs font-bold mb-3 shadow-sm">
              <Sparkles className="h-3.5 w-3.5 text-cyan-400" />
              <span>⚡🧠 Parecer de Gestão & Decisão Estratégica JEV</span>
            </div>

            <h2 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
              Diagnóstico de Gestão & Criação de Valor
            </h2>
            <p className="text-sm text-slate-300 mt-2 leading-relaxed">
              {parecerTexto}
            </p>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6 pt-6 border-t border-slate-800">
              <div className="bg-slate-950/50 p-3 rounded-xl border border-slate-800/80">
                <span className="text-[11px] text-slate-400 uppercase font-semibold">ROE dos Sócios</span>
                <div className="text-xl font-bold text-emerald-400 mt-0.5">{indices.rentabilidade.roe_pct}% a.a.</div>
              </div>
              <div className="bg-slate-950/50 p-3 rounded-xl border border-slate-800/80">
                <span className="text-[11px] text-slate-400 uppercase font-semibold">Liquidez Corrente</span>
                <div className="text-xl font-bold text-cyan-400 mt-0.5">{indices.liquidez.liquidez_corrente}x</div>
              </div>
              <div className="bg-slate-950/50 p-3 rounded-xl border border-slate-800/80">
                <span className="text-[11px] text-slate-400 uppercase font-semibold">Margem Líquida</span>
                <div className="text-xl font-bold text-indigo-300 mt-0.5">{indices.rentabilidade.margem_liquida_pct}%</div>
              </div>
              <div className="bg-slate-950/50 p-3 rounded-xl border border-slate-800/80">
                <span className="text-[11px] text-slate-400 uppercase font-semibold">Lucro Líquido</span>
                <div className="text-xl font-bold text-emerald-400 mt-0.5">{formatarMoeda(totais.lucro_liquido)}</div>
              </div>
            </div>
          </div>

          {/* Card Flutuante de Score & Rating */}
          <div className="bg-slate-950/80 border border-slate-800 rounded-2xl p-6 text-center min-w-[240px] shadow-xl flex flex-col items-center justify-center">
            <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Rating de Solvência</span>
            <div className="mt-2 text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">
              {score}
              <span className="text-lg text-slate-500 font-normal">/100</span>
            </div>
            <div className="mt-2 px-3 py-1 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-xs font-bold">
              {rating}
            </div>
            <p className="text-[11px] text-slate-400 mt-3 max-w-[200px]">
              Avaliado com base em liquidez, margens, CCL e retorno real ao capital.
            </p>
          </div>
        </div>
      </div>

      {/* 4 Pilares de Soluções de Gestão Confiáveis JEV */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Target className="h-5 w-5 text-cyan-400" />
              <span>4 Pilares de Soluções de Gestão Confiáveis</span>
            </h3>
            <p className="text-xs text-slate-400">Diretrizes práticas de tomada de decisão estruturadas pelo JEV Engine</p>
          </div>
          <span className="text-xs font-semibold px-2.5 py-1 rounded-lg bg-slate-800 text-slate-300 border border-slate-700">
            ⚡🧠 Management Matrix
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {(parecerGestao?.pilares_gestao || []).map((pilar) => (
            <div 
              key={pilar.id} 
              className="bg-slate-900/70 border border-slate-800 hover:border-slate-700 transition-all rounded-2xl p-5 shadow-lg space-y-3"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="h-8 w-8 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 font-bold">
                    {pilar.id === 'tesouraria' && <Wallet className="h-4 w-4" />}
                    {pilar.id === 'estrutura_capital' && <ShieldCheck className="h-4 w-4" />}
                    {pilar.id === 'eficiencia_margens' && <TrendingUp className="h-4 w-4" />}
                    {pilar.id === 'retorno_dividendos' && <Award className="h-4 w-4" />}
                  </div>
                  <h4 className="font-bold text-xs text-white">{pilar.titulo}</h4>
                </div>
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                  pilar.status === 'Excelente' || pilar.status === 'Controlado' || pilar.status === 'Alta' || pilar.status === 'Atrativo'
                    ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                    : 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                }`}>
                  {pilar.status}
                </span>
              </div>

              <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80 text-xs text-slate-300">
                <span className="text-slate-400 font-semibold block text-[11px]">Diagnóstico:</span>
                {pilar.diagnostico}
              </div>

              <div className="p-3 rounded-xl bg-cyan-950/20 border border-cyan-500/20 text-xs text-cyan-200">
                <strong className="text-cyan-300 flex items-center gap-1 mb-1 font-semibold">
                  <CheckCircle className="h-3.5 w-3.5 text-cyan-400" /> Solução Recomendada de Gestão:
                </strong>
                {pilar.solucao_confiavel}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Sazonalidade Trimestral & Plano de Ação Estratégico */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Análise de Sazonalidade dos 4 Trimestres */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-emerald-400" />
              <span>Evolução & Sazonalidade dos 4 Trimestres</span>
            </h3>
            <span className="text-xs text-slate-400 font-mono">1T a 4T</span>
          </div>

          <p className="text-xs text-slate-300">
            {parecerGestao?.sazonalidade_trimestral?.resumo || 'Comportamento operacional saudável nos 4 trimestres do exercício.'}
          </p>

          <div className="grid grid-cols-2 gap-3">
            {(parecerGestao?.sazonalidade_trimestral?.destaques || [
              { trimestre: '1T', foco: 'Início do ciclo e montagem de estoques', ritmo: 'Estável' },
              { trimestre: '2T', foco: 'Aceleração de entregas comerciais', ritmo: 'Crescente' },
              { trimestre: '3T', foco: 'Expansão de margem e ganho de escala', ritmo: 'Forte' },
              { trimestre: '4T', foco: 'Pico de faturamento e lucro acumulado', ritmo: 'Excelente' },
            ]).map((t, idx) => (
              <div key={idx} className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="font-extrabold text-sm text-cyan-400">{t.trimestre}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-semibold">{t.ritmo}</span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-1.5 leading-tight">{t.foco}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Plano de Ação Estratégico Priorizado */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <FileText className="h-4 w-4 text-amber-400" />
              <span>Roadmap de Ações para a Diretoria</span>
            </h3>
            <span className="text-xs text-cyan-400 font-semibold">Priorizado</span>
          </div>

          <div className="space-y-3">
            {(parecerGestao?.plano_acao || [
              { ordem: 1, acao: 'Otimização de Capital de Giro', prazo: '30 dias', responsavel: 'Tesouraria', impacto: 'Alto', detalhe: 'Sincronizar prazos de clientes e fornecedores.' },
              { ordem: 2, acao: 'Alongamento de Dívidas', prazo: '60 dias', responsavel: 'Controladoria', impacto: 'Alto', detalhe: 'Trocar passivo de curto por longo prazo.' },
              { ordem: 3, acao: 'Controle Orçamentário SG&A', prazo: '90 dias', responsavel: 'Operações', impacto: 'Médio', detalhe: 'Travas trimestrais de despesas fixas.' }
            ]).map((item) => (
              <div key={item.ordem} className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex items-start gap-3">
                <div className="h-6 w-6 rounded-full bg-cyan-500/20 border border-cyan-500/40 text-cyan-300 font-bold text-xs flex items-center justify-center shrink-0 mt-0.5">
                  {item.ordem}
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-xs text-white">{item.acao}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 font-semibold">{item.prazo}</span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-1">{item.detalhe}</p>
                  <div className="text-[10px] text-slate-500 mt-1">Responsável: <span className="text-slate-300 font-medium">{item.responsavel}</span></div>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>

      {/* Contas de Maior Relevância Estratégica (Destaques JEV) */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Zap className="h-4 w-4 text-cyan-400" />
            <span>Rubricas Contábeis de Maior Impacto Estratégico</span>
          </h3>
          <span className="text-xs text-slate-400 font-mono">⚡🧠 JEV Score</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {destaques.map((conta, idx) => (
            <div key={idx} className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3.5 flex flex-col justify-between space-y-2">
              <div>
                <div className="font-semibold text-xs text-white">{conta.conta}</div>
                <div className="text-[11px] text-cyan-400 mt-0.5">{conta.grupo}</div>
              </div>
              <div className="flex items-center justify-between pt-2 border-t border-slate-800/60">
                <div className="text-xs font-bold text-white">{formatarMoeda(conta.saldo_atual)}</div>
                <div className="text-[10px] text-slate-400">
                  Var: <span className={conta.variacao_percentual >= 0 ? 'text-emerald-400' : 'text-rose-400'}>
                    {conta.variacao_percentual > 0 ? `+${conta.variacao_percentual}%` : `${conta.variacao_percentual}%`}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
};
