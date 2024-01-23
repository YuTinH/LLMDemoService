from langchain.llms.base import LLM

from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers.generation import GenerationConfig

from agent.transform import trans_general_history


class QwenCFG:
    num_gpus = 1

    multi_gpu_model_cache_dir = "./temp_model_dir"
    llm_name_or_path = 'Qwen/Qwen-7B-Chat'  # 本地模型文件 or huggingface远程仓库
    device_map = 'auto'
    fp16 = False
    bf16 = False
    quantization_bit = None


DEFAULT_CFG = QwenCFG()


class QwenService(LLM):
    history = []
    tokenizer: object = None
    model: object = None

    @property
    def _llm_type(self) -> str:
        return "Qwen"

    def _stream_call(self,
                     query: str,
                     history=[],
                     system="You are a helpful assistant.",
                     stop_words_ids= None,
                     logits_processor=None,
                     generation_config=None,
                     **kwargs) -> str:
        response = ''
        history = trans_general_history(history) if history is not None else history
        history.append([query, response])
        for response in self.model.chat_stream(self.tokenizer, query, history, system,
                                               stop_words_ids, logits_processor, generation_config,
                                               **kwargs):
            yield response, history
        history[-1][-1] = response
        yield response, history

    def _call(self,
              query,
              history=None,
              max_length=2048,
              top_p=0.7,
              temperature=0.95,
              **kwargs):
        
        gen_kwargs = {"max_length": max_length, "top_p": top_p, "temperature": temperature}
        history = trans_general_history(history) if history is not None else history
        response, history = self.model.chat(self.tokenizer, query, history=history, **gen_kwargs)

        return response, history
    
    def load_model(self, model_args):
        base_cfg = DEFAULT_CFG
        for k, v in model_args.items():
            setattr(base_cfg, k, v)
        model_args = base_cfg
        
        model_path = model_args.llm_name_or_path
        device_map = model_args.device_map
        # Note: The default behavior now has injection attack prevention off.
        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        if model_args.fp16:
            model = AutoModelForCausalLM.from_pretrained(model_path, device_map=device_map, trust_remote_code=True, fp16=True).eval()
        elif model_args.bf16:
            model = AutoModelForCausalLM.from_pretrained(model_path, device_map=device_map, trust_remote_code=True, bf16=True).eval()
        else:
            model = AutoModelForCausalLM.from_pretrained(model_path, device_map=device_map, trust_remote_code=True).eval()

        # Specify hyperparameters for generation
        model.generation_config = GenerationConfig.from_pretrained("Qwen/Qwen-7B-Chat", trust_remote_code=True) # 可指定不同的生成长度、top_p等相关超参

        self.tokenizer = tokenizer
        self.model = model