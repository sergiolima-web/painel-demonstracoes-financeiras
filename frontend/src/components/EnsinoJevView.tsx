import React, { useState, useEffect } from 'react';
import { Brain, Plus, Trash2, RefreshCw, CheckCircle2, Search, ArrowRight, ShieldCheck, HelpCircle } from 'lucide-react';
import api from '../services/api';

interface RegraDePara {
  id: string;
  termo_origem: string;
  termo_normalizado: string;
  conta_matriz_id: string;
  conta_matriz_nome: string;
  observacao?: string;
}

export const EnsinoJevView: React.FC = () => {
  const [regras, setRegras] = useState<RegraDePara[]>([]);
  const [termoOrigem, setTermoOrigem] = useState('');
  const [contaDestinoId, setContaDestinoId] = useState('vendas_mercadorias');
  const [observacao, setObservacao] = useState('');
  const [loading, setLoading] = useState(false);
  const [mensagemSucesso, setMensagemSucesso] = useState('');
  const [busca, setBusca] = useState('');

  const carregarRegras = async () => {
    try {
      setLoading(true);
      const res = await api.get('/api/regras-depara');
      if (res.data && res.data.regras) {
        setRegras(res.data.regras);
      }
    } catch (err) {
      console.error('Erro ao carregar regras de-para', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    carregarRegras();
  }, []);

  const handleSalvar = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!termoOrigem.trim()) return;

    try {
      setLoading(true);
      const res = await api.post('/api/regras-depara', {
        termo_origem: termoOrigem.trim(),
        conta_matriz_id: contaDestinoId,
        conta_matriz_nome: contaDestinoId,
        observacao: observacao || 'Particularidade cadastrada via painel React'
      });

      if (res.data && res.data.status === 'sucesso') {
        setMensagemSucesso(`✅ JEV aprendeu com sucesso: "${termoOrigem}" será conglutinado na conta selecionada.`);
        setTermoOrigem('');
        setObservacao('');
        carregarRegras();
        setTimeout(() => setMensagemSucesso(''), 4000);
      }
    } catch (err) {
      console.error('Erro ao cadastrar regra', err);
    } finally {
      setLoading(false);
    }
  };

  const handleExcluir = async (id: string) => {
    try {
      await api.delete(`/api/regras-depara/${id}`);
      carregarRegras();
    } catch (err) {
      console.error('Erro ao excluir regra', err);
    }
  };

  const regrasFiltradas = regras.filter(r => 
    r.termo_origem.toLowerCase().includes(busca.toLowerCase()) ||
    r.conta_matriz_id.toLowerCase().includes(busca.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Banner Principal */}
      <div className="bg-gradient-to-r from-slate-900 via-cyan-950/40 to-slate-900 border border-cyan-500/30 rounded-3xl p-6 sm:p-8 shadow-2xl flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div className="space-y-3 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/15 border border-cyan-400/30 text-cyan-300 text-xs font-bold">
            <Brain className="h-4 w-4" />
            <span>TypeSafe JEV Decision Engine • Aprendizado Contínuo</span>
          </div>
          <h2 className="text-2xl font-extrabold text-white">
            Módulo de Ensino Ativo & Conglutinação de Contas
          </h2>
          <p className="text-sm text-slate-300 leading-relaxed">
            Ensine ao motor JEV as particularidades de nomenclatura do seu balancete. As regras memorizadas são salvas com segurança no backend e aplicadas com prioridade absoluta nas importações da <strong className="text-amber-400">Matriz da Empresa</strong>.
          </p>
        </div>

        <div className="bg-slate-950/80 border border-slate-800 rounded-2xl p-5 text-center min-w-[200px] shrink-0 shadow-lg">
          <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Regras Ativas</span>
          <div className="text-4xl font-black text-cyan-400 mt-2">
            {regras.length}
          </div>
          <span className="text-[11px] text-emerald-400 font-bold block mt-1 flex items-center justify-center gap-1">
            <ShieldCheck className="h-3.5 w-3.5" />
            Protegido & Persistente
          </span>
        </div>
      </div>

      {/* Formulário de Cadastro */}
      <div className="bg-slate-900/80 border border-cyan-500/30 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Plus className="h-4 w-4 text-cyan-400" />
            <span>Cadastrar Nova Regra de De-Para (Particularidade)</span>
          </h3>
          <span className="text-xs text-slate-400 flex items-center gap-1">
            <HelpCircle className="h-3.5 w-3.5" />
            Reconhecimento semântico imediato
          </span>
        </div>

        <form onSubmit={handleSalvar} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Termo, Código ou Nome no seu Balancete/Planilha:
              </label>
              <input
                type="text"
                required
                placeholder="Ex: 4.1.2.05 - Aluguel Galpão Logística ou Taxa Segurança Noturna"
                value={termoOrigem}
                onChange={e => setTermoOrigem(e.target.value)}
                className="w-full px-4 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
              />
              <span className="text-[10px] text-slate-400 mt-1 block">
                O JEV fará a correspondência mesmo com variações ou números de conta.
              </span>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Destino Oficial na Matriz Corporativa (142 Contas):
              </label>
              <select
                value={contaDestinoId}
                onChange={e => setContaDestinoId(e.target.value)}
                className="w-full px-4 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
              >
                <optgroup label="1. RECEITA OPERACIONAL BRUTA">
                  <option value="vendas_mercadorias">1.01 VENDAS DE MERCADORIAS</option>
                </optgroup>
                <optgroup label="2. DEDUÇÕES DA RECEITA BRUTA">
                  <option value="vendas_canceladas">2.01 (-) Vendas Canceladas e Devoluções</option>
                  <option value="imposto_incidente">2.02 (-) Imposto Incidente Sobre Vendas</option>
                  <option value="icms_vendas">2.03 (-) ICMS Sobre Vendas</option>
                  <option value="pis_vendas">2.04 (-) PIS Sobre Vendas</option>
                  <option value="cofins_vendas">2.05 (-) COFINS Sobre Vendas</option>
                </optgroup>
                <optgroup label="4. CUSTO OPERACIONAL BRUTO (CMV)">
                  <option value="custo_mercadoria">4.01 (-) Custo de Mercadoria Vendida</option>
                </optgroup>
                <optgroup label="6.01 DESPESAS COM PESSOAL">
                  <option value="salarios_ordenados">6.01 (-) Salários e Ordenados</option>
                  <option value="ferias">6.01 (-) Férias</option>
                  <option value="decimo_terceiro">6.01 (-) 13º Salário</option>
                  <option value="rescisao">6.01 (-) Rescisão Contratual</option>
                  <option value="pro_labore">6.01 (-) Pró-Labore</option>
                </optgroup>
                <optgroup label="6.02 ENCARGOS SOCIAIS">
                  <option value="fgts">6.02 (-) FGTS</option>
                  <option value="inss">6.02 (-) INSS</option>
                  <option value="pis_folha">6.02 (-) PIS sobre Folha</option>
                </optgroup>
                <optgroup label="6.03 BENEFÍCIOS">
                  <option value="vale_transporte">6.03 (-) Vale Transporte</option>
                  <option value="assist_medica">6.03 (-) Assistência Médica</option>
                  <option value="uniforme">6.03 (-) Uniforme</option>
                  <option value="treinamento">6.03 (-) Treinamento</option>
                  <option value="auxilio_alimentacao">6.03 (-) Auxílio Alimentação</option>
                </optgroup>
                <optgroup label="6.04 MATERIAL E MANUTENÇÃO">
                  <option value="mat_escritorio">6.04 (-) Material de Escritório</option>
                  <option value="mat_limpeza">6.04 (-) Material de Limpeza</option>
                  <option value="mat_informatica">6.04 (-) Material de Informática</option>
                  <option value="mat_uso_consumo">6.04 (-) Material de Uso e Consumo</option>
                  <option value="mat_uso_crucial">6.04 (-) Material de Uso Crucial</option>
                  <option value="mat_embalagem">6.04 (-) Material de Embalagem</option>
                  <option value="manut_equipamentos">6.04 (-) Manutenção de Equipamentos</option>
                </optgroup>
                <optgroup label="6.05 VEÍCULOS">
                  <option value="manut_veiculos">6.05 (-) Manutenção de Veículos</option>
                  <option value="combustivel">6.05 (-) Combustível</option>
                </optgroup>
                <optgroup label="6.06 VIAGEM E HOSPEDAGEM">
                  <option value="viagem_func">6.06 (-) Viagem Funcionários</option>
                  <option value="viagem_terceiros">6.06 (-) Viagem Terceiros</option>
                  <option value="hospedagem">6.06 (-) Hospedagem</option>
                </optgroup>
                <optgroup label="6.07 DEMAIS ADMINISTRATIVAS">
                  <option value="energia">6.07 (-) Energia Elétrica</option>
                  <option value="telefonia">6.07 (-) Telefonia</option>
                  <option value="agua_esgoto">6.07 (-) Água e Esgoto</option>
                  <option value="aluguel_cofre">6.07 (-) Aluguel Cofre</option>
                  <option value="correios">6.07 (-) Correios e Malote</option>
                  <option value="internet">6.07 (-) Internet</option>
                  <option value="publicidade">6.07 (-) Publicidade / Redes Sociais</option>
                  <option value="licencas_software">6.07 (-) Licenças/Software ERP</option>
                  <option value="condominio">6.07 (-) Condomínio RMC</option>
                  <option value="depreciacao">6.07 (-) Depreciação Acumulada</option>
                  <option value="aluguel_predial">6.07 (-) Despesas c/ Aluguel Predial</option>
                </optgroup>
                <optgroup label="6.08 PERDAS DE CRÉDITOS">
                  <option value="pdd">6.08 (-) PDD / Perdas de Crédito</option>
                </optgroup>
                <optgroup label="6.09 IMPOSTOS E TAXAS">
                  <option value="iptu">6.09 (-) IPTU</option>
                  <option value="taxas_federais">6.09 (-) Taxas Federais</option>
                  <option value="taxas_estaduais">6.09 (-) Taxas Estaduais</option>
                  <option value="taxas_municipais">6.09 (-) Taxas Municipais</option>
                  <option value="issqn">6.09 (-) ISSQN</option>
                  <option value="siscomex">6.09 (-) Siscomex</option>
                </optgroup>
                <optgroup label="6.10 SERVIÇOS PJ/PF">
                  <option value="honorarios_adv">6.10 (-) Honorários Advocatícios</option>
                  <option value="honorarios_contabeis">6.10 (-) Honorários Contábeis</option>
                  <option value="consultoria_ti">6.10 (-) Consultoria e TI</option>
                  <option value="vigilancia_seguranca">6.10 (-) Vigilância e Segurança</option>
                  <option value="serv_diversos_pj">6.10 (-) Serviços Diversos PJ</option>
                </optgroup>
                <optgroup label="6.11 RESULTADO FINANCEIRO OPERACIONAL">
                  <option value="juros_multas_pagos">6.11 (-) Juros e Multas Pagos</option>
                  <option value="descontos_concedidos">6.11 (-) Descontos Concedidos</option>
                  <option value="tarifas_bancarias">6.11 (-) Tarifas Bancárias</option>
                  <option value="tarifas_cartao">6.11 (-) Tarifas Cartão de Crédito</option>
                </optgroup>
                <optgroup label="6.12 DESPESAS INDEDUTÍVEIS">
                  <option value="juros_indedutiveis">6.12 (-) Juros Indedutíveis</option>
                  <option value="auto_infracao">6.12 (-) Auto de Infração</option>
                  <option value="parcelamento_tributo">6.12 (-) Parcelamento Tributos</option>
                </optgroup>
                <optgroup label="8. RESULTADO NÃO OPERACIONAL">
                  <option value="juros_selic_impostos">8.01 (+) Juros Selic s/ Impostos</option>
                  <option value="rendimento_aplicacao">8.01 (+) Rendimento de Aplicação Financeira</option>
                  <option value="despesas_juros_despesas">8.02 (-) Despesas Juros Não Operacionais</option>
                  <option value="compensacoes_rf">8.03 (+) Compensações Processos RF</option>
                  <option value="bonificacoes_fornec">8.03 (+) Bonificações Recebidas Fornecedores</option>
                  <option value="acordos_promocionais">8.03 (+) Acordos Promocionais</option>
                  <option value="aluguel_loja">8.03 (+) Aluguel Espaço - Loja</option>
                </optgroup>
                <optgroup label="10. PROVISÃO IRPJ / CSLL">
                  <option value="prov_irpj">10.01 (-) Provisão de IRPJ</option>
                  <option value="prov_csll">10.02 (-) Provisão de CSLL</option>
                </optgroup>
              </select>
            </div>
          </div>

          {mensagemSucesso && (
            <div className="p-3.5 rounded-xl bg-emerald-500/15 border border-emerald-500/40 text-emerald-300 text-xs font-semibold flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4" />
              <span>{mensagemSucesso}</span>
            </div>
          )}

          <div className="flex justify-end pt-2">
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 via-blue-600 to-indigo-600 text-white text-xs font-black shadow-lg shadow-cyan-500/25 hover:brightness-110 transition-all flex items-center gap-2"
            >
              <Brain className="h-4 w-4" />
              <span>Ensinar ao JEV & Salvar Regra Permanente</span>
            </button>
          </div>
        </form>
      </div>

      {/* Tabela de Regras Ativas */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="p-4 border-b border-slate-800 flex flex-col sm:flex-row justify-between items-center gap-3 bg-slate-950/40">
          <div className="flex items-center gap-2">
            <Brain className="h-4 w-4 text-cyan-400" />
            <h3 className="text-sm font-bold text-white">
              Regras & Particularidades Ativas no JEV ({regras.length})
            </h3>
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            <div className="relative flex-1 sm:w-64">
              <Search className="h-3.5 w-3.5 absolute left-3 top-2.5 text-slate-500" />
              <input
                type="text"
                placeholder="Buscar regra..."
                value={busca}
                onChange={e => setBusca(e.target.value)}
                className="w-full pl-8 pr-3 py-1.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
              />
            </div>
            <button
              onClick={carregarRegras}
              className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-cyan-300 text-xs font-semibold flex items-center gap-1.5 transition-colors"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
              <span>Atualizar</span>
            </button>
          </div>
        </div>

        {regrasFiltradas.length === 0 ? (
          <div className="p-8 text-center space-y-2">
            <div className="text-3xl">💡</div>
            <h4 className="text-sm font-bold text-slate-300">Nenhuma particularidade cadastrada no momento</h4>
            <p className="text-xs text-slate-500 max-w-md mx-auto">
              O motor JEV está utilizando a árvore semântica contábil padrão. Cadastre regras acima para mapear termos específicos.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/80 text-slate-400 font-semibold uppercase tracking-wider border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4"># ID</th>
                  <th className="py-3 px-4 min-w-[220px]">Termo / Conta de Origem</th>
                  <th className="py-3 px-4">Destino</th>
                  <th className="py-3 px-4 min-w-[250px]">Conta de Destino na Matriz</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-center">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-200">
                {regrasFiltradas.map((r, i) => (
                  <tr key={r.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4 font-mono text-slate-500">{r.id || `regra_${i+1}`}</td>
                    <td className="py-3 px-4 font-bold text-white">
                      "{r.termo_origem}"
                    </td>
                    <td className="py-3 px-4 text-slate-400">
                      <ArrowRight className="h-4 w-4" />
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-3 py-1 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 font-mono text-xs font-semibold">
                        {r.conta_matriz_id}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                        Ativa (JEV)
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <button
                        onClick={() => handleExcluir(r.id)}
                        className="px-2.5 py-1 rounded-lg bg-red-500/10 hover:bg-red-500/25 border border-red-500/30 text-red-300 text-xs font-semibold transition-all flex items-center gap-1 mx-auto"
                        title="Remover regra"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                        <span>Excluir</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
