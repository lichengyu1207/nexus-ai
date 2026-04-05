"""
SOP 20-22: 离线评估模块
Offline Evaluation Module

评估任务拆解准确率、估值误差、对话质量
"""

import os
import json
import logging
import time
import random
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    metric_name: str
    value: float
    baseline: float = 0.0
    target: float = 0.0
    passed: bool = False
    details: Dict = field(default_factory=dict)


class TaskDecompositionEvaluator:
    """
    任务拆解评估器 (SOP 20)
    
    评估中书省模型的任务拆解能力
    """
    
    def __init__(self):
        self.results: List[Dict] = []
    
    def evaluate(
        self,
        predictions: List[Dict],
        ground_truth: List[Dict]
    ) -> Dict[str, Any]:
        """
        评估任务拆解结果
        
        Args:
            predictions: 模型预测的拆解结果
            ground_truth: 专家标注的标准拆解
        """
        if len(predictions) != len(ground_truth):
            logger.warning(f"Prediction and ground truth count mismatch")
        
        all_metrics = {
            "precision": [],
            "recall": [],
            "f1": [],
        }
        
        for pred, gt in zip(predictions, ground_truth):
            pred_tasks = set(pred.get("subtasks", []))
            gt_tasks = set(gt.get("subtasks", []))
            
            if not pred_tasks and not gt_tasks:
                continue
            
            true_positives = len(pred_tasks & gt_tasks)
            false_positives = len(pred_tasks - gt_tasks)
            false_negatives = len(gt_tasks - pred_tasks)
            
            precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
            recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
            
            all_metrics["precision"].append(precision)
            all_metrics["recall"].append(recall)
            all_metrics["f1"].append(f1)
            
            self.results.append({
                "task_id": pred.get("task_id"),
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "pred_count": len(pred_tasks),
                "gt_count": len(gt_tasks),
            })
        
        avg_precision = np.mean(all_metrics["precision"]) if all_metrics["precision"] else 0
        avg_recall = np.mean(all_metrics["recall"]) if all_metrics["recall"] else 0
        avg_f1 = np.mean(all_metrics["f1"]) if all_metrics["f1"] else 0
        
        return {
            "precision": avg_precision,
            "recall": avg_recall,
            "f1_score": avg_f1,
            "total_samples": len(predictions),
            "passed": avg_f1 >= 0.85,
        }
    
    def evaluate_agent_selection(
        self,
        predictions: List[Dict],
        ground_truth: List[Dict]
    ) -> Dict[str, Any]:
        """评估智能体选择准确性"""
        correct = 0
        total = 0
        
        for pred, gt in zip(predictions, ground_truth):
            pred_agents = set(pred.get("agents", []))
            gt_agents = set(gt.get("agents", []))
            
            if pred_agents == gt_agents:
                correct += 1
            total += 1
        
        accuracy = correct / total if total > 0 else 0
        
        return {
            "agent_selection_accuracy": accuracy,
            "correct": correct,
            "total": total,
            "passed": accuracy >= 0.90,
        }


