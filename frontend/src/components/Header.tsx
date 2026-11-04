import { Download, Upload, Cpu, Activity, FileText, Calendar, Brain } from 'lucide-react';
import { downloadModeloPlanilha, downloadModeloPdf } from '../services/api';
import { TipoPeriodo } from '../types/financeiro';

interface HeaderProps {
  onUpload: (file: File) => void;
  isLoading: boolean;
  jevStatus: { jev_habilitado?: boolean; badge?: string; icone?: string };
  periodoAtivo: TipoPeriodo;
  onSelecionarPeriodo: (periodo: TipoPeriodo) => void;
  onAbrirEnsinoJev?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ 
  onUpload, 
  isLoading, 
  jevStatus,
  periodoAtivo,
  onSelecionarPeriodo
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      onUpload(e.target.files[0]);
    }
  };

  const periodos: Array<{ id: TipoPeriodo; rotulo: string; descricao: string }> = [
    { id: 'todos_trimestres', rotulo: '4 Trimestres (1T a 4T)', descricao: 'Visão comparativa lado a lado dos 4 trimestres' },
    { id: '1T', rotulo: '1º Trim (1T)', descricao: 'Janeiro a Março' },
    { id: '2T', rotulo: '2º Trim (2T)', descricao: 'Abril a Junho' },
    { id: '3T', rotulo: '3º Trim (3T)', descricao: 'Julho a Setembro' },
    { id: '4T', rotulo: '4º Trim (4T)', descricao: 'Outubro a Dezembro' },
    { id: 'anual', rotulo: 'Consolidado Anual', descricao: 'Exercício completo acumulado' },
  ];

  return (
    <header className="bg-slate-900/90 backdrop-blur-md border-b border-slate-800 sticky top-0 z-50 shadow-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Linha Superior: Logo, Status JEV e Ações Organizadas */}
        <div className="h-16 flex items-center justify-between gap-4">
          
          {/* Logo e Título */}
          <div className="flex items-center space-x-3 min-w-0">
            <div className="h-10 w-10 shrink-0 rounded-xl bg-gradient-to-tr from-cyan-600 via-indigo-600 to-blue-500 flex items-center justify-center shadow-lg shadow-cyan-500/20 border border-cyan-400/30">
              <Activity className="h-5 w-5 text-white" />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap sm:flex-nowrap">
                <h1 className="text-base sm:text-lg font-bold text-white tracking-tight truncate">
                  Painel Executivo & Matriz DRE
                </h1>
                <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-[11px] font-semibold text-emerald-400 shrink-0">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                  JEV Engine Ativo
                </span>
              </div>
              <p className="text-xs text-slate-400 truncate hidden sm:block mt-0.5">
                Estrutura Corporativa Oficial & Demonstrações Financeiras
              </p>
            </div>
          </div>

          {/* Ações e Atalhos */}
          <div className="flex items-center gap-2 shrink-0">
            
            {/* Botão Módulo de Ensino JEV */}
            {onAbrirEnsinoJev && (
              <button
                onClick={onAbrirEnsinoJev}
                className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-cyan-950/40 hover:bg-cyan-900/60 text-cyan-300 border border-cyan-500/40 hover:text-white text-xs font-semibold transition-all shadow-sm"
                title="Abrir o Módulo de Ensino JEV (De-Para & Particularidades)"
              >
                <Brain className="h-3.5 w-3.5 text-cyan-400" />
                <span className="hidden md:inline">Ensinar JEV</span>
              </button>
            )}

            {/* Modelos de Download */}
            <div className="hidden sm:flex items-center gap-1.5">
              <button
                onClick={downloadModeloPlanilha}
                className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition-colors shadow-sm"
                title="Baixar planilha modelo Excel (.xlsx)"
              >
                <Download className="h-3.5 w-3.5 text-cyan-400" />
                <span>Excel</span>
              </button>

              <button
                onClick={downloadModeloPdf}
                className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition-colors shadow-sm"
                title="Baixar modelo demonstrativo PDF (.pdf)"
              >
                <FileText className="h-3.5 w-3.5 text-rose-400" />
                <span>PDF</span>
              </button>
            </div>

            {/* Botão Upload Primário */}
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept=".xlsx,.xls,.csv,.pdf"
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={isLoading}
              className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-cyan-600 via-indigo-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-xs font-semibold shadow-lg shadow-cyan-500/20 border border-cyan-400/30 transition-all disabled:opacity-50 shrink-0"
            >
              <Upload className="h-3.5 w-3.5" />
              <span>{isLoading ? 'Analisando JEV...' : 'Importar Arquivo'}</span>
            </button>
          </div>

        </div>

        {/* Linha Inferior: Barra de Controle de Períodos (Trimestres e Anual) */}
        <div className="py-2.5 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <Calendar className="h-3.5 w-3.5 text-cyan-400" />
            <span className="font-semibold text-slate-300">Visualização de Período:</span>
          </div>

          <div className="flex flex-wrap items-center gap-1.5 bg-slate-950/60 p-1 rounded-xl border border-slate-800">
            {periodos.map((p) => {
              const ativo = periodoAtivo === p.id;
              return (
                <button
                  key={p.id}
                  onClick={() => onSelecionarPeriodo(p.id)}
                  title={p.descricao}
                  className={`px-3 py-1 text-xs font-medium rounded-lg transition-all flex items-center gap-1.5 ${
                    ativo
                      ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-md shadow-cyan-500/25 font-semibold'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                  }`}
                >
                  {p.id === 'todos_trimestres' && <span>📊</span>}
                  {p.id.startsWith('1') && <span>🌱</span>}
                  {p.id.startsWith('2') && <span>📈</span>}
                  {p.id.startsWith('3') && <span>⚡</span>}
                  {p.id.startsWith('4') && <span>🎯</span>}
                  {p.id === 'anual' && <span>🏛️</span>}
                  <span>{p.rotulo}</span>
                </button>
              );
            })}
          </div>
        </div>

      </div>
    </header>
  );
};
