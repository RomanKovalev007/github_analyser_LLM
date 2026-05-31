import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from agent.agent import run_agent
from eval.cases import TEST_CASES


async def run_single(repo_url: str, question: str, keywords: list[str]) -> dict:
    try:
        answer = await run_agent(repo_url, question)
        answer_lower = answer.lower()
        hits = [kw for kw in keywords if kw.lower() in answer_lower]
        passed = len(hits) == len(keywords)
        return {"passed": passed, "hits": hits, "missing": list(set(keywords) - set(hits)), "answer": answer[:300]}
    except Exception as e:
        return {"passed": False, "error": str(e)}


async def main():
    results = []
    for i, (repo_url, question, keywords) in enumerate(TEST_CASES, 1):
        print(f"[{i}/{len(TEST_CASES)}] {question[:60]}...")
        result = await run_single(repo_url, question, keywords)
        result.update({"repo": repo_url, "question": question, "expected": keywords})
        results.append(result)
        status = "✅" if result["passed"] else "❌"
        print(f"  {status} hits={result.get('hits')} missing={result.get('missing')}")

    passed = sum(1 for r in results if r["passed"])
    print(f"\nResult: {passed}/{len(results)} passed ({100*passed//len(results)}%)")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"eval/results_{timestamp}.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Saved to eval/results_{timestamp}.json")


if __name__ == "__main__":
    asyncio.run(main())
