"""
Vocabularies that encode the job description as machine-readable signal.

The Senior AI Engineer JD is unusually explicit about what counts and what does
not. These sets turn that prose into the terms the scorer looks for in a
candidate's titles, career-history descriptions, and skills. Keeping them in one
place makes the scoring auditable and easy to defend at interview.
"""

# Core of the role: retrieval, ranking, search, recommendation, modern ML.
# (Matched on word boundaries via khoj.match, so short tokens are safe.)
CORE_ML = {
    "embedding", "embeddings", "retrieval", "ranking", "recommendation",
    "recommender", "recsys", "relevance", "information retrieval",
    "semantic search", "vector search", "nearest neighbor", "nlp",
    "natural language", "machine learning", "deep learning", "ml", "llm", "llms",
    "language model", "fine-tuning", "fine-tuned", "finetuning", "transformer",
    "transformers", "personalization", "rag", "model training", "feature engineering",
    "learning to rank", "learning-to-rank", "ltr",
}

# Plain-language evidence of real retrieval/ranking/search work. The strongest
# tier-5 candidates describe their systems without product buzzwords ("the
# ranking layer", "connect users with relevant information"), so we credit the
# work itself, not just the brand names. These phrases come from the actual
# career-history descriptions of the dataset's genuine builders.
PLAIN_IR = {
    "ranking model", "ranking models", "ranking layer", "ranking system",
    "recommendation system", "recommendation models", "discovery feed",
    "search and discovery", "search backend", "search infrastructure",
    "personalization infrastructure", "personalization system", "matching layer",
    "connect users with relevant", "most relevant results", "relevance over time",
    "query understanding", "embedding-based retrieval", "hybrid retrieval",
    "candidate generation", "two-tower", "two tower", "dense retrieval",
    "sparse retrieval", "index refresh", "embedding drift", "content matching",
    "how content is represented", "intelligence layer", "relevance improvement",
}

# Vector databases and hybrid-search infrastructure the JD names explicitly.
VECTOR_INFRA = {
    "pinecone", "weaviate", "qdrant", "milvus", "opensearch", "elasticsearch",
    "faiss", "vespa", "bm25", "hybrid search", "annoy", "hnsw", "pgvector",
}

# Embedding model families the JD lists as evidence of real retrieval work.
EMBED_MODELS = {"sentence-transformer", "sentence transformers", "bge", "e5",
                "openai embedding", "cohere embed", "instructor", "gte"}

# Evaluation literacy the JD calls essential. ("map" dropped: too ambiguous even
# on word boundaries; "mean average precision" covers it.)
EVAL_TERMS = {"ndcg", "mrr", "mean average precision", "precision@", "recall@",
              "a/b test", "ab test", "offline eval", "online eval", "ranking metric",
              "evaluation framework", "offline metrics", "online engagement",
              "holdout", "click-through", "human judgments", "relevance judgments"}

# "Nice to have" per the JD.
NICE = {"lora", "qlora", "peft", "xgboost", "lightgbm", "learning to rank",
        "hr-tech", "recruiting", "marketplace", "distributed systems",
        "inference optimization", "open source", "open-source"}

# Evidence the person actually shipped production systems to real users.
PRODUCTION = {"production", "deployed", "shipped", "real users", "at scale",
              "scaled", "served", "latency", "throughput", "live", "users",
              "owned", "end to end", "end-to-end", "launched", "rolled out"}

# Titles that clearly fit the role.
GOOD_TITLES = {
    "ai engineer", "machine learning engineer", "ml engineer", "applied scientist",
    "applied ml", "research engineer", "data scientist", "search engineer",
    "relevance engineer", "recommendation", "nlp engineer", "ml scientist",
    "staff machine learning", "senior machine learning", "principal machine learning",
}

# Adjacent titles: possible fit only if the career history proves ML/IR work.
ADJACENT_TITLES = {
    "software engineer", "backend engineer", "data engineer", "analytics engineer",
    "full stack developer", "fullstack", "platform engineer", "data analyst",
    "research scientist",
}

# Titles that, paired with an AI-heavy skill list, signal a keyword stuffer.
OFFROLE_TITLES = {
    "business analyst", "hr manager", "mechanical engineer", "accountant",
    "project manager", "customer support", "operations manager", "content writer",
    "sales executive", "civil engineer", "graphic designer", "marketing manager",
    "qa engineer", "mobile developer", "frontend engineer", ".net developer",
    "java developer", "devops engineer", "cloud engineer",
}

# Indian consulting/services houses. A whole career here is a JD disqualifier
# unless there is also product-company experience.
SERVICES_FIRMS = {
    "infosys", "tcs", "tata consultancy", "wipro", "accenture", "cognizant",
    "capgemini", "tech mahindra", "hcl", "mindtree", "ltimindtree", "mphasis",
    "deloitte", "ibm", "dxc",
}

# Recognizable product companies (real and the dataset's fictional placeholders).
PRODUCT_FIRMS = {
    "swiggy", "cred", "flipkart", "razorpay", "zomato", "google", "microsoft",
    "amazon", "meta", "uber", "netflix", "atlassian", "phonepe", "myntra",
    "wayne enterprises", "initech", "pied piper", "globex", "acme corp", "acme",
    "dunder mifflin", "hooli", "stark industries",
}

# Computer-vision / speech / robotics focus without NLP/IR is a JD disqualifier.
CV_SPEECH_ROBOTICS = {
    "computer vision", "image classification", "object detection", "segmentation",
    "speech recognition", "tts", "text to speech", "asr", "robotics", "slam",
    "gans", "opencv", "yolo", "pose estimation", "image moderation", "resnet",
    "facial recognition", "ocr", "video analytics",
}

# Genuine NLP / information-retrieval evidence. Tightened: bare "text" and
# "search" were so common they disabled the CV disqualifier entirely.
NLP_IR = {"nlp", "natural language", "information retrieval", "retrieval",
          "semantic search", "ranking", "recommendation", "language model",
          "llm", "question answering", "named entity", "text classification"}

# Templated "tell" sentences that mark the dataset's 1,000 analyst decoys: people
# who list AI keywords aspirationally but whose real work is classical modeling,
# analytics, or classification. These phrases are near-exclusive to that class.
ANALYST_TELL = {
    "still building depth on the engineering",
    "strongest at the modeling and analysis side",
    "lighter on the deep-learning side",
    "production deployment was handled by the platform team",
    "my professional experience there is limited",
    "beyond the surface level",
    "looking to grow into",
    "want to grow into",
    "transitioning toward",
    "building competence on the ml side",
    "interested in transitioning",
    "lightweight deployment",
    "predictive modeling for customer",
    "dashboarding/analytics",
}

# Indian metros the JD welcomes (Pune/Noida preferred; these are in scope).
INDIA_HUBS = {"pune", "noida", "hyderabad", "mumbai", "delhi", "gurugram",
              "gurgaon", "bengaluru", "bangalore", "new delhi", "ncr", "chennai"}

# Recent-only LangChain-on-OpenAI signal (framework enthusiast risk).
FRAMEWORK_ONLY = {"langchain", "llamaindex", "autogpt", "openai api", "prompt engineering"}
