#!/usr/bin/env python3
"""
Spam Detection Benchmark Tool for Ollama Models.

This script tests various Ollama models on a dataset of SPAM and HAM emails,
measures their performance (accuracy, speed, efficiency), and generates
detailed reports in CSV and TXT formats.
"""

import argparse
import datetime
import logging
import os
import sys
import time
from typing import Dict, List, Tuple

import pandas as pd
import requests
# import questionary # Removed interactive dependency

# Configuration
# DEFAULT_MODELS will be fetched dynamically from Ollama if not specified
DEFAULT_MODELS = []
OLLAMA_API_URL = "http://localhost:11434/api/generate"
# OLLAMA_TAGS_URL = "http://localhost:11434/api/tags" # Not needed here anymore
# Store benchmark data in the root benchmark folder
BENCHMARK_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "benchmark",
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Default Test Data
DEFAULT_TEST_EMAILS = [
    # SPAM (10)
    {
        "email_id": 1,
        "category": "SPAM",
        "subject": "You won $1M!",
        "content": "Congratulations! Click here to claim your prize. You have been selected as the winner of our grand lottery.",
    },
    {
        "email_id": 2,
        "category": "SPAM",
        "subject": "Urgent: Update your bank details",
        "content": "Dear customer, your account has been suspended. Please login immediately to verify your identity via this link.",
    },
    {
        "email_id": 3,
        "category": "SPAM",
        "subject": "Buy Viagra Cheap",
        "content": "Best prices for pills. 100% effective. Fast shipping worldwide. No prescription needed.",
    },
    {
        "email_id": 4,
        "category": "SPAM",
        "subject": "Investment Opportunity: Crypto",
        "content": "Double your Bitcoin in 24 hours! Guaranteed returns. Join our exclusive mining pool now.",
    },
    {
        "email_id": 5,
        "category": "SPAM",
        "subject": "Invoice #12345 overdue",
        "content": "Attached is your invoice for services rendered. Please pay immediately to avoid legal action. Open the zip file.",
    },
    {
        "email_id": 6,
        "category": "SPAM",
        "subject": "Package delivery failed",
        "content": "We could not deliver your parcel. Please pay the customs fee of $2.99 to reschedule delivery.",
    },
    {
        "email_id": 7,
        "category": "SPAM",
        "subject": "Business Proposal from Prince",
        "content": "I am a prince from Nigeria. I need your help to transfer $50M. You will keep 10%.",
    },
    {
        "email_id": 8,
        "category": "SPAM",
        "subject": "Your computer is infected",
        "content": "We detected a virus on your PC. Call Microsoft Support immediately at this number to fix it.",
    },
    {
        "email_id": 9,
        "category": "SPAM",
        "subject": "Lose weight fast!",
        "content": "New miracle diet pill. Lose 10kg in a week without exercise. Order now for a free trial.",
    },
    {
        "email_id": 10,
        "category": "SPAM",
        "subject": "Hot singles in your area",
        "content": "Lonely women want to meet you. Sign up for free dating site. Chat now.",
    },
    # HAM (10)
    {
        "email_id": 11,
        "category": "HAM",
        "subject": "Team Meeting",
        "content": "Hi team, meeting tomorrow at 10am in conference room B to discuss the Q4 roadmap.",
    },
    {
        "email_id": 12,
        "category": "HAM",
        "subject": "Project Update",
        "content": "Here is the latest status report. We are on track for the deadline. Let me know if you have questions.",
    },
    {
        "email_id": 13,
        "category": "HAM",
        "subject": "Lunch?",
        "content": "Hey, do you want to grab some lunch later? Maybe that new Italian place?",
    },
    {
        "email_id": 14,
        "category": "HAM",
        "subject": "Order Confirmation",
        "content": "Thank you for your purchase. Your order #998877 has been received and will ship soon.",
    },
    {
        "email_id": 15,
        "category": "HAM",
        "subject": "Flight Itinerary",
        "content": "Your flight to Berlin is confirmed. Departure: Dec 20, 14:00. Seat: 12A.",
    },
    {
        "email_id": 16,
        "category": "HAM",
        "subject": "Support Ticket #5566",
        "content": "We have received your request. A support agent will review it shortly. Ticket ID: 5566.",
    },
    {
        "email_id": 17,
        "category": "HAM",
        "subject": "Happy Birthday!",
        "content": "Wishing you a fantastic birthday! Hope you have a great day with friends and family.",
    },
    {
        "email_id": 18,
        "category": "HAM",
        "subject": "Invitation: Wedding",
        "content": "You are cordially invited to the wedding of John and Jane. RSVP by next Friday.",
    },
    {
        "email_id": 19,
        "category": "HAM",
        "subject": "Newsletter: Tech Trends",
        "content": "This week in tech: AI advancements, new gadgets, and software updates. Read the full article.",
    },
    {
        "email_id": 20,
        "category": "HAM",
        "subject": "Re: Question about report",
        "content": "Yes, the numbers look correct. I double-checked the spreadsheet. Good job.",
    },
    # SPAM (Hard/Tricky)
    {
        "email_id": 21,
        "category": "SPAM",
        "subject": "Re: Invoice 2024-001",
        "content": "Please find attached the updated invoice as discussed. Let me know if you have any questions. (Attachment: invoice.zip)",
    },
    {
        "email_id": 22,
        "category": "SPAM",
        "subject": "Security Alert: New login from unknown device",
        "content": "We detected a login to your account from Russia. If this wasn't you, please secure your account immediately by clicking here.",
    },
    {
        "email_id": 23,
        "category": "SPAM",
        "subject": "HR: Annual Employee Survey",
        "content": "All employees are required to complete the annual satisfaction survey. Please log in with your domain credentials to participate.",
    },
    {
        "email_id": 24,
        "category": "SPAM",
        "subject": "Your shipment is on hold",
        "content": "DHL: Your package is pending delivery. Address verification required. Please confirm your details to avoid return to sender.",
    },
    {
        "email_id": 25,
        "category": "SPAM",
        "subject": "Partnership Opportunity",
        "content": "Hi, I came across your website and I think our SEO services would be a great fit. We can boost your traffic by 200%. Let's chat.",
    },
    # HAM (Hard/Tricky)
    {
        "email_id": 26,
        "category": "HAM",
        "subject": "Reset your password",
        "content": "You requested a password reset for your account. Click the link below to set a new password. If you didn't request this, ignore this email.",
    },
    {
        "email_id": 27,
        "category": "HAM",
        "subject": "Weekly Newsletter: 50% Off Sale",
        "content": "Don't miss our summer sale! 50% off all items. Shop now. Unsubscribe here.",
    },
    {
        "email_id": 28,
        "category": "HAM",
        "subject": "URGENT: Production Server Down",
        "content": "The main database server is not responding. CPU usage at 100%. Please investigate immediately. This is a critical alert.",
    },
    {
        "email_id": 29,
        "category": "HAM",
        "subject": "Application for Developer Position",
        "content": "Dear Hiring Manager, I would like to apply for the Python Developer role. Attached is my CV. I look forward to hearing from you.",
    },
    {
        "email_id": 30,
        "category": "HAM",
        "subject": "Reminder: Invoice #9988 due tomorrow",
        "content": "Hi, just a friendly reminder that invoice #9988 is due tomorrow. Please let me know if payment has been scheduled. Thanks!",
    },
]

