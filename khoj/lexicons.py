"""
Vocabularies that encode the job description as machine-readable signal.

The Senior AI Engineer JD is unusually explicit about what counts and what does
not. These sets turn that prose into the terms the scorer looks for in a
candidate's titles, career-history descriptions, and skills. Keeping them in one
place makes the scoring auditable and easy to defend at interview.
"""

# Core of the role: retrieval, ranking, search, recommendation, modern ML.
CORE_ML = {
    "embedding", "embeddings", "retrieval", "ranking", "rank", "recommendation",
    "recommender", "recsys", "search", "relevance", "information retrieval",
    "semantic search", "vector search", "nearest neighbor", "ann", "nlp",
    "natural language", "machine learning", "deep learning", "ml ", "llm",
    "language model", "fine-tun", "finetun", "transformer", "personalization",
    "matching", "rag", "neural", "model training", "feature engineering",
    "learning to rank", "learning-to-rank", "ltr",
}

# Vector databases and hybrid-search infrastructure the JD names explicitly.
VECTOR_INFRA = {
    "pinecone", "weaviate", "qdrant", "milvus", "opensearch", "elasticsearch",
    "faiss", "vespa", "bm25", "hybrid search", "annoy", "hnsw", "pgvector",
}

# Embedding model families the JD lists as evidence of real retrieval work.
EMBED_MODELS = {"sentence-transformer", "sentence transformers", "bge", "e5",
                "openai embedding", "cohere embed", "instructor", "gte"}

# Evaluation literacy the JD calls essential.
EVAL_TERMS = {"ndcg", "mrr", "map", "precision@", "recall@", "a/b test",
              "ab test", "offline eval", "online eval", "ranking metric",
              "evaluation framework", "holdout", "click-through"}

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
    "gans", "gan ", "opencv", "yolo", "pose estimation",
}

NLP_IR = {"nlp", "natural language", "information retrieval", "retrieval",
          "search", "ranking", "recommendation", "text", "language model", "llm"}

# Indian metros the JD welcomes (Pune/Noida preferred; these are in scope).
INDIA_HUBS = {"pune", "noida", "hyderabad", "mumbai", "delhi", "gurugram",
              "gurgaon", "bengaluru", "bangalore", "new delhi", "ncr", "chennai"}

# Recent-only LangChain-on-OpenAI signal (framework enthusiast risk).
FRAMEWORK_ONLY = {"langchain", "llamaindex", "autogpt", "openai api", "prompt engineering"}
