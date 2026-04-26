import logging
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from app.core.config import settings
import concurrent.futures

def fetch_and_extract_text(url: str, timeout: int = 5) -> str:
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'lxml')
        # Remover scripts y estilos para obtener texto limpio
        for script in soup(["script", "style", "noscript", "header", "footer", "nav"]):
            script.extract()
            
        text = soup.get_text(separator=' ', strip=True)
        # Limitar longitud para no desbordar el contexto del LLM
        return text[:2000]
    except Exception as e:
        logging.warning(f"Error extrayendo {url}: {e}")
        return ""

def perform_web_search(query: str, max_results: int = None) -> tuple[str, list[str]]:
    """
    Realiza una búsqueda en DuckDuckGo, extrae las URLs y raspa el texto real de las páginas.
    """
    if max_results is None:
        max_results = settings.web_search_max_results
        
    try:
        results = list(DDGS().text(query, max_results=max_results))
        
        if not results:
            return "", []
            
        urls = [res.get('href') for res in results if res.get('href')]
        
        context_parts = []
        sources = []
        
        # Paralelizar las peticiones HTTP para minimizar el tiempo de espera
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(urls), 3)) as executor:
            future_to_url = {executor.submit(fetch_and_extract_text, url): url for url in urls}
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    page_text = future.result()
                    if page_text:
                        context_parts.append(f"--- Fuente: {url} ---\n{page_text}")
                        sources.append(url)
                except Exception as e:
                    pass
                
        # Si el scraping real falla en todas las URLs (bloqueos, etc), recaemos en los snippets básicos
        if not context_parts:
            for res in results:
                title = res.get('title', '')
                body = res.get('body', '')
                url = res.get('href', '')
                context_parts.append(f"[{title}] {body}")
                if url:
                    sources.append(url)
                    
        combined_context = "\n\n".join(context_parts)
        return combined_context, sources
        
    except Exception as e:
        logging.error(f"Error en web_search fallback: {e}")
        return "", []