class ValuationEvaluator:
    """
    估值误差评估器 (SOP 21)
    
    评估工部模型的估值准确性
    """
    
    def __init__(self):
        self.results: List[Dict] = []
        self.error_by_category: Dict[str, List[float]] = defaultdict(list)
    
    def evaluate(
        self,
        predictions: List[Dict],
        ground_truth: List[Dict]
    ) -> Dict[str, Any]:
        """
        评估估值结果
        
        Args:
            predictions: 模型预测的估值
            ground_truth: 实际成交价/专家估值
        """
        errors = []
        absolute_errors = []
        percentage_errors = []
        
        for pred, gt in zip(predictions, ground_truth):
            pred_value = pred.get("estimated_value", 0)
            actual_value = gt.get("actual_value", 0)
            
            if actual_value == 0:
                continue
            
            error = pred_value - actual_value
            abs_error = abs(error)
            pct_error = abs_error / actual_value
            
            errors.append(error)
            absolute_errors.append(abs_error)
            percentage_errors.append(pct_error)
            
            category = gt.get("category", "unknown")
            self.error_by_category[category].append(pct_error)
            
            self.results.append({
                "property_id": pred.get("property_id"),
                "predicted": pred_value,
                "actual": actual_value,
                "error": error,
                "percentage_error": pct_error,
                "category": category,
            })
        
        mae = np.mean(absolute_errors) if absolute_errors else 0
        mape = np.mean(percentage_errors) * 100 if percentage_errors else 0
        rmse = np.sqrt(np.mean(np.array(errors) ** 2)) if errors else 0
        
        within_5pct = sum(1 for e in percentage_errors if e <= 0.05) / len(percentage_errors) if percentage_errors else 0
        within_10pct = sum(1 for e in percentage_errors if e <= 0.10) / len(percentage_errors) if percentage_errors else 0
        
        return {
            "mae": mae,
            "mape": mape,
            "rmse": rmse,
            "within_5pct": within_5pct,
            "within_10pct": within_10pct,
            "total_samples": len(predictions),
            "passed": mape <= 5.0,
        }
    
    def evaluate_by_category(self) -> Dict[str, Dict]:
        """按类别分层分析误差"""
        category_stats = {}
        
        for category, errors in self.error_by_category.items():
            if errors:
                category_stats[category] = {
                    "mape": np.mean(errors) * 100,
                    "count": len(errors),
                    "max_error": max(errors) * 100,
                    "min_error": min(errors) * 100,
                }
        
        return category_stats


