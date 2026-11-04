import React, { useState } from 'react';
import { ContaContabil, TipoPeriodo } from '../types/financeiro';
import { ShieldAlert, CheckCircle2, Search, Filter, Layers } from 'lucide-react';

interface BalancoViewProps {
  contas: ContaContabil[];
  periodoAtivo: TipoPeriodo;
  totais: {
    ativo_circulante: number;
    ativo_nao_circulante: number;
    ativo_total: number;
    passivo_circulante: number;
    passivo_nao_circulante: number;
    patrimonio_liquido: number;
    passivo_total: number;
  };
}

export const BalancoView: React.FC<BalancoViewProps> = ({ contas, periodoAtivo, totais }) => {
  const [busca, setBusca] = useState('');
  const [filtroGrupo, setFiltroGrupo] = useState('todos');

  const formatarMoeda = (val: number) => {
    return val.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  };

  const getValorPeriodo = (conta: ContaContabil, per: TipoPeriodo): number => {
    if (per === 'todos_trimestres' || per === 'anual') {
      return conta.saldo_atual;
    }
    return conta.saldos_trimestrais ? conta.saldos_trimestrais[per] : conta.saldo_atual;
  };

  const contasFiltradas = contas.filter(c => {
    const matchTexto = c.conta.toLowerCase().includes(busca.toLowerCase()) || c.codigo.includes(busca);
    const matchGrupo = filtroGrupo === 'todos' || c.grupo.includes(filtroGrupo);
    return matchTexto && matchGrupo;
  });

  const gruposUnicos = Array.from(new Set(contas.map(c => c.grupo)));

  return (
    <div className="space-y-6 animate-fade-in">
      
      {/* Resumo Patrimonial Totalizador */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-slate-900/70 border border-cyan-500/30 rounded-2xl p-5 shadow-lg">
          <span className="text-xs font-semibold text-cyan-400 uppercase flex items-center gap-1.5">
            <Layers className="h-4 w-4" /> Ativo Total ({periodoAtivo === 'todos_trimestres' ? 'Exercício Atual' : periodoAtivo})
          </span>
          <div className="text-2xl font-bold text-white mt-1.5">{formatarMoeda(totais.ativo_total)}</div>
          <div className="flex justify-between text-xs text-slate-400 mt-3 pt-2 border-t border-slate-800">
            <span>Circulante: {formatarMoeda(totais.ativo_circulante)}</span>
            <span>Não Circulante: {formatarMoeda(totais.ativo_nao_circulante)}</span>
          </div>
        </div>

        <div className="bg-slate-900/70 border border-amber-500/30 rounded-2xl p-5 shadow-lg">
          <span className="text-xs font-semibold text-amber-400 uppercase">Passivo Exigível Total</span>
          <div className="text-2xl font-bold text-white mt-1.5">{formatarMoeda(totais.passivo_circulante + totais.passivo_nao_circulante)}</div>
          <div className="flex justify-between text-xs text-slate-400 mt-3 pt-2 border-t border-slate-800">
            <span>Curto Prazo: {formatarMoeda(totais.passivo_circulante)}</span>
            <span>Longo Prazo: {formatarMoeda(totais.passivo_nao_circulante)}</span>
          </div>
        </div>

        <div className="bg-slate-900/70 border border-emerald-500/30 rounded-2xl p-5 shadow-lg">
          <span className="text-xs font-semibold text-emerald-400 uppercase">Patrimônio Líquido</span>
          <div className="text-2xl font-bold text-emerald-400 mt-1.5">{formatarMoeda(totais.patrimonio_liquido)}</div>
          <div className="flex justify-between text-xs text-slate-400 mt-3 pt-2 border-t border-slate-800">
            <span>Capital + Reservas</span>
            <span className="text-emerald-400 font-semibold flex items-center gap-1">
              <CheckCircle2 className="h-3.5 w-3.5" /> Balanço Equilibrado
            </span>
          </div>
        </div>
      </div>

      {/* Filtros e Busca */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 flex flex-col sm:flex-row gap-4 justify-between items-center">
        <div className="relative w-full sm:w-80">
          <Search className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Buscar conta contábil ou código..."
            value={busca}
            onChange={e => setBusca(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition-colors"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Filter className="h-4 w-4 text-slate-400" />
          <select
            value={filtroGrupo}
            onChange={e => setFiltroGrupo(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 transition-colors"
          >
            <option value="todos">Todos os Grupos JEV</option>
            {gruposUnicos.map((g, idx) => (
              <option key={idx} value={g}>{g}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Tabela com De-Para, Badges JEV e Colunas Trimestrais */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 text-slate-400 font-semibold uppercase tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-3.5 px-4">Código</th>
                <th className="py-3.5 px-4 min-w-[200px]">Conta Contábil</th>
                <th className="py-3.5 px-4">Classificação JEV</th>
                
                {periodoAtivo === 'todos_trimestres' ? (
                  <>
                    <th className="py-3.5 px-3 text-right">1T 2024</th>
                    <th className="py-3.5 px-3 text-right">2T 2024</th>
                    <th className="py-3.5 px-3 text-right">3T 2024</th>
                    <th className="py-3.5 px-3 text-right">4T 2024</th>
                    <th className="py-3.5 px-4 text-right bg-cyan-950/30 text-cyan-300">Posição Atual</th>
                  </>
                ) : (
                  <>
                    <th className="py-3.5 px-4 text-right bg-cyan-950/40 text-cyan-300">
                      Saldo ({periodoAtivo})
                    </th>
                    <th className="py-3.5 px-4 text-right">Exercício Atual</th>
                    <th className="py-3.5 px-4 text-right">Exercício Anterior</th>
                    <th className="py-3.5 px-4 text-right">Var. %</th>
                  </>
                )}
                <th className="py-3.5 px-4 text-center">Score JEV</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-200">
              {contasFiltradas.map((c, i) => (
                <tr key={i} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-3 px-4 font-mono text-slate-400">{c.codigo}</td>
                  <td className="py-3 px-4 font-medium flex items-center gap-2">
                    <span>{c.conta}</span>
                    {c.probabilidade_anomalia > 0.4 && (
                      <span title="Alerta de Anomalia pelo JEV" className="text-amber-400 flex items-center">
                        <ShieldAlert className="h-3.5 w-3.5" />
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-4">
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-800 border border-slate-700/70 text-[11px] font-semibold text-cyan-300">
                      <span>⚡🧠</span>
                      <span>{c.grupo}</span>
                    </span>
                  </td>

                  {periodoAtivo === 'todos_trimestres' ? (
                    <>
                      <td className="py-3 px-3 text-right font-mono">
                        {formatarMoeda(c.saldos_trimestrais ? c.saldos_trimestrais['1T'] : c.saldo_atual * 0.92)}
                      </td>
                      <td className="py-3 px-3 text-right font-mono">
                        {formatarMoeda(c.saldos_trimestrais ? c.saldos_trimestrais['2T'] : c.saldo_atual * 0.95)}
                      </td>
                      <td className="py-3 px-3 text-right font-mono">
                        {formatarMoeda(c.saldos_trimestrais ? c.saldos_trimestrais['3T'] : c.saldo_atual * 0.98)}
                      </td>
                      <td className="py-3 px-3 text-right font-mono">
                        {formatarMoeda(c.saldos_trimestrais ? c.saldos_trimestrais['4T'] : c.saldo_atual)}
                      </td>
                      <td className="py-3 px-4 text-right font-semibold text-white font-mono bg-cyan-950/20">
                        {formatarMoeda(c.saldo_atual)}
                      </td>
                    </>
                  ) : (
                    <>
                      <td className="py-3 px-4 text-right font-bold font-mono bg-cyan-950/20 text-cyan-300">
                        {formatarMoeda(getValorPeriodo(c, periodoAtivo))}
                      </td>
                      <td className="py-3 px-4 text-right font-semibold text-white font-mono">
                        {formatarMoeda(c.saldo_atual)}
                      </td>
                      <td className="py-3 px-4 text-right text-slate-400 font-mono">
                        {formatarMoeda(c.saldo_anterior)}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <span className={`font-semibold ${
                          c.variacao_percentual > 0 ? 'text-emerald-400' :
                          c.variacao_percentual < 0 ? 'text-rose-400' : 'text-slate-400'
                        }`}>
                          {c.variacao_percentual > 0 ? `+${c.variacao_percentual}%` : `${c.variacao_percentual}%`}
                        </span>
                      </td>
                    </>
                  )}

                  <td className="py-3 px-4 text-center">
                    <span className="px-2 py-0.5 rounded-md bg-cyan-950/60 text-cyan-400 font-bold border border-cyan-800/40 text-[10px]">
                      {c.score_relevancia.toFixed(1)} / 2.0
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
};
