# required: tools that MUST be called. forbidden: tools that must NOT be called.
QUESTIONS = [
    {"q": "Hello!", "required": set(), "forbidden": {"calculator", "wikipedia_search", "search_documents", "current_time"}},
    {"q": "What is 17 * 23?", "required": {"calculator"}, "forbidden": {"wikipedia_search"}},
    {"q": "What time is it now?", "required": {"current_time"}, "forbidden": {"wikipedia_search"}},
    {"q": "Who wrote War and Peace?", "required": {"wikipedia_search"}, "forbidden": {"search_documents"}},
    {"q": "What do my documents say about my job experience?", "required": {"search_documents"}, "forbidden": {"wikipedia_search"}},
    {"q": "How many years have passed since Saint Petersburg was founded?",
     "required": {"wikipedia_search", "current_time", "calculator"}, "forbidden": set()},
    {"q": "What is the capital of France?", "required": ("wikipedia_search"), "forbidden": {"search_documents"}},
]