from google.generativeai import configure, embeddings

configure(api_key="AIzaSyC7LlqtO9BPw7POjxQ_MBc2v2xGMcLKOs8")

resp = embeddings.embed_content(
    model="models/embedding-001",  # hoặc thử "models/gemini-embedding-001" nếu docs có
    content="Xin chào, tôi đang thử embedding.",
    output_dimensionality=768,
)

print(len(resp['embedding']))

# python