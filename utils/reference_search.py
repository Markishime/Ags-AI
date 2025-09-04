"""
Reference Search Module for Agricultural Analysis
Searches both Firestore database and web for relevant references
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False
    logger.warning("Tavily client not available. Web search will be disabled.")

try:
    # Use our configured Firestore client instead of direct import
    from utils.firebase_config import get_firestore_client
    FIRESTORE_AVAILABLE = True
except ImportError:
    FIRESTORE_AVAILABLE = False
    logger.warning("Firestore not available. Database search will be disabled.")


class ReferenceSearchEngine:
    """Search engine for finding relevant references from database and web"""
    
    def __init__(self):
        self.tavily_client = None
        self.firestore_client = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize Tavily and Firestore clients"""
        # Initialize Tavily client
        if TAVILY_AVAILABLE:
            # Try Streamlit secrets first
            tavily_api_key = None
            try:
                import streamlit as st
                if hasattr(st, 'secrets') and 'tavily' in st.secrets:
                    tavily_api_key = st.secrets.tavily.get('tavily_api_key')
            except:
                pass
            
            # Fallback to environment variable
            if not tavily_api_key:
                tavily_api_key = os.getenv('TAVILY_API_KEY')
                
            if tavily_api_key:
                try:
                    self.tavily_client = TavilyClient(api_key=tavily_api_key)
                    logger.info("Tavily client initialized successfully")
                except Exception as e:
                    logger.error(f"Failed to initialize Tavily client: {str(e)}")
            else:
                logger.warning("TAVILY_API_KEY not found in environment variables")
        
        # Initialize Firestore client
        if FIRESTORE_AVAILABLE:
            try:
                self.firestore_client = get_firestore_client()
                logger.info("Firestore client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Firestore client: {str(e)}")
    
    def search_database_references(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for references in Firestore reference_documents collection with enhanced PDF support"""
        if not self.firestore_client:
            logger.warning("Firestore client not available")
            return []
        
        try:
            # Search in reference_documents collection
            ref = self.firestore_client.collection('reference_documents')
            
            # Get more documents to filter (increased from limit * 3 to limit * 5)
            docs = ref.limit(limit * 5).stream()
            
            results = []
            for doc in docs:
                doc_data = doc.to_dict()
                doc_data['id'] = doc.id
                
                # Enhanced content extraction for PDFs
                title = self._extract_pdf_title(doc_data)
                content = self._extract_pdf_content(doc_data)
                file_type = doc_data.get('file_type', '').lower()
                file_name = doc_data.get('file_name', '')
                
                # Check if query terms appear in title, content, or tags
                searchable_text = f"{title} {content} {doc_data.get('tags', '')}".lower()
                query_terms = query.lower().split()
                
                if any(term in searchable_text for term in query_terms):
                    result = {
                        'id': doc.id,
                        'title': title,
                        'content': content,
                        'source': 'Database',
                        'url': doc_data.get('url', ''),
                        'tags': doc_data.get('tags', []),
                        'created_at': doc_data.get('created_at', ''),
                        'relevance_score': self._calculate_relevance_score(query_terms, searchable_text),
                        'file_type': file_type,
                        'file_name': file_name
                    }
                    
                    # Add PDF-specific information
                    if file_type == 'pdf' or file_name.lower().endswith('.pdf'):
                        result.update({
                            'pdf_title': doc_data.get('pdf_title', title),
                            'pdf_abstract': doc_data.get('pdf_abstract', ''),
                            'pdf_keywords': doc_data.get('pdf_keywords', []),
                            'pdf_authors': doc_data.get('pdf_authors', []),
                            'pdf_pages': doc_data.get('pdf_pages', 0),
                            'pdf_language': doc_data.get('pdf_language', 'en')
                        })
                    
                    results.append(result)
            
            # Sort by relevance and limit results
            results.sort(key=lambda x: x['relevance_score'], reverse=True)
            logger.info(f"Found {len(results)} relevant database references for query: {query}")
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error searching database references: {str(e)}")
            return []
    
    def _extract_pdf_title(self, doc_data: Dict[str, Any]) -> str:
        """Extract PDF title with fallback options"""
        # Try different title fields in order of preference
        title_fields = ['pdf_title', 'title', 'document_title', 'name']
        
        for field in title_fields:
            title = doc_data.get(field, '').strip()
            if title and len(title) > 3:  # Valid title
                return title
        
        # Fallback to filename without extension
        file_name = doc_data.get('file_name', '')
        if file_name:
            import os
            name_without_ext = os.path.splitext(file_name)[0]
            if name_without_ext:
                return name_without_ext.replace('_', ' ').replace('-', ' ').title()
        
        return 'Untitled Document'
    
    def _extract_pdf_content(self, doc_data: Dict[str, Any]) -> str:
        """Extract PDF content with fallback options"""
        # Try different content fields in order of preference
        content_fields = ['pdf_content', 'content', 'text_content', 'extracted_text', 'abstract']
        
        for field in content_fields:
            content = doc_data.get(field, '').strip()
            if content and len(content) > 50:  # Substantial content
                # Truncate very long content to avoid token limits
                if len(content) > 2000:
                    content = content[:2000] + "..."
                return content
        
        # If no substantial content, try to build from available fields
        content_parts = []
        
        # Add abstract if available
        abstract = doc_data.get('pdf_abstract', '').strip()
        if abstract:
            content_parts.append(f"Abstract: {abstract}")
        
        # Add keywords if available
        keywords = doc_data.get('pdf_keywords', [])
        if keywords:
            content_parts.append(f"Keywords: {', '.join(keywords)}")
        
        # Add tags if available
        tags = doc_data.get('tags', [])
        if tags:
            content_parts.append(f"Tags: {', '.join(tags)}")
        
        return ' '.join(content_parts) if content_parts else 'No content available'
    
    def search_web_references(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for references on the web using Tavily API with enhanced search strategies"""
        if not self.tavily_client:
            logger.warning("Tavily client not available")
            return []
        
        try:
            # Create multiple search queries for comprehensive results
            search_queries = self._create_search_queries(query)
            all_results = []
            
            # Search with different query variations
            for search_query in search_queries:
                try:
                    response = self.tavily_client.search(
                        query=search_query,
                        search_depth="advanced",
                        max_results=limit // len(search_queries) + 2,  # Distribute results across queries
                        include_domains=["researchgate.net", "sciencedirect.com", "mpob.gov.my", 
                                       "fao.org", "cabi.org", "springer.com", "wiley.com", 
                                       "academic.oup.com", "nature.com", "frontiersin.org"],
                        exclude_domains=["wikipedia.org", "reddit.com", "youtube.com", "facebook.com"]
                    )
                    
                    for result in response.get('results', []):
                        all_results.append({
                            'title': result.get('title', 'Untitled'),
                            'content': result.get('content', ''),
                            'source': 'Web',
                            'url': result.get('url', ''),
                            'published_date': result.get('published_date', ''),
                            'relevance_score': result.get('score', 0.0),
                            'search_query_used': search_query
                        })
                        
                except Exception as e:
                    logger.warning(f"Error with search query '{search_query}': {str(e)}")
                    continue
            
            # Remove duplicates based on URL
            seen_urls = set()
            unique_results = []
            for result in all_results:
                url = result.get('url', '')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_results.append(result)
            
            # Sort by relevance and limit results
            unique_results.sort(key=lambda x: x['relevance_score'], reverse=True)
            logger.info(f"Found {len(unique_results)} unique web references for query: {query}")
            return unique_results[:limit]
            
        except Exception as e:
            logger.error(f"Error searching web references: {str(e)}")
            return []
    
    def _create_search_queries(self, original_query: str) -> List[str]:
        """Create multiple search query variations for comprehensive results"""
        query_terms = original_query.lower().split()
        
        # Base agricultural terms
        base_terms = ['oil palm', 'cultivation', 'malaysia']
        
        # Extract key terms from original query
        important_terms = ['nutrient', 'fertilizer', 'soil', 'yield', 'economic', 'forecast', 
                          'analysis', 'recommendations', 'management', 'sustainability', 'regenerative']
        
        found_terms = [term for term in important_terms if term in query_terms]
        
        # Create different query variations
        queries = []
        
        # 1. Original query (truncated)
        if len(original_query) <= 400:
            queries.append(original_query)
        
        # 2. Base + found terms
        if found_terms:
            base_query = f"{' '.join(base_terms)} {' '.join(found_terms[:3])}"
            if len(base_query) <= 400:
                queries.append(base_query)
        
        # 3. Specific agricultural focus
        agri_query = f"oil palm cultivation malaysia agricultural practices"
        if len(agri_query) <= 400:
            queries.append(agri_query)
        
        # 4. Research focus
        research_query = f"oil palm research malaysia scientific studies"
        if len(research_query) <= 400:
            queries.append(research_query)
        
        # 5. Economic focus
        economic_query = f"oil palm economics malaysia yield optimization"
        if len(economic_query) <= 400:
            queries.append(economic_query)
        
        # Ensure all queries are under 400 characters
        final_queries = []
        for query in queries:
            if len(query) > 400:
                query = query[:397] + "..."
            final_queries.append(query)
        
        # Remove duplicates and limit to 3 queries max
        unique_queries = list(dict.fromkeys(final_queries))[:3]
        
        return unique_queries if unique_queries else [f"oil palm cultivation malaysia"]
    
    def _calculate_relevance_score(self, query_terms: List[str], text: str) -> float:
        """Calculate relevance score based on term frequency"""
        score = 0.0
        text_lower = text.lower()
        
        for term in query_terms:
            if term in text_lower:
                # Count occurrences
                count = text_lower.count(term)
                score += count * 0.1
                
                # Bonus for title matches
                if term in text_lower[:100]:  # First 100 chars (likely title)
                    score += 0.5
        
        return min(score, 1.0)  # Cap at 1.0
    
    def search_all_references(self, query: str, db_limit: int = 8, web_limit: int = 8) -> Dict[str, List[Dict[str, Any]]]:
        """Search both database and web for references with enhanced limits"""
        logger.info(f"Searching references for query: {query}")
        
        # Search database references
        db_results = self.search_database_references(query, db_limit)
        logger.info(f"Found {len(db_results)} database references")
        
        # Search web references
        web_results = self.search_web_references(query, web_limit)
        logger.info(f"Found {len(web_results)} web references")
        
        return {
            'database_references': db_results,
            'web_references': web_results,
            'total_found': len(db_results) + len(web_results),
            'search_query': query,
            'search_timestamp': datetime.now().isoformat()
        }
    
    def format_references_for_display(self, references: Dict[str, List[Dict[str, Any]]]) -> str:
        """Format references for display in results"""
        if not references or references.get('total_found', 0) == 0:
            return "No relevant references found."
        
        formatted_text = []
        formatted_text.append("## 📚 Research References")
        formatted_text.append("")
        
        # Database references
        db_refs = references.get('database_references', [])
        if db_refs:
            formatted_text.append("### 🗄️ Database References")
            formatted_text.append("")
            for i, ref in enumerate(db_refs, 1):
                formatted_text.append(f"**{i}. {ref['title']}**")
                formatted_text.append(f"   - Source: {ref['source']}")
                if ref.get('url'):
                    formatted_text.append(f"   - URL: {ref['url']}")
                if ref.get('tags'):
                    formatted_text.append(f"   - Tags: {', '.join(ref['tags'])}")
                formatted_text.append(f"   - Relevance: {ref.get('relevance_score', 0):.2f}")
                formatted_text.append("")
        
        # Web references
        web_refs = references.get('web_references', [])
        if web_refs:
            formatted_text.append("### 🌐 Web References")
            formatted_text.append("")
            for i, ref in enumerate(web_refs, 1):
                formatted_text.append(f"**{i}. {ref['title']}**")
                formatted_text.append(f"   - Source: {ref['source']}")
                if ref.get('url'):
                    formatted_text.append(f"   - URL: {ref['url']}")
                if ref.get('published_date'):
                    formatted_text.append(f"   - Published: {ref['published_date']}")
                formatted_text.append(f"   - Relevance: {ref.get('relevance_score', 0):.2f}")
                formatted_text.append("")
        
        return "\n".join(formatted_text)
    
    def get_reference_summary(self, references: Dict[str, List[Dict[str, Any]]]) -> str:
        """Get a comprehensive summary of references for inclusion in analysis"""
        if not references or references.get('total_found', 0) == 0:
            return "No relevant references found to support this analysis."
        
        db_count = len(references.get('database_references', []))
        web_count = len(references.get('web_references', []))
        
        summary_parts = []
        summary_parts.append(f"Analysis supported by {db_count} database reference(s) and {web_count} web reference(s).")
        
        # Add key insights from top references
        all_refs = references.get('database_references', []) + references.get('web_references', [])
        if all_refs:
            # Sort by relevance score
            sorted_refs = sorted(all_refs, key=lambda x: x.get('relevance_score', 0), reverse=True)
            
            # Add top 3 references
            top_refs = sorted_refs[:3]
            summary_parts.append("Key references:")
            
            for i, ref in enumerate(top_refs, 1):
                title = ref.get('title', 'Untitled')[:100]  # Truncate long titles
                source = ref.get('source', 'Unknown')
                score = ref.get('relevance_score', 0)
                summary_parts.append(f"{i}. {title} ({source}, relevance: {score:.2f})")
            
            # Add PDF-specific information if available
            pdf_refs = [ref for ref in all_refs if ref.get('file_type') == 'pdf' or ref.get('file_name', '').lower().endswith('.pdf')]
            if pdf_refs:
                summary_parts.append(f"Found {len(pdf_refs)} PDF research documents with detailed content.")
        
        return " ".join(summary_parts)


# Global instance
reference_search_engine = ReferenceSearchEngine()
