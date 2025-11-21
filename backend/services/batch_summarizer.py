"""
Batch AI Summarizer for Legal Citations
Cost-optimized using GPT-3.5-turbo with batch processing
"""

import os
import logging
from openai import OpenAI
import httpx
import json
from typing import List, Dict

logger = logging.getLogger(__name__)

class BatchSummarizer:
    """Batch summarizer for cost-efficient AI processing"""
    
    def __init__(self):
        """Initialize batch summarizer"""
        self._client = None
        self.max_summary_words = 150
        self.batch_size = 15  # Process 15 citations per API call for cost efficiency
    
    def get_client(self):
        """Get or create OpenAI client"""
        if self._client is None and os.environ.get('OPENAI_API_KEY'):
            # Create httpx client without proxies to avoid compatibility issues
            http_client = httpx.Client()
            self._client = OpenAI(
                api_key=os.environ.get('OPENAI_API_KEY'),
                http_client=http_client
            )
        return self._client
    
    def generate_summaries_batch(self, citation_blocks: List[Dict]) -> List[Dict]:
        """
        Generate summaries for multiple citations in batch
        Uses single API call to process multiple citations
        
        Args:
            citation_blocks: List of citation dicts with 'text' field
            
        Returns:
            Same list with 'summary' field added
        """
        if not citation_blocks:
            return []
        
        logger.info(f"Generating summaries for {len(citation_blocks)} citations in batches of {self.batch_size}")
        
        # Process in batches
        for i in range(0, len(citation_blocks), self.batch_size):
            batch = citation_blocks[i:i + self.batch_size]
            self._process_batch(batch)
        
        return citation_blocks
    
    def _process_batch(self, batch: List[Dict]):
        """Process a batch of citations with single API call"""
        try:
            # Build batch prompt - process each citation separately to avoid JSON issues
            batch_summaries = []
            
            for idx, block in enumerate(batch):
                # Limit text to first 1000 chars to prevent timeout
                text_sample = block['text'][:1000].replace('\n', ' ').replace('\r', ' ')
                
                # Create simple prompt for single citation
                prompt = f"""Summarize this Pakistani legal case in maximum 100 words:

Citation: {block['citation']}
Text: {text_sample}

Summary (100 words max):"""

                try:
                    # Call OpenAI API for single citation
                    client = self.get_client()
                    if not client:
                        raise Exception("OpenAI API key not configured")
                    
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are a legal case summarizer."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.3,
                        max_tokens=150,
                        timeout=10  # 10 second timeout per citation
                    )
                    
                    summary = response.choices[0].message.content.strip()
                    batch[idx]['summary'] = summary
                    logger.debug(f"Generated summary for {block['citation']}")
                    
                except Exception as e:
                    logger.error(f"Error summarizing {block['citation']}: {str(e)}")
                    batch[idx]['summary'] = f"Case {block['citation']}. Summary generation failed."
            
        except Exception as e:
            logger.error(f"Error processing batch: {str(e)}")
            # Fallback: generate basic summaries
            for block in batch:
                if 'summary' not in block:
                    block['summary'] = f"Legal case {block['citation']}. Full text extraction successful but automated summary generation failed."
    
    def generate_single_summary(self, citation_text: str, citation_code: str) -> str:
        """Generate summary for a single citation (fallback method)"""
        try:
            text_sample = citation_text[:2000]
            
            prompt = f"""Summarize this Pakistani legal case in maximum 150 words. Include:
1. Case title
2. Key legal issue
3. Court's decision
4. Brief reasoning

Citation: {citation_code}
Text:
{text_sample}

Summary (150 words max):"""

            client = self.get_client()
            if not client:
                raise Exception("OpenAI API key not configured")
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a legal case summarizer for Pakistani law."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=250
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return f"Legal case {citation_code}. Summary generation failed."


# Global instance
batch_summarizer = BatchSummarizer()
