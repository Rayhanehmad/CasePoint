"""
Test script for improved citation extraction
Demonstrates extraction of complete citations without breaking at internal references
"""

import logging
import sys
sys.path.insert(0, 'backend')

from services.citation_parser import citation_parser

# Enable debug logging to see the START/END markers
logging.basicConfig(
    level=logging.DEBUG,
    format='%(message)s'
)

# Sample text with multiple citations and internal references
sample_text = """
2003 MLD 1077
Muhammad Ashraf v. The State
The court held that when a case cites PLD 2001 SC 123 and CLC 1999 Karachi 456 within the judgment, those internal references should remain part of this citation block and not break it into separate blocks. The principle established in SCMR 1998 1 was also discussed extensively in this case.

2003 MLD 1088
Abdul Rehman v. Federation of Pakistan
This judgment discusses constitutional matters. Reference was made to PLD 1996 SC 324 regarding fundamental rights. The court analyzed several precedents including YLR 2000 45 and PTD 2001 100 before reaching its conclusion.

PLD 2024 SC 1
State v. Ahmed Ali
Supreme Court judgment on criminal procedure. The court examined CLD 1995 Lahore 234 and distinguished it from the present case. Multiple references to older cases like MLD 1990 567 were made throughout the detailed analysis.
"""

print("=" * 80)
print("TESTING IMPROVED CITATION EXTRACTION")
print("=" * 80)

print("\n📄 SAMPLE DOCUMENT:")
print(sample_text[:300] + "...\n")

print("=" * 80)
print("EXTRACTING CITATIONS WITH IMPROVED METHOD")
print("=" * 80)

# Extract citations
citation_blocks = citation_parser.split_document_by_citations(sample_text)

print(f"\n✅ TOTAL CITATIONS EXTRACTED: {len(citation_blocks)}\n")

# Display each citation with clear markers
for i, block in enumerate(citation_blocks, 1):
    print(f"\n{'=' * 80}")
    print(f"===== START CITATION {i} =====")
    print(f"{'=' * 80}")
    print(f"[CITATION ID] {block['citation']}")
    print(f"[CODE] {block['code']}")
    print(f"[YEAR] {block['year']}")
    print(f"[COURT] {block['court']}")
    print(f"[TEXT LENGTH] {block['text_length']} characters")
    print(f"\n[TITLE PREVIEW]")
    title_preview = block['text'].split('\n')[0][:100]
    print(f"{title_preview}...")
    print(f"\n[FULL TEXT]")
    print(block['text'])
    print(f"\n{'=' * 80}")
    print(f"===== END CITATION {i} =====")
    print(f"{'=' * 80}\n")

# Check for internal references
print("\n" + "=" * 80)
print("VERIFICATION: CHECKING FOR INTERNAL REFERENCES")
print("=" * 80)

for i, block in enumerate(citation_blocks, 1):
    text = block['text']
    internal_refs = []
    
    # Check for common citation codes
    for code in ['PLD', 'CLC', 'CLD', 'MLD', 'SCMR', 'YLR', 'PTD', 'PCrLJ']:
        if code in text and code != block['code']:
            internal_refs.append(code)
    
    if internal_refs:
        print(f"\n✅ Citation {i} ({block['citation']}) contains internal references: {', '.join(set(internal_refs))}")
        print(f"   → These references are correctly kept within the same block!")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
