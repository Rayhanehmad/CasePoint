"""
Batch AI Summarizer for Legal Citations
Cost-optimized using GPT-3.5-turbo with batch processing
"""

import os
import logging
import openai
import json
from typing import List, Dict

logger = logging.getLogger(__name__)

class BatchSummarizer:
    """Batch summarizer for cost-efficient AI processing"""
    
    def __init__(self):
        """Initialize batch summarizer"""
        openai.api_key = os.environ.get('OPENAI_API_KEY')
        self.max_summary_words = 150
        self.batch_size = 15  # Process 15 citations per API call for cost efficiency
    
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
            # Build batch prompt
            batch_input = []
            for idx, block in enumerate(batch):
                # Limit text to first 2000 chars to save tokens
                text_sample = block['text'][:2000]
                batch_input.append({
                    'index': idx,
                    'citation': block['citation'],
                    'text': text_sample
                })
            
            # Create prompt for batch processing
            prompt = f"""You are a legal case summarizer for Pakistani law. Below are {len(batch)} legal citations with their text. For each citation, generate a concise summary (maximum 150 words) that includes:
1. Case title (parties involved)
2. Key legal issue
3. Court's decision/holding
4. Brief reasoning

Return your response as a JSON array with format: [{{"index": 0, "summary": "..."}}, {{"index": 1, "summary": "..."}}]

Citations:
---
{json.dumps(batch_input, indent=2)}
---

Respond ONLY with the JSON array, no other text."""

            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a legal case summarizer. Always respond with valid JSON arrays."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=len(batch) * 200  # Allocate ~200 tokens per summary
            )
            
            # Parse response
            response_text = response.choices[0].message['content'].strip()
            
            # Extract JSON from response (handle markdown code blocks)
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()
            
            summaries = json.loads(response_text)
            
            # Apply summaries to batch
            for summary_obj in summaries:
                idx = summary_obj['index']
                if 0 <= idx < len(batch):
                    batch[idx]['summary'] = summary_obj['summary']
                    logger.debug(f"Generated summary for {batch[idx]['citation']}")
            
            # Calculate cost (approximate)
            tokens_used = response.usage['total_tokens']
            cost = (tokens_used / 1000) * 0.002  # GPT-3.5-turbo: $0.002 per 1k tokens
            logger.info(f"Batch processed: {len(batch)} citations, {tokens_used} tokens, ~${cost:.4f}")
            
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

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a legal case summarizer for Pakistani law."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=250
            )
            
            return response.choices[0].message['content'].strip()
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return f"Legal case {citation_code}. Summary generation failed."


# Global instance
batch_summarizer = BatchSummarizer()
