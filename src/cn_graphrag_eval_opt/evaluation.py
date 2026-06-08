from __future__ import annotations

from statistics import mean

from cn_graphrag_eval_opt.models import CaseEvaluation, EvaluationResult, PipelineConfig, QACase
from cn_graphrag_eval_opt.retrieval import GraphRAGRetriever
from cn_graphrag_eval_opt.text import term_coverage, tokenize


def evaluate_cases(
    qa_cases: list[QACase],
    retriever: GraphRAGRetriever,
    config: PipelineConfig,
) -> EvaluationResult:
    case_results: list[CaseEvaluation] = []
    for case in qa_cases:
        retrieved = retriever.retrieve(case.question, top_k=config.top_k, mode=config.query_mode)
        contexts = [result.chunk.text for result in retrieved]
        generated_answer = synthesize_answer(case.question, contexts)
        context_text = "\n".join(contexts)
        metrics = {
            "retrieval_recall": _retrieval_recall(case, context_text, [r.chunk.chunk_id for r in retrieved]),
            "context_precision": _context_precision(case, contexts),
            "answer_relevance": _answer_relevance(case.answer, generated_answer),
            "faithfulness": _faithfulness(generated_answer, context_text),
            "estimated_context_chars": float(sum(len(context) for context in contexts)),
            "estimated_token_cost": float(round(sum(len(context) for context in contexts) / 3.2, 2)),
        }
        case_results.append(
            CaseEvaluation(
                question=case.question,
                expected_answer=case.answer,
                generated_answer=generated_answer,
                retrieved_chunk_ids=[result.chunk.chunk_id for result in retrieved],
                metrics=metrics,
            )
        )

    aggregate = _aggregate(case_results)
    return EvaluationResult(cases=case_results, aggregate=aggregate)


def synthesize_answer(question: str, contexts: list[str]) -> str:
    if not contexts:
        return "未检索到足够上下文。"
    question_terms = set(tokenize(question))
    best_sentence = contexts[0]
    best_score = -1
    for context in contexts:
        for sentence in _sentences_for_answer(context):
            score = sum(1 for term in question_terms if term in sentence)
            if score > best_score:
                best_sentence = sentence
                best_score = score
    return best_sentence.strip()


def _retrieval_recall(case: QACase, context_text: str, chunk_ids: list[str]) -> float:
    if case.required_terms:
        return term_coverage(case.required_terms, context_text)
    if case.gold_context_ids:
        matched = sum(1 for chunk_id in case.gold_context_ids if chunk_id in chunk_ids)
        return matched / len(case.gold_context_ids)
    if case.answer:
        return term_coverage(_answer_terms(case.answer), context_text)
    return 0.0


def _context_precision(case: QACase, contexts: list[str]) -> float:
    if not contexts:
        return 0.0
    terms = case.required_terms or _answer_terms(case.answer)
    if not terms:
        return 0.0
    relevant = sum(1 for context in contexts if any(term in context for term in terms))
    return relevant / len(contexts)


def _answer_relevance(expected: str, generated: str) -> float:
    if not expected:
        return 0.0
    expected_terms = set(tokenize(expected))
    generated_terms = set(tokenize(generated))
    if not expected_terms:
        return 0.0
    return len(expected_terms & generated_terms) / len(expected_terms)


def _faithfulness(answer: str, context_text: str) -> float:
    answer_terms = set(tokenize(answer))
    if not answer_terms:
        return 0.0
    faithful_terms = sum(1 for term in answer_terms if term in context_text)
    return faithful_terms / len(answer_terms)


def _aggregate(case_results: list[CaseEvaluation]) -> dict[str, float]:
    if not case_results:
        return {}
    keys = case_results[0].metrics.keys()
    return {key: round(mean(case.metrics[key] for case in case_results), 4) for key in keys}


def _sentences_for_answer(text: str) -> list[str]:
    sentences = []
    current = ""
    for char in text:
        current += char
        if char in "。！？!?；;":
            sentences.append(current)
            current = ""
    if current.strip():
        sentences.append(current)
    return sentences or [text]


def _answer_terms(answer: str) -> list[str]:
    return [term for term in tokenize(answer) if len(term) >= 2][:8]