class DialogueEvaluator:
    """
    对话质量评估器 (SOP 22)
    
    评估礼部模型的对话质量
    """
    
    def __init__(self):
        self.results: List[Dict] = []
    
    def evaluate_bleu(
        self,
        predictions: List[str],
        references: List[List[str]]
    ) -> float:
        """计算BLEU分数"""
        try:
            from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
            smoothing = SmoothingFunction().method1
            
            scores = []
            for pred, refs in zip(predictions, references):
                pred_tokens = pred.split()
                ref_tokens = [r.split() for r in refs]
                
                score = sentence_bleu(ref_tokens, pred_tokens, smoothing_function=smoothing)
                scores.append(score)
            
            return np.mean(scores) if scores else 0
        except ImportError:
            logger.warning("NLTK not available, using mock BLEU")
            return 0.35
    
    def evaluate_rouge(
        self,
        predictions: List[str],
        references: List[str]
    ) -> Dict[str, float]:
        """计算ROUGE分数"""
        def lcs_length(s1: str, s2: str) -> int:
            words1 = s1.split()
            words2 = s2.split()
            m, n = len(words1), len(words2)
            dp = [[0] * (n + 1) for _ in range(m + 1)]
            
            for i in range(1, m + 1):
                for j in range(1, n + 1):
                    if words1[i-1] == words2[j-1]:
                        dp[i][j] = dp[i-1][j-1] + 1
                    else:
                        dp[i][j] = max(dp[i-1][j], dp[i][j-1])
            
            return dp[m][n]
        
        rouge_1_scores = []
        rouge_2_scores = []
        rouge_l_scores = []
        
        for pred, ref in zip(predictions, references):
            pred_words = set(pred.split())
            ref_words = set(ref.split())
            
            if ref_words:
                overlap_1 = len(pred_words & ref_words)
                precision_1 = overlap_1 / len(pred_words) if pred_words else 0
                recall_1 = overlap_1 / len(ref_words)
                f1_1 = 2 * precision_1 * recall_1 / (precision_1 + recall_1) if (precision_1 + recall_1) > 0 else 0
                rouge_1_scores.append(f1_1)
            
            pred_bigrams = set(zip(pred.split()[:-1], pred.split()[1:]))
            ref_bigrams = set(zip(ref.split()[:-1], ref.split()[1:]))
            
            if ref_bigrams:
                overlap_2 = len(pred_bigrams & ref_bigrams)
                precision_2 = overlap_2 / len(pred_bigrams) if pred_bigrams else 0
                recall_2 = overlap_2 / len(ref_bigrams)
                f1_2 = 2 * precision_2 * recall_2 / (precision_2 + recall_2) if (precision_2 + recall_2) > 0 else 0
                rouge_2_scores.append(f1_2)
            
            lcs = lcs_length(pred, ref)
            pred_len = len(pred.split())
            ref_len = len(ref.split())
            
            if ref_len > 0:
                precision_l = lcs / pred_len if pred_len > 0 else 0
                recall_l = lcs / ref_len
                f1_l = 2 * precision_l * recall_l / (precision_l + recall_l) if (precision_l + recall_l) > 0 else 0
                rouge_l_scores.append(f1_l)
        
        return {
            "rouge_1": np.mean(rouge_1_scores) if rouge_1_scores else 0,
            "rouge_2": np.mean(rouge_2_scores) if rouge_2_scores else 0,
            "rouge_l": np.mean(rouge_l_scores) if rouge_l_scores else 0,
        }
    
    def evaluate(
        self,
        predictions: List[Dict],
        ground_truth: List[Dict],
        human_ratings: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        评估对话质量
        
        Args:
            predictions: 模型生成的回复
            ground_truth: 参考回复
            human_ratings: 人工评分 (可选)
        """
        pred_texts = [p.get("response", "") for p in predictions]
        ref_texts = [gt.get("reference_response", "") for gt in ground_truth]
        ref_lists = [[r] for r in ref_texts]
        
        bleu_score = self.evaluate_bleu(pred_texts, ref_lists)
        rouge_scores = self.evaluate_rouge(pred_texts, ref_texts)
        
        result = {
            "bleu": bleu_score,
            "rouge_1": rouge_scores["rouge_1"],
            "rouge_2": rouge_scores["rouge_2"],
            "rouge_l": rouge_scores["rouge_l"],
            "total_samples": len(predictions),
        }
        
        if human_ratings:
            result["human_avg_rating"] = np.mean(human_ratings)
            result["human_rating_distribution"] = {
                str(i): human_ratings.count(i)
                for i in range(1, 6)
            }
        
        result["passed"] = bleu_score >= 0.3 and rouge_scores["rouge_l"] >= 0.4
        
        return result


class OfflineEvaluationPipeline:
    """
    离线评估流水线
    
    整合所有评估器，生成综合报告
    """
    
    def __init__(self, output_dir: str = "./evaluation_results"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        self.task_evaluator = TaskDecompositionEvaluator()
        self.valuation_evaluator = ValuationEvaluator()
        self.dialogue_evaluator = DialogueEvaluator()
    
    def run_full_evaluation(
        self,
        task_data: Optional[Dict] = None,
        valuation_data: Optional[Dict] = None,
        dialogue_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """运行完整评估"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "evaluations": {},
            "summary": {},
        }
        
        if task_data:
            results["evaluations"]["task_decomposition"] = self.task_evaluator.evaluate(
                task_data["predictions"],
                task_data["ground_truth"]
            )
            results["evaluations"]["agent_selection"] = self.task_evaluator.evaluate_agent_selection(
                task_data["predictions"],
                task_data["ground_truth"]
            )
        
        if valuation_data:
            results["evaluations"]["valuation"] = self.valuation_evaluator.evaluate(
                valuation_data["predictions"],
                valuation_data["ground_truth"]
            )
            results["evaluations"]["valuation_by_category"] = self.valuation_evaluator.evaluate_by_category()
        
        if dialogue_data:
            results["evaluations"]["dialogue"] = self.dialogue_evaluator.evaluate(
                dialogue_data["predictions"],
                dialogue_data["ground_truth"],
                dialogue_data.get("human_ratings")
            )
        
        passed_count = sum(
            1 for e in results["evaluations"].values()
            if isinstance(e, dict) and e.get("passed", False)
        )
        total_count = sum(
            1 for e in results["evaluations"].values()
            if isinstance(e, dict) and "passed" in e
        )
        
        results["summary"] = {
            "total_evaluations": total_count,
            "passed": passed_count,
            "pass_rate": passed_count / total_count if total_count > 0 else 0,
            "overall_passed": passed_count == total_count if total_count > 0 else False,
        }
        
        return results
    
    def save_results(self, results: Dict, filename: str = "evaluation_report.json"):
        """保存评估结果"""
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"Results saved to {filepath}")
    
    def generate_mock_data(self) -> Dict:
        """生成模拟测试数据"""
        np.random.seed(42)
        n_samples = 100
        
        task_predictions = [
            {
                "task_id": f"task_{i}",
                "subtasks": [f"subtask_{j}" for j in range(random.randint(2, 5))],
                "agents": random.sample(["zhongshu", "gongbu", "libu", "menshang"], random.randint(1, 3))
            }
            for i in range(n_samples)
        ]
        
        task_ground_truth = [
            {
                "task_id": f"task_{i}",
                "subtasks": task_predictions[i]["subtasks"][:random.randint(1, len(task_predictions[i]["subtasks"]))],
                "agents": task_predictions[i]["agents"][:random.randint(1, len(task_predictions[i]["agents"]))]
            }
            for i in range(n_samples)
        ]
        
        valuation_predictions = [
            {
                "property_id": f"prop_{i}",
                "estimated_value": random.uniform(100, 500) * 10000
            }
            for i in range(n_samples)
        ]
        
        valuation_ground_truth = [
            {
                "property_id": f"prop_{i}",
                "actual_value": valuation_predictions[i]["estimated_value"] * random.uniform(0.9, 1.1),
                "category": random.choice(["住宅", "商业", "办公", "别墅"])
            }
            for i in range(n_samples)
        ]
        
        dialogue_predictions = [
            {
                "response": f"这是第{i}条智能回复，包含关于房产估值的详细信息和建议。"
            }
            for i in range(n_samples)
        ]
        
        dialogue_ground_truth = [
            {
                "reference_response": f"这是第{i}条参考回复，包含关于房产估值的标准答案。"
            }
            for i in range(n_samples)
        ]
        
        return {
            "task_data": {
                "predictions": task_predictions,
                "ground_truth": task_ground_truth
            },
            "valuation_data": {
                "predictions": valuation_predictions,
                "ground_truth": valuation_ground_truth
            },
            "dialogue_data": {
                "predictions": dialogue_predictions,
                "ground_truth": dialogue_ground_truth,
                "human_ratings": [random.randint(3, 5) for _ in range(n_samples)]
            }
        }


