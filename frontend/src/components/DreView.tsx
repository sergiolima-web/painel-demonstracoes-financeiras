import React from 'react';
import { ItemDre, TipoPeriodo } from '../types/financeiro';
import { TrendingUp, BarChart3, ArrowRight, DollarSign } from 'lucide-react';

interface DreViewProps {
  itens: ItemDre[];
  periodoAtivo: TipoPeriodo;
  totais: {
    receita_bruta: number;
    lucro_liquido: number;
  };
}

export const DreView: React.FC<DreViewProps> = ({ itens, periodoAtivo, totais }) => {
  const formatarMoeda = (val: number) => {
    return val.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  };

  const getValorPeriodo = (item: ItemDre, per: TipoPeriodo): number => {
    if (per === 'todos_trimestres' || per === 'anual') {
      return item.saldo_atual;
    }
    return item.saldos_trimestrais ? item.saldos_trimestrais[per] : item.saldo_atual * 0.25;
  };

  return (
    <div className="space-y-6 animate-fade-in">
      
      {/* Cards de Resumo da DRE */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-slate-900/70 border border-cyan-500/30 rounded-2xl p-5 shadow-lg">
          <span className="text-xs font-semibold text-cyan-400 uppercase flex items-center gap-1.5">
            <DollarSign className="h-4 w-4" /> Receita Bruta ({periodoAtivo === 'todos_trimestres' ? 'Exercício Completo' : periodoAtivo})
          </span>
          <div className="text-2xl font-bold text-white mt-1.5">{formatarMoeda(totais.receita_bruta)}</div>
          <p className="text-xs text-slate-400 mt-2">Volume operacional de faturamento apurado</p>
        </div>

        <div className="bg-slate-900/70 border border-emerald-500/30 rounded-2xl p-5 shadow-lg">
          <span className="text-xs font-semibold text-emerald-400 uppercase flex items-center gap-1.5">
            <TrendingUp className="h-4 w-4" /> Lucro Líquido ({periodoAtivo === 'todos_trimestres' ? 'Exercício Completo' : periodoAtivo})
          </span>
          <div className="text-2xl font-bold text-emerald-400 mt-1.5">{formatarMoeda(totais.lucro_liquido)}</div>
          <p className="text-xs text-slate-400 mt-2">Resultado final líquido após tributos e despesas</p>
        </div>

        <div className="bg-slate-900/70 border border-indigo-500/30 rounded-2xl p-5 shadow-lg">
          <span className="text-xs font-semibold text-indigo-400 uppercase flex items-center gap-1.5">
            <BarChart3 className="h-4 w-4" /> Margem Líquida
          </span>
          <div className="text-2xl font-bold text-indigo-300 mt-1.5">
            {totais.receita_bruta > 0 ? ((totais.lucro_liquido / (totais.receita_bruta * 0.88)) * 100).toFixed(1) : '0.0'}%
          </div>
          <p className="text-xs text-slate-400 mt-2">Eficiência líquida gerada por real faturado</p>
        </div>
      </div>

      {/* Tabela DRE Gerencial Trimestral */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="p-4 border-b border-slate-800 flex flex-wrap justify-between items-center bg-slate-950/40 gap-2">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-bold text-white">Demonstração do Resultado do Exercício (DRE)</h3>
            <span className="px-2.5 py-0.5 rounded-full bg-cyan-950 border border-cyan-800/60 text-cyan-400 text-[10px] font-bold">
              {periodoAtivo === 'todos_trimestres' ? 'Visão 4 Trimestres & Total' : `Filtro: ${periodoAtivo}`}
            </span>
          </div>
          <span className="text-xs text-slate-400">Valores em Reais (R$)</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 text-slate-400 font-semibold uppercase tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-3.5 px-4">Código</th>
                <th className="py-3.5 px-4 min-w-[240px]">Estrutura de Resultados</th>
                
                {periodoAtivo === 'todos_trimestres' ? (
                  <>
                    <th className="py-3.5 px-3 text-right">1º Trim (1T)</th>
                    <th className="py-3.5 px-3 text-right">2º Trim (2T)</th>
                    <th className="py-3.5 px-3 text-right">3º Trim (3T)</th>
                    <th className="py-3.5 px-3 text-right">4º Trim (4T)</th>
                    <th className="py-3.5 px-4 text-right bg-cyan-950/30 text-cyan-300">Total Anual</th>
                  </>
                ) : (
                  <>
                    <th className="py-3.5 px-4 text-right bg-cyan-950/40 text-cyan-300">
                      Saldo ({periodoAtivo})
                    </th>
                    <th className="py-3.5 px-4 text-right">Total Exercício</th>
                    <th className="py-3.5 px-4 text-right">Exercício Anterior</th>
                    <th className="py-3.5 px-4 text-right">Variação %</th>
                  </>
                )}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-200">
              {itens.map((item, i) => {
                const isLucro = item.conta.toLowerCase().includes('lucro') || item.conta.toLowerCase().includes('resultado');
                const isReceita = item.conta.toLowerCase().includes('receita');
                const isNegativo = item.saldo_atual < 0;

                return (
                  <tr key={i} className={`hover:bg-slate-800/40 transition-colors ${
                    isLucro ? 'bg-emerald-950/20 font-bold text-emerald-200' :
                    isReceita ? 'bg-cyan-950/15 font-semibold text-cyan-100' : ''
                  }`}>
                    <td className="py-3 px-4 font-mono text-slate-400">{item.codigo}</td>
                    <td className="py-3 px-4 font-medium">{item.conta}</td>
                    
                    {periodoAtivo === 'todos_trimestres' ? (
                      <>
                        <td className="py-3 px-3 text-right font-mono">
                          {formatarMoeda(item.saldos_trimestrais ? item.saldos_trimestrais['1T'] : item.saldo_atual * 0.22)}
                        </td>
                        <td className="py-3 px-3 text-right font-mono">
                          {formatarMoeda(item.saldos_trimestrais ? item.saldos_trimestrais['2T'] : item.saldo_atual * 0.24)}
                        </td>
                        <td className="py-3 px-3 text-right font-mono">
                          {formatarMoeda(item.saldos_trimestrais ? item.saldos_trimestrais['3T'] : item.saldo_atual * 0.26)}
                        </td>
                        <td className="py-3 px-3 text-right font-mono">
                          {formatarMoeda(item.saldos_trimestrais ? item.saldos_trimestrais['4T'] : item.saldo_atual * 0.28)}
                        </td>
                        <td className={`py-3 px-4 text-right font-bold font-mono bg-cyan-950/20 ${
                          isNegativo ? 'text-rose-300' : 'text-white'
                        }`}>
                          {formatarMoeda(item.saldo_atual)}
                        </td>
                      </>
                    ) : (
                      <>
                        <td className="py-3 px-4 text-right font-bold font-mono bg-cyan-950/20 text-cyan-300">
                          {formatarMoeda(getValorPeriodo(item, periodoAtivo))}
                        </td>
                        <td className={`py-3 px-4 text-right font-semibold font-mono ${
                          isNegativo ? 'text-rose-300' : 'text-white'
                        }`}>
                          {formatarMoeda(item.saldo_atual)}
                        </td>
                        <td className="py-3 px-4 text-right text-slate-400 font-mono">
                          {formatarMoeda(item.saldo_anterior)}
                        </td>
                        <td className="py-3 px-4 text-right">
                          <span className={`font-semibold ${
                            item.variacao_percentual > 0 ? 'text-emerald-400' :
                            item.variacao_percentual < 0 ? 'text-rose-400' : 'text-slate-400'
                          }`}>
                            {item.variacao_percentual > 0 ? `+${item.variacao_percentual}%` : `${item.variacao_percentual}%`}
                          </span>
                        </td>
                      </>
                    )}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
};
