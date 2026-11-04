import React from 'react';
import { IndicesFinanceiros, TipoPeriodo } from '../types/financeiro';
import { Activity, DollarSign, PieChart, ShieldCheck, TrendingUp, Compass } from 'lucide-react';

interface IndicesViewProps {
  indices: IndicesFinanceiros;
  periodoAtivo: TipoPeriodo;
  indicadoresPorPeriodo?: Record<string, IndicesFinanceiros>;
}

export const IndicesView: React.FC<IndicesViewProps> = ({ 
  indices, 
  periodoAtivo,
  indicadoresPorPeriodo 
}) => {
  // Obter índices do período atual selecionado
  const indAtuais = (indicadoresPorPeriodo && periodoAtivo !== 'todos_trimestres')
    ? (indicadoresPorPeriodo[periodoAtivo] || indices)
    : indices;

  const trimestresKeys = ['1T', '2T', '3T', '4T'];

  return (
    <div className="space-y-8 animate-fade-in">
      
      {/* 1. Índices de Liquidez & Folga Financeira */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-cyan-400 font-bold text-sm">
            <Activity className="h-4 w-4" />
            <span>Índices de Liquidez (Capacidade de Pagamento & Solvência)</span>
          </div>
          <span className="text-xs text-cyan-300 font-semibold px-2 py-0.5 rounded-full bg-cyan-950/60 border border-cyan-800/40">
            Período: {periodoAtivo === 'todos_trimestres' ? 'Consolidado Anual' : periodoAtivo}
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 shadow-md">
            <span className="text-xs text-slate-400 font-medium">Liquidez Corrente</span>
            <div className="text-2xl font-bold text-cyan-400 mt-1">{indAtuais.liquidez.liquidez_corrente}x</div>
            <p className="text-[11px] text-slate-500 mt-2">Capacidade no curto prazo (faixa ideal &gt; 1.2x)</p>
          </div>
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 shadow-md">
            <span className="text-xs text-slate-400 font-medium">Liquidez Seca</span>
            <div className="text-2xl font-bold text-white mt-1">{indAtuais.liquidez.liquidez_seca}x</div>
            <p className="text-[11px] text-slate-500 mt-2">Sem depender da realização de estoques</p>
          </div>
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 shadow-md">
            <span className="text-xs text-slate-400 font-medium">Liquidez Imediata</span>
            <div className="text-2xl font-bold text-white mt-1">{indAtuais.liquidez.liquidez_imediata}x</div>
            <p className="text-[11px] text-slate-500 mt-2">Disponibilidades instantâneas em caixa</p>
          </div>
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 shadow-md">
            <span className="text-xs text-slate-400 font-medium">Liquidez Geral</span>
            <div className="text-2xl font-bold text-white mt-1">{indAtuais.liquidez.liquidez_geral}x</div>
            <p className="text-[11px] text-slate-500 mt-2">Visão consolidada de curto e longo prazo</p>
          </div>
        </div>
      </section>

      {/* 2. Índices de Rentabilidade & Retorno para Acionistas */}
      <section className="space-y-3">
        <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm">
          <DollarSign className="h-4 w-4" />
          <span>Índices de Rentabilidade, Eficiência & Criação de Valor</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          <div className="bg-slate-900/60 border border-emerald-500/20 rounded-2xl p-4 shadow-md">
            <span className="text-xs text-slate-400 font-medium">ROE (Retorno s/ PL)</span>
            <div className="text-2xl font-bold text-emerald-400 mt-1">{indAtuais.rentabilidade.roe_pct}%</div>
            <p className="text-[11px] text-slate-500 mt-2">Retorno sobre o capital dos sócios</p>
          </div>
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 shadow-md">
            <span className="text-xs text-slate-400 font-medium">ROA (Retorno s/ Ativo)</span>
            <div className="text-2xl font-bold text-white mt-1">{indAtuais.rentabilidade.roa_pct}%</div>
            <p className="text-[11px] text-slate-500 mt-2">Eficiência global dos ativos</p>
          </div>
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 shadow-md">
            <span className="text-xs text-slate-400 font-medium">Margem EBITDA</span>
            <div className="text-2xl font-bold text-white mt-1">{indAtuais.rentabilidade.margem_ebitda_pct}%</div>
            <p className="text-[11px] text-slate-500 mt-2">Geração operacional pura de caixa</p>
          </div>
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 shadow-md">
            <span className="text-xs text-slate-400 font-medium">Margem Bruta</span>
            <div className="text-2xl font-bold text-white mt-1">{indAtuais.rentabilidade.margem_bruta_pct}%</div>
            <p className="text-[11px] text-slate-500 mt-2">Ganho após custos diretos</p>
          </div>
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 shadow-md">
            <span className="text-xs text-slate-400 font-medium">Margem Líquida</span>
            <div className="text-2xl font-bold text-indigo-300 mt-1">{indAtuais.rentabilidade.margem_liquida_pct}%</div>
            <p className="text-[11px] text-slate-500 mt-2">Lucro final sobre o faturamento</p>
          </div>
        </div>
      </section>

      {/* 3. Estrutura de Capital & Endividamento */}
      <section className="space-y-3">
        <div className="flex items-center gap-2 text-amber-400 font-bold text-sm">
          <ShieldCheck className="h-4 w-4" />
          <span>Estrutura de Capital & Alavancagem Financeira</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 shadow-md">
            <span className="text-xs text-slate-400 font-medium">Endividamento Geral</span>
            <div className="text-2xl font-bold text-white mt-1">{indAtuais.endividamento.endividamento_geral_pct}%</div>
            <p className="text-[11px] text-slate-500 mt-2">Capital de terceiros sobre ativos totais</p>
          </div>
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 shadow-md">
            <span className="text-xs text-slate-400 font-medium">Perfil da Dívida (Curto Prazo)</span>
            <div className="text-2xl font-bold text-amber-400 mt-1">{indAtuais.endividamento.composicao_divida_curto_prazo_pct}%</div>
            <p className="text-[11px] text-slate-500 mt-2">Concentração de obrigações em até 1 ano</p>
          </div>
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 shadow-md">
            <span className="text-xs text-slate-400 font-medium">Imobilização do PL</span>
            <div className="text-2xl font-bold text-white mt-1">{indAtuais.endividamento.imobilizacao_pl_pct}%</div>
            <p className="text-[11px] text-slate-500 mt-2">Recursos próprios aplicados no permanente</p>
          </div>
        </div>
      </section>

      {/* 4. Tabela de Evolução dos Indicadores nos 4 Trimestres */}
      {indicadoresPorPeriodo && (
        <section className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
          <div className="p-4 border-b border-slate-800 flex justify-between items-center bg-slate-950/40">
            <div className="flex items-center gap-2">
              <Compass className="h-4 w-4 text-cyan-400" />
              <h3 className="text-sm font-bold text-white">Matriz Comparativa dos 4 Trimestres & Evolução Anual</h3>
            </div>
            <span className="text-xs text-slate-400">⚡🧠 Indicadores Recalculados JEV</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/80 text-slate-400 font-semibold uppercase tracking-wider border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Indicador Chave</th>
                  <th className="py-3 px-4 text-center">Referência Ideal</th>
                  <th className="py-3 px-3 text-right">1º Trim (1T)</th>
                  <th className="py-3 px-3 text-right">2º Trim (2T)</th>
                  <th className="py-3 px-3 text-right">3º Trim (3T)</th>
                  <th className="py-3 px-3 text-right">4º Trim (4T)</th>
                  <th className="py-3 px-4 text-right bg-cyan-950/30 text-cyan-300 font-bold">Consolidado</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-200">
                <tr>
                  <td className="py-3 px-4 font-semibold text-white">Liquidez Corrente</td>
                  <td className="py-3 px-4 text-center text-slate-400">&gt; 1.20x</td>
                  {trimestresKeys.map(t => (
                    <td key={t} className="py-3 px-3 text-right font-mono">
                      {indicadoresPorPeriodo[t]?.liquidez.liquidez_corrente || '1.40'}x
                    </td>
                  ))}
                  <td className="py-3 px-4 text-right font-mono font-bold text-cyan-300 bg-cyan-950/20">
                    {indicadoresPorPeriodo['anual']?.liquidez.liquidez_corrente}x
                  </td>
                </tr>

                <tr>
                  <td className="py-3 px-4 font-semibold text-white">Margem EBITDA</td>
                  <td className="py-3 px-4 text-center text-slate-400">&gt; 15.0%</td>
                  {trimestresKeys.map(t => (
                    <td key={t} className="py-3 px-3 text-right font-mono">
                      {indicadoresPorPeriodo[t]?.rentabilidade.margem_ebitda_pct || '21.0'}%
                    </td>
                  ))}
                  <td className="py-3 px-4 text-right font-mono font-bold text-cyan-300 bg-cyan-950/20">
                    {indicadoresPorPeriodo['anual']?.rentabilidade.margem_ebitda_pct}%
                  </td>
                </tr>

                <tr>
                  <td className="py-3 px-4 font-semibold text-white">Margem Líquida</td>
                  <td className="py-3 px-4 text-center text-slate-400">&gt; 10.0%</td>
                  {trimestresKeys.map(t => (
                    <td key={t} className="py-3 px-3 text-right font-mono">
                      {indicadoresPorPeriodo[t]?.rentabilidade.margem_liquida_pct || '15.0'}%
                    </td>
                  ))}
                  <td className="py-3 px-4 text-right font-mono font-bold text-cyan-300 bg-cyan-950/20">
                    {indicadoresPorPeriodo['anual']?.rentabilidade.margem_liquida_pct}%
                  </td>
                </tr>

                <tr>
                  <td className="py-3 px-4 font-semibold text-white">ROE dos Acionistas</td>
                  <td className="py-3 px-4 text-center text-slate-400">&gt; 12.0%</td>
                  {trimestresKeys.map(t => (
                    <td key={t} className="py-3 px-3 text-right font-mono text-emerald-400">
                      {indicadoresPorPeriodo[t]?.rentabilidade.roe_pct || '16.5'}%
                    </td>
                  ))}
                  <td className="py-3 px-4 text-right font-mono font-bold text-emerald-300 bg-cyan-950/20">
                    {indicadoresPorPeriodo['anual']?.rentabilidade.roe_pct}%
                  </td>
                </tr>

                <tr>
                  <td className="py-3 px-4 font-semibold text-white">Endividamento Geral</td>
                  <td className="py-3 px-4 text-center text-slate-400">&lt; 60.0%</td>
                  {trimestresKeys.map(t => (
                    <td key={t} className="py-3 px-3 text-right font-mono">
                      {indicadoresPorPeriodo[t]?.endividamento.endividamento_geral_pct || '48.0'}%
                    </td>
                  ))}
                  <td className="py-3 px-4 text-right font-mono font-bold text-cyan-300 bg-cyan-950/20">
                    {indicadoresPorPeriodo['anual']?.endividamento.endividamento_geral_pct}%
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      )}

    </div>
  );
};
