import argparse
import sys

# Ensure environment variables (including HF_HOME and HF_TOKEN) are loaded FIRST
from src.utils.security import load_secure_key

from src.core.ingester import Ingester
from src.core.querier import Querier
from src.utils.logger import setup_logger

logger = setup_logger("cli")

def main():
    parser = argparse.ArgumentParser(description="Async Pedagogy Insight Engine CLI")
    parser.add_argument("action", choices=["ingest", "query"], help="Action to perform: ingest data or run queries.")
    parser.add_argument("--model", choices=["qwen", "google"], required=True, help="Which embedding model to use (qwen or google).")
    
    args = parser.parse_args()

    try:
        if args.action == "ingest":
            logger.info(f"Starting ingestion using model: {args.model}")
            ingester = Ingester(model_type=args.model)
            ingester.run()
        elif args.action == "query":
            logger.info(f"Starting queries using model: {args.model}")
            querier = Querier(model_type=args.model)
            querier.run_all()
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
