.PHONY: install
install:
	pip install '.[test]'

.PHONY: install-e
install-e:
	pip install -e '.[test]'

.PHONY: pre-commit
pre-commit:
	pre-commit run --all-files --show-diff-on-failure

.PHONY: pre-commit-update
pre-commit-update:
	pre-commit autoupdate

.PHONY: cog
cog:
	cog -r README.md

.PHONY: cog-check
cog-check:
	cog --check README.md

.PHONY: test
test:
	pytest
