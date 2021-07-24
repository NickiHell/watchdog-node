import random

import torch
from transformers import (
    GPT2LMHeadModel,
    GPT2Tokenizer,
    T5ForConditionalGeneration,
    T5Tokenizer,
)


def sberbank_small_gpt3(text: str, model_name, max_length=64) -> str:
    def load_tokenizer_and_model(model_name_or_path):
        return GPT2Tokenizer.from_pretrained(model_name_or_path), GPT2LMHeadModel.from_pretrained(
            model_name_or_path)

    def generate(
        model, tok, text,
        do_sample=True, max_length=50, repetition_penalty=5.0,
        top_k=5, top_p=0.95, temperature=1,
        num_beams=None,
        no_repeat_ngram_size=3
    ):
        input_ids = tok.encode(text, return_tensors="pt")
        out = model.generate(
            input_ids,
            max_length=max_length,
            repetition_penalty=repetition_penalty,
            do_sample=do_sample,
            top_k=top_k, top_p=top_p, temperature=temperature,
            num_beams=num_beams, no_repeat_ngram_size=no_repeat_ngram_size
        )
        return list(map(tok.decode, out))

    tok, model = load_tokenizer_and_model(model_name)
    generated: str = generate(model, tok, text, max_length=max_length, num_beams=random.randint(5, 10))[0]
    end = generated.replace(text, '').rfind('.')
    return generated.strip()[:end+1] if end else generated.strip()


# def generate_sber(text: str, model_name):
#     model_name_or_path = model_name
#     tokenizer = GPT2Tokenizer.from_pretrained(model_name_or_path)
#     model = GPT2LMHeadModel.from_pretrained(model_name_or_path)
#     input_ids = tokenizer.encode(text, return_tensors="pt")
#     out = model.generate(input_ids)
#     generated_text = list(map(tokenizer.decode, out))[0]
#     return generated_text


def generate_rut5_base_multitask(text, **kwargs):
    tokenizer = T5Tokenizer.from_pretrained("cointegrated/rut5-base-multitask")
    model = T5ForConditionalGeneration.from_pretrained("cointegrated/rut5-base-multitask")
    inputs = tokenizer(text, return_tensors='pt')
    with torch.no_grad():
        hypotheses = model.generate(**inputs, num_beams=10, **kwargs)
    return tokenizer.decode(hypotheses[0], skip_special_tokens=True)
