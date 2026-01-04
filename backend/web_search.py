import arxiv
from duckduckgo_search import DDGS

class WebSearcher:
    def __init__(self):
        self.ddgs = DDGS()

    def search_arxiv(self, query, max_results=5):
        """Busca papers académicos en ArXiv."""
        try:
            print(f"🔍 Buscando en ArXiv: {query}")
            client = arxiv.Client()
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance
            )
            
            results = []
            for r in client.results(search):
                results.append({
                    "title": r.title,
                    "summary": r.summary.replace("\n", " "),
                    "url": r.entry_id,
                    "published": r.published.strftime("%Y-%m-%d"),
                    "source": "ArXiv"
                })
            
            print(f"✅ Encontrados {len(results)} papers en ArXiv")
            return results
        except Exception as e:
            print(f"❌ Error buscando en ArXiv: {e}")
            return []

    def search_web(self, query, max_results=5):
        """Busca información general en DuckDuckGo."""
        try:
            print(f"🔍 Buscando en DuckDuckGo: {query}")
            results = []
            # Usar 'text' para búsqueda estándar
            for r in self.ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r['title'],
                    "summary": r['body'],
                    "url": r['href'],
                    "source": "Web (DuckDuckGo)"
                })
            
            print(f"✅ Encontrados {len(results)} resultados web")
            return results
        except Exception as e:
            print(f"❌ Error buscando en Web: {e}")
            return []

    def unified_search(self, query):
        """Combina búsquedas de ArXiv y Web."""
        # Detectar si la consulta parece muy técnica para priorizar arxiv
        arxiv_results = self.search_arxiv(query)
        web_results = self.search_web(query)
        
        # Combinar: Primero papers, luego web
        return arxiv_results + web_results

if __name__ == "__main__":
    # Test rápido
    searcher = WebSearcher()
    res = searcher.unified_search("RAG retrieval augmented generation")
    for item in res:
        print(f"- [{item['source']}] {item['title']}: {item['url']}")
