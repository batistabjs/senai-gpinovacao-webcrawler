import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import logging
from urllib.parse import urljoin, parse_qs, urlparse
from typing import List, Dict, Optional
import json

class SenaiWebCrawler:
    
    def __init__(self, base_url: str, delay: float = 1.0):
        self.base_url = base_url
        self.delay = delay
        self.session = requests.Session()
        
        # Headers para simular um browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def fetch_page(self: str) -> Optional[BeautifulSoup]:
        try:
            response = requests.get(self.base_url, timeout=30)
            response.raise_for_status()
            
            return BeautifulSoup(response.content, 'html.parser')
            
        except requests.exceptions.RequestException as e:
            self.logger.error("Erro ao acessar {url}: {e}")
            return None
    
    def extract_idea_data(self, soup: BeautifulSoup) -> List[Dict]:
        ideas_data = []
        # destaque
        #destaque_tag = soup.select('.destaque')
        #print(destaque_tag)
        # detalhes
        #detalhes_tag = soup.select('#detalhes')    
        #print(detalhes_tag)
        # equipe
        equipe_tag = soup.find("div", id = "equipe")
        # comentarios
        comentarios_tag = soup.find("div", id = "comentarios")
        # complementos
        complementos_tag = soup.find("div", id = "complementos")
        
        print (soup.select("div.destaque > h2:nth-of-type(1)"))
        print (soup.select('div#detalhes > p:nth-of-type(2)'))
        try:
            idea_data = {
                'idea_titulo': soup.select("div.destaque > h2:nth-of-type(1)").get_text(strip=True),
                #'idea_estado': soup.select('div#detalhes > p')[1].get_text(strip=True)#,detalhes_tag.find('p')[1].get_text(strip=True),
                #'idea_departamento': detalhes_tag.find('p')[2].get_text(strip=True),
                #'idea_demanda': detalhes_tag.find('p')[3].get_text(strip=True)
            }

            print(idea_data)
            
            #ideas_data.append(idea_data)
            
        except Exception as e:
            self.logger.warning(f"Erro ao extrair dados da ideia: {e}")
        
        return ideas_data
      
    def crawl_all_pages(self, urls) -> Dict:
        all_data = {
            'ideias': [],
            'total_paginas': 0,
            'total_ideias': 0
        }

        for url in urls:
            self.logger.info(f" URL {url}")
            self.base_url = url
            
            # Fetch da página atual
            soup = self.fetch_page()
            if not soup:
                self.logger.error(f"Não foi possível acessar a página {url}")

            # Extrair dados das ideias
            ideas_data = self.extract_idea_data(soup)
            if not ideas_data:
                self.logger.info(f"Nenhuma Ideia encontrada na página {url}")
            
            all_data['ideias'].extend(ideas_data)
            
            # Delay entre requisições
            time.sleep(self.delay)
            
            all_data['total_ideias'] = len(all_data['ideias'])
            
        return all_data
    
    def save_to_files(self, data: Dict, base_filename: str = 'senai_data'):
        try:
            # Salvar em JSON
            json_filename = f"{base_filename}.json"
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.logger.info("Dados salvos em {json_filename}")
            
            # Salvar ideias em CSV
            if data['ideias']:
                csv_filename = f"{base_filename}_ideias.csv"
                df_users = pd.DataFrame(data['ideias'])
                df_users.to_csv(csv_filename, index=False, encoding='utf-8')
                self.logger.info("Ideias salvas em {csv_filename}")
                
        except Exception as e:
            self.logger.error("Erro ao salvar arquivos: {e}")

def json_extract_links(arquivo_json: str, chaves: List[str] = None) -> Dict[str, List[str]]:
    try:
        with open(arquivo_json, 'r', encoding='utf-8') as file:
            ideia_list = json.load(file)
            ideia_links = []

            for ideia in ideia_list['ideias']:
                ideia_links.append(ideia['idea_url'])

            return ideia_links
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print("Erro ao processar arquivo: {e}")
        return {}

def main():
    # URL da ideia
    urls = json_extract_links('senai1885_ideia_links_reduce.json');
    print(urls)

    # Inicializar crawler
    crawler = SenaiWebCrawler('', delay=3) # 545 pag totais
    print("🚀 Iniciando extração de dados da plataforma SENAI...")

    # Executar crawling
    data = crawler.crawl_all_pages(urls)
    
    # Exibir resultados
    print("\n📊 Resultados da Extração:")
    print("Total de páginas processadas: {data['total_paginas']}")
    print("Total de ideias encontradas: {data['total_ideias']}")
    
    # Salvar dados
    print("\n💾 Salvando dados...")
    crawler.save_to_files(data, 'senai_desafio_1885')
    
    print("\n✅ Extração concluída com sucesso!")
    
    return data

if __name__ == "__main__":
    # Executar o programa
    extracted_data = main()
