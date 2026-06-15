"""
Configuration — JD-derived constants, weights, and thresholds.

Everything in this file is derived from careful reading of the job description
for Senior AI Engineer at Redrob AI (Series A, Pune/Noida).
"""

from datetime import date

# =============================================================================
# Reference date for time calculations
# =============================================================================
# Use a fixed date so results are reproducible regardless of when the code runs.
REFERENCE_DATE = date(2026, 6, 13)

# =============================================================================
# JD-Derived Skill Categories
# =============================================================================

# Skills the JD says "you absolutely need"
CORE_MUST_HAVE_SKILLS = {
    # Embeddings & retrieval
    "embeddings", "sentence-transformers", "sentence transformers",
    "openai embeddings", "bge", "e5", "embedding",
    # Vector databases & hybrid search
    "pinecone", "weaviate", "qdrant", "milvus", "opensearch",
    "elasticsearch", "faiss", "vector search", "vector database",
    "hybrid search",
    # Core ML/AI
    "nlp", "natural language processing", "information retrieval",
    "ranking", "recommendation systems", "search",
    "retrieval", "re-ranking", "reranking",
    # Evaluation
    "ndcg", "mrr", "map", "a/b testing", "ab testing",
    # Python
    "python",
}

# Skills the JD says "we'd like but won't reject you for"
NICE_TO_HAVE_SKILLS = {
    "lora", "qlora", "peft", "fine-tuning", "fine tuning",
    "fine-tuning llms", "llm fine-tuning",
    "xgboost", "learning to rank", "learning-to-rank",
    "lightgbm", "catboost",
    "distributed systems", "large-scale inference",
    "hr-tech", "recruiting", "marketplace",
    "open-source", "open source",
}

# Skills the JD explicitly says "we do NOT want primary expertise in"
NEGATIVE_DOMAIN_SKILLS = {
    "computer vision", "image classification", "object detection",
    "image segmentation", "opencv", "yolo",
    "speech recognition", "speech", "tts", "text-to-speech",
    "asr", "automatic speech recognition",
    "robotics", "ros", "robot operating system",
    "gans", "generative adversarial",
}

# Adjacent/related ML skills — not in JD but indicate ML competence
ADJACENT_ML_SKILLS = {
    "deep learning", "machine learning", "pytorch", "tensorflow",
    "keras", "scikit-learn", "sklearn", "huggingface", "transformers",
    "bert", "gpt", "llm", "rag", "langchain", "llamaindex",
    "mlops", "mlflow", "wandb", "weights & biases",
    "feature engineering", "model deployment", "model serving",
    "bentoml", "triton", "onnx", "tensorrt",
}

# =============================================================================
# Company Classification
# =============================================================================

# JD explicitly calls out these as bad fit (entire career here = heavy penalty)
SERVICE_CONSULTING_COMPANIES = {
    "tcs", "infosys", "wipro", "accenture", "cognizant", "capgemini",
    "hcl", "tech mahindra", "mindtree", "mphasis", "l&t infotech",
    "hexaware", "persistent systems", "cyient", "zensar",
    "genpact ai", "genpact",
}

# Known product/tech companies (positive signal)
PRODUCT_COMPANIES = {
    # Global Tech Product Companies
    "google", "meta", "facebook", "amazon", "microsoft", "apple",
    "netflix", "uber", "airbnb", "stripe", "spotify", "twitter",
    "linkedin", "salesforce", "adobe", "atlassian", "shopify",
    # Indian Product Startups & Unicorns
    "flipkart", "swiggy", "zomato", "razorpay", "cred",
    "phonepe", "paytm", "ola", "meesho", "groww", "zerodha",
    "freshworks", "zoho", "postman", "browserstack", "chargebee",
    "hasura", "druva", "icertis", "innovaccer", "unacademy",
    "byju's", "dream11", "nykaa", "inmobi", "policybazaar", "vedantu",
    "pharmeasy", "upgrad", "glance",
    # AI/ML Indian Product Companies
    "rephrase.ai", "aganitha", "niramai", "saarthi.ai", "sarvam ai",
    "mad street den", "observe.ai", "krutrim", "wysa", "haptik",
    "yellow.ai", "verloop.io", "locobuzz",
    # Redrob itself
    "redrob",
    # Fictional Product Companies
    "stark industries", "wayne enterprises", "pied piper",
    "hooli", "globex inc", "initech", "acme corp", "dunder mifflin",
}