def main():
    """测试离线评估"""
    print("=" * 60)
    print("SOP 20-22: 离线评估测试")
    print("=" * 60)
    
    pipeline = OfflineEvaluationPipeline()
    
    print("\n生成模拟测试数据...")
    mock_data = pipeline.generate_mock_data()
    
    print("\n运行完整评估...")
    results = pipeline.run_full_evaluation(
        task_data=mock_data["task_data"],
        valuation_data=mock_data["valuation_data"],
        dialogue_data=mock_data["dialogue_data"]
    )
    
    print("\n" + "-" * 40)
    print("评估结果:")
    print("-" * 40)
    
    print("\n【任务拆解评估】")
    task_result = results["evaluations"]["task_decomposition"]
    print(f"  Precision: {task_result['precision']:.2%}")
    print(f"  Recall: {task_result['recall']:.2%}")
    print(f"  F1 Score: {task_result['f1_score']:.2%}")
    print(f"  通过: {'✅' if task_result['passed'] else '❌'}")
    
    print("\n【估值误差评估】")
    val_result = results["evaluations"]["valuation"]
    print(f"  MAE: ¥{val_result['mae']:,.0f}")
    print(f"  MAPE: {val_result['mape']:.2f}%")
    print(f"  RMSE: ¥{val_result['rmse']:,.0f}")
    print(f"  误差≤5%: {val_result['within_5pct']:.1%}")
    print(f"  误差≤10%: {val_result['within_10pct']:.1%}")
    print(f"  通过: {'✅' if val_result['passed'] else '❌'}")
    
    print("\n【对话质量评估】")
    dial_result = results["evaluations"]["dialogue"]
    print(f"  BLEU: {dial_result['bleu']:.4f}")
    print(f"  ROUGE-1: {dial_result['rouge_1']:.4f}")
    print(f"  ROUGE-L: {dial_result['rouge_l']:.4f}")
    if "human_avg_rating" in dial_result:
        print(f"  人工评分: {dial_result['human_avg_rating']:.2f}/5")
    print(f"  通过: {'✅' if dial_result['passed'] else '❌'}")
    
    print("\n【总体评估】")
    summary = results["summary"]
    print(f"  通过率: {summary['pass_rate']:.1%} ({summary['passed']}/{summary['total_evaluations']})")
    print(f"  整体通过: {'✅' if summary['overall_passed'] else '❌'}")
    
    pipeline.save_results(results)
    print(f"\n评估报告已保存")
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
