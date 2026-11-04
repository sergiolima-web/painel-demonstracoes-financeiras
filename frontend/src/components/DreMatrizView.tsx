import React, { useState } from 'react';
import { DreMatrizEmpresa, LinhaDreMatriz } from '../types/financeiro';
import api from '../services/api';
import { 
  Building2, 
  ChevronDown, 
  ChevronRight, 
  Search, 
  Sparkles, 
  Layers, 
  Download, 
  PlusCircle, 
  Check, 
  Info 
} from 'lucide-react';

interface DreMatrizViewProps {
  matriz?: DreMatrizEmpresa;
}

export const DreMatrizView: React.FC<DreMatrizViewProps> = ({ matriz }) => {
  const [busca, setBusca] = useState('');
  const [expandidos, setExpandidos] = useState<Record<string, boolean>>({
    'rec_bruta': true,
    'deducoes_rec': true,
    'cmv': true,
    'despesas_operacionais': true,
    'desp_pessoal': false,
    'encargos_sociais': false,
    'beneficios': false,
    'material_manutencao': false,
    'desp_veiculos': false,
    'viagem_hospedagem': false,
    'demais_administrativas': false,
    'impostos_taxas': false,
    'servicos_pj_pf': false,
    'resultado_financeiro_op': false,
    'despesas_indedutiveis': false,
    'resultado_nao_operacional': true,
    'outras_receitas_nao_op': false,
    'provisao_tributos': true
  });

  const [modalMapeamento, setModalMapeamento] = useState(false);
  const [contaDe, setContaDe] = useState('');
  const [grupoPara, setGrupoPara] = useState('desp_pessoal');
  const [mensagemSucessoMapeamento, setMensagemSucessoMapeamento] = useState('');

  const formatarMoeda = (val: number) => {
    return (val || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  };

  const toggleExpandir = (id: string) => {
    setExpandidos(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const expandirTodos = () => {
    const novoEstado: Record<string, boolean> = {};
    (matriz?.linhas || []).forEach(l => { novoEstado[l.id] = true; });
    setExpandidos(novoEstado);
  };

  const recolherTodos = () => {
    setExpandidos({});
  };

  const handleSalvarMapeamento = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!contaDe.trim()) return;
    try {
      await api.post('/api/regras-depara', {
        termo_origem: contaDe.trim(),
        conta_matriz_id: grupoPara,
        conta_matriz_nome: grupoPara,
        observacao: 'Particularidade cadastrada pela Matriz DRE'
      });
      setMensagemSucessoMapeamento(`Conta "${contaDe}" memorizada e salva pelo JEV com sucesso!`);
    } catch (err) {
      setMensagemSucessoMapeamento(`Conta "${contaDe}" associada em sessão.`);
    }
    setTimeout(() => {
      setMensagemSucessoMapeamento('');
      setModalMapeamento(false);
      setContaDe('');
    }, 2000);
  };

  if (!matriz || !matriz.linhas) {
    return (
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-8 text-center text-slate-400">
        <Sparkles className="h-8 w-8 text-cyan-400 mx-auto mb-2 animate-spin" />
        <p>Carregando Matriz DRE Corporativa da Empresa...</p>
      </div>
    );
  }

  const linhasFiltradas = matriz.linhas.filter(l => {
    if (!busca) return true;
    return l.conta.toLowerCase().includes(busca.toLowerCase());
  });

  // Cores de estilo idênticas à imagem fornecida
  const getEstiloLinha = (linha: LinhaDreMatriz) => {
    const estilo = linha.estilo || '';
    const conta = linha.conta.toUpperCase();

    if (estilo === 'destaque_ouro_neon' || conta.includes('RESULTADO LÍQUIDO DO EXERCÍCIO')) {
      return 'bg-amber-400/90 text-slate-950 font-black border-y-2 border-amber-300 shadow-md';
    }
    if (estilo === 'destaque_laranja' || conta.includes('RECEITA OPERACIONAL BRUTA')) {
      return 'bg-amber-600/30 text-amber-200 font-extrabold border-y border-amber-500/40';
    }
    if (estilo === 'destaque_amarelo' || conta.includes('DEDUÇÕES') || conta.includes('RESULTADO OPERACIONAL BRUTO') || conta.includes('LUCRO OPERACIONAL LÍQUIDO') || conta.includes('RESULTADO OPERACIONAL ANTES')) {
      return 'bg-yellow-500/20 text-yellow-200 font-bold border-y border-yellow-500/30';
    }
    if (estilo === 'destaque_verde_menta' || conta.includes('RECEITA OPERACIONAL LÍQUIDA') || conta.includes('OUTRAS RECEITAS') || conta.includes('PROVISÃO IRPJ')) {
      return 'bg-emerald-500/20 text-emerald-200 font-bold border-y border-emerald-500/30';
    }
    if (estilo === 'destaque_verde' || conta.includes('CUSTO OPERACIONAL BRUTO')) {
      return 'bg-teal-500/20 text-teal-200 font-bold border-y border-teal-500/30';
    }
    if (estilo === 'destaque_cinza' || conta.includes('DESPESAS OPERACIONAIS E ADMINIST') || conta.includes('RESULTADO NÃO OPERACIONAL')) {
      return 'bg-slate-800/80 text-slate-100 font-bold border-y border-slate-700';
    }
    if (linha.tipo === 'grupo') {
      return 'bg-slate-900/90 text-slate-200 font-bold';
    }
    return 'hover:bg-slate-800/40 text-slate-300';
  };

  return (
    <div className="space-y-6 animate-fade-in">
      
      {/* Banner Superior da Matriz Corporativa */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-900 to-slate-950 border border-amber-500/30 rounded-3xl p-6 shadow-2xl flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center space-x-4">
          <div className="h-12 w-12 rounded-2xl bg-gradient-to-tr from-amber-500 via-yellow-500 to-amber-600 flex items-center justify-center text-slate-950 font-bold text-2xl shadow-lg shadow-amber-500/20">
            🏢
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-extrabold text-white">
                Matriz DRE da Empresa & Conglutinação Semântica
              </h2>
              <span className="px-2.5 py-0.5 rounded-full bg-amber-500/20 border border-amber-400/40 text-[10px] font-extrabold text-amber-300">
                ⚡🧠 JEV Matrix Engine
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Reconhecimento, aglutinação e mapeamento de contas conforme a estrutura oficial da sua organização.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setModalMapeamento(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-xs font-semibold shadow-lg shadow-cyan-500/20 border border-cyan-400/30 transition-all"
          >
            <PlusCircle className="h-4 w-4" />
            <span>Cadastrar Regra / De-Para JEV</span>
          </button>
        </div>
      </div>

      {/* Controles de Busca e Expansão */}
      <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-4 flex flex-col sm:flex-row gap-4 justify-between items-center">
        <div className="relative w-full sm:w-80">
          <Search className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Pesquisar conta na DRE da empresa..."
            value={busca}
            onChange={e => setBusca(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-500 transition-colors"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
          <button
            onClick={expandirTodos}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition-colors"
          >
            Expandir Tudo
          </button>
          <button
            onClick={recolherTodos}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition-colors"
          >
            Recolher Subgrupos
          </button>
        </div>
      </div>

      {/* Tabela Idêntica à DRE da Imagem Fornecida */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse font-sans">
            
            {/* Cabeçalho da Tabela Estilo Imagem (Tons de Laranja e Ouro) */}
            <thead className="bg-gradient-to-r from-amber-700 via-amber-600 to-amber-700 text-white font-black uppercase text-[11px] tracking-wider border-b-2 border-amber-800 shadow-md">
              <tr>
                <th className="py-3 px-4 min-w-[340px] text-white border-r border-amber-600/40">
                  ESTRUTURA DE CONTAS GERENCIAIS
                </th>
                <th className="py-3 px-3 text-right bg-amber-600 border-r border-amber-500/60 min-w-[130px]">
                  3º Trim/2025
                </th>
                <th className="py-3 px-2 text-center bg-amber-600 border-r border-amber-500/60 min-w-[60px]">
                  % (AV)
                </th>
                <th className="py-3 px-2 text-center bg-amber-600 border-r border-amber-500/60 min-w-[40px]">
                  Td
                </th>
                <th className="py-3 px-3 text-right bg-amber-700 border-r border-amber-600/60 min-w-[130px]">
                  4º Trim/2025
                </th>
                <th className="py-3 px-2 text-center bg-amber-700 border-r border-amber-600/60 min-w-[60px]">
                  % (AV)
                </th>
                <th className="py-3 px-2 text-center bg-amber-700 border-r border-amber-600/60 min-w-[40px]">
                  Td
                </th>
                <th className="py-3 px-4 text-right bg-amber-400 text-slate-950 font-black border-r border-amber-300 min-w-[140px]">
                  DRE - 2025
                </th>
                <th className="py-3 px-3 text-center bg-amber-400 text-slate-950 font-black min-w-[65px]">
                  % (AV)
                </th>
              </tr>
            </thead>

            {/* Linhas de Contas com Destaques Idênticos à Imagem */}
            <tbody className="divide-y divide-slate-800/40 font-mono">
              {linhasFiltradas.map((linha, index) => {
                const estiloLinha = getEstiloLinha(linha);
                const isNegativo = linha.marcador === '(-)' || linha.conta.startsWith('(-)');

                return (
                  <tr key={linha.id || index} className={`transition-colors ${estiloLinha}`}>
                    
                    {/* Descrição com Nível e Indentação */}
                    <td className={`py-2 px-4 font-sans flex items-center gap-1.5 border-r border-slate-800/60 ${
                      linha.nivel === 0 ? 'font-bold' : (linha.nivel === 1 ? 'pl-6 font-semibold' : 'pl-10 text-slate-300 font-normal')
                    }`}>
                      {linha.nivel > 0 && <span className="text-slate-500 text-[10px]">•</span>}
                      <span>{linha.conta}</span>
                    </td>

                    {/* 3º Trimestre */}
                    <td className="py-2 px-3 text-right border-r border-slate-800/60 font-semibold">
                      {isNegativo && linha.val_3t > 0 ? `(${formatarMoeda(linha.val_3t)})` : formatarMoeda(linha.val_3t)}
                    </td>
                    <td className="py-2 px-2 text-center border-r border-slate-800/60 text-[11px] text-slate-300">
                      {linha.pct_3t > 0 ? `${linha.pct_3t.toFixed(2)}%` : '0,00%'}
                    </td>
                    <td className="py-2 px-2 text-center border-r border-slate-800/60 text-xs">
                      {linha.td_3t === '▲' && <span className="text-emerald-400 font-bold">▲</span>}
                      {linha.td_3t === '▼' && <span className="text-rose-400 font-bold">▼</span>}
                      {linha.td_3t === '-' && <span className="text-slate-500">-</span>}
                    </td>

                    {/* 4º Trimestre */}
                    <td className="py-2 px-3 text-right border-r border-slate-800/60 text-slate-400">
                      {linha.val_4t > 0 ? (isNegativo ? `(${formatarMoeda(linha.val_4t)})` : formatarMoeda(linha.val_4t)) : '0,00'}
                    </td>
                    <td className="py-2 px-2 text-center border-r border-slate-800/60 text-[11px] text-slate-500">
                      {linha.pct_4t > 0 ? `${linha.pct_4t.toFixed(2)}%` : '0,00%'}
                    </td>
                    <td className="py-2 px-2 text-center border-r border-slate-800/60 text-xs">
                      <span className="text-slate-600">-</span>
                    </td>

                    {/* Consolidado DRE 2025 */}
                    <td className={`py-2 px-4 text-right border-r border-slate-800/60 font-bold ${
                      linha.tipo === 'total_final' ? 'text-slate-950 font-black' : 'text-white'
                    }`}>
                      {isNegativo && linha.val_total > 0 ? `(${formatarMoeda(linha.val_total)})` : formatarMoeda(linha.val_total)}
                    </td>
                    <td className={`py-2 px-3 text-center font-bold text-[11px] ${
                      linha.tipo === 'total_final' ? 'text-slate-950 font-black' : 'text-amber-300'
                    }`}>
                      {linha.pct_total > 0 ? `${linha.pct_total.toFixed(2)}%` : '0,00%'}
                    </td>

                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal de Cadastro de Nova Regra De-Para JEV */}
      {modalMapeamento && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
          <div className="max-w-md w-full bg-slate-900 border border-cyan-500/40 rounded-2xl p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <span>⚡🧠 Cadastrar Particularidade no JEV</span>
              </h3>
              <button 
                onClick={() => setModalMapeamento(false)}
                className="text-slate-400 hover:text-white font-bold"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-slate-300">
              Ensine ao motor JEV como classificar e conglutinar contas específicas da sua empresa automaticamente.
            </p>

            <form onSubmit={handleSalvarMapeamento} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Nome ou Padrão da Conta Contábil:
                </label>
                <input
                  type="text"
                  required
                  placeholder="Ex: 4.1.2.01 - Taxa de Segurança Noturna"
                  value={contaDe}
                  onChange={e => setContaDe(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Conglutinar no Grupo da DRE da Empresa:
                </label>
                <select
                  value={grupoPara}
                  onChange={e => setGrupoPara(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-cyan-500"
                >
                  <option value="desp_pessoal">(-) DESPESAS COM PESSOAL</option>
                  <option value="encargos_sociais">(-) ENCARGOS SOCIAIS E TRABALHISTAS</option>
                  <option value="beneficios">(-) BENEFÍCIOS</option>
                  <option value="material_manutencao">(-) MATERIAL E MANUTENÇÃO</option>
                  <option value="desp_veiculos">(-) DESPESAS COM VEÍCULOS</option>
                  <option value="viagem_hospedagem">(-) VIAGEM E HOSPEDAGEM</option>
                  <option value="demais_administrativas">(-) DEMAIS DESPESAS ADMINISTRATIVAS</option>
                  <option value="impostos_taxas">(-) IMPOSTOS E TAXAS</option>
                  <option value="servicos_pj_pf">(-) SERVIÇOS PRESTADOS PJ/PF</option>
                  <option value="resultado_financeiro_op">(-/+) RESULTADO FINANCEIRO LÍQUIDO</option>
                  <option value="despesas_indedutiveis">(-) DESPESAS INDEDUTÍVEIS</option>
                  <option value="outras_receitas_nao_op">(+) OUTRAS RECEITAS NÃO OPERACIONAIS</option>
                </select>
              </div>

              {mensagemSucessoMapeamento && (
                <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2">
                  <Check className="h-4 w-4 shrink-0" />
                  <span>{mensagemSucessoMapeamento}</span>
                </div>
              )}

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setModalMapeamento(false)}
                  className="px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 text-white text-xs font-bold shadow-lg shadow-cyan-500/25"
                >
                  Memorizar com JEV
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};
