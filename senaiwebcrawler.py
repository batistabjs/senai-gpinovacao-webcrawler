import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import logging
from urllib.parse import urljoin, parse_qs, urlparse
from typing import List, Dict, Optional
import json

class SenaiWebCrawler:
    
    def __init__(self, base_url: str, max_pages: int, delay: float = 1.0):
        self.base_url = base_url
        self.delay = delay
        self.max_pages = max_pages
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
    
    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            return BeautifulSoup(response.content, 'html.parser')
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro ao acessar {url}: {e}")
            return None
    
    def extract_idea_data(self, soup: BeautifulSoup) -> List[Dict]:
        ideas_data = []
        
        # titulo-18
        ideas_tag = soup.find_all('h3', class_=lambda value: value == 'titulo-18')
        
        for link in ideas_tag:
            try:
                idea_data = {
                    'idea_titulo': link.find('a').get_text(strip=True),
                    'idea_url': link.find('a')['href'],
                }
                
                ideas_data.append(idea_data)
                
            except Exception as e:
                self.logger.warning(f"Erro ao extrair dados da ideia: {e}")
                continue
        
        return ideas_data
    
    def find_next_page(self, soup: BeautifulSoup, current_page: int) -> Optional[str]:
        """
        Encontra a próxima página se existir
        
        Args:
            soup: BeautifulSoup da página atual
            current_page: Número da página atual
            
        Returns:
            URL da próxima página ou None
        """
        # Procurar por links de paginação
        pagination_links = soup.find_all('a', href=lambda x: x and 'page=' in x)
        
        if pagination_links:
            # Buscar página seguinte
            next_page = current_page + 1
            for link in pagination_links:
                href = link.get('href')
                if f'page={next_page}' in href:
                    return urljoin(self.base_url, href)
        
        # Alternativa: tentar construir URL da próxima página
        try:
            parsed_url = urlparse(self.base_url)
            base_without_params = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
            next_url = f"{base_without_params}?page={current_page + 1}"
            
            # Verificar se a próxima página existe
            test_soup = self.fetch_page(next_url)
            if test_soup and self.extract_user_data(test_soup):
                return next_url
        except:
            pass
        
        return None
    
    def crawl_all_pages(self) -> Dict:
        all_data = {
            'ideias': [],
            'total_paginas': 0,
            'total_ideias': 0
        }
        
        current_page = 1
        current_url = self.base_url
        
        while current_page <= self.max_pages:
            self.logger.info(f"Página {current_page}, URL {current_url}")
            
            # Fetch da página atual
            soup = self.fetch_page(current_url)
            if not soup:
                self.logger.error(f"Não foi possível acessar a página {current_page}")
                break

            # Extrair dados das ideias
            ideas_data = self.extract_idea_data(soup)
            if not ideas_data:
                self.logger.info(f"Nenhuma Ideia encontrada na página {current_page}")
                break
            
            all_data['ideias'].extend(ideas_data)
            all_data['total_paginas'] = current_page
            
            # Buscar próxima página
            next_url = self.find_next_page(soup, current_page)
            if not next_url:
                self.logger.info("Não há mais páginas para processar")
                break
            
            current_url = next_url
            current_page += 1
            
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
            self.logger.info(f"Dados salvos em {json_filename}")
            
            # Salvar ideias em CSV
            if data['ideias']:
                csv_filename = f"{base_filename}_ideias.csv"
                df_users = pd.DataFrame(data['ideias'])
                df_users.to_csv(csv_filename, index=False, encoding='utf-8')
                self.logger.info(f"Ideias salvas em {csv_filename}")
                
        except Exception as e:
            self.logger.error(f"Erro ao salvar arquivos: {e}")

def main():
    # URL do desafio
    url = "https://plataforma.gpinovacao.senai.br/plataforma/desafio/1885?page=1"
    
    # Inicializar crawler
    crawler = SenaiWebCrawler(url, max_pages=5, delay=1.5) # 545 pag totais
    print("🚀 Iniciando extração de dados da plataforma SENAI...")

    # Executar crawling
    data = crawler.crawl_all_pages()
    
    # Exibir resultados
    print(f"\n📊 Resultados da Extração:")
    print(f"Total de páginas processadas: {data['total_paginas']}")
    print(f"Total de ideias encontradas: {data['total_ideias']}")
    
    # Salvar dados
    print(f"\n💾 Salvando dados...")
    crawler.save_to_files(data, 'senai_desafio_1885')
    
    print(f"\n✅ Extração concluída com sucesso!")
    
    return data

if __name__ == "__main__":
    # Executar o programa
    extracted_data = main()
