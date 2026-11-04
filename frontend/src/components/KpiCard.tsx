import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface KpiCardProps {
  titulo: string;
  valor: string;
  subtitulo?: string;
  variacao?: number;
  tipoVariacao?: 'positivo' | 'negativo' | 'neutro';
  icone?: React.ReactNode;
  badge?: string;
}

export const KpiCard: React.FC<KpiCardProps> = ({
  titulo,
  valor,
  subtitulo,
  variacao,
  tipoVariacao,
  icone,
  badge
}) => {
  return (
    <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-5 hover:border-slate-700/80 transition-all duration-300 shadow-lg shadow-black/20 relative overflow-hidden group">
      <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-br from-cyan-500/5 to-transparent rounded-bl-full pointer-events-none group-hover:from-cyan-500/10 transition-colors"></div>
      
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{titulo}</span>
        {icone && (
          <div className="p-2 rounded-xl bg-slate-800/80 border border-slate-700/50 text-cyan-400">
            {icone}
          </div>
        )}
      </div>

      <div className="flex items-baseline justify-between">
        <h3 className="text-2xl font-bold text-white tracking-tight">{valor}</h3>
        {badge && (
          <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-300">
            {badge}
          </span>
        )}
      </div>

      {(subtitulo || variacao !== undefined) && (
        <div className="mt-3 flex items-center justify-between text-xs text-slate-400 pt-2 border-t border-slate-800/60">
          <span>{subtitulo}</span>
          {variacao !== undefined && (
            <div className={`flex items-center gap-1 font-semibold ${
              tipoVariacao === 'positivo' ? 'text-emerald-400' :
              tipoVariacao === 'negativo' ? 'text-rose-400' : 'text-slate-400'
            }`}>
              {variacao > 0 ? <TrendingUp className="h-3.5 w-3.5" /> :
               variacao < 0 ? <TrendingDown className="h-3.5 w-3.5" /> :
               <Minus className="h-3.5 w-3.5" />}
              <span>{variacao > 0 ? `+${variacao}%` : `${variacao}%`}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