# get_ollama_models removed from here, use model_selector.py if needed externally


def ensure_benchmark_dir(output_dir: str):
    """Ensures the benchmark directory exists."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)


def load_test_emails(filepath: str) -> pd.DataFrame:
    """
    Loads test emails from a CSV file. If the file doesn't exist,
    creates it with default data.
    """
    if not os.path.exists(filepath):
        logger.info(f"Creating default test dataset at {filepath}...")
        df = pd.DataFrame(DEFAULT_TEST_EMAILS)
        df.to_csv(filepath, index=False)
        return df

    logger.info(f"Loading test emails from {filepath}...")
    return pd.read_csv(filepath)


def call_ollama(
    model: str, subject: str, content: str, use_thinking: bool = False
) -> Tuple[str, float, int, str]:
    """
    Calls the Ollama API to classify an email.
    Returns: (prediction, response_time_ms, total_tokens, confidence)
    """
    prompt = (
        f"Klassifiziere diese E-Mail als SPAM oder HAM. "
        f"Antworte NUR mit 'SPAM' oder 'HAM' und einer kurzen Begründung (max 15 Wörter).\n\n"
        f"Betreff: {subject}\n\nInhalt: {content}"
    )

    # Adjust parameters based on thinking mode
    # Thinking models need room to think. Standard models should be concise.
    # We limit standard models to 150 tokens to prevent verbosity (like Ministral's 600+ tokens)
    # while ensuring enough space for the classification and short justification.
    num_predict = 2000 if use_thinking else 150
    timeout = 300 if use_thinking else 120

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": num_predict},
    }

    # Optimization for Ministral: Use a lightweight system prompt to reduce input tokens
    # (The default system prompt is ~600 tokens long due to tool definitions)
    if "ministral" in model.lower():
        payload["system"] = (
            f"You are an intelligent Spam Detection System. "
            f"Analyze the email content and metadata critically. "
            f"Legitimate emails (HAM) can come from unknown senders. "
            f"Only mark as SPAM if there are clear indicators like phishing, scams, unsolicited offers, or malicious content. "
            f"The current date is {datetime.datetime.now().strftime('%Y-%m-%d')}."
        )

    # Only add 'think' parameter if explicitly requested (to enable/disable)
    # If use_thinking is True, we don't set 'think': False.
    # If use_thinking is False, we set 'think': False to suppress it on reasoning models.
    if not use_thinking:
        payload["think"] = False

    start_time = time.time()
    try:
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        end_time = time.time()

        response_time_ms = (end_time - start_time) * 1000
        response_text = data.get("response", "").strip()
        total_tokens = data.get("eval_count", 0) + data.get("prompt_eval_count", 0)

        # Check if model ran out of context
        if data.get("done_reason") == "length":
            logger.warning(
                f"Model {model} hit token limit (num_predict). Response might be incomplete."
            )

        # Extract prediction
        prediction = "UNKNOWN"
        if "SPAM" in response_text.upper():
            prediction = "SPAM"
        elif "HAM" in response_text.upper():
            prediction = "HAM"

        # Simple confidence estimation (placeholder as Ollama doesn't give confidence score directly in this mode easily)
        confidence = "high"  # Placeholder

        return prediction, response_time_ms, total_tokens, confidence

    except requests.exceptions.Timeout:
        return "TIMEOUT", -1, 0, "none"
    except requests.exceptions.ConnectionError:
        return "ERROR", -1, 0, "none"
    except Exception as e:
        logger.error(f"Error calling Ollama: {e}")
        return "ERROR", -1, 0, "none"


def test_model(
    model: str, emails: pd.DataFrame, use_thinking: bool = False
) -> List[Dict]:
    """
    Tests a single model against the dataframe of emails.
    """
    results = []
    total = len(emails)
    correct_count = 0

    # Progress bar simulation
    sys.stdout.write(f"Testing {model} (Thinking: {use_thinking})... [")
    sys.stdout.flush()

    for i, row in emails.iterrows():
        prediction, duration, tokens, confidence = call_ollama(
            model, row["subject"], row["content"], use_thinking
        )

        is_correct = prediction == row["category"]
        if is_correct:
            correct_count += 1

        result = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "model": model,
            "email_id": row["email_id"],
            "expected": row["category"],
            "predicted": prediction,
            "correct": is_correct,
            "response_time_ms": round(duration, 2),
            "response_tokens": tokens,
            "confidence": confidence,
        }
        results.append(result)

        # Update progress bar
        progress = int((i + 1) / total * 20)
        sys.stdout.write(
            "\r"
            + f"Testing {model} (Thinking: {use_thinking})... [{'█' * progress}{' ' * (20 - progress)}] {i + 1}/{total}"
        )
        sys.stdout.flush()

    accuracy = (correct_count / total) * 100
    sys.stdout.write(f" ({accuracy:.1f}% accuracy)\n")

    return results


def calculate_score(model_results: pd.DataFrame, total_emails: int) -> Dict:
    """
    Calculates the aggregated score for a model.
    """
    # Filter out errors/timeouts for average calculation
    valid_results = model_results[model_results["response_time_ms"] > 0]

    correct = model_results["correct"].sum()
    accuracy_pct = (correct / total_emails) * 100

    avg_response_ms = (
        valid_results["response_time_ms"].mean() if not valid_results.empty else 0
    )
    total_tokens = model_results["response_tokens"].sum()

    # Calculate TPS (Tokens Per Second)
    # Sum of all tokens / Sum of all durations (in seconds)
    total_duration_sec = valid_results["response_time_ms"].sum() / 1000
    avg_tps = (total_tokens / total_duration_sec) if total_duration_sec > 0 else 0

    false_positives = len(
        model_results[
            (model_results["expected"] == "HAM")
            & (model_results["predicted"] == "SPAM")
        ]
    )
    false_negatives = len(
        model_results[
            (model_results["expected"] == "SPAM")
            & (model_results["predicted"] == "HAM")
        ]
    )

    # Score Calculation (Weighted Model - Adjusted for Spam Filter priorities)
    # Priority: Accuracy is King. Speed is secondary for background tasks.

    # 1. Accuracy (90% weight)
    #    - 100% accuracy = 90 points
    accuracy_score = accuracy_pct * 0.9

    # 2. Speed/TPS (10% weight)
    #    - Target: 100 TPS = 10 points (capped)
    #    - Formula: (TPS / 100) * 10
    speed_score = min(10, (avg_tps / 100) * 10)

    final_score = accuracy_score + speed_score

    return {
        "model": model_results["model"].iloc[0],
        "total_emails": total_emails,
        "correct": correct,
        "accuracy_pct": round(accuracy_pct, 2),
        "avg_response_ms": round(avg_response_ms, 2),
        "avg_tps": round(avg_tps, 2),
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "total_tokens": total_tokens,
        "score": round(final_score, 2),
    }


def assign_badges(df: pd.DataFrame) -> pd.DataFrame:
    """
    Assigns badges (Rating) to models based on their performance relative to others.
    Badges:
    - 🏆 Allround-Bester (Highest Score)
    - 🎯 Präzisions-Bester (Highest Accuracy)
    - ⚡ Geschwindigkeits-Bester (Highest TPS with Accuracy >= 80%)
    """
    if df.empty:
        return df

    # Initialize rating column
    df["rating"] = ""

    # Use a dictionary to collect badges per index to ensure clean formatting
    badge_map = {idx: [] for idx in df.index}

    # 1. Allround-Bester (Highest Score)
    best_score_idx = df["score"].idxmax()
    badge_map[best_score_idx].append("🏆Allround")

    # 2. Präzisions-Bester (Highest Accuracy)
    best_acc_idx = df.sort_values(
        by=["accuracy_pct", "score"], ascending=[False, False]
    ).index[0]
    badge_map[best_acc_idx].append("🎯Präzision")

    # 3. Geschwindigkeits-Bester (Highest TPS with Acc >= 80%)
    # Ensure avg_tps is numeric
    df["avg_tps"] = pd.to_numeric(df["avg_tps"], errors="coerce").fillna(0)

    decent_models = df[df["accuracy_pct"] >= 80.0]
    if not decent_models.empty:
        best_speed_idx = decent_models["avg_tps"].idxmax()
        badge_map[best_speed_idx].append("⚡Speed")

    # Join badges with a single space
    for idx, badges in badge_map.items():
        df.at[idx, "rating"] = " ".join(badges)

    return df


def generate_recommendation(scores_df: pd.DataFrame, output_path: str):
    """
    Generates the recommendation text file with detailed insights.
    """
    if scores_df.empty:
        return

    # Sort by Score (Weighted) for the main list
    scores_df = scores_df.sort_values(by="score", ascending=False).reset_index(
        drop=True
    )

    # Assign badges dynamically (now called rating)
    scores_df = assign_badges(scores_df)

    best_overall = scores_df.iloc[0]

    with open(output_path, "w") as f:
        f.write("=== SPAM DETECTION BENCHMARK RESULTS ===\n")
        f.write(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Test Emails: {best_overall['total_emails']}\n\n")

        # --- 1. THE VERDICT ---
        f.write(f"🏆 OVERALL WINNER: {best_overall['model']}\n")
        f.write(f"   Rating:   {best_overall['rating']}\n")
        f.write(f"   Score:    {best_overall['score']}/100\n")
        f.write(f"   Accuracy: {best_overall['accuracy_pct']}%\n")
        f.write(
            f"   Speed:    {best_overall['avg_response_ms'] / 1000:.2f}s per mail ({best_overall['avg_tps']:.1f} tps)\n"
        )
        f.write("\n")

        # --- 2. DETAILED LEADERBOARD ---
        f.write("📊 LEADERBOARD (Sorted by Weighted Score):\n")
        # Header
        header = f"{'Rank':<4} | {'Model':<25} | {'Score':<6} | {'Acc %':<6} | {'TPS':<6} | {'Rating'}"
        f.write(header + "\n")
        f.write("-" * 80 + "\n")

        for i, row in scores_df.iterrows():
            rank = f"#{i + 1}"
            rating = row["rating"].strip()
            f.write(
                f"{rank:<4} | {row['model']:<25} | {row['score']:<6} | {row['accuracy_pct']:<6} | {row['avg_tps']:<6.1f} | {rating}\n"
            )

        f.write("\n")
        f.write("ℹ️  Rating Key:\n")
        f.write("    🏆 Allround: Highest Weighted Score\n")
        f.write("    🎯 Präzision: Highest Accuracy\n")
        f.write("    ⚡ Speed: Highest TPS (with >80% Accuracy)\n")


def check_reasoning_support(model: str) -> bool:
    """
    Checks if the model supports reasoning (thinking) by sending a probe request.
    """
    print(f"   Checking reasoning support for {model}...", end="", flush=True)
    payload = {
        "model": model,
        "prompt": "Hi",
        "stream": False,
        "options": {"num_predict": 10},
    }
    try:
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            has_thinking = "thinking" in data and data["thinking"]
            print(f" {'YES' if has_thinking else 'NO'}")
            return has_thinking
    except Exception:
        pass
    print(" NO (Error/Timeout)")
    return False


def main():
    parser = argparse.ArgumentParser(description="Spam Detection Benchmark Tool")
    parser.add_argument("--model", help="Test only a specific model")
    parser.add_argument(
        "--quick", action="store_true", help="Run a quick test with only 5 emails"
    )
    parser.add_argument("--input", help="Path to custom test emails CSV")
    parser.add_argument("--output", default=BENCHMARK_DIR, help="Output directory")
    args = parser.parse_args()

    ensure_benchmark_dir(args.output)

    print("🔍 Spam Detection Benchmark")
    print("============================")

    # Load Data
    input_file = (
        args.input if args.input else os.path.join(args.output, "test_emails.csv")
    )
    emails_df = load_test_emails(input_file)

    if args.quick:
        emails_df = emails_df.head(5)
        print(f"Loading test emails... ✓ {len(emails_df)} emails loaded (Quick Mode)")
    else:
        print(f"Loading test emails... ✓ {len(emails_df)} emails loaded")

    # Determine models to test
    if args.model:
        models_to_test = [args.model]
    else:
        print("⚠️  No model specified.")
        print("   Please use --model <name> to specify a model.")
        print("   Or run 'python start_benchmark.py' for interactive selection.")
        return

    all_detailed_results = []
    model_scores = []

    print("")

    for model in models_to_test:
        # Determine test configurations based on reasoning support
        test_configs = []

        if check_reasoning_support(model):
            test_configs.append({"thinking": True, "label": f"{model} (Thinking:on)"})
            test_configs.append({"thinking": False, "label": f"{model} (Thinking:off)"})
        else:
            test_configs.append({"thinking": False, "label": model})

        for config in test_configs:
            display_model_name = config["label"]
            use_thinking = config["thinking"]

            model_results = test_model(model, emails_df, use_thinking)

            # Update model name in results
            for res in model_results:
                res["model"] = display_model_name

            all_detailed_results.extend(model_results)

            # Calculate score for this model configuration
            df_results = pd.DataFrame(model_results)
            score_data = calculate_score(df_results, len(emails_df))
            model_scores.append(score_data)

    # Save Detailed Results (Append mode logic could be complex for detailed results,
    # but user asked specifically for model_scores.csv persistence.
    # For detailed results, we might want to keep them per run or append.
    # Let's append to detailed_results.csv as well for consistency)
    detailed_csv_path = os.path.join(args.output, "detailed_results.csv")
    new_detailed_df = pd.DataFrame(all_detailed_results)

    if os.path.exists(detailed_csv_path):
        existing_detailed = pd.read_csv(detailed_csv_path)
        # Remove old entries for the tested models to avoid duplicates if re-testing
        # We need to filter by the display names now
        tested_labels = [res["model"] for res in all_detailed_results]
        existing_detailed = existing_detailed[
            ~existing_detailed["model"].isin(tested_labels)
        ]
        final_detailed_df = pd.concat(
            [existing_detailed, new_detailed_df], ignore_index=True
        )
    else:
        final_detailed_df = new_detailed_df

    final_detailed_df.to_csv(detailed_csv_path, index=False)

    # Save Model Scores (Persistent Leaderboard)
    scores_csv_path = os.path.join(args.output, "model_scores.csv")
    new_scores_df = pd.DataFrame(model_scores)

    if os.path.exists(scores_csv_path):
        existing_scores = pd.read_csv(scores_csv_path)
        # Remove old entries for the tested models (overwrite logic)
        tested_labels = [score["model"] for score in model_scores]
        existing_scores = existing_scores[~existing_scores["model"].isin(tested_labels)]
        final_scores_df = pd.concat([existing_scores, new_scores_df], ignore_index=True)
    else:
        final_scores_df = new_scores_df

    # Clean up columns: Remove 'stars' if present, reset 'rating'
    if "stars" in final_scores_df.columns:
        final_scores_df = final_scores_df.drop(columns=["stars"])
    if "badges" in final_scores_df.columns:
        final_scores_df = final_scores_df.drop(columns=["badges"])
    if "rating" in final_scores_df.columns:
        final_scores_df = final_scores_df.drop(columns=["rating"])

    # Recalculate badges for the entire leaderboard
    final_scores_df = assign_badges(final_scores_df)

    # Sort by Score (descending)
    final_scores_df = final_scores_df.sort_values(
        by="score", ascending=False
    ).reset_index(drop=True)
    final_scores_df.to_csv(scores_csv_path, index=False)

    # Generate Recommendation based on the FULL leaderboard
    rec_path = os.path.join(args.output, "recommendation.txt")
    generate_recommendation(final_scores_df, rec_path)

    # Create Log file (empty for now, just to satisfy requirement of existence or maybe copy stdout?)
    # The requirement says "benchmark_YYYYMMDD_HHMMSS.log # Timestamped Log-Datei"
    # I'll just write a simple log summary there.
    log_filename = f"benchmark_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    log_path = os.path.join(args.output, log_filename)
    with open(log_path, "w") as f:
        f.write(f"Benchmark run at {datetime.datetime.now()}\n")
        f.write(f"Models tested: {', '.join(models_to_test)}\n")
        f.write(f"Total emails: {len(emails_df)}\n")
        f.write("Results saved to CSV files.\n")

    print(f"\n✅ Results saved to {args.output}/")

    # Console Output Summary
    if not final_scores_df.empty:
        top_model = final_scores_df.iloc[0]

        print(f"\n🏆 Winner: {top_model['model']}")
        print(f"   Rating: {top_model['rating']}")
        print(f"   Score:  {top_model['score']} | Acc: {top_model['accuracy_pct']}%")
        print(
            f"   Speed:  {top_model['avg_response_ms'] / 1000:.2f}s per mail ({top_model['avg_tps']:.1f} tps)"
        )

        # Check for Speed King alternative (already covered by badges, but explicit mention is nice)
        if "⚡ Speed" not in top_model["rating"]:
            # Find who has the speed badge
            speed_winners = final_scores_df[
                final_scores_df["rating"].str.contains("⚡ Speed", na=False)
            ]
            if not speed_winners.empty:
                speed_king = speed_winners.iloc[0]
                print(f"\n⚡ Speed Alternative: {speed_king['model']}")
                print(
                    f"   {speed_king['avg_tps']:.0f} TPS (vs {top_model['avg_tps']:.0f}) | {speed_king['accuracy_pct']}% Acc"
                )


if __name__ == "__main__":
    main()
