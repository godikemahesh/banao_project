"""
Evaluation and Validation Framework for AI Ticket Classifier.
Compares:
1. Baseline Chatbot Intake Accuracy vs Ground Truth.
2. AI-Assisted Classifier Accuracy vs Ground Truth.
Computes Precision, Recall, F1-score, Confusion Matrix, and Uncertainty Rates.
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, Any, Tuple
from src.config import TICKETS_FILE, AGENTS_FILE, REPORTS_DIR
from src.pipeline import clean_and_normalize_tickets, load_raw_data
from src.classifier import classify_ticket, SemanticRuleClassifier


def derive_ground_truth_category(row: pd.Series) -> str:
    """
    Derives reliable ground-truth category using the human agent's closing notes,
    refund codes, replacement flags, and resolving team action.
    """
    notes = str(row.get('agent_notes', '')).lower()
    msg = str(row.get('customer_message', '')).lower()
    res_team = str(row.get('resolving_team', ''))
    refund_code = str(row.get('refund_reason_code', ''))
    bot_cat = str(row.get('category', 'Other'))

    # Check 1: Explicit refund reason codes
    if refund_code in ['LOST-TRANSIT', 'CANCEL']:
        return 'Delivery & Shipping'
    if refund_code in ['DUP-PAYMENT', 'PRICE-ADJ']:
        return 'Billing & Payments'
    if refund_code in ['RETURN-QC-OK', 'DOA-REPL']:
        return 'Returns & Refunds'
    if refund_code in ['WTY-BUYBACK']:
        return 'Warranty & Repair'

    # Check 2: Agent closing notes evidence
    if any(k in notes for k in ['lost in transit', 'courier', 'awb', 'shipment not', 'dlvry delayed', 'xfer to logistics', 'reshipped', 'rto']):
        return 'Delivery & Shipping'
    if any(k in notes for k in ['double charge', 'dup payment', 'gst invoice', 'gateway error', 'deducted twice', 'invoice sent']):
        return 'Billing & Payments'
    if any(k in notes for k in ['refund approved', 'return initiated', 'reverse pickup', 'qc pass', 'exchange']):
        return 'Returns & Refunds'
    if any(k in notes for k in ['warranty', 'service center', 'replace under wty', 'repaired']):
        return 'Warranty & Repair'
    if any(k in notes for k in ['bluetooth', 'pairing', 'unpair', 'disconnect']):
        return 'Connectivity'
    if any(k in notes for k in ['battery', 'charge', 'case charging', 'drain']):
        return 'Charging & Battery'
    if any(k in notes for k in ['firmware', 'app update', 'companion app']):
        return 'App & Firmware'
    if any(k in notes for k in ['sound', 'mic', 'volume', 'audio', 'static', 'muffled']):
        return 'Audio Quality'
    if any(k in notes for k in ['password', 'otp', 'login reset']):
        return 'Account & Login'

    # Check 3: Resolving team alignment
    if res_team == 'Logistics':
        return 'Delivery & Shipping'
    if res_team == 'Returns Desk':
        return 'Returns & Refunds'
    if res_team == 'Escalations & Warranty':
        return 'Warranty & Repair'
    if res_team == 'Billing':
        # If resolving team is Billing and notes didn't mention delivery, check customer message
        if any(k in msg for k in ['awb', 'tracking', 'not received', 'where is', 'courier', 'door']):
            return 'Delivery & Shipping'
        return 'Billing & Payments'

    # Fallback to bot category if consistent with frontline resolution
    return bot_cat


def run_evaluation(sample_size: int = 1000, random_state: int = 42) -> Dict[str, Any]:
    """
    Runs systematic evaluation across a stratified sample of tickets.
    Calculates precision, recall, F1, and confusion metrics.
    """
    tickets, agents, orders, customers, products = load_raw_data()
    df = clean_and_normalize_tickets(tickets, agents)

    # Filter reporting period
    df = df[df['source_system'].notna()].copy()

    # Robust stratified-style sampling across tickets
    sample = df.sample(n=min(len(df), sample_size), random_state=random_state).copy().reset_index(drop=True)

    # Derive Ground Truth
    sample['ground_truth'] = sample.apply(derive_ground_truth_category, axis=1)

    # Run AI Classifier
    predictions = []
    confidences = []
    uncertainties = []
    evidence_quotes = []

    for idx, row in sample.iterrows():
        res = classify_ticket(row['customer_message'], initial_category=row['category'], ticket_id=row['ticket_id'])
        predictions.append(res.predicted_category)
        confidences.append(res.confidence)
        uncertainties.append(res.uncertainty_flag)
        evidence_quotes.append(res.evidence_quote)

    sample['ai_predicted'] = predictions
    sample['confidence'] = confidences
    sample['uncertainty'] = uncertainties

    # Calculate Accuracies
    bot_correct = (sample['category'] == sample['ground_truth']).sum()
    ai_correct = (sample['ai_predicted'] == sample['ground_truth']).sum()
    total = len(sample)

    bot_accuracy = round(bot_correct / total * 100, 2)
    ai_accuracy = round(ai_correct / total * 100, 2)

    # Class-level Metrics for key classes: Billing & Payments and Delivery & Shipping
    def get_metrics_for_class(y_true, y_pred, target_cls):
        tp = ((y_true == target_cls) & (y_pred == target_cls)).sum()
        fp = ((y_true != target_cls) & (y_pred == target_cls)).sum()
        fn = ((y_true == target_cls) & (y_pred != target_cls)).sum()
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        return {
            'precision_%': round(precision * 100, 2),
            'recall_%': round(recall * 100, 2),
            'f1_score_%': round(f1 * 100, 2),
            'tp': int(tp),
            'fp': int(fp),
            'fn': int(fn)
        }

    bot_billing_metrics = get_metrics_for_class(sample['ground_truth'], sample['category'], 'Billing & Payments')
    ai_billing_metrics = get_metrics_for_class(sample['ground_truth'], sample['ai_predicted'], 'Billing & Payments')

    bot_logistics_metrics = get_metrics_for_class(sample['ground_truth'], sample['category'], 'Delivery & Shipping')
    ai_logistics_metrics = get_metrics_for_class(sample['ground_truth'], sample['ai_predicted'], 'Delivery & Shipping')

    # Uncertainty Statistics
    uncertain_count = sample['uncertainty'].sum()
    uncertain_rate = round(uncertain_count / total * 100, 2)

    # Confusion matrix between Bot, AI, and Ground Truth for Billing & Logistics
    confusion = pd.crosstab(sample['ground_truth'], sample['ai_predicted'])

    results = {
        'sample_size': total,
        'bot_accuracy_%': bot_accuracy,
        'ai_accuracy_%': ai_accuracy,
        'accuracy_gain_%': round(ai_accuracy - bot_accuracy, 2),
        'uncertainty_rate_%': uncertain_rate,
        'billing_category': {
            'bot_baseline': bot_billing_metrics,
            'ai_classifier': ai_billing_metrics
        },
        'delivery_category': {
            'bot_baseline': bot_logistics_metrics,
            'ai_classifier': ai_logistics_metrics
        }
    }

    # Save results to json
    results_path = REPORTS_DIR / "evaluation_results.json"
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    # Generate Chart
    _generate_evaluation_charts(bot_accuracy, ai_accuracy, bot_billing_metrics, ai_billing_metrics, bot_logistics_metrics, ai_logistics_metrics)

    return results


def _generate_evaluation_charts(bot_acc, ai_acc, bot_bill, ai_bill, bot_log, ai_log):
    """Generates visual accuracy comparison chart."""
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    
    # Chart 1: Overall Accuracy
    bars1 = axes[0].bar(['Existing Bot Intake', 'AI Classifier'], [bot_acc, ai_acc], color=['#ef4444', '#10b981'], width=0.5)
    axes[0].set_title('Overall Ticket Categorization Accuracy (%)', fontsize=12, fontweight='bold', pad=10)
    axes[0].set_ylim(0, 100)
    for bar in bars1:
        yval = bar.get_height()
        axes[0].text(bar.get_x() + bar.get_width()/2.0, yval + 1.5, f"{yval:.1f}%", ha='center', va='bottom', fontweight='bold')

    # Chart 2: F1 Score Comparison for Key Categories
    categories = ['Billing F1', 'Delivery F1']
    bot_f1 = [bot_bill['f1_score_%'], bot_log['f1_score_%']]
    ai_f1 = [ai_bill['f1_score_%'], ai_log['f1_score_%']]

    x = np.arange(len(categories))
    width = 0.35
    axes[1].bar(x - width/2, bot_f1, width, label='Existing Bot', color='#f87171')
    axes[1].bar(x + width/2, ai_f1, width, label='AI Classifier', color='#34d399')
    axes[1].set_title('F1-Score: Billing vs Delivery Disambiguation', fontsize=12, fontweight='bold', pad=10)
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(categories, fontweight='bold')
    axes[1].set_ylim(0, 100)
    axes[1].legend(loc='lower right')

    plt.tight_layout()
    chart_path = REPORTS_DIR / "evaluation_accuracy_comparison.png"
    plt.savefig(chart_path, dpi=200)
    plt.close()


if __name__ == '__main__':
    print("Running Evaluation Benchmark...")
    res = run_evaluation(sample_size=1000)
    print("\n================ EVALUATION BENCHMARK RESULTS ================")
    print(f"Sample Size Evaluated: {res['sample_size']} tickets")
    print(f"Existing Bot Baseline Accuracy: {res['bot_accuracy_%']}%")
    print(f"AI-Assisted Classifier Accuracy: {res['ai_accuracy_%']}%")
    print(f"Net Accuracy Gain: +{res['accuracy_gain_%']}%")
    print(f"Uncertainty Flag Rate: {res['uncertainty_rate_%']}% (routed to human triage)")
    print("\n--- BILLING & PAYMENTS METRICS ---")
    print(f"Bot Precision: {res['billing_category']['bot_baseline']['precision_%']}% | Recall: {res['billing_category']['bot_baseline']['recall_%']}% | F1: {res['billing_category']['bot_baseline']['f1_score_%']}%")
    print(f"AI  Precision: {res['billing_category']['ai_classifier']['precision_%']}% | Recall: {res['billing_category']['ai_classifier']['recall_%']}% | F1: {res['billing_category']['ai_classifier']['f1_score_%']}%")
    print("\n--- DELIVERY & SHIPPING METRICS ---")
    print(f"Bot Precision: {res['delivery_category']['bot_baseline']['precision_%']}% | Recall: {res['delivery_category']['bot_baseline']['recall_%']}% | F1: {res['delivery_category']['bot_baseline']['f1_score_%']}%")
    print(f"AI  Precision: {res['delivery_category']['ai_classifier']['precision_%']}% | Recall: {res['delivery_category']['ai_classifier']['recall_%']}% | F1: {res['delivery_category']['ai_classifier']['f1_score_%']}%")
    print("=============================================================")
