import axios from 'axios';
import { DemonstracaoData } from '../types/financeiro';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 30000,
});

export const getStatusJev = async () => {
  const response = await api.get('/api/status-jev');
  return response.data;
};

export const getDadosPadrao = async (): Promise<DemonstracaoData> => {
  const response = await api.get<DemonstracaoData>('/api/dados-demonstracao-padrao');
  return response.data;
};

export const uploadDemonstracao = async (
  file: File,
  anoDestino: string = '2026',
  trimestresAutorizados: string[] = ['1T', '2T', '3T', '4T']
): Promise<DemonstracaoData> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('ano_destino', anoDestino);
  formData.append('trimestres_autorizados', JSON.stringify(trimestresAutorizados));
  const response = await api.post<DemonstracaoData>('/api/upload-demonstracao', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const downloadModeloPlanilha = async () => {
  const response = await api.get('/api/modelo-planilha', {
    responseType: 'blob',
  });
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', 'Modelo_Balanco_DRE_Acionistas.xlsx');
  document.body.appendChild(link);
  link.click();
  link.remove();
};

export const downloadModeloPdf = async () => {
  const response = await api.get('/api/modelo-pdf', {
    responseType: 'blob',
  });
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', 'Modelo_Balanco_DRE_Acionistas.pdf');
  document.body.appendChild(link);
  link.click();
  link.remove();
};

export default api;
