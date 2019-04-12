
# BEGIN-EVAL makefile-parser --make-help Makefile

help:
	@echo ""
	@echo "  Targets"
	@echo ""
	@echo "    start-worker-train  Start a training worker"
	@echo "    start-worker-eval   Start an evaluation worker"
	@echo "    start-server        Start redis server"
	@echo ""
	@echo "  Variables"
	@echo ""

# END-EVAL

# Start a training worker
start-worker-train:
	rq worker ocr-tasks

# Start an evaluation worker
start-worker-eval:
	rq worker ocr-evals

# Start redis server
start-server:
	python ocrd.py
