import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cn_graphrag_eval_opt.fusion import reciprocal_rank_fusion
from cn_graphrag_eval_opt.graph import GraphIndex
from cn_graphrag_eval_opt.models import Chunk
from cn_graphrag_eval_opt.retrieval import GraphRAGRetriever


class RankFusionTest(unittest.TestCase):
    def test_reciprocal_rank_fusion_combines_ranked_signals(self):
        fused = reciprocal_rank_fusion(
            {
                "lexical": ["c1", "c2", "c3"],
                "graph": ["c2", "c4"],
                "dense": ["c3", "c2"],
            },
            k=60,
        )

        self.assertEqual(fused[0].item_id, "c2")
        self.assertEqual(
            {contribution.signal for contribution in fused[0].signals},
            {"lexical", "graph", "dense"},
        )
        self.assertGreater(fused[0].score, fused[1].score)

    def test_retriever_mix_mode_exposes_fusion_trace(self):
        chunks = [
            Chunk(
                chunk_id="c1",
                doc_id="policy",
                title="Security policy",
                source="memory",
                text="Security audit requires access review and account approval.",
            ),
            Chunk(
                chunk_id="c2",
                doc_id="ops",
                title="Operations",
                source="memory",
                text="Finance invoice approval follows a monthly operations checklist.",
            ),
        ]
        retriever = GraphRAGRetriever(GraphIndex.from_chunks(chunks))

        results = retriever.retrieve("security audit access", top_k=1, mode="mix")

        self.assertEqual(results[0].chunk.chunk_id, "c1")
        self.assertTrue(any(item.startswith("lexical:rank=") for item in results[0].evidence))
        self.assertTrue(any(item.startswith("dense:rank=") for item in results[0].evidence))


if __name__ == "__main__":
    unittest.main()
