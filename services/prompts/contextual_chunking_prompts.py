"""
Centralized prompt templates for the RAG pipeline.

Keeping prompts here (instead of inline in service code) makes them
easy to find, version, and tune independently of the business logic
that calls them.
"""

# ----------------------------------------
# Contextual chunking (contextual retrieval)
# ----------------------------------------
#
# Used by ChunkEmbedder to generate a short piece of context for each
# chunk before it is embedded, so retrieval still works even when a
# chunk reads ambiguously on its own (missing the subject/section it
# belongs to, referenced pronouns, etc).

CONTEXTUAL_CHUNK_SYSTEM_PROMPT = (
    "You are an assistant that writes short context notes for chunks "
    "taken from a larger document. Your note will be prepended to the "
    "chunk before it is embedded and indexed, so it must help a search "
    "system understand what the chunk is about within the larger "
    "document. Be concise and strictly factual - only use information "
    "that is present in the document, never invent details."
)

CONTEXTUAL_CHUNK_USER_PROMPT = """Here is the full document for reference:

<document>
{document}
</document>

Here is a chunk taken from that document:

<chunk>
{chunk}
</chunk>

Write a short (1-2 sentence) context note that situates this chunk \
within the overall document, so the chunk can be understood on its \
own and retrieved accurately by a search system. Respond with only \
the context note - no preamble, no labels, no quotation marks."""