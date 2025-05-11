# Makefile
clean-cache:
	@echo "Удаление кеш-папок ..."
	@sudo find . -type d -name "__pycache__" -exec rm -rf {} +
	@echo "... успешно."