.PHONY: test test-signal test-rebalance

test: test-signal test-rebalance

test-signal:
	@echo "=== Test: momentum signal ==="
	python rebalance.py signal
	@echo ""

test-rebalance:
	@echo "=== Test: switch from IEMA to SPYL ==="
	python rebalance.py rebalance --target SPYL --target-price 67.50 --cash 1200 --holding IEMA:120:185.50
	@echo "=== Test: fresh start, cash only ==="
	python rebalance.py rebalance --target SPYL --target-price 67.50 --cash 50000
	@echo "=== Test: already in target, extra cash ==="
	python rebalance.py rebalance --target SPYL --cash 4500 --holding SPYL:350:67.50
	@echo "=== Test: already in target, no extra cash ==="
	python rebalance.py rebalance --target SPYL --cash 100 --holding SPYL:350:67.50
	@echo "=== Test: multiple holdings, switch to bonds ==="
	python rebalance.py rebalance --target ETFBTBSP --target-price 228.60 --cash 500 --holding SPYL:350:67.50 --holding ETFBCASH:10:145.00
	@echo "=== Test: missing target-price error ==="
	python rebalance.py rebalance --target ETFBCASH --cash 1000 2>&1; test $$? -eq 1 && echo "  -> Correctly exited with error"
