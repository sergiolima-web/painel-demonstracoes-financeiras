export interface SaldosTrimestrais {
  '1T': number;
  '2T': number;
  '3T': number;
  '4T': number;
  'anual': number;
}

export interface ContaContabil {
  codigo: string;
  conta: string;
  tipo: string;
  saldo_atual: number;
  saldo_anterior: number;
  saldos_trimestrais?: SaldosTrimestrais;
  saldos_anuais?: Record<string, number>;
  variacao_nominal: number;
  variacao_percentual: number;
  grupo: string;
  confianca_ia: number;
  score_relevancia: number;
  probabilidade_anomalia: number;
  badge_ia: string;
}

export interface ItemDre {
  codigo: string;
  conta: string;
  saldo_atual: number;
  saldo_anterior: number;
  saldos_trimestrais?: SaldosTrimestrais;
  saldos_anuais?: Record<string, number>;
  variacao_percentual: number;
}

export interface IndicesFinanceiros {
  estrutura: {
    ativo_total: number;
    passivo_exigivel: number;
    patrimonio_liquido: number;
    ccl?: number;
  };
  liquidez: {
    liquidez_corrente: number;
    liquidez_seca: number;
    liquidez_imediata: number;
    liquidez_geral: number;
    ccl?: number;
  };
  rentabilidade: {
    margem_bruta_pct: number;
    margem_operacional_pct: number;
    margem_ebitda_pct: number;
    margem_liquida_pct: number;
    roe_pct: number;
    roa_pct: number;
    roic_pct?: number;
  };
  eficiencia?: {
    giro_ativo: number;
  };
  endividamento: {
    endividamento_geral_pct: number;
    composicao_divida_curto_prazo_pct: number;
    imobilizacao_pl_pct: number;
    solvencia_geral?: number;
    cobertura_juros?: number;
  };
}

export interface PilarGestao {
  id: string;
  titulo: string;
  status: string;
  icone: string;
  diagnostico: string;
  solucao_confiavel: string;
}

export interface SazonalidadeTrimestral {
  resumo: string;
  destaques: Array<{
    trimestre: string;
    foco: string;
    ritmo: string;
  }>;
}

export interface ItemPlanoAcao {
  ordem: number;
  acao: string;
  responsavel: string;
  prazo: string;
  impacto: string;
  detalhe: string;
}

export interface SolucoesGestaoJev {
  icone: string;
  badge: string;
  score_saude: number;
  rating: string;
  status_cor: 'emerald' | 'cyan' | 'amber' | 'rose';
  parecer_sintese: string;
  pilares_gestao: PilarGestao[];
  sazonalidade_trimestral: SazonalidadeTrimestral;
  plano_acao: ItemPlanoAcao[];
}

export interface LinhaDreMatriz {
  id: string;
  codigo?: string;
  conta: string;
  marcador?: string;
  tipo: string;
  estilo?: string;
  nivel: number;
  val_3t: number;
  pct_3t: number;
  td_3t: string;
  val_4t: number;
  pct_4t: number;
  td_4t: string;
  val_total: number;
  pct_total: number;
}

export interface DreMatrizEmpresa {
  titulo: string;
  empresa_modelo: string;
  colunas: string[];
  linhas: LinhaDreMatriz[];
  resumo_executivo: {
    receita_bruta_anual: number;
    receita_liquida_anual: number;
    cmv_anual: number;
    despesas_op_anual: number;
    lucro_liquido_anual: number;
    margem_liquida_anual: number;
  };
}

export interface DemonstracaoData {
  arquivo: string;
  formato?: string;
  tipo_documento?: string;
  aba_sugerida?: string;
  somente_dre?: boolean;
  paginas_processadas?: number;
  balanco_equilibrado?: boolean;
  diferenca_balanco?: number;
  total_linhas_lidas?: number;
  totais_balanco: {
    ativo_circulante: number;
    ativo_nao_circulante: number;
    ativo_total: number;
    passivo_circulante: number;
    passivo_nao_circulante: number;
    patrimonio_liquido: number;
    passivo_total: number;
    disponibilidades: number;
  };
  totais_balanco_por_ano?: Record<string, {
    ativo_circulante: number;
    ativo_nao_circulante: number;
    ativo_total: number;
    passivo_circulante: number;
    passivo_nao_circulante: number;
    patrimonio_liquido: number;
    passivo_total: number;
    disponibilidades: number;
  }>;
  totais_dre: {
    receita_bruta: number;
    lucro_liquido: number;
  };
  totais_dre_por_ano?: Record<string, {
    receita_bruta: number;
    lucro_liquido: number;
  }>;
  indices_financeiros: IndicesFinanceiros;
  indicadores_por_periodo?: Record<string, IndicesFinanceiros>;
  anos_disponiveis?: string[];
  ano_ativo?: string;
  indicadores_por_ano?: Record<string, IndicesFinanceiros>;
  parecer_gestao_jev?: SolucoesGestaoJev;
  dre_matriz_empresa?: DreMatrizEmpresa;
  dre_matriz_por_ano?: Record<string, DreMatrizEmpresa>;
  contas_detalhadas: ContaContabil[];
  itens_dre: ItemDre[];
  destaques_acionistas: ContaContabil[];
  motor_ia: {
    icone: string;
    nome: string;
    status: string;
  };
}

export type TipoPeriodo = 'todos_trimestres' | '1T' | '2T' | '3T' | '4T' | 'anual';