# Kept for backward compatibility in imports
FICTIONAL_PRODUCT_COMPANIES = set()

# =============================================================================
# ML/AI Title Keywords
# =============================================================================

# Words in job titles that indicate ML/AI/NLP production work
ML_TITLE_KEYWORDS = {
    "machine learning", "ml", "ai", "artificial intelligence",
    "data scientist", "data science", "nlp", "nlu",
    "deep learning", "research scientist", "research engineer",
    "applied scientist", "ranking", "search engineer",
    "recommendation", "information retrieval",
}

# Non-technical titles that indicate keyword stuffing when combined with
# many AI skills — the JD explicitly warns about this pattern
KEYWORD_STUFFER_TITLES = {
    "marketing manager", "marketing director", "marketing specialist",
    "hr manager", "hr director", "human resources manager",
    "accountant", "accounting manager", "finance manager",
    "sales manager", "sales director", "sales representative",
    "content writer", "copywriter",
    "graphic designer",
    "customer support", "customer service representative",
    "administrative assistant", "office manager",
    "legal counsel", "lawyer",
    "recruiter", "talent acquisition specialist",
    # Found via dataset audit — non-tech titles with AI skill inflation
    "business analyst", "project manager", "operations manager",
    "sales executive",
}

# =============================================================================
# Experience Band Scoring
# =============================================================================

# JD says "5-9 years" with ideal being "6-8 years"
EXPERIENCE_IDEAL_MIN = 6.0
EXPERIENCE_IDEAL_MAX = 8.0
EXPERIENCE_ACCEPTABLE_MIN = 4.0
EXPERIENCE_ACCEPTABLE_MAX = 12.0

# =============================================================================
# Location
# =============================================================================

# JD says Pune/Noida preferred, Tier-1 Indian cities welcome
PREFERRED_LOCATIONS = {
    "pune", "noida", "delhi", "delhi ncr", "new delhi",
    "gurgaon", "gurugram",
}
ACCEPTABLE_LOCATIONS = {
    "hyderabad", "mumbai", "bangalore", "bengaluru",
    "chennai", "kolkata",
}
PREFERRED_COUNTRY = "india"

# =============================================================================
# Behavioral Signal Thresholds
# =============================================================================

# Dead lead: inactive for 6+ months
ACTIVITY_STALE_MONTHS = 6

# JD prefers notice period < 30 days, can buy out up to 30
NOTICE_PERIOD_IDEAL_MAX = 30
NOTICE_PERIOD_ACCEPTABLE_MAX = 90

# Minimum engagement signals
MIN_RECRUITER_RESPONSE_RATE = 0.10   # Below this = ghost
MIN_PROFILE_COMPLETENESS = 40.0      # Below this = not serious

# =============================================================================
# Education
# =============================================================================

RELEVANT_EDUCATION_FIELDS = {
    "computer science", "computer engineering", "cs",
    "artificial intelligence", "machine learning",
    "data science", "statistics", "mathematics",
    "information technology", "electrical engineering",
    "electronics", "ece", "eee",
}

# =============================================================================
# Scoring Weights (tuned for NDCG@10 optimization)
# =============================================================================

WEIGHTS = {
    "career_relevance":     0.30,  # Product company + ML/AI roles
    "skills_match":         0.25,  # Core JD skill alignment
    "experience_band":      0.15,  # Years of experience fit
    "behavioral_signals":   0.15,  # Engagement, response rate, activity
    "location_logistics":   0.10,  # Location, notice period, work mode
    "education":            0.05,  # Institution tier, relevant degree
}

# =============================================================================
# Honeypot Detection Thresholds
# =============================================================================

# If a candidate claims expert in N+ skills with 0 months duration each
HONEYPOT_EXPERT_ZERO_DURATION_THRESHOLD = 3

# If total claimed skill duration exceeds possible career span by this factor
HONEYPOT_DURATION_IMPOSSIBILITY_FACTOR = 2.0

# =============================================================================
# Suspicion Thresholds (for borderline profiles, not hard honeypots)
# =============================================================================

SUSPICION_THRESHOLDS = {
    # Expert skills with 0 duration (1-2, below the hard honeypot threshold of 3)
    "expert_zero_dur_1_2": 0.15,
    # Job duration exceeds calendar dates by 6-12 months (below hard threshold of 12)
    "date_mismatch_6_12": 0.10,
    # Single skill duration > 2x career span
    "skill_dur_extreme": 0.05,
}
