import time
import json
from typing import List
from enum import Enum
from pydantic import BaseModel, Field, field_validator
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import ServerSentEvent, EventSourceResponse

from langchain.embeddings import HuggingFaceBgeEmbeddings
from backend.llm import QwenService, ChatGLMService

from arguments import (
    api_config,
    llm_config,
    embeddings_config
)

app = FastAPI(
    title="Core LLM & Embeddings model service API",
    version='0.0.1'
)

### CORS (Cross-Origin Resource Sharing)

origins = [
    f"http://{api_config.view['host']}",
    f"http://{api_config.view['url']}",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================== Initialize components =================== #
print('Loading LLM model')
models = {}
for name, single_model in llm_config.items():
    assert single_model.type.lower() in ['chatglm', 'qwen']
    if single_model.type.lower() == 'chatglm':
        model = ChatGLMService()
    else:
        model = QwenService()
    model.load_model(single_model)
    models[name] = model
model_names = list(llm_config.keys())

print('Loading embedding function')
embedding_func = HuggingFaceBgeEmbeddings(**embeddings_config)

# Check health of application
@app.get('/notify/v1/health')
def get_health():
    """
    Usage on K8S
    readinessProbe:
        httpGet:   path: /notify/v1/health
            port: 80
    livenessProbe:
        httpGet:
            path: /notify/v1/health
            port: 80
    :return:
        dict(msg='OK')
    """
    return dict(msg='OK')

class ChatRole(str, Enum):
    system = 'system'
    user = 'user'
    assistant = 'assistant'
    observation = 'observaton'

model_enum = {k: k for k in model_names}
model_enum.update({'DEFAULT': None})
SelectModels = Enum('SelectModels', model_enum)

class ChatMessage(BaseModel):
    query: str = Field(..., description='Inputs for chat')
    history: list = Field([], description='Chat history')
    role: ChatRole = Field(None, description='Prompt role')
    temperature: float = Field(None, ge=0, le=1.0, description='Inference parameter Temerpature')
    top_p: float = Field(None, ge=0, le=1.0, description='Inference parameter Top p')
    repetition_penalty: float = Field(None, ge=0, description='To avoid repeating')
    select_model: SelectModels = Field(model_names[0], description='The model selected for inference')

@app.post('/api/chat')
async def get_chat_response(args: ChatMessage):
    kwargs = {}
    for key, val in args.model_dump().items():
        if val is not None and key not in ['select_model']:
            kwargs[key] = val
    
    st_time = time.time()
    model_name = args.select_model.value if args.select_model.value is not None else model_names[0]
    response, history = models[model_name]._call(**kwargs)
    end_time = time.time()
    data = {'response': response, 'history': history, 'inference_time': end_time-st_time}
    return {'msg': '生成成功', 'data': data}


@app.post('/api/stream_chat')
async def get_stream_chat_response(args: ChatMessage, response: Response):
    response.headers['Content-Type'] = 'text/event-stream'
    response.headers['Cache-Control'] = 'no-cache'
    
    kwargs = {}
    for key, val in args.model_dump().items():
        if val is not None and key not in ['select_model']:
            kwargs[key] = val
    model_name = args.select_model.value if args.select_model.value is not None else model_names[0]
    
    async def event_generator():
        response, history = '', []
        for response, history in models[model_name]._stream_call(**kwargs):
            yield {
                "event": "stream_chat",
                "retry": 15000,
                "data": json.dumps({'response': response})
            }
        yield {
            "event": "stream_chat",
            "retry": 15000,
            "data": json.dumps({'response': response, 'history': history})
        }
        
        yield {"event": "stream_chat", "retry": 0, "data": '[DONE]'}
    
    return EventSourceResponse(event_generator())


class EmbeddingData(BaseModel):
    texts: List[str]
    
    @field_validator('texts', mode='before')
    def validate_text_list(cls, value):
        if not value:
            return []
        
        if not isinstance(value, list):
            raise ValueError('传入texts类型错误，必须是list类型')
        else:
            for val in value:
                if not isinstance(val, str):
                    raise ValueError('texts参数类型错误，内部必须是str类型')
        return value

@app.post('/api/embedding')
async def get_embedding(args: EmbeddingData):
    try:
        try:
            embeddings = embedding_func.embed_documents(args.texts)
        except NotImplementedError:
            embeddings = [embedding_func.embed_query(x) for x in args.texts]
        data = {'embeddings': embeddings}
        return {'status': 200, 'msg': '生成成功', 'data': data}
    except Exception as e:
        print(e)
        return {'status': 500, 'msg': '数据验证未通过！', 'data': {}}
    

def main():
    import uvicorn
    uvicorn.run(app,
                host=api_config.model['host'],
                port=api_config.model['port'])
    

if __name__ == '__main__':
    main()