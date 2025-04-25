# Packaging

See https://packaging.python.org/en/latest/tutorials/packaging-projects/

Dependencies

    pip install --upgrade build twine

Build distribution package

    python -m build
    
Upload to TestPypi

    python -m twine upload --repository testpypi dist/*

Remove editable installed version

    pip uninstall --yes harbor_ls

Test install

    pip install --index-url https://test.pypi.org/simple/ --no-deps harbor_ls

Upload to (production) Pypi

    python -m twine upload dist/*
