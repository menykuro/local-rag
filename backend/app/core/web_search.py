"""Busqueda web y extraccion de texto para fallback de consultas."""

import concurrent.futures
import logging

import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

from app.core.config import settings


def fetch_and_extract_text(url: str, timeout: int = 5) -> str:
    """Descarga una URL y devuelve texto limpio truncado para contexto de LLM."""
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "lxml")
        for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
            tag.extract()

        text = soup.get_text(separator=" ", strip=True)
        return text[:2000]
    except Exception as exc:
        logging.warning(f"Error extrayendo {url}: {exc}")
        return ""


def perform_web_search(query: str, max_results: int = None) -> tuple[str, list[str]]:
    """Busca resultados en DuckDuckGo y construye contexto textual util."""
    if max_results is None:
        max_results = settings.web_search_max_results

    try:
        results = list(DDGS().text(query, max_results=max_results))
        if not results:
            return "", []

        urls = [row.get("href") for row in results if row.get("href")]
        context_parts = []
        sources = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(urls), 3)) as executor:
            future_to_url = {executor.submit(fetch_and_extract_text, url): url for url in urls}
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    page_text = future.result()
                    if page_text:
                        context_parts.append(f"--- Fuente: {url} ---\n{page_text}")
                        sources.append(url)
                except Exception:
                    continue

        if not context_parts:
            for row in results:
                title = row.get("title", "")
                body = row.get("body", "")
                url = row.get("href", "")
                context_parts.append(f"[{title}] {body}")
                if url:
                    sources.append(url)

        return "\n\n".join(context_parts), sources
    except Exception as exc:
        logging.error(f"Error en web_search fallback: {exc}")
        return "", []
