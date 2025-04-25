# Packaging

## Pypi

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

## Docker Hub

Build the image using the working state to test it

    docker build -t harbor_ls .

Test it, and once it is deemed good, release the image on Docker Hub

    docker tag harbor_ls:latest docker.io/nipil/harbor_ls:latest
    docker push docker.io/nipil/harbor_ls:latest

    docker tag harbor_ls:latest docker.io/nipil/harbor_ls:1.0.3
    docker push docker.io/nipil/harbor_ls:1.0.3
